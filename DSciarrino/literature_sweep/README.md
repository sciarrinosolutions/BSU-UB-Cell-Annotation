# Literature Sweep: scRNA-seq Cell Type Annotation

First-pass sweep (October 2026) for freely accessible papers to support building
**rules for cell type annotation** from RNA expression, plus **benchmarks** to evaluate
against. Focus areas follow the Talkington group: **monocytes and T cells**, with broader
immune/TME coverage, and **LLM / agentic annotation** methods.

## Files

| File | What it is |
|---|---|
| [`verified_papers.csv`](verified_papers.csv) | **Main output.** 101 curated papers, each verified against Europe PMC or arXiv, with PMID / PMCID / DOI, free-access route, license, citation count, free-text URL, priority and rationale. |
| [`seed_papers.csv`](seed_papers.csv) | Curated input list (title, category, focus, priority, why). Edit this to add papers, then re-run `verify_papers.py`. |
| [`candidates_raw.csv`](candidates_raw.csv) | Unscreened pool of 1,748 open-access / preprint records from broad keyword searches. Noisy; mine it for more papers. |
| [`search_europepmc.py`](search_europepmc.py) | Broad topic searches → `candidates_raw.csv`. |
| [`verify_papers.py`](verify_papers.py) | Verifies each seed paper → `verified_papers.csv`. |

Re-run (needs `requests`; `pandas` is optional for exploring):

```bash
python search_europepmc.py
python verify_papers.py
```

## Method

1. **Broad sweep:** nine topic queries against the Europe PMC REST API, restricted to open-access
   or preprint records (Europe PMC covers PubMed, PMC, bioRxiv and medRxiv).
2. **Curation:** papers selected from the sweep plus well-known landmark papers, organized
   into categories.
3. **Verification:** every paper is looked up by title (or arXiv ID). Only exact title matches
   (similarity ≥ 0.85, nearly all 1.0) are accepted, and identifiers come from the database, not
   from memory. When a journal version is paywalled, a free preprint version is used if one exists.
4. **arXiv** (not indexed by Europe PMC) is queried directly for CS-venue LLM/agent papers.

Google Scholar was **not** queried. It has no API and blocks automated access. Europe PMC and arXiv
cover the same biomedical and ML literature.

## Results at a glance

- **101 papers verified; 96 have a legal free full text.**
- Access routes: 60 PMC open access, 10 PMC free (author manuscripts), 15 bioRxiv/medRxiv preprints,
  8 arXiv, 3 free on the publisher's site.
- Licenses: 41 CC BY, 1 CC0, 22 CC BY-NC / NC-ND, 8 arXiv (check each), 29 with no reuse license
  (free to read, not to redistribute).

| Category | Count | Covers |
|---|---|---|
| `marker_database` | 6 | Curated marker sources (CellMarker 2.0, PanglaoDB, HPA, Cell Ontology…) |
| `annotation_method` | 20 | Marker-based, hierarchical and reference-based methods; reviews/best practices |
| `benchmark` | 15 | Head-to-head comparisons of annotation methods, foundation models, LLMs and LLM agents |
| `benchmark_dataset` | 9 | Labeled data usable as ground truth (sorted PBMC, CITE-seq, Tabula Sapiens, CELLxGENE, TISCH2) |
| `llm_agent` | 23 | GPT-based, multi-LLM consensus, RAG/knowledge-graph and multi-agent annotation |
| `foundation_model` | 7 | scGPT, Geneformer, scBERT, UCE, scFoundation, TOSICA, CellFM |
| `monocyte` | 9 | Blood monocyte/DC nomenclature and subsets; tumor-infiltrating myeloid cells |
| `t_cell` | 10 | T cell reference atlases (ProjecTILs, CD4 map), exhaustion and TIL states |
| `tme` | 2 | Pan-cancer TME resources |

## Priority 1: start here

These are direct sources of marker rules, core ground-truth datasets, or the most relevant
LLM/agent work. **The priority tiers are my judgment and still need review by the team.**
All links below go to free full text.

### Marker sources (for building rules)

| Paper | Year | Why |
|---|---|---|
| [CellMarker 2.0](https://europepmc.org/article/PMC/PMC9825416), Hu et al., *NAR* | 2023 | Largest manually curated human/mouse marker DB |
| [PanglaoDB](https://europepmc.org/article/PMC/PMC6450036), Franzén et al., *Database* | 2019 | Marker DB with per-marker sensitivity/specificity |
| [Cell Marker Accordion](https://europepmc.org/article/PMC/PMC12234662), Busarello et al., *Nat Commun* | 2025 | Weighted consensus markers; includes disease states |
| [A single-cell type transcriptomics map of human tissues](https://europepmc.org/article/PMC/PMC8318366), Karlsson et al., *Sci Adv* | 2021 | Human Protein Atlas cell-type enrichment; independent evidence |
| [The Cell Ontology 2016](https://europepmc.org/article/PMC/PMC4932724), Diehl et al., *J Biomed Semant* | 2016 | Standard label vocabulary (CL IDs) for rule outputs |

### Annotation methods whose design maps onto "rules"

| Paper | Year | Why |
|---|---|---|
| [scType](https://europepmc.org/article/PMC/PMC8913782), Ianevski et al., *Nat Commun* | 2022 | Positive **and negative** marker sets; ships an immune-heavy marker DB |
| [scGate](https://europepmc.org/article/PMC/PMC9048671), Andreatta et al., *Bioinformatics* | 2022 | Hierarchical boolean marker gates for immune cells, the closest existing design to a rule engine |
| [Garnett](https://europepmc.org/article/PMC/PMC6791524), Pliner et al., *Nat Methods* | 2019 | Human-readable hierarchical marker file format |
| [CellAssign](https://europepmc.org/article/PMC/PMC7485597), Zhang et al., *Nat Methods* | 2019 | Probabilistic marker-matrix assignment, built for the TME |
| [CellTypist](https://europepmc.org/article/PMC/PMC7612735), Domínguez Conde et al., *Science* | 2022 | Immune-focused models plus a curated immune cell encyclopedia |
| [Seurat v4 / Azimuth](https://europepmc.org/article/PMC/PMC8238499), Hao et al., *Cell* | 2021 | 211k-cell CITE-seq PBMC reference with protein-validated labels |
| [SingleR](https://europepmc.org/article/PMC/PMC6340744), Aran et al., *Nat Immunol* | 2019 | Most-cited reference-correlation method; common baseline |

### Monocytes

| Paper | Year | Why |
|---|---|---|
| [Nomenclature of monocytes and DCs in blood](http://hdl.handle.net/11379/41075), Ziegler-Heitbrock et al., *Blood* | 2010 | Official classical / intermediate / non-classical definitions |
| [New types of human blood DCs, monocytes, and progenitors](https://europepmc.org/article/PMC/PMC5775029), Villani et al., *Science* | 2017 | scRNA-seq-defined monocyte (Mono1–4) and DC subsets |
| [Human monocyte subsets and phenotypes](https://europepmc.org/article/PMC/PMC6728754), Kapellos et al., *Front Immunol* | 2019 | Review of subset markers across diseases |
| [Pan-cancer tumor-infiltrating myeloid cells in ICB](https://europepmc.org/article/PMC/PMC11271490), Li et al., *Nat Commun* | 2024 | Open-access pan-cancer myeloid analysis |

### T cells

| Paper | Year | Why |
|---|---|---|
| [ProjecTILs](https://europepmc.org/article/PMC/PMC8137700), Andreatta et al., *Nat Commun* | 2021 | TIL reference atlas: naive, effector-memory, precursor-exhausted, exhausted, Treg, Th1, Tfh |
| [CD4+ T cell reference map](https://europepmc.org/article/PMC/PMC9323004), Andreatta et al., *eLife* | 2022 | CD4 subtype reference (CC0) |
| [Human T cell tissue and activation signatures](https://europepmc.org/article/PMC/PMC6797728), Szabo et al., *Nat Commun* | 2019 | Resting vs. activated, tissue vs. blood signatures |
| [T cell exhaustion-associated immune environments in breast cancer](https://europepmc.org/article/PMC/PMC9822999), Tietscher et al., *Nat Commun* | 2023 | Exhaustion map in tumors |

### Benchmarks and ground-truth data

| Paper | Year | Why |
|---|---|---|
| [Comparison of automatic cell identification methods](https://europepmc.org/article/PMC/PMC6734286), Abdelaal et al., *Genome Biol* | 2019 | 22 classifiers × 27 datasets; the standard benchmark, with public code and data |
| [Assigning cell type labels to clusters](https://europepmc.org/article/PMC/PMC6720041), Diaz-Mejia et al., *F1000Res* | 2019 | Benchmarks marker-based labeling, which is closest to the rules approach |
| [Zero-shot limitations of single-cell foundation models](https://europepmc.org/article/PMC/PMC12007350), Kedzierska et al., *Genome Biol* | 2025 | Shows scGPT/Geneformer can underperform simple baselines |
| [Benchmarking LLM-based agents for single-cell omics](https://europepmc.org/article/PMC/PMC13064268), Liu et al., *Genome Biol* | 2026 | **Directly relevant**: evaluates LLM agents on scRNA-seq tasks |
| [Zheng et al. 2017 (PBMC 68k + FACS-sorted populations)](https://europepmc.org/article/PMC/PMC5241818), *Nat Commun* | 2017 | Sorted immune populations give ground truth |
| [CITE-seq](https://europepmc.org/article/PMC/PMC5669064), Stoeckius et al., *Nat Methods* | 2017 | Surface-protein ground truth for immune labels |
| [Kang et al. 2018 (IFN-β-stimulated PBMC)](https://europepmc.org/article/PMC/PMC5784859), *Nat Biotechnol* | 2018 | Tests robustness of rules to activation state |
| [Tabula Sapiens](https://europepmc.org/article/PMC/PMC9812260), *Science* | 2022 | Expert-annotated multi-organ reference |
| [CZ CELLxGENE Discover](https://europepmc.org/article/PMC/PMC11701654), *NAR* | 2025 | Large source of labeled data with Cell Ontology IDs |
| [TISCH2](https://europepmc.org/article/PMC/PMC9825603), Han et al., *NAR* | 2023 | Uniformly annotated tumor datasets |

### LLM / agentic annotation

| Paper | Year | Why |
|---|---|---|
| [GPTCelltype](https://europepmc.org/article/PMC/PMC11310073), Hou & Ji, *Nat Methods* | 2024 | Baseline: GPT-4 annotates from marker lists, scored against manual labels |
| [CASSIA](https://europepmc.org/article/PMC/PMC12796229), Xie et al., *Nat Commun* | 2025 | Multi-agent annotation with dedicated validation/scoring agents |
| [CellTypeAgent](https://arxiv.org/abs/2505.08844), *arXiv* | 2025 | Checks LLM proposals against CELLxGENE expression to reduce hallucination |
| [AnnDictionary](https://europepmc.org/article/PMC/PMC12569162), Crowley et al., *Nat Commun* | 2025 | Benchmarks many LLMs on annotation |
| [LICT](https://europepmc.org/article/PMC/PMC12462508), Ye et al., *Commun Biol* | 2025 | Multi-LLM annotation with an objective credibility check |
| [mLLMCelltype (LLM consensus)](https://www.biorxiv.org/content/biorxiv/early/2025/04/17/2025.04.10.647852.full.pdf), Yang et al., *Commun Biol* | 2026 | Consensus across LLMs improves accuracy |

Priority 2 and 3 papers are in `verified_papers.csv`. They include other annotation tools (SCSA,
scCATCH, CHETAH, scPred, scArches, scANVI), method reviews, more T cell / TME atlases, foundation
models, and recent agent frameworks (CellAgent, scAgent, ReCellTy, scHilda, CellPilot, Biomni…).

## Paywalled: no legal free version found

These are important but excluded from ingestion. Request them through the library if needed.

| Paper | Notes |
|---|---|
| Clarke et al., *Nat Protoc* 2021, annotation guidelines tutorial | [doi](https://doi.org/10.1038/s41596-021-00534-0). Free reviews in the list cover similar ground. |
| Dutertre et al., *Immunity* 2019, mononuclear phagocyte subset markers (DC3 vs. monocytes) | [doi](https://doi.org/10.1016/j.immuni.2019.08.008) |
| Mulder et al., *Immunity* 2021, MoMac-VERSE monocyte/macrophage atlas | [doi](https://doi.org/10.1016/j.immuni.2021.07.007) |
| Cheng et al., *Cell* 2021, pan-cancer tumor-infiltrating myeloid atlas | [doi](https://doi.org/10.1016/j.cell.2021.01.010). Li et al. 2024 (above) is the free substitute. |
| Zheng et al., *Science* 2021, pan-cancer tumor-infiltrating T cells | [doi](https://doi.org/10.1126/science.abe6474) |

## Caveats

- **"Free" is not the same as "reusable."** CC BY / CC0 content can be redistributed with
  attribution. NC/ND licenses and author manuscripts can be read and mined for facts (marker lists),
  but **don't commit their full text or figures to this public repo**.
- Whether each paper has **usable marker tables or labeled data** still needs to be confirmed
  paper by paper. `has_suppl` only means supplementary files exist.
- Citation counts come from Europe PMC and run lower than Google Scholar's.
- Preprints are not peer-reviewed. Several journal versions (scGPT, scBERT, UCE) are paywalled, so the
  preprints are listed instead.

## Suggested next steps

1. Team review of the priority tiers, especially the monocyte and T cell sets.
2. Pull full-text XML for the priority 1 papers from Europe PMC (`/{PMCID}/fullTextXML`) and extract
   marker tables into a structured rule format (cell type → positive/negative markers, tissue,
   species, source).
3. Download the benchmark datasets (Zheng 2017 sorted PBMC, Hao 2021 CITE-seq PBMC, Kang 2018) and
   set up an evaluation harness.
