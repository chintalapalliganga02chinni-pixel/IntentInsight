import sqlite3


connection = sqlite3.connect("intentinsight.db")
connection.row_factory = sqlite3.Row

missing = connection.execute(
    """
    SELECT
        pr.id,
        pr.number,
        pr.title,
        pr.merged_at,
        pr.merge_commit_sha
    FROM pull_requests AS pr
    LEFT JOIN research_records AS rr
        ON rr.repository_id = pr.repository_id
        AND rr.pull_request_number = pr.number
    WHERE pr.merged_at IS NOT NULL
      AND rr.id IS NULL
    ORDER BY pr.number
    """
).fetchall()

print("Missing research records:", len(missing))

for row in missing:
    print(
        f"PR #{row['number']} | "
        f"title={row['title']!r} | "
        f"merged_at={row['merged_at']} | "
        f"merge_commit_sha={row['merge_commit_sha']}"
    )

connection.close()