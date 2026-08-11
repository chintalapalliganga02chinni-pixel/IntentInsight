"""Utilities for deriving reproducible module identities from file paths."""

from __future__ import annotations

from pathlib import PurePosixPath


def normalize_filename(filename: str) -> str:
    """Normalize repository-relative file paths."""

    value = filename.strip().replace("\\", "/")

    while value.startswith("./"):
        value = value[2:]

    return value.strip("/")


def filename_to_module(filename: str) -> str:
    """
    Convert a repository-relative path into a structural module identity.

    Python package examples:

        flask/app.py
            -> flask.app

        flask/__init__.py
            -> flask

        flask/testsuite/testing.py
            -> flask.testsuite.testing

    Non-Python files retain a path-derived identity:

        docs/views.rst
            -> docs.views

        pyproject.toml
            -> pyproject
    """

    normalized = normalize_filename(filename)

    if not normalized:
        return "<unknown>"

    path = PurePosixPath(normalized)
    parts = list(path.parts)

    if not parts:
        return "<unknown>"

    filename_part = parts[-1]

    if filename_part == "__init__.py":
        module_parts = parts[:-1]
    else:
        stem = filename_part.rsplit(".", 1)[0]
        module_parts = parts[:-1] + [stem]

    module_parts = [
        part
        for part in module_parts
        if part and part not in {".", ".."}
    ]

    if not module_parts:
        return "<root>"

    return ".".join(module_parts)