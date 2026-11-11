# Annotation Explorer

A sample application for browsing the cell-annotation literature, laid out like
the mockup (`../Mockup for Cell Annotation Program.drawio`):

- **Left:** every paper from the literature sweep, in rank order.
- **Top right:** an enhanced abstract written by the ingestion agent, plus
  links, citation counts with a by-year chart, ranking scores and any marker
  definitions the paper gives.
- **Bottom right:** how the paper relates to each step of the scRNA-seq
  workflow (sequencing → quantification → preprocessing → dimensionality
  reduction → batch correction → clustering → annotation → trajectory /
  cell–cell communication). Click a step for details and the algorithms and
  tools involved.
- **"All ingested papers" view** (toggle above the diagram): the same diagram
  shaded by how many papers perform each step, labeled with the top tool. Clicking
  a step shows ranked bar charts of its most-used tools and methods. You can count
  by papers using it, use as a baseline, proposed methods, or citation-weighted
  use, and restrict to the preferred tier. Click a bar (or any highlighted tool
  pill on a paper) for a tool card: steps, versions, the papers that use it, and a
  button to filter the paper list to them.
- **Help:** the **Help** button (top right) and the small **?** links open the help pages in
  `web/help/` in a new tab, at the relevant section.
- **Resizable sections:** drag the borders between the paper list, the abstract,
  the workflow panel, and the diagram/step details. You can also focus a border
  and use the arrow keys. Double-clicking a border resets it. Sizes are
  remembered in your browser. On narrow screens the sections stack and the
  borders aren't draggable.

## Run it

```bash
python pipeline/build_index.py
python -m http.server 8765 --directory web
```

Then open <http://localhost:8765>. A local server is needed because browsers
block loading `data/papers.json` from a `file://` page. In Claude Code, the
`annotation-explorer` entry in the repo's `.claude/launch.json` starts the same
server.

## How it works

```
literature_sweep/screened_papers.csv ─┐
literature_sweep/citations_openalex.csv ─┼─► pipeline/build_index.py ─► web/data/papers.json ─► web/ (app)
ingested/<id>.json (agent output) ─────┘          ▲
                                                  │ validates against
                                   schema/ingested_paper.schema.json
```

**Ranking** follows [`../SKILLS.md`](../SKILLS.md) in two layers:
1. **Tier:** the relevance label decides the order of the groups (preferred →
   caution → later → exclude).
2. **Within a tier:** 0.5 × recency + 0.5 × citation impact (OpenAlex
   citations per year, as a percentile across all papers).

**Ingestion** is the agent's job. See [`AGENT_INGEST.md`](AGENT_INGEST.md) for
the contract and rules. The loop is:

```bash
python pipeline/build_index.py --pending 10      # what to ingest next
python pipeline/fetch_sources.py --next 5        # download texts into sources/
# agent reads sources/<id>/paper.md, writes ingested/<id>.json
python pipeline/build_index.py                   # validate, rank, rebuild the app data
```

For now Claude acts as the agent by hand. An automated agent can be swapped
in later without changing the app, as long as it writes valid
`ingested/<id>.json` files.

**Tool and method popularity.** `vocab/vocabulary.json` lists standard names
with aliases, so "Seurat", "Seurat v4" and "Seurat v5" count as one tool (the
versions are kept separately). The build classes each use per paper:
- **proposed:** the paper's own method.
- **used:** performed with an existing tool.
- **compared:** a benchmark baseline.
- **mentioned:** the step is only discussed.

Steps a paper marks `unknown` (e.g. abstract-only records) are left out of the
counts rather than counted as absent. Names not in the vocabulary are still
counted under their own names, marked `*` in the app, and listed in
`cache/unlisted_names.json`.

## What's in this sample

13 of 101 papers are ingested. The first 8 were chosen to cover the project's
priorities; the next 5 are simply the top-ranked papers that hadn't been ingested yet:
CZ CELLxGENE, CellMarker 2.0, the zero-shot evaluation of foundation models,
Seurat v4 (WNN / Azimuth) and TISCH2. The first 8:

| Paper | Why it's in the sample |
|---|---|
| CellTypeAgent | Dr. Talkington's "useful" example: an LLM agent with database verification |
| GPT-4 for cell type annotation (GPTCelltype) | The LLM baseline |
| CASSIA | A multi-agent annotation system, tested on cancer and T cell states |
| ScType | Positive/negative marker rules |
| CellTypist | Immune reference classifier; monocyte and T cell markers |
| ProjecTILs | Tumor T cell reference atlas |
| Villani 2017 | Blood monocyte and DC subsets (**abstract only**: the full text wasn't downloadable) |
| CD4+ T cell reference map | Dr. Talkington's "less useful" example (`later` tier) |

The other 88 papers appear in the list with their ranking and metadata, marked
"pending". With 13 papers, the popularity counts are a demonstration, not a
finding. Ingest more preferred papers before drawing conclusions.

## Files

| Path | What it is |
|---|---|
| `pipeline/build_index.py` | Ranks papers, validates and merges ingested records, writes `web/data/papers.json` |
| `pipeline/fetch_sources.py` | Downloads paper text for the agent (Europe PMC full text, arXiv PDF, or abstract) |
| `pipeline/common.py` | Shared paths and the list of workflow steps |
| `pipeline/vocab.py` | Maps tool and method names onto the vocabulary |
| `vocab/vocabulary.json` | Standard tool and method names, aliases, kinds, languages and links |
| `cache/unlisted_names.json` | Names from ingested records that aren't in the vocabulary yet |
| `schema/ingested_paper.schema.json` | What an ingested record must contain |
| `ingested/` | Agent output, one JSON per paper |
| `cache/openalex_history.json` | Citations-by-year for the charts (fetched once) |
| `sources/` | Downloaded texts (git-ignored) |
| `web/` | The app (plain HTML/CSS/JS, no build step) |
| `web/help/` | Help pages (plain HTML, shared `help.css`; the page list and menu are in `help.js`) |
| `pipeline/check_help.py` | Checks help links, sections and the menu; also runs at the end of every build |

## Maintaining the help

The help pages are part of the app. When you add or change a feature:

1. Update the matching page in `web/help/` and its "Last reviewed" date.
2. When adding a page, add it to the `PAGES` list in `web/help/help.js`.
3. Keep section ids stable: the app links to `help/<page>.html#<section>`. Pass these paths to
   `helpLink()` in `app.js` as literal strings so the checker can find them.
4. Run `python pipeline/check_help.py` (it also runs as part of `build_index.py`).

Don't write current counts into the help; the overview page reads them live from `web/data/papers.json`.
