from pathlib import Path
import json
import sqlite3

import pandas as pd

from intentinsight.application.workbench import PullRequestAnalysisService, ResearchArtifactStore


SCHEMA = """
CREATE TABLE repositories (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL);
CREATE TABLE research_records (repository_id INTEGER, pull_request_number INTEGER, eligible INTEGER);
CREATE TABLE pull_requests (
    id INTEGER PRIMARY KEY, repository_id INTEGER, number INTEGER, title TEXT, description TEXT,
    author TEXT, state TEXT, created_at TEXT, updated_at TEXT, merged_at TEXT, merge_commit_sha TEXT,
    base_sha TEXT, head_sha TEXT, commits_count INTEGER, changed_files_count INTEGER, additions INTEGER, deletions INTEGER
);
CREATE TABLE pull_request_intents (
    repository_id INTEGER, pull_request_number INTEGER, combined_text TEXT, model_name TEXT, embedding_dimension INTEGER
);
CREATE TABLE pull_request_structures (
    repository_id INTEGER, pull_request_number INTEGER, structural_text TEXT, model_name TEXT, module_count INTEGER, module_profile_json TEXT
);
CREATE TABLE intent_impact_divergence (
    repository_id INTEGER, pull_request_number INTEGER, intent_impact_divergence REAL, intent_similarity REAL,
    module_entropy REAL, module_concentration REAL, top_module_weight REAL, package_count INTEGER, cross_package_spread INTEGER, module_count INTEGER
);
CREATE TABLE pull_request_files (repository_id INTEGER, pull_request_number INTEGER, filename TEXT, status TEXT, additions INTEGER, deletions INTEGER, changes INTEGER);
"""


def test_store_exposes_resolved_root(tmp_path: Path) -> None:
    store = ResearchArtifactStore(tmp_path)
    assert store.root == tmp_path.resolve()


def test_explorer_search_can_filter_divergence(tmp_path: Path) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    connection.execute("INSERT INTO repositories VALUES (1, 'org/repo')")
    connection.execute("INSERT INTO research_records VALUES (1, 1, 1)")
    connection.execute("INSERT INTO research_records VALUES (1, 2, 1)")
    connection.execute("INSERT INTO pull_requests VALUES (1,1,1,'Low','d','a','closed','c','u','m','s','b','h',1,1,1,1)")
    connection.execute("INSERT INTO pull_requests VALUES (2,1,2,'High','d','a','closed','c','u','m','s','b','h',1,1,1,1)")
    connection.execute("INSERT INTO intent_impact_divergence VALUES (1,1,.2,.8,.1,.9,.9,1,0,1)")
    connection.execute("INSERT INTO intent_impact_divergence VALUES (1,2,.8,.2,.1,.9,.9,1,0,2)")
    connection.commit()

    class Artifacts(ResearchArtifactStore):
        def load_rework_analysis(self):
            return pd.DataFrame([
                {"repository_id": 1, "pull_request_number": 1, "rework_90d": 0},
                {"repository_id": 1, "pull_request_number": 2, "rework_90d": 1},
            ])

    frame = PullRequestAnalysisService(connection, Artifacts(tmp_path)).search(min_divergence=.7, max_divergence=1.0)
    assert list(frame["number"]) == [2]
