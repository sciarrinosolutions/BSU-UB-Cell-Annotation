"""Fetch citation counts from OpenAlex for every paper in screened_papers.csv.

Europe PMC undercounts citations for preprints and CS-venue papers, and has
none for arXiv. OpenAlex covers both and usually merges preprint and journal
versions of a paper. Papers are looked up by DOI.

Writes citations_openalex.csv. The input is not modified, and the script
refuses to overwrite an existing output file.

Usage:
    python fetch_openalex_citations.py
"""

import csv
import sys
import time
from datetime import date
from pathlib import Path

import requests

HERE = Path(__file__).parent
IN = HERE / "screened_papers.csv"
OUT = HERE / "citations_openalex.csv"
API = "https://api.openalex.org/works/doi:{}"
HEADERS = {"User-Agent": "BSU-UB-Cell-Annotation literature sweep"}
FIELDS = ["doi", "title", "openalex_id", "openalex_cited_by", "retrieved"]


def lookup(doi: str):
    for attempt in range(3):
        r = requests.get(API.format(doi), headers=HEADERS, timeout=30)
        if r.status_code == 429:
            time.sleep(2 ** attempt * 5)
            continue
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"OpenAlex rate limit persisted for {doi}")


def main():
    if OUT.exists():
        sys.exit(f"{OUT.name} already exists; move or rename it first.")

    with IN.open(encoding="utf-8") as f:
        papers = list(csv.DictReader(f))

    today = date.today().isoformat()
    rows = []
    for p in papers:
        work = lookup(p["doi"])
        rows.append({
            "doi": p["doi"],
            "title": p["title"],
            "openalex_id": work["id"] if work else "",
            "openalex_cited_by": work["cited_by_count"] if work else "",
            "retrieved": today,
        })
        print(f"{rows[-1]['openalex_cited_by'] if work else 'NOT FOUND':>9}  {p['title'][:80]}")
        time.sleep(0.2)

    with OUT.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    found = sum(bool(r["openalex_id"]) for r in rows)
    print(f"\n{found}/{len(rows)} found in OpenAlex -> {OUT.name}")


if __name__ == "__main__":
    main()
