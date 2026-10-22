"""Literature sweep for scRNA-seq cell type annotation papers via the Europe PMC REST API.

Runs a set of topic queries, keeps only freely readable records (open-access PMC
articles or preprints), and writes the de-duplicated candidates to
candidates_raw.csv for manual curation.

Usage:
    python search_europepmc.py
"""

import csv
import time
from pathlib import Path

import requests

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
OUT = Path(__file__).parent / "candidates_raw.csv"
PAGE_SIZE = 100
MAX_PER_QUERY = 200

# Topic -> Europe PMC query. Each query is restricted to free full text
# (open access) or preprints in a single request.
FREE = "(OPEN_ACCESS:y OR SRC:PPR)"
SC = '("single-cell" OR "single cell" OR scRNA-seq OR scRNAseq)'
QUERIES = {
    "marker_database": f'{SC} AND ("marker database" OR "cell marker" OR "marker gene database") AND (TITLE:marker OR TITLE:database)',
    "annotation_method": f'{SC} AND TITLE:("cell type annotation" OR "cell-type annotation" OR "cell type identification" OR "cell identity" OR "automatic annotation" OR "automated annotation")',
    "benchmark": f'{SC} AND TITLE:(benchmark* OR comparison OR evaluation) AND ("cell type" OR annotation OR classification)',
    "llm_agent": f'{SC} AND ("large language model" OR GPT OR LLM OR "language model" OR agent* OR agentic) AND ("cell type" OR annotation)',
    "foundation_model": f'{SC} AND TITLE:("foundation model" OR transformer OR pretrained OR "pre-trained") AND ("cell type" OR annotation)',
    "reference_atlas_immune": f'{SC} AND TITLE:(atlas OR reference) AND (immune OR PBMC OR "blood")',
    "monocyte": f'{SC} AND TITLE:(monocyte* OR "dendritic cell*" OR "mononuclear phagocyte*" OR myeloid)',
    "t_cell": f'{SC} AND TITLE:("T cell*" OR "T-cell*" OR "T lymphocyte*") AND (atlas OR exhaust* OR "reference" OR states OR landscape)',
    "tumor_microenvironment": f'{SC} AND TITLE:("tumor microenvironment" OR "tumour microenvironment" OR "pan-cancer" OR "tumor-infiltrating" OR "tumour-infiltrating") AND (immune OR myeloid OR "T cell")',
}

FIELDS = [
    "topic", "pmid", "pmcid", "doi", "title", "authors", "journal", "year",
    "source", "is_open_access", "license", "cited_by", "has_suppl", "url",
]


def search(query: str):
    cursor = "*"
    fetched = 0
    while fetched < MAX_PER_QUERY:
        params = {
            "query": f"({query}) AND {FREE}",
            "format": "json",
            "resultType": "core",
            "pageSize": PAGE_SIZE,
            "cursorMark": cursor,
            "sort": "CITED desc",
        }
        r = requests.get(API, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        results = data.get("resultList", {}).get("result", [])
        if not results:
            break
        yield from results
        fetched += len(results)
        next_cursor = data.get("nextCursorMark")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(0.3)


def to_row(topic: str, rec: dict) -> dict:
    pmcid = rec.get("pmcid", "")
    doi = rec.get("doi", "")
    if pmcid:
        url = f"https://europepmc.org/article/PMC/{pmcid}"
    elif doi:
        url = f"https://doi.org/{doi}"
    else:
        url = f"https://europepmc.org/article/{rec.get('source', '')}/{rec.get('id', '')}"
    return {
        "topic": topic,
        "pmid": rec.get("pmid", ""),
        "pmcid": pmcid,
        "doi": doi,
        "title": rec.get("title", "").strip(),
        "authors": rec.get("authorString", ""),
        "journal": rec.get("journalInfo", {}).get("journal", {}).get("title", "")
        or rec.get("bookOrReportDetails", {}).get("publisher", ""),
        "year": rec.get("pubYear", ""),
        "source": rec.get("source", ""),
        "is_open_access": rec.get("isOpenAccess", ""),
        "license": rec.get("license", ""),
        "cited_by": rec.get("citedByCount", 0),
        "has_suppl": rec.get("hasSuppl", ""),
        "url": url,
    }


def main():
    rows: dict[str, dict] = {}
    for topic, query in QUERIES.items():
        n = 0
        for rec in search(query):
            row = to_row(topic, rec)
            key = (row["doi"] or row["pmid"] or row["title"]).lower()
            if key in rows:
                if topic not in rows[key]["topic"].split(";"):
                    rows[key]["topic"] += f";{topic}"
                continue
            rows[key] = row
            n += 1
        print(f"{topic}: {n} new records")

    ordered = sorted(rows.values(), key=lambda r: int(r["cited_by"] or 0), reverse=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(ordered)
    print(f"Wrote {len(ordered)} records to {OUT}")


if __name__ == "__main__":
    main()
