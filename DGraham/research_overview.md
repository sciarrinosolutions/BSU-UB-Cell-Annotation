# Knowledge Base Overview: Source Papers

**Project:** Project B, a human-in-the-loop cell-type annotation assistant for tumor scRNA-seq data

## Scope
- **Cell types, not states.** Exhaustion, activation, M1/M2 and similar labels are excluded from the project.
- **A two-level taxonomy:**
  - **Level 1 (broad class):** immune, malignant, stromal, or other.
  - **Level 2 (lineage / type):** e.g., lymphoid vs. myeloid; B vs. T; CD4 vs. CD8; monocyte vs. macrophage vs. dendritic cell (not collapsed to "myeloid").
- **Termination:** if a cluster can't be named, report its distinguishing genes for a scientist to interpret.

**Inclusion criteria for this knowledge base:** peer-reviewed; human; gives the agent marker evidence for Level 1 or Level 2 calls, a documented failure mode, or a tested lesson on how to make and check annotation decisions.

## How to read this file
Each included paper has its own summary page in `summaries/`, and the full-text PDFs are in `sources/`. This file is the index: what each paper is, what it contributes, and what to watch out for.

Papers play one of two roles:
- **Marker reference:** evidence for marker rules (which genes define which cell type, and which genes mislead).
- **Method lessons:** papers on automated or LLM-based annotation. **The agent does not run these tools.** These papers instead give tested lessons on how to structure decisions, when to abstain, and how to evaluate the agent.

## At a glance
| # | Source | Role | Levels | Use it for |
|---|---|---|---|---|
| 1 | Lodi 2025, *Cell Rep Med* | Marker reference (primary) | 1, 2 | Level 1 marker panel; annotation pitfalls |
| 2 | Caro 2026, *Nat Commun* | Marker reference (primary) | 2 | Monocyte vs. macrophage vs. DC; DC3 caveat |
| 3 | Domínguez Conde 2022, *Science* | Marker reference + method lessons | 2 | CD4 vs. CD8, T vs. NK, B vs. plasma; doublet examples |
| 4 | Luo 2022, *Nat Commun* | Marker reference (secondary) | 1 | Second source for Level 1 markers; stromal–immune mimics |
| 5 | Nofech-Mozes 2023, *Nat Commun* (scATOMIC) | Method lessons | 1, 2 | Hierarchy with abstention to the parent label; malignant call |
| 6 | Hou & Ji 2024, *Nat Methods* (GPTCelltype) | Method lessons | — | Single-LLM baseline; failure modes; evaluation scoring scheme |
| 7 | Xie 2026, *Nat Commun* (CASSIA) | Method lessons | — | Multi-agent design: validate, score, report; confidence thresholds |
| 8 | Yang 2026, *Commun Biol* (mLLMCelltype) | Method lessons | 1 → 2 | Level-by-level annotation; disagreement as a review signal |

---

## Marker references

### 1. Lodi et al. 2025: Spatially informed pan-cancer TME atlas
**Citation:** Lodi F, … Lambrechts D. *Decoding tumor heterogeneity: A spatially informed pan-cancer analysis of the tumor microenvironment.* Cell Reports Medicine 6:102416 (2025). DOI: 10.1016/j.xcrm.2025.102416 · CC BY-NC 4.0
**Page:** `summaries/lodi_et_al_2025_pancancer_tme_atlas_cellrepmed.md`

**Summary:** 611,750 cells from 230 fresh human samples (160 patients, 9 cancer types), processed with one dissociation protocol and no cell sorting. Every major compartment is annotated consistently.

**What it contributes:**
- **The primary Level 1 marker panel** (Fig. 1D), three markers per type. Examples: T cell CD3D/CD3E/TRAC; NK NCAM1/KLRC3/KLRC1; macrophage/monocyte CD68/LYZ/AIF1; mast MS4A2/TPSAB1/CPA3; epithelial/cancer EPCAM/KRT7/KRT18; fibroblast COL1A1/COL10A1/BGN; endothelial CLDN5/PECAM1/VWF.
- **Level 2 support** for T vs. NK, B vs. plasma, mast cells, pDC, and cDC.
- **Annotation pitfalls that become agent checks:**
  - DCs and mast cells hide inside myeloid clusters.
  - Neutrophils sit inside the monocyte/macrophage cluster.
  - **FOXP3 does not imply CD4** (CD8+ regulatory T cells exist).
  - Hemoglobin, dissociation-stress, and doublet artifacts create fake clusters.
  - The monocyte–macrophage boundary is a continuum.

**Watch out for:** only three display markers per type (full lists are in the online app); no negative markers; no malignant-vs-normal method; weak neutrophil markers; no CD4 vs. CD8 rule in the main text; its Methods misprint "TSPAB" for TPSAB1.

### 2. Caro et al. 2026: Pan-cancer tumor-associated dendritic cell atlas
**Citation:** Caro AA, Kancheva D, … Laoui D. *Pan-cancer single-cell atlases of mouse and human tumor-associated dendritic cells.* Nature Communications (2026). DOI: 10.1038/s41467-026-73721-w · CC BY-NC-ND 4.0 (drafted from the accepted manuscript)
**Page:** `summaries/caro_et_al_2026_pancancer_tadc_atlas_natcommun.md`

**Summary:** A human atlas of 61,432 monocytes, macrophages, and DCs from 10 cancer types, with DCs re-clustered and checked against fate-mapping signatures. Only the human Level 2 content is used.

**What it contributes:**
- **The primary myeloid Level 2 reference:**
  - monocyte (CD14, FCN1, VCAN; non-classical FCGR3A, LST1, CX3CR1)
  - macrophage (C1QA/C1QB, APOE, APOC1)
  - cDC1 (CLEC9A, XCR1); cDC2 (FCER1A, CD1C, HLA-DPB1)
  - pDC (LILRA4, IRF7, CLEC4C); mature DC (CCR7, LAMP3)
- **The most important caveat in the knowledge base:** DC3, a cDC2-like DC, expresses CD14, C1QA, C1QC, and FCGR3A, and its progenitor expresses FCN1, S100A9, and VCAN. **No single monocyte or macrophage gene can rule out a DC.** Rules for this split need a positive DC marker first, plus abstention when both signatures are strong.
- Mature CCR7+ DCs can lose their lineage markers; the paper leaves them unassigned.

**Watch out for:** built from DC-enriched or immune-sorted data, so proportions won't match unsorted samples; most clusters are states; final figure numbers may differ from the manuscript.

### 3. Domínguez Conde et al. 2022: Cross-tissue immune atlas and CellTypist
**Citation:** Domínguez Conde C, Xu C, Jarvis LB, Rainbow DB, Wells SB, … Teichmann SA. *Cross-tissue immune cell analysis reveals tissue-specific features in humans.* Science 376:eabl5197 (2022). DOI: 10.1126/science.abl5197 · CC BY 4.0
**Page:** `summaries/dominguez_conde_et_al_2022_celltypist_immune_atlas_science.md`

**Summary:** About 330,000 immune cells from 16 **healthy** tissues of 12 organ donors. Also introduces CellTypist, a classifier that labels at a broad level (32 types) and a fine level (91 types).

**What it contributes:**
- **Lymphoid Level 2 markers that Lodi lacks:**
  - CD4 T (CD4, CD40LG) and CD8 T (CD8A, CD8B)
  - NK (FCGR3A or NCAM1; no TCR)
  - B (MS4A1, CD19) and plasma (CD38, XBP1, SDC1)
  - MAIT (TRAV1-2, SLC4A10)
- **A second source** for the cDC1, cDC2, and monocyte markers in Caro 2026.
- **Labelled doublet clusters** (myeloid–T, myeloid–B, T–B) showing what mixed-lineage artifacts look like.
- **Method lessons from CellTypist:** a two-level hierarchy works for immune annotation; accuracy depends on how well a type is represented in training; γδ T cells co-cluster with cytotoxic αβ T cells and ILC3 with NK cells, so flag rather than force.

**Watch out for:** healthy tissue, not tumor (lineage markers transfer; tumor states don't); immune cells only; several genes come from dot-plot axes and should be confirmed against the published figures.

### 4. Luo et al. 2022: Pan-cancer cancer-associated fibroblast atlas
**Citation:** Luo H, Xia X, Huang L-B, … Park J, Xu H. *Pan-cancer single-cell analysis reveals the heterogeneity and plasticity of cancer-associated fibroblasts in the tumor microenvironment.* Nature Communications 13:6619 (2022). DOI: 10.1038/s41467-022-34395-2 · CC BY 4.0
**Page:** `summaries/luo_et_al_2022_pancancer_caf_atlas_natcommun.md`

**Summary:** 855,271 unsorted cells from 226 samples across 10 solid cancer types. Its main topic, fibroblast subtypes, is out of scope.

**What it contributes:**
- **A second source for Level 1 markers:** epithelial EPCAM/KRT19, fibroblast DCN/COL1A1, endothelial VWF/PECAM1, myeloid CD68/CD14, plasma IGHG1/JCHAIN.
- **The only source for stromal–immune mimics,** which matter at the Level 1 immune vs. stromal step:
  - fibroblasts expressing macrophage genes (CD68, CD163, CD14)
  - fibroblast/endothelial hybrids (possibly pericytes)
  - nerve-like cells clustering with fibroblasts
  - **DCs expressing the T-cell markers CD3D/CD3E**

**Watch out for:** only two markers per compartment and no negative markers; pericytes not separated from fibroblasts; simple QC with no ambient-RNA correction; mimic populations inferred from trajectories with limited validation.

---

## Method lessons

### 5. Nofech-Mozes et al. 2023: scATOMIC
**Citation:** Nofech-Mozes I, Soave D, Awadalla P, Abelson S. *Pan-cancer classification of single cells in the tumour microenvironment.* Nature Communications 14:1615 (2023). DOI: 10.1038/s41467-023-37353-8 · CC BY 4.0
**Page:** `summaries/nofech_mozes_et_al_2023_scatomic_natcommun.md`

**Summary:** A classifier built for tumor data, trained on ~300,000 cells and validated on 225 biopsies across 13 cancer types. It labels cells down a fixed tree: blood vs. non-blood, then lineage, then type.

**What it contributes:**
- **A working example of the project's core design:** classify down a hierarchy, apply a confidence threshold at each level, and **keep the broader parent label when confidence is low** ("T or NK cell", "macrophage or dendritic cell").
- **Known hard boundaries:** cDC and CD4/CD8 T cells were its weakest immune classes; CD8 T cells were trained into both the CD4 and NK branches because some resemble each.
- **The malignant call:** an expression-based cancer signature agreed with copy-number calls a median 85.9% of the time per biopsy. Disagreements clustered in low-CNV tumors, and in one case copy-number inference missed real cancer cells. Lesson: use both kinds of evidence and flag disagreements.
- **Benchmark evidence:** six common annotation tools were accurate on immune and stromal cells (median F1 > 0.85) but much weaker on cancer cells.

**Watch out for:** no neutrophils, pericytes, or smooth muscle in its tree; part of its immune reference is blood-derived; its gene features are in supplementary data, not the main text.

### 6. Hou & Ji 2024: Assessing GPT-4 for cell type annotation (GPTCelltype)
**Citation:** Hou W, Ji Z. *Assessing GPT-4 for cell type annotation in single-cell RNA-seq analysis.* Nature Methods 21:1462–1465 (2024). DOI: 10.1038/s41592-024-02235-4 · CC BY 4.0
**Page:** `summaries/hou_and_ji_2024_gpt4_cell_type_annotation_natmethods.md`

**Summary:** Tested GPT-4 naming cell types from each cluster's top marker genes across 10 datasets (hundreds of tissues and cell types, including colon cancer, lung cancer, and B-cell lymphoma).

**What it contributes:**
- **The single-LLM baseline:** GPT-4 fully or partly matched expert labels for more than 75% of cell types in most studies, and beat SingleR, ScType, and CellMarker 2.0.
- **Failure modes:** agreement dropped for subtypes, for clusters of 10 or fewer cells, and for malignant cells (missed in B-cell lymphoma). The same input gave a different label 15% of the time.
- **Input guidance for a single prompt:** top 10 Wilcoxon marker genes worked best; prompt style mattered little.
- **The evaluation scheme the later papers reuse:** full match (1), partial match (0.5), mismatch (0), based on the Cell Ontology. A correct Level 1 but wrong Level 2 call is a partial match.

**Watch out for:** agreement with original labels isn't accuracy; possible training-data contamination; tested 2023 GPT-4 versions; labels were free text, not a fixed taxonomy.

### 7. Xie et al. 2026: CASSIA
**Citation:** Xie E, Cheng L, Shireman J, Cai Y, Liu J, Mohanty C, Dey M, Kendziorski C. *CASSIA: a multi-agent large language model for automated and interpretable cell annotation.* Nature Communications 17:389 (2026). DOI: 10.1038/s41467-025-67084-x
**Page:** `summaries/xie_et_al_2026_cassia_multiagent_annotation_natcommun.md`

**Summary:** Separate LLM agents annotate, validate, format, score, and report each cluster label; optional agents refine low-scoring labels and measure agreement across repeated runs. Benchmarked on 970 cell types, plus cancer, immune, and non-model-species datasets.

**What it contributes:**
- **The closest published version of Project B's agent design,** with evidence that each part helps. Fully correct labels rose 12–41% over the next-best method.
- **A validator step:** checks that the markers the annotator cites are actually in the input list (a simple guard against made-up evidence).
- **Confidence thresholds:**
  - quality score below **75/100** → mostly wrong or partly correct; flag for review.
  - agreement across **5 repeated runs**: wrong labels had much lower consensus (median ~60) than correct ones (~90).
- **Cancer prompting:** adding *"You should carefully distinguish between cancer cells and normal cells with reasoning"* raised cancer-cell detection from 72.5% to 88–100%.
- **Expert labels can be wrong:** in 11 of 15 confident disagreements, independent LLMs sided with CASSIA (e.g., "monocytes" that were Schwann cells; "neutrophils" that were macrophages).

**Watch out for:** depends on input marker quality and upstream QC; cancer results rest on 5 datasets; the quality score is itself an LLM judgment; tested models are already superseded; confirm the license before committing the PDF.

### 8. Yang et al. 2026: mLLMCelltype
**Citation:** Yang C, Zhang X, Chen J. *Large language model consensus substantially improves the cell type annotation accuracy for scRNA-seq data.* Communications Biology (2026). DOI: 10.1038/s42003-026-10420-8 · CC BY-NC-ND 4.0 (drafted from the unedited accepted manuscript; figures not available)
**Page:** `summaries/yang_et_al_2026_mllmcelltype_consensus_commsbio.md`

**Summary:** Six LLMs annotate each cluster; clusters they disagree on go to rounds of deliberation. Benchmarked on 49 datasets: 77.2% mean accuracy vs. 61.5% for GPTCelltype.

**What it contributes:**
- **A tested method for level-by-level annotation:** at the finer level, give the model the cluster's parent label and markers comparing it with its **sibling clusters**. This improved fine-level accuracy by 4.8 percentage points.
- **How many markers:** ~8–15 for broad lineages, ~15–25 for subtypes (reconciling Hou & Ji's 10 and CASSIA's ~50).
- **Disagreement thresholds for review:** consensus at or below 66.7%, or Shannon entropy above 1.
- **A trap:** with poor input, all models fell back to broad labels like "T cell" and agreed strongly. **High agreement on a broad label can mean bad data, not confidence.**

**Watch out for:** no tumor-specific evaluation in the main text; figures missing from this version; models share training data, so they can agree confidently on a wrong label; tested models are a generation old.

---

## How the sources fit together

### Marker evidence by annotation decision
| Decision | Primary source | Second source | Key caution |
|---|---|---|---|
| Level 1 broad class (immune / stromal / epithelial) | Lodi 2025 | Luo 2022 | Doublets and stromal–immune mimics (Luo, Domínguez Conde) |
| Malignant vs. normal epithelium | scATOMIC 2023 (lessons) | CASSIA 2026 (prompting) | Markers alone can't show malignancy; needs copy-number or expression-signature evidence |
| T vs. NK | Lodi 2025 | Domínguez Conde 2022 | CD8 T and NK overlap (scATOMIC) |
| CD4 vs. CD8 T | Domínguez Conde 2022 | none yet (gap) | FOXP3 doesn't imply CD4 (Lodi) |
| B vs. plasma | Domínguez Conde 2022 | Lodi 2025 | |
| Monocyte vs. macrophage vs. DC | Caro 2026 | Domínguez Conde 2022, Lodi 2025 | DC3 expresses monocyte/macrophage genes (Caro) |
| Mast cell, pDC | Lodi 2025 | Caro 2026 (pDC) | DCs and mast cells hide in myeloid clusters (Lodi) |
| Fibroblast, endothelial | Lodi 2025 | Luo 2022 | Pericytes not separated (Luo) |

### Design lessons for the agent (from the method papers)
| Lesson | Sources |
|---|---|
| Annotate down a fixed hierarchy: Level 1 first, then Level 2 | scATOMIC, mLLMCelltype, CellTypist (Domínguez Conde) |
| At Level 2, give the parent label and sibling-cluster markers | mLLMCelltype |
| Use ~10–15 markers for Level 1 and ~15–25 for Level 2 (test on lab data) | mLLMCelltype, Hou & Ji, CASSIA |
| When evidence is weak, keep the broader parent label rather than force a finer one | scATOMIC |
| Check that every marker the agent cites is in its input | CASSIA |
| Score each label and send low scores to review (starting point: 75/100) | CASSIA |
| Ask more than once; disagreement across runs is the strongest warning sign | CASSIA, mLLMCelltype, Hou & Ji |
| Don't trust high agreement on a broad label without checking data quality | mLLMCelltype |
| Explicitly instruct the agent to reason about cancer vs. normal, and pair with copy-number evidence | CASSIA, scATOMIC |
| Treat a cluster matching two lineages as a likely doublet until QC says otherwise | Domínguez Conde, Lodi, Luo |
| Record the reasoning, markers used, and score for each label so a scientist can review it | CASSIA, mLLMCelltype |
| Grade the agent with full (1) / partial (0.5) / mismatch (0) against expert labels; check markers before assuming the agent is wrong | Hou & Ji, CASSIA |

## Known gaps
- **Malignant call evidence:** the agent can't infer malignancy from markers alone, and no peer-reviewed copy-number benchmark is included. Copy-number scores would need to be supplied upstream, or epithelial clusters flagged for a scientist.
- **Neutrophils:** no source gives clean lineage markers.
- **Pericytes / smooth muscle cells:** current sources can't separate them from fibroblasts.
- **CD4 vs. CD8 in tumors:** current markers come from healthy tissue; a tumor T-cell source would confirm them.

## Considered and excluded
| Source | DOI | Reason |
|---|---|---|
| Tabula Sapiens Consortium 2026, *Cell* | 10.1016/j.cell.2026.08.010 | Healthy tissue only; no marker tables in the paper |
| Kang et al. 2024, *Nat Commun* 15:4067 | 10.1038/s41467-024-48310-4 | Mostly cell states; no marker table; redundant with Lodi 2025 |
| Nieto et al. 2021, *Genome Res* 31:1913 | 10.1101/gr.273300.120 | Outdated; superseded by Lodi 2025 and scATOMIC 2023 |
| Chang et al. 2026, *bioRxiv* (CNV inference benchmark) | 10.64898/2026.04.12.718050 | Not peer reviewed |
| Chen et al. 2025, *arXiv* (CellTypeAgent) | arXiv:2505.08844 | Not peer reviewed |

## Open questions for review
1. Does the **stromal** class split into fibroblast and endothelial at Level 2?
2. Is a **DC3-like** cluster labelled "cDC2" or "DC (unresolved)" at Level 2?
3. Does the taxonomy include **neutrophils, pericytes, or smooth muscle**? If so, more sources are needed.
4. For the **malignant** class, will copy-number scores be supplied to the agent, or should epithelial clusters always go to a scientist?
