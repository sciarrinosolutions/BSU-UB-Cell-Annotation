"""Rank screened papers by relevance, recency and citation impact.

Reads screened_papers.csv (output of apply_screening.py) and writes
ranked_papers.csv with a score and rank for every paper. No paper is dropped.
The scoring is described in ../SKILLS.md ("Ranking"). The input is not
modified, and the script refuses to overwrite an existing output file.

By default citation counts come from Europe PMC (the cited_by column). Pass
--citations citations_openalex.csv to use OpenAlex counts instead (see
fetch_openalex_citations.py), with --out to choose the output file.

Usage:
    python rank_papers.py
    python rank_papers.py --citations citations_openalex.csv --out ranked_papers_openalex.csv
"""

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
IN = HERE / "screened_papers.csv"
OUT = HERE / "ranked_papers.csv"

WEIGHTS = {"relevance": 0.50, "recency": 0.25, "citations": 0.25}
RELEVANCE = {"preferred": 1.0, "caution": 0.6, "later": 0.3, "exclude": 0.0}
RECENCY_YEARS = 10  # recency falls to 0 at this age
RECENT_YEARS = 5  # papers this new or newer are flagged "recent"
UNKNOWN_CITATIONS = 0.5


def percentiles(values: list[float]) -> list[float]:
    """Percentile rank (0-1) of each value; ties share the average rank."""
    order = sorted(values)
    n = len(order)
    if n < 2:
        return [0.5] * n
    out = []
    for v in values:
        below = sum(x < v for x in order)
        equal = sum(x == v for x in order)
        out.append((below + (equal - 1) / 2) / (n - 1))
    return out


def load_citations(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as f:
        return {r["doi"].lower(): r["openalex_cited_by"] for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--citations", type=Path, help="CSV of OpenAlex counts by DOI")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    out = args.out if args.out.is_absolute() else HERE / args.out
    if out.exists():
        sys.exit(f"{out.name} already exists; move or rename it first.")

    with IN.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    if args.citations:
        path = args.citations if args.citations.is_absolute() else HERE / args.citations
        counts = load_citations(path)
        source = "OpenAlex"
    else:
        counts = {r["doi"].lower(): r["cited_by"] for r in rows}
        source = "Europe PMC"

    this_year = date.today().year
    for r in rows:
        age = max(this_year - int(r["year"]), 0)
        r["_recency"] = max(0.0, 1 - age / RECENCY_YEARS)
        r["_recent"] = age < RECENT_YEARS
        r["_cites"] = counts.get(r["doi"].lower(), "")
        r["_cpy"] = float(r["_cites"]) / (age + 1) if r["_cites"] != "" else None

    known = [r for r in rows if r["_cpy"] is not None]
    for r, p in zip(known, percentiles([r["_cpy"] for r in known])):
        r["_cite"] = p
    for r in rows:
        r.setdefault("_cite", UNKNOWN_CITATIONS)
        r["_score"] = (
            WEIGHTS["relevance"] * RELEVANCE[r["relevance"]]
            + WEIGHTS["recency"] * r["_recency"]
            + WEIGHTS["citations"] * r["_cite"]
        )

    rows.sort(
        key=lambda r: (r["_score"], r["markers_defined"] == "yes", int(r["year"])),
        reverse=True,
    )

    new = [
        "rank", "score", "recency_score", "citation_source", "citations_used",
        "citations_per_year", "citation_score", "flags",
    ]
    with out.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=new + fields)
        w.writeheader()
        for i, r in enumerate(rows, 1):
            flags = []
            if r["_recent"]:
                flags.append("recent")
            if r["_cpy"] is None:
                flags.append("citations unknown")
            w.writerow({
                "rank": i,
                "score": f"{r['_score']:.3f}",
                "recency_score": f"{r['_recency']:.2f}",
                "citation_source": source,
                "citations_used": r["_cites"],
                "citations_per_year": "" if r["_cpy"] is None else f"{r['_cpy']:.1f}",
                "citation_score": f"{r['_cite']:.2f}",
                "flags": "; ".join(flags),
                **{k: r[k] for k in fields},
            })
    print(f"Ranked {len(rows)} papers using {source} citations -> {out.name}")


if __name__ == "__main__":
    main()
