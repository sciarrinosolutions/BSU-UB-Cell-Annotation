# Hou & Ji 2024: Assessing GPT-4 for cell type annotation (GPTCelltype)

**Reference:** Hou W, Ji Z. (2024). *Assessing GPT-4 for cell type annotation in single-cell RNA-seq analysis.* Nature Methods 21:1462–1465. DOI: 10.1038/s41592-024-02235-4
**Resource:** [Article](https://doi.org/10.1038/s41592-024-02235-4) · [GPTCelltype R package](https://github.com/Winnie09/GPTCelltype) · [Analysis code](https://github.com/Winnie09/GPTCelltype_Paper) · Zenodo 10.5281/zenodo.8317406 (package), 10.5281/zenodo.8317410 (analysis)
**Open access:** yes, CC BY 4.0.
**Species / tissue:** Ten datasets covering five species and hundreds of tissues and cell types, with both normal and cancer samples. The cancer data are colon cancer, lung cancer, and B-cell lymphoma. Mostly human.
**Taxonomy level:** Not tied to a level. A **method lessons** paper: how an LLM performs when it names cell types from marker genes, and where it fails.

## Why it's in the knowledge base
This is the baseline that Project B's agent improves on. It shows that a general LLM given a cluster's top marker genes agrees well with expert labels. It also shows where that unconstrained approach breaks down, which is exactly what the project's taxonomy, rule table, abstention, and human review are designed to address.

## What it does
GPT-4 (June 2023 version) received the top differentially expressed genes for each cluster and was asked to name its cell type. Its answers were compared with the original studies' manual labels using a three-level score (Methods):
- **Full match (1):** same label or same Cell Ontology term.
- **Partial match (0.5):** same broad type but a different or finer label (e.g., "fibroblast" vs. "stromal cell").
- **Mismatch (0):** different broad type.

It was compared with GPT-3.5, SingleR, ScType, and CellMarker 2.0, and tested in simulations with mixed, unknown, incomplete, and noisy gene lists.

The basic prompt was: *"Identify cell types of [tissue] cells using the following markers separately for each row. Only provide the cell type name. Do not show numbers before the name. Some can be a mixture of multiple cell types."* followed by one gene list per cluster.

## Key results
- **Agreement with experts:** GPT-4's labels fully or partially matched manual labels for more than 75% of cell types in most studies and tissues (Fig. 2b).
- **Better than the other tools:** average agreement was higher than GPT-3.5, SingleR, ScType, and CellMarker 2.0 across datasets (Fig. 2d). Examples: lung cancer 0.85 vs. SingleR 0.60; colon cancer 0.86 vs. 0.64.
- **Best input:** the **top 10 differential genes from a two-sided Wilcoxon test**. Using 20 or 30 genes, or a t-test, gave lower agreement (Fig. 2a).
- **Prompt style mattered little.** The basic prompt, a chain-of-thought prompt, and repeating the query five times and taking the majority answer performed similarly (Fig. 2a).
- **Where agreement drops** (Fig. 2b):
  - **Major types vs. subtypes:** full matches were more frequent for major types (e.g., T cells) than for subtypes (e.g., CD4 memory T cells).
  - **Small populations:** performance dipped for clusters of 10 cells or fewer.
  - **Cell type:** highest for immune cells such as granulocytes, B cells, and T/NK cells; lower for malignant, endothelial, and epithelial cells.
  - **Malignant cells:** identified in colon and lung cancer but not in B-cell lymphoma. The authors suggest combining with other evidence such as copy-number variation.
- **Some "mismatches" were GPT-4 being more specific.** For cells labelled "stromal cells" by experts, GPT-4 said "fibroblasts/osteoblasts." Collagen gene expression supported GPT-4's finer call (Fig. 2c).
- **Simulations (Fig. 2g):** 93% accuracy telling pure from mixed cell types, and 99% telling known from unknown types. Agreement fell when fewer genes were given or random genes were added, but stayed reasonably high.
- **Reproducibility (Fig. 2h–i):** the same input gave identical labels 85% of the time. Agreement between two GPT-4 versions was substantial: Cohen's kappa 0.65 in the text, 0.67 in Fig. 2i.

## Lessons for the agent's decisions (Project B interpretation, not stated in the paper)
- **Give the agent the top ~10 Wilcoxon marker genes per cluster.** More genes added noise in this study.
- **Don't rely on prompt tricks for accuracy.** Structure is a better lever: a fixed taxonomy and rule table constrain the labels; this paper's prompt did not.
- **Expect the same weak spots:** subtypes, small clusters, and malignant cells. These are where the agent should abstain or ask for review.
- **Don't treat "malignant" as something an LLM can infer from markers alone.** Even GPT-4 struggled; pair it with copy-number or cancer-signature evidence (see scATOMIC 2023, CASSIA 2026).
- **Ask the agent the same question more than once.** Since 15% of repeated queries gave a different label, a cluster whose label changes across runs is a candidate for review.
- **Reuse the paper's scoring scheme for evaluation.** Full / partial / mismatch with Cell Ontology names is a ready-made way to compare the agent's labels with Dr. Talkington's, and it fits a two-level taxonomy, where a correct Level 1 but wrong Level 2 call is a partial match.

## Limits and caveats
- **Agreement isn't accuracy.** Labels were compared with the original authors' manual annotations, which are themselves judgment calls.
- **Possible training-data contamination.** GPT-4's training data is undisclosed, and datasets published before September 2021 may have been seen during training. The authors say those results should be interpreted cautiously.
- **The model is old.** It tested GPT-4 versions from March and June 2023. Current models will behave differently, so treat the numbers as a baseline, not a prediction.
- **Hallucination risk.** The authors recommend experts validate GPT-4 labels before downstream analysis.
- **Unconstrained labels.** GPT-4 chose free-text names, not labels from a fixed taxonomy. The seminar deck lists unconstrained prompting as out of scope for Project B.
- **Brief Communication format.** Short paper; most per-dataset details are in supplementary tables.

## Relevance to Project B
The **reference point for what an unconstrained LLM can and can't do** in cell annotation. It supports the core idea (marker genes plus an LLM gives expert-like labels for major types) and documents the failure modes that justify the project's design: subtypes, small clusters, malignant cells, run-to-run variation, and hallucination. Its full/partial/mismatch scoring is also a practical template for evaluating the agent against expert review.

---
**Review status:** Unreviewed · Drafted by Claude from the published PDF (uploaded by user) · Value: high (LLM baseline + evaluation method) · Revised 2026-10-22 (removed reference to an excluded preprint) · Student check: pending (David Graham)
