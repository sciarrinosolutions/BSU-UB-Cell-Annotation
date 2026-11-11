"""Paths and helpers shared by the pipeline scripts."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWEEP = ROOT.parent / "literature_sweep"
SCREENED = SWEEP / "screened_papers.csv"
CITATIONS = SWEEP / "citations_openalex.csv"
SCHEMA = ROOT / "schema" / "ingested_paper.schema.json"
INGESTED = ROOT / "ingested"
SOURCES = ROOT / "sources"
CACHE = ROOT / "cache"
WEB_DATA = ROOT / "web" / "data"

HEADERS = {"User-Agent": "BSU-UB-Cell-Annotation annotation explorer"}

# Workflow steps shown in the app, in pipeline order (keys match the schema).
STAGES = [
    ("sequencing", "scRNA-seq"),
    ("quantification", "Quantification"),
    ("preprocessing", "Expression matrix & preprocessing"),
    ("dimensionality_reduction", "Dimensionality reduction"),
    ("batch_correction", "Batch correction"),
    ("clustering", "Clustering"),
    ("annotation", "Annotation"),
    ("trajectory", "Trajectory"),
    ("cell_communication", "Cell–cell communication"),
]


def paper_id(doi: str) -> str:
    """Stable, filename-safe id derived from the DOI."""
    return re.sub(r"[^a-z0-9]+", "-", doi.lower()).strip("-")


def load_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))
