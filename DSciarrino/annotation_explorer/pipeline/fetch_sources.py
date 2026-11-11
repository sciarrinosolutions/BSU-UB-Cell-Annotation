"""Download the readable text of papers so the ingestion agent can read them.

For each paper, writes sources/<id>/:
  paper.md     title, abstract and full-text sections (best available version)
  source.json  where each part came from

Order of preference: Europe PMC full-text XML (PMC papers), the arXiv PDF
(arXiv papers), then the abstract alone (Europe PMC or arXiv). sources/ is
git-ignored: full texts may not be redistributable, so they stay local.

Usage:
    python pipeline/fetch_sources.py <id> [<id> ...]
    python pipeline/fetch_sources.py --next 5    # next 5 un-ingested papers by rank
"""

import argparse
import csv
import io
import json
import re
import sys
import xml.etree.ElementTree as ET

import requests

from common import HEADERS, INGESTED, SCREENED, SOURCES, paper_id

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
ARXIV = "http://export.arxiv.org/api/query"


def text_of(el) -> str:
    return " ".join("".join(el.itertext()).split())


def jats_to_markdown(xml: str) -> str:
    """Convert JATS full-text XML into headed plain text."""
    root = ET.fromstring(xml)
    out = []
    title = root.find(".//article-meta//article-title")
    if title is not None:
        out.append(f"# {text_of(title)}\n")
    for ab in root.findall(".//article-meta/abstract"):
        out.append("## Abstract\n")
        for p in ab.iter("p"):
            out.append(text_of(p) + "\n")

    def walk(sec, depth):
        t = sec.find("title")
        if t is not None and text_of(t):
            out.append(f"\n{'#' * min(depth, 6)} {text_of(t)}\n")
        for child in sec:
            if child.tag == "p":
                out.append(text_of(child) + "\n")
            elif child.tag == "sec":
                walk(child, depth + 1)
            elif child.tag in ("table-wrap", "fig"):
                cap = child.find(".//caption")
                label = child.find("label")
                if cap is not None:
                    name = text_of(label) if label is not None else child.tag
                    out.append(f"[{name}] {text_of(cap)}\n")

    body = root.find("body")
    if body is not None:
        # Short formats put the main text straight under <body>, without <sec>.
        out.append("\n## Main text\n")
        walk(body, 2)
    back = root.find("back")
    if back is not None:
        for sec in back.findall("sec"):
            walk(sec, 2)
    return "\n".join(out)


def epmc_record(doi: str) -> dict:
    r = requests.get(
        f"{EPMC}/search",
        params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "core"},
        headers=HEADERS, timeout=60,
    )
    r.raise_for_status()
    results = r.json().get("resultList", {}).get("result", [])
    return results[0] if results else {}


def arxiv_id(paper: dict) -> str:
    m = re.search(r"arxiv\.org/abs/([\w.]+)", paper["free_url"]) or re.search(r"arXiv\.([\w.]+)", paper["doi"])
    return m.group(1) if m else ""


def fetch(paper: dict) -> dict:
    pid = paper_id(paper["doi"])
    sources = []
    body = ""

    if paper["pmcid"]:
        r = requests.get(f"{EPMC}/{paper['pmcid']}/fullTextXML", headers=HEADERS, timeout=60)
        if r.ok and r.text.strip().startswith("<"):
            body = jats_to_markdown(r.text)
            sources.append({"label": "Europe PMC full text", "url": f"https://europepmc.org/article/PMC/{paper['pmcid']}"})

    ax = arxiv_id(paper)
    if not body and ax:
        meta = requests.get(ARXIV, params={"id_list": ax}, headers=HEADERS, timeout=60).text
        abstract = re.search(r"<summary>(.*?)</summary>", meta, re.S)
        body = f"# {paper['title']}\n\n## Abstract\n\n" + (" ".join(abstract.group(1).split()) if abstract else "")
        sources.append({"label": "arXiv abstract", "url": f"https://arxiv.org/abs/{ax}"})
        pdf = requests.get(f"https://arxiv.org/pdf/{ax}", headers=HEADERS, timeout=120)
        if pdf.ok and pdf.content[:4] == b"%PDF":
            from pypdf import PdfReader
            pages = PdfReader(io.BytesIO(pdf.content)).pages
            body += "\n\n## Full text (extracted from PDF)\n\n" + "\n".join(p.extract_text() or "" for p in pages)
            sources.append({"label": "arXiv PDF", "url": f"https://arxiv.org/pdf/{ax}"})

    if not body:
        rec = epmc_record(paper["doi"])
        abstract = re.sub(r"<[^>]+>", " ", rec.get("abstractText", ""))
        if abstract:
            body = f"# {paper['title']}\n\n## Abstract\n\n{' '.join(abstract.split())}"
            sources.append({"label": "Europe PMC abstract", "url": f"https://europepmc.org/article/{rec.get('source')}/{rec.get('id')}"})

    folder = SOURCES / pid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "paper.md").write_text(body or "(no text found)", encoding="utf-8")
    manifest = {"id": pid, "doi": paper["doi"], "title": paper["title"], "free_url": paper["free_url"], "sources": sources}
    (folder / "source.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return {"id": pid, "chars": len(body), "sources": [s["label"] for s in sources]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--next", type=int, metavar="N", help="fetch the next N un-ingested papers by rank")
    args = ap.parse_args()

    with SCREENED.open(encoding="utf-8") as f:
        papers = {paper_id(p["doi"]): p for p in csv.DictReader(f)}

    ids = list(args.ids)
    if args.next:
        import subprocess
        out = subprocess.run(
            [sys.executable, str(__file__).replace("fetch_sources", "build_index"), "--pending", str(args.next)],
            capture_output=True, text=True, check=True,
        ).stdout
        ids += [line.split()[1] for line in out.splitlines() if line.startswith("#")]

    done = {p.stem for p in INGESTED.glob("*.json")}
    for pid in ids:
        if pid not in papers:
            print(f"unknown id: {pid}")
            continue
        if pid in done:
            print(f"note: {pid} is already ingested; fetching anyway")
        result = fetch(papers[pid])
        print(f"{result['id']:<40} {result['chars']:>8} chars  {', '.join(result['sources']) or 'NOTHING FOUND'}")


if __name__ == "__main__":
    main()
