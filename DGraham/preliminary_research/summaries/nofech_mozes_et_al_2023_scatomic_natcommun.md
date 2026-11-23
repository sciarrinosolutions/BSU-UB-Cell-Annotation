# Nofech-Mozes 2023: scATOMIC, a hierarchical pan-cancer cell classifier

**Reference:** Nofech-Mozes I, Soave D, Awadalla P, Abelson S. (2023). *Pan-cancer classification of single cells in the tumour microenvironment.* Nature Communications 14:1615. DOI: 10.1038/s41467-023-37353-8 · PMCID: PMC10036554
**Resource:** [Article](https://doi.org/10.1038/s41467-023-37353-8) · [scATOMIC R package, code, and manual](https://github.com/abelson-lab/scATOMIC) · Reprocessed training/validation data and figure scripts: Zenodo 10.5281/zenodo.7419236
**Open access:** yes, CC BY 4.0.
**Species / tissue:** Human. Training reference of 301,662 cells: patient tumour data plus cancer cell lines from 19 cancer types, a blood CITE-seq dataset, and stromal cells from tumour and normal tissue. External validation on 225 primary biopsies across 13 cancer types (>350,000 cells), plus 62 metastatic biopsies.
**Taxonomy level:** Level 1 (blood vs. non-blood; cancer vs. stromal vs. normal tissue) and Level 2 (immune lineages, endothelial, fibroblast). A **method lessons** paper, not a marker paper. The agent doesn't run scATOMIC; it learns from how scATOMIC makes and checks decisions.

## Why it's in the knowledge base
1. **Its design matches Project B's.** scATOMIC classifies down a fixed cell-type tree (Fig. 1a). At each step, a cell that doesn't pass a confidence threshold **keeps its parent label** instead of being forced into a finer one, e.g. "T or NK cell", "CD4 or CD8 T cell", "Macrophage or dendritic cell" (Fig. 1e, Fig. 4a). That is abstention built into the classifier.
2. **It makes the malignant call without needing CNV.** It scores cancer-specific up- and down-regulated programs to separate cancer cells from normal cells of the same tissue (Fig. 1f). That matters most in tumours with low CNV burden, where copy-number calls are least reliable (Fig. 3; Supp. Fig. 8).
3. **It's benchmarked in tumours against the usual tools** (Fig. 2c), so it shows where automated annotation is reliable (immune and stromal cells) and where it isn't (cancer cells).

## The classification tree (Fig. 1a)
| Level | Branches |
|---|---|
| Top | Blood cell vs. non-blood cell |
| Non-blood | Cancer cell (grouped by organ system, then cancer type) · Stromal (endothelial, fibroblast) · Oligodendrocyte · Enteric glial |
| Blood | B/plasma (B, plasma) · Myeloid (dendritic: ASDC, pDC, cDC; monocyte/macrophage: monocyte, macrophage) · Mast · HSPC · T/NK |
| T/NK | CD4 T (Treg, naive, Tfh, effector/memory) · CD8 T and NK (naive CD8, effector/memory CD8, exhausted CD8, NK) |

Two design notes:
- **CD8 T cells sit in both T/NK branches.** The authors found some CD8 T cells look more like NK cells (cytotoxic) and others more like CD4 T cells, so they trained them into both. This performed better than a single branch (Methods; Supp. Fig. 1). It's further evidence that the CD8/NK and CD4/CD8 boundaries are where classifiers struggle.
- **States in the tree are finer than Level 2.** Collapse Treg, naive, Tfh, effector/memory, and exhausted labels to CD4 T or CD8 T.

## Key results
- **Accuracy:** internal 5-fold cross-validation gave median F1 of 0.90–0.99 per cell type (Fig. 2a). External validation gave a median F1 of 0.99 (Fig. 2b).
- **Weakest immune classes** (read from Fig. 2a–b, approximate): cDC (~0.90 internal), HSPC (variable), and CD4/CD8 T cells (lower and more variable in external data than B, plasma, mast, NK, or pDC).
- **Comparison with other tools (Fig. 2c):** all six tools (SingleR, Seurat label transfer, SingleCellNet, scmap-cell, CHETAH, scType) were accurate for non-malignant cells (median F1 > 0.85). For **cancer cells, the others performed much worse.** The next best, SingleR, scored median F1 0.92 (blood), 0.97 (stroma), and 0.76 (cancer), versus 0.95, 0.99, and 0.99 for scATOMIC.
- **Agreement with CNV inference (Fig. 3):** a median of 85.9% agreement with CopyKAT's aneuploid/diploid calls per biopsy. Disagreements clustered in tumours with low CNV levels, subclones, few malignant cells, or few normal reference cells (Supp. Fig. 8).
- **A case where CNV missed cancer cells (Fig. 5c–d):** in an ER-low breast tumour, scATOMIC called a small population malignant, matching the histology report, while CNV inference called it diploid.
- **It handles cells missing from its reference by abstaining.** In a lung dataset, epithelial cells absent from the reference weren't forced into a label; they kept a broader class, and the cancer-signature step then separated normal lung cells from cancer cells (Supp. Fig. 9).

## Lessons for the agent's decisions (Project B interpretation, not stated in the paper)
- **Decide Level 1 before Level 2, down a fixed tree.** Only move to a finer label once the broader one is settled.
- **When evidence for the finer label is weak, stop at the broader one.** Labelling a cluster "T or NK cell" or "myeloid (macrophage or DC unresolved)" and flagging it is a valid outcome, not a failure.
- **Expect errors at the same boundaries scATOMIC found hardest:** cDC vs. macrophage, CD4 vs. CD8 T, and CD8 T vs. NK. Require stronger evidence before committing to these splits.
- **Don't call a cluster malignant from lineage markers alone.** Epithelial markers show tissue of origin, not malignancy. Use copy-number or cancer-signature evidence if it's supplied, and flag the cluster when the two disagree or when no such evidence exists.
- **Watch the share of uncertain calls in a sample.** scATOMIC warns when fewer than 75% of cells get confident labels (Methods; Supp. Fig. 12). Many flagged clusters in one sample may point to a data-quality problem rather than many hard cells.

## Limits and caveats
- **No neutrophils, pericytes, or smooth muscle cells in the tree.** Those cells will be forced into a neighbouring class or left at a parent label.
- **Stromal coverage is thin:** only endothelial cells and fibroblasts.
- **Part of the immune reference comes from blood** (a peripheral blood CITE-seq dataset). Tumour-specific myeloid states may be less well represented.
- **Validation ground truth isn't independent of other tools.** It used authors' labels, checked with CNV inference for cancer cells and with CITE-seq surface proteins for blood cells.
- **Not a source of marker rules.** The genes used per class are in Supplementary Data 7, not the main text. Its query preprocessing also imputes expression (MAGIC), which differs from standard marker-based workflows.
- **Package version described is v1.1.0 (2023).** Check the GitHub repository for updates before using it.

## Relevance to Project B
A **working, tumour-tested example of the project's core design:** a fixed hierarchy, a confidence threshold at each level, and abstention to the parent label when evidence is weak. It also shows which boundaries are hardest in tumour data, and that the malignant call needs evidence beyond lineage markers, ideally from more than one source.

---
**Review status:** Unreviewed · Drafted by Claude from the published PDF (uploaded by user) · Value: high (method lessons: hierarchy + abstention design) · Revised 2026-10-22 for the lessons-not-tools approach · Student check: pending (David Graham)
