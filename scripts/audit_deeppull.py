import csv
from collections import Counter
from pathlib import Path

path = Path("datasets/external/deeppull/python.csv")

with path.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)

print("=" * 72)
print("DEEP PULL PYTHON DATASET AUDIT")
print("=" * 72)
print()

print("Columns:", len(header))
print()

duplicates = [
    column
    for column, count in Counter(header).items()
    if count > 1
]

print("Duplicate column names:")
for column in duplicates:
    print("  ", repr(column))

print()

print("Columns:")
for i, column in enumerate(header, start=1):
    print(f"{i:3}: {column}")

print()

rows = 0
missing = Counter()
reopening = Counter()
decision = Counter()
dates = []

with path.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        rows += 1

        for key, value in row.items():
            if value is None or value == "":
                missing[key] += 1

        reopening[row.get("reopening", "")] += 1
        decision[row.get("decision", "")] += 1

        created = row.get("created_at", "")
        if created:
            dates.append(created)

print("Rows:", rows)

print()
print("Reopening values:")
for key, value in reopening.items():
    print(f"  {key!r}: {value}")

print()
print("Decision values:")
for key, value in decision.items():
    print(f"  {key!r}: {value}")

print()

if dates:
    print("Created-at range:")
    print("  first:", min(dates))
    print("  last: ", max(dates))

print()
print("Missing-value counts:")
for key, value in missing.most_common():
    if value:
        print(f"  {key}: {value}")

print()
print("Potential project/repository columns:")
for column in header:
    lowered = column.lower()
    if any(term in lowered for term in [
        "project",
        "repo",
        "repository",
        "owner",
        "name"
    ]):
        print("  ", column)

print()
print("=" * 72)
print("AUDIT COMPLETE")
print("=" * 72)
