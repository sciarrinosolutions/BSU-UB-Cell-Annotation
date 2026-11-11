"""Rank the papers and merge in the agent's ingestion records.

Ranking follows ../../SKILLS.md in two layers:
  1. Tier: the relevance label (preferred > caution > later > exclude).
  2. Within a tier: 0.5 x recency + 0.5 x citation impact, where citation impact
     is the percentile of OpenAlex citations per year across all papers.

Inputs:  ../literature_sweep/screened_papers.csv, citations_openalex.csv,
         ingested/*.json (validated against the schema)
Output:  web/data/papers.json (regenerated on every run)

Citation-by-year histories for ingested papers are fetched from OpenAlex once
and cached in cache/openalex_history.json; pass --offline to skip fetching.

Usage:
    python pipeline/build_index.py
    python pipeline/build_index.py --pending 10   # list the next papers to ingest
"""

import argparse
import csv
import json
import sys
from datetime import date

import jsonschema
import requests

from common import (
    CACHE, CITATIONS, HEADERS, INGESTED, SCREENED, STAGES, WEB_DATA, load_schema, paper_id,
)
from vocab import Vocabulary

TIERS = ["preferred", "caution", "later", "exclude"]
TIER_LABELS = {
    "preferred": "Preferred",
    "caution": "Use with caution",
    "later": "Later (refinement)",
    "exclude": "Out of scope",
}
RECENCY_YEARS = 10
RECENT_YEARS = 5
HISTORY_CACHE = CACHE / "openalex_history.json"


def percentiles(values):
    order = sorted(values)
    n = len(order)
    if n < 2:
        return [0.5] * n
    return [
        (sum(x < v for x in order) + (sum(x == v for x in order) - 1) / 2) / (n - 1)
        for v in values
    ]


def load_papers():
    with SCREENED.open(encoding="utf-8") as f:
        papers = list(csv.DictReader(f))
    with CITATIONS.open(encoding="utf-8") as f:
        cites = {r["doi"].lower(): r for r in csv.DictReader(f)}

    this_year = date.today().year
    for p in papers:
        p["id"] = paper_id(p["doi"])
        c = cites.get(p["doi"].lower(), {})
        p["citations"] = int(c["openalex_cited_by"]) if c.get("openalex_cited_by") else None
        p["openalex_id"] = c.get("openalex_id", "")
        p["citations_retrieved"] = c.get("retrieved", "")
        age = max(this_year - int(p["year"]), 0)
        p["recency"] = max(0.0, 1 - age / RECENCY_YEARS)
        p["recent"] = age < RECENT_YEARS
        p["cpy"] = p["citations"] / (age + 1) if p["citations"] is not None else None

    known = [p for p in papers if p["cpy"] is not None]
    for p, pct in zip(known, percentiles([p["cpy"] for p in known])):
        p["citation_score"] = pct
    for p in papers:
        p.setdefault("citation_score", 0.5)
        p["within_tier_score"] = 0.5 * p["recency"] + 0.5 * p["citation_score"]

    papers.sort(key=lambda p: (
        TIERS.index(p["relevance"]),
        -p["within_tier_score"],
        p["markers_defined"] != "yes",
        -int(p["year"]),
    ))
    tier_counts = {}
    for i, p in enumerate(papers, 1):
        p["rank"] = i
        tier_counts[p["relevance"]] = tier_counts.get(p["relevance"], 0) + 1
        p["tier_rank"] = tier_counts[p["relevance"]]
    return papers


def load_ingested(known_ids):
    schema = load_schema()
    records, errors = {}, []
    for path in sorted(INGESTED.glob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            jsonschema.validate(rec, schema)
        except (json.JSONDecodeError, jsonschema.ValidationError) as e:
            errors.append(f"{path.name}: {getattr(e, 'message', e)}")
            continue
        if rec["id"] != path.stem:
            errors.append(f"{path.name}: id '{rec['id']}' doesn't match file name")
        elif rec["id"] not in known_ids:
            errors.append(f"{path.name}: no paper with this id in the screened list")
        else:
            records[rec["id"]] = rec
    return records, errors


def citation_histories(papers, offline):
    cache = json.loads(HISTORY_CACHE.read_text(encoding="utf-8")) if HISTORY_CACHE.exists() else {}
    if not offline:
        for p in papers:
            if p["id"] in cache or not p["openalex_id"]:
                continue
            work = p["openalex_id"].rsplit("/", 1)[-1]
            r = requests.get(f"https://api.openalex.org/works/{work}", headers=HEADERS, timeout=30)
            if r.ok:
                years = r.json().get("counts_by_year", [])
                cache[p["id"]] = sorted(
                    ({"year": y["year"], "count": y["cited_by_count"]} for y in years),
                    key=lambda y: y["year"],
                )
        CACHE.mkdir(exist_ok=True)
        HISTORY_CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return cache


ROLE_PRIORITY = ["proposed", "compared", "used"]


def usage_stats(records):
    """Per workflow step: which papers use which canonical tools and methods.

    Each use is classed per paper as proposed / used / compared (from the paper's
    top-level tools and algorithms) or mentioned (step only discussed). Steps a
    paper marks none or unknown don't contribute. The app aggregates these into
    counts so it can apply filters (tier, metric) on the fly.
    """
    vocab = Vocabulary()
    stages = {k: {"involvement": {}, "tools": {}, "methods": {}} for k, _ in STAGES}
    aliases = {"tools": {}, "methods": {}}

    for pid, rec in records.items():
        # Role of each canonical tool/method in this paper, from its top-level lists.
        roles = {}
        for item in rec.get("tools", []) + rec.get("algorithms", []):
            for kind in ("tools", "methods"):
                entry, _ = vocab.lookup(item["name"], kind)
                if entry is None:
                    continue
                prev = roles.get(entry["name"])
                if prev is None or ROLE_PRIORITY.index(item["role"]) < ROLE_PRIORITY.index(prev):
                    roles[entry["name"]] = item["role"]

        for stage_key, _ in STAGES:
            st = rec["workflow"][stage_key]
            stages[stage_key]["involvement"][pid] = st["involvement"]
            if st["involvement"] in ("none", "unknown"):
                continue
            for kind in ("tools", "methods"):
                seen = {}
                for raw in st.get(kind, []):
                    entry, version = vocab.canon(raw, kind)
                    aliases[kind][raw] = entry["name"]
                    use = seen.setdefault(entry["name"], {"id": pid, "versions": set()})
                    if version:
                        use["versions"].add(version)
                    bucket = stages[stage_key][kind].setdefault(entry["name"], {
                        "name": entry["name"],
                        **{k: entry[k] for k in ("kind", "language", "url") if entry.get(k)},
                        "unlisted": bool(entry.get("unlisted")),
                        "uses": [],
                    })
                    use["bucket"] = bucket
                for name, use in seen.items():
                    role = roles.get(name)
                    cls = role if role in ("proposed", "compared") else (
                        "mentioned" if st["involvement"] == "mentioned" else "used")
                    use["bucket"]["uses"].append({"id": pid, "cls": cls, "versions": sorted(use["versions"])})

    for st in stages.values():
        for kind in ("tools", "methods"):
            st[kind] = sorted(st[kind].values(), key=lambda b: (-len(b["uses"]), b["name"].lower()))

    # Also map paper-level tool/algorithm names so the app can link any pill.
    for rec in records.values():
        for item in rec.get("tools", []) + rec.get("algorithms", []):
            for kind in ("tools", "methods"):
                entry, _ = vocab.lookup(item["name"], kind)
                if entry:
                    aliases[kind].setdefault(item["name"], entry["name"])

    unlisted = {k: sorted(v) for k, v in vocab.unlisted.items()}
    return {"stages": stages, "aliases": aliases, "unlisted": unlisted}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="don't fetch citation histories")
    ap.add_argument("--pending", type=int, metavar="N", help="list the top N papers not yet ingested and exit")
    args = ap.parse_args()

    papers = load_papers()
    records, errors = load_ingested({p["id"] for p in papers})

    if args.pending:
        todo = [p for p in papers if p["id"] not in records][: args.pending]
        for p in todo:
            print(f"#{p['rank']:<4} {p['id']:<40} {p['title'][:70]}")
        return

    ingested = [p for p in papers if p["id"] in records]
    histories = citation_histories(ingested, args.offline)

    out = []
    for p in papers:
        out.append({
            "rank": p["rank"],
            "tier": p["relevance"],
            "tier_rank": p["tier_rank"],
            "id": p["id"],
            "doi": p["doi"],
            "title": p["title"].rstrip("."),
            "first_author": p["first_author"],
            "journal": p["journal"],
            "year": int(p["year"]),
            "category": p["category"],
            "focus": p["focus"],
            "rule": int(p["rule"]),
            "reason": p["reason"],
            "markers_defined": p["markers_defined"] == "yes",
            "why_listed": p["why"],
            "pmid": p["pmid"],
            "pmcid": p["pmcid"],
            "free_access": p["free_access"],
            "access_route": p["access_route"],
            "license": p["license"],
            "free_url": p["free_url"],
            "citations": p["citations"],
            "citations_per_year": round(p["cpy"], 1) if p["cpy"] is not None else None,
            "citations_retrieved": p["citations_retrieved"],
            "openalex_id": p["openalex_id"],
            "recent": p["recent"],
            "scores": {
                "recency": round(p["recency"], 3),
                "citations": round(p["citation_score"], 3),
                "within_tier": round(p["within_tier_score"], 3),
            },
            "citation_history": histories.get(p["id"], []),
            "ingest": records.get(p["id"]),
        })

    usage = usage_stats(records)

    WEB_DATA.mkdir(parents=True, exist_ok=True)
    index = {
        "generated": date.today().isoformat(),
        "tiers": [{"key": t, "label": TIER_LABELS[t]} for t in TIERS],
        "stages": [{"key": k, "label": label} for k, label in STAGES],
        "usage": usage["stages"],
        "aliases": usage["aliases"],
        "papers": out,
    }
    (WEB_DATA / "papers.json").write_text(json.dumps(index, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} papers ranked, {len(records)} ingested -> web/data/papers.json")

    CACHE.mkdir(exist_ok=True)
    (CACHE / "unlisted_names.json").write_text(json.dumps(usage["unlisted"], indent=1), encoding="utf-8")
    n_unlisted = sum(len(v) for v in usage["unlisted"].values())
    if n_unlisted:
        print(f"{n_unlisted} tool/method names aren't in vocab/vocabulary.json "
              f"(listed in cache/unlisted_names.json); they're counted under their own names.")
    if errors:
        print("\nSkipped invalid ingestion records:", *errors, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
