"""Join the SKILLS.md screening decisions onto the verified paper list.

Reads verified_papers.csv and screening_decisions.csv (relevance, rule, reason,
markers_defined per paper, decided using ../SKILLS.md) and writes
screened_papers.csv. Neither input is modified, and the script refuses to
overwrite an existing output file.

Usage:
    python apply_screening.py
"""

import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent
PAPERS = HERE / "verified_papers.csv"
DECISIONS = HERE / "screening_decisions.csv"
OUT = HERE / "screened_papers.csv"
NEW_FIELDS = ["relevance", "rule", "reason", "markers_defined"]
ORDER = {"preferred": 0, "caution": 1, "later": 2, "exclude": 3}


def key(row: dict) -> str:
    return (row["doi"] or row["title"]).strip().lower()


def main():
    if OUT.exists():
        sys.exit(f"{OUT.name} already exists; move or rename it first.")

    with PAPERS.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        papers = list(reader)
    with DECISIONS.open(encoding="utf-8") as f:
        decisions = {key(d): d for d in csv.DictReader(f)}

    missing = [p["title"] for p in papers if key(p) not in decisions]
    if missing:
        sys.exit("No screening decision for:\n  " + "\n  ".join(missing))

    rows = []
    for p in papers:
        d = decisions[key(p)]
        rows.append({**p, **{k: d[k] for k in NEW_FIELDS}})
    rows.sort(key=lambda r: (ORDER[r["relevance"]], r["category"], r["title"]))

    with OUT.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=NEW_FIELDS + fields)
        w.writeheader()
        w.writerows(rows)

    counts = {k: sum(r["relevance"] == k for r in rows) for k in ORDER}
    print(f"Wrote {len(rows)} papers to {OUT.name}: {counts}")


if __name__ == "__main__":
    main()
