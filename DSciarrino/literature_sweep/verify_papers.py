"""Verify each paper in seed_papers.csv against Europe PMC.

For every title, finds the best-matching Europe PMC record(s), and reports
identifiers plus whether a free full text exists. A paper can have several
records (journal article + preprint), so all close matches are checked and the
best free version is kept.

Writes verified_papers.csv.

Usage:
    python verify_papers.py
"""

import csv
import re
import time
from difflib import SequenceMatcher
from pathlib import Path

import requests

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ARXIV_API = "http://export.arxiv.org/api/query"
HERE = Path(__file__).parent
SEED = HERE / "seed_papers.csv"
OUT = HERE / "verified_papers.csv"
MIN_SIMILARITY = 0.85

FIELDS = [
    "priority", "category", "focus", "title", "first_author", "journal", "year", "pmid",
    "pmcid", "doi", "free_access", "access_route", "license", "cited_by",
    "has_suppl", "free_url", "match_score", "why",
]


def norm(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def query_records(title: str):
    words = norm(title).split()
    # Title-word query is more forgiving of punctuation than an exact phrase.
    q = " AND ".join(f"TITLE:{w}" for w in words if len(w) > 2)
    r = requests.get(
        API,
        params={"query": q, "format": "json", "resultType": "core", "pageSize": 25},
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("resultList", {}).get("result", [])


def free_url(rec: dict):
    """Return (route, url) for the best free full text, or ("", "")."""
    if rec.get("pmcid") and rec.get("inEPMC") == "Y":
        route = "PMC open access" if rec.get("isOpenAccess") == "Y" else "PMC free"
        return route, f"https://europepmc.org/article/PMC/{rec['pmcid']}"
    for u in rec.get("fullTextUrlList", {}).get("fullTextUrl", []):
        if u.get("availabilityCode") in ("OA", "F"):
            route = "preprint" if rec.get("source") == "PPR" else "publisher free"
            return route, u.get("url", "")
    if rec.get("source") == "PPR":
        doi = rec.get("doi", "")
        return "preprint", f"https://doi.org/{doi}" if doi else ""
    return "", ""


def first_author(rec: dict) -> str:
    authors = rec.get("authorList", {}).get("author", [])
    if authors:
        a = authors[0]
        return a.get("lastName") or a.get("collectiveName") or a.get("fullName", "")
    return (rec.get("authorString") or "").split(",")[0]


def verify_arxiv(seed: dict) -> dict:
    """arXiv is not indexed by Europe PMC; look the paper up by arXiv id."""
    arxiv_id = seed["arxiv_id"]
    r = requests.get(ARXIV_API, params={"id_list": arxiv_id}, timeout=60)
    r.raise_for_status()
    entry = re.search(r"<entry>(.*?)</entry>", r.text, re.S)
    row = {k: seed.get(k, "") for k in ("priority", "category", "focus", "title", "why")}
    if not entry:
        row.update(free_access="NOT FOUND", match_score=0)
        return row
    e = entry.group(1)
    title = " ".join(re.search(r"<title>(.*?)</title>", e, re.S).group(1).split())
    author = re.search(r"<name>(.*?)</name>", e)
    doi = re.search(r"<arxiv:doi[^>]*>(.*?)</arxiv:doi>", e)
    row.update(
        title=title,
        first_author=author.group(1).split()[-1] if author else "",
        journal="arXiv preprint",
        year=re.search(r"<published>(\d{4})", e).group(1),
        doi=doi.group(1) if doi else f"10.48550/arXiv.{arxiv_id}",
        free_access="yes",
        access_route="arXiv",
        license="see arXiv abstract page",
        free_url=f"https://arxiv.org/abs/{arxiv_id}",
        match_score=round(SequenceMatcher(None, norm(seed["title"]), norm(title)).ratio(), 3),
    )
    return row


def verify(seed: dict) -> dict:
    if seed.get("arxiv_id"):
        return verify_arxiv(seed)
    target = norm(seed["title"])
    matches = []
    for rec in query_records(seed["title"]):
        score = SequenceMatcher(None, target, norm(rec.get("title", ""))).ratio()
        if score >= MIN_SIMILARITY:
            matches.append((score, rec))

    row = {k: seed.get(k, "") for k in ("priority", "category", "focus", "title", "why")}
    if not matches:
        row.update(free_access="NOT FOUND", match_score=0)
        return row

    # Prefer the peer-reviewed record for metadata, then any free version.
    matches.sort(key=lambda m: (m[1].get("source") != "PPR", m[0]), reverse=True)
    score, main = matches[0]
    route, url, lic, suppl = "", "", main.get("license", ""), main.get("hasSuppl", "")
    for _, rec in matches:
        route, url = free_url(rec)
        if url:
            lic = rec.get("license", "") or lic
            suppl = rec.get("hasSuppl", "") or suppl
            break

    row.update(
        title=re.sub(r"<[^>]+>", "", main.get("title", "")).strip(),
        first_author=first_author(main),
        journal=main.get("journalInfo", {}).get("journal", {}).get("title", "")
        or ("bioRxiv/medRxiv/arXiv preprint" if main.get("source") == "PPR" else ""),
        year=main.get("pubYear", ""),
        pmid=main.get("pmid", ""),
        pmcid=main.get("pmcid", ""),
        doi=main.get("doi", ""),
        free_access="yes" if url else "no",
        access_route=route,
        license=lic,
        cited_by=max(int(r.get("citedByCount", 0) or 0) for _, r in matches),
        has_suppl=suppl,
        free_url=url,
        match_score=round(score, 3),
    )
    return row


def main():
    with SEED.open(encoding="utf-8") as f:
        seeds = list(csv.DictReader(f))
    rows = []
    for s in seeds:
        row = verify(s)
        print(f"{row['free_access']:>9} {row.get('access_route', ''):16} {s['title'][:80]}")
        rows.append(row)
        time.sleep(0.3)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    found = sum(r["free_access"] != "NOT FOUND" for r in rows)
    free = sum(r["free_access"] == "yes" for r in rows)
    print(f"\n{len(rows)} seeds, {found} found, {free} with free full text -> {OUT}")


if __name__ == "__main__":
    main()
