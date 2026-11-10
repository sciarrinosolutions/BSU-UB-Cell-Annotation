---
name: literature-filter-talkington
description: >-
  Screens and ranks research papers for the BSU-UB cell annotation project using
  the literature-filtering rules set by Dr. Anne Talkington, plus recency and
  citation impact. Papers are ranked, never discarded. Use when deciding which
  papers to read first, triaging search results (e.g.
  literature_sweep/candidates_raw.csv or verified_papers.csv), adding papers to
  seed_papers.csv, or explaining why a paper ranks where it does.
---

# Literature filter: Talkington group rules

Use this skill to decide how useful a paper is for building the cell type
annotation system, and to **rank** papers so the most useful ones are read
first. **No paper is thrown away.** Even out-of-scope papers stay in the list,
ranked at the bottom with the reason recorded, so any decision can be reversed. The rules come from Dr. Talkington's guidance to
the team (November 2026). Anything marked **Interpretation** is our reading of
a case her guidance doesn't cover directly; check those with her before relying
on them.

## Project goal (the lens for every decision)

We are building an **algorithm, using AI agents, that identifies and annotates
cell types from scRNA-seq data in the cancer setting**. The group's own work
focuses on monocytes and T cells, but being able to tell other cell types apart
is also valuable. At this stage we are **building the algorithm first** and
**refining it later**. A paper is useful now if it helps us design that initial
algorithm.

## Ratings

Give every paper exactly one rating:

| Rating | Meaning | What to do with it |
|---|---|---|
| `preferred` | Directly helps build the initial algorithm | Ingest now |
| `caution` | Broad or general; may lack depth but points to better papers | Read for orientation and mine its references; don't extract rules from it directly |
| `later` | Relevant but too narrow for the first build | Keep a record of it and come back during refinement |
| `exclude` | Out of scope | Keep it, ranked at the bottom, with the reason recorded |

## Rules

Apply them in this order. The first rule that decides the rating wins.

### 1. Out of scope → `exclude`

- **Disease states outside cancer** (e.g. viral infection, autoimmunity,
  fibrosis, neurodegeneration, chronic inflammatory disease).
- **Microbiome** topics.
- Non-scRNA-seq contexts that can't inform RNA-based annotation (e.g. bulk-only
  studies with no cell type definitions).

Exceptions to the non-cancer rule:
- If the paper is mainly an **annotation algorithm, benchmark, or labeled
  dataset**, and the non-cancer samples are just the test data, skip to rule 3.
- If the paper is mainly a **cell reference or marker definition** that could be
  reused (e.g. a reference map of an immune cell lineage), rate it `later`
  instead of `exclude`. This matches Dr. Talkington's CD4 map example below.

**Interpretation:** healthy-tissue and healthy-blood references (e.g. PBMC
atlases, Tabula Sapiens) are *not* "disease outside cancer". They describe the
normal cell types the algorithm has to recognize, so don't exclude them under
this rule.

### 2. Too specific → `later`

The paper focuses narrowly, for example:
- one cell subtype in one specific disease state, or
- one particular biological process (one pathway, one differentiation step, one
  treatment response).

These papers may matter later, during algorithm refinement, but they don't help
the initial build.

### 3. Algorithm papers → `preferred`

The paper describes a **method or algorithm for cell type identification or
annotation**: marker-based, reference-based, machine learning, foundation model,
LLM, or agent-based. Papers that use agents or LLMs in a way similar to our
approach are especially valuable. So are papers that survey the state of the
field, its recent advances and its remaining gaps.

**Interpretation:** benchmark papers that compare annotation algorithms, and
papers that provide labeled ground-truth datasets for evaluating them, count as
algorithm papers here, because we need them to measure the algorithm.

### 4. Experimental papers → `preferred` only if they define markers

Strictly experimental or biological papers (e.g. "we profiled tumor X and found
Y") are **not preferred**, **unless** they establish a **clear set of markers
that defines a cell type**. In that case they are a direct source of annotation
rules and rate `preferred`. Otherwise, rate them `later` if they are in scope or
`exclude` if they are not.

### 5. Very general papers → `caution`

Broad papers (e.g. a general cancer immunology review) can be included, but with
caution. They may be an interesting starting point without enough depth to be
useful right away. Use them to **find other papers** by following their
references and the papers that cite them.

## Things that are *not* filters

- **Cell "type" vs. "state":** the group does make this distinction, but the
  terminology isn't standardized across the literature. **Never include or
  exclude a paper because of the words "type" or "state".** Judge what the paper
  actually does.
- **Cell lineage:** monocyte and T cell papers are especially relevant, but
  papers about other cell types aren't excluded. Broader coverage is useful.
- Citation count, publication year and journal prestige don't change the
  relevance **rating**. Recency and citations enter only the **ranking score**
  (see "Ranking" below), and journal prestige isn't used at all.

## Worked examples (from Dr. Talkington)

**Useful (`preferred`):** *CellTypeAgent: Trustworthy cell type annotation with
Large Language Models.*
It describes an algorithm, and uses agents in a way similar to what we are
building. It's a good starting point for understanding the current state of the
field, including recent advances and remaining gaps. Many similar papers are
already on our list.

**Less useful (`later`):** *A CD4+ T cell reference map delineates
subtype-specific adaptation during acute and chronic viral infections.*
It isn't about cancer, and its focus on one specific cell subtype makes it better
suited to a later stage of algorithm refinement than to the initial build.
(Rule 1: it's a reusable reference map in a non-cancer setting, so it rates
`later`, not `exclude`.)

The strictly experimental papers Dr. Talkington pointed out at the team meeting
also fall in the less-useful category (rule 4). They aren't in the repo yet.

## Procedure

For each paper:

1. Read the title and abstract. If those are ambiguous, skim the methods and
   look for marker tables.
2. Work through rules 1–5 in order and stop at the first one that decides the
   rating.
3. Record the result with these fields:
   - `relevance`: one of `preferred` / `caution` / `later` / `exclude`
   - `rule`: the rule number that decided it (1–5)
   - `reason`: one sentence in plain language tied to the rule (e.g. "Agent-based
     annotation algorithm benchmarked on tumor data")
   - `markers_defined`: `yes` if the paper gives an explicit marker set for one or
     more cell types, otherwise `no`
4. When unsure between two ratings, choose the more conservative one (`later`
   over `preferred`, `caution` over `preferred`) and add `needs review` to the
   reason.

When screening the team's lists (`literature_sweep/verified_papers.csv`,
`candidates_raw.csv`), add these fields as new columns rather than deleting rows,
so the decisions can be audited and reversed.

5. Compute the ranking score (next section) and sort by it.

## Ranking

Papers should be **relevant, recent and highly cited**. Each paper gets a score
from 0 to 1, and the list is sorted by that score:

```
score = 0.50 × relevance + 0.25 × recency + 0.25 × citation impact
```

| Component | How it's computed |
|---|---|
| **relevance** | From the rating: `preferred` 1.0, `caution` 0.6, `later` 0.3, `exclude` 0.0 |
| **recency** | 1.0 for the current year, falling by 0.1 per year, reaching 0 at 10 or more years old. Papers from the last 5 years count as **recent**. |
| **citation impact** | Citations **per year** since publication (counting the publication year as year 1), as a percentile within the list being ranked (0 = least cited, 1 = most cited) |

Why it's built this way:
- **Relevance carries half the weight**, so Dr. Talkington's rules stay the main
  factor. A highly cited but out-of-scope paper can't outrank a relevant one on
  citations alone.
- **Citations are per year.** Raw counts favor old papers, which would work
  against recency. Dividing by age lets a 2025 paper with 100 citations compete
  with a 2017 paper with 1,000.
- **Percentiles, not raw counts.** Citation counts are very skewed (a few papers
  have thousands of citations), and percentiles keep one landmark paper from
  flattening everyone else's scores.
- **Missing citation counts** (e.g. arXiv, which doesn't report them) get a
  neutral 0.5 and the flag `citations unknown`, so papers aren't penalized just
  for where they're hosted.

Ties are broken by `markers_defined = yes` first, then by more recent year.

The weights are a starting point, not a rule from Dr. Talkington. Adjust them in
`literature_sweep/rank_papers.py` if the team wants recency or citations to
count for more or less.

**Citation source:** use **OpenAlex** (`fetch_openalex_citations.py`, then
`rank_papers.py --citations citations_openalex.csv`). Europe PMC counts only
citations from papers it indexes, and that misses preprint and CS-venue
citations (e.g. 0 for GenePT and Biomni, where OpenAlex reports 205 and 289),
and it has no counts for arXiv papers. OpenAlex covers both and usually merges a
preprint's citations with its journal version. Use one source for every paper
in a ranking, because mixing sources makes the percentiles unfair. Counts are a
snapshot as of the `retrieved` date, so re-fetch them to refresh.

## Open questions for Dr. Talkington

These are borderline cases on the current list that her guidance doesn't settle:

- **Healthy-reference papers** (PBMC atlases, Tabula Sapiens): we treat them as in
  scope (see the interpretation under rule 1). Is that right?
- **Benchmark datasets drawn from non-cancer patients:** e.g. Kang et al. 2018
  (stimulated PBMCs from lupus patients). Under the rule 1 exception these count
  as benchmark data (rule 3), not as excluded disease papers. Is that right?
- **Marker-defining papers outside cancer:** e.g. Kapellos et al. 2019 (monocyte
  subsets in chronic inflammatory diseases). Under the rule 1 exception this rates
  `later`. Should monocyte subset markers count as `preferred` even though the
  disease setting is outside cancer?
- **Foundation-model papers** (scGPT, Geneformer, etc.): these are algorithms
  (rule 3), but they aren't specific to annotation. Should they be `preferred` or
  `caution`?
