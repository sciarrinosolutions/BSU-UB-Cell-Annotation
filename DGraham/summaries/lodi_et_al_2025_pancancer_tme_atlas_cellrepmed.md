# Lodi 2025: Spatially informed pan-cancer atlas of the tumor microenvironment

**Reference:** Lodi F, Vanmassenhove S, Chen D, Boeckx B, … Qian J, Marine J-C, Lambrechts D. (2025). *Decoding tumor heterogeneity: A spatially informed pan-cancer analysis of the tumor microenvironment.* Cell Reports Medicine 6:102416. DOI: 10.1016/j.xcrm.2025.102416 · PMCID: PMC12629804
**Resource:** [Full text (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12629804/) · [Shiny atlas: full marker lists per cell type and subtype](http://apps.lambrechtslab.sites.vib.be/PanCancer-Atlas) · [Code](https://github.com/lambrechtslab/Pan-cancer_Lodietal) · Read counts: https://lambrechtslab.sites.vib.be/en/dataaccess
**Open access:** yes, CC BY-NC 4.0.
**Species / tissue:** Human. 230 fresh samples from 160 patients, 9 cancer types: breast, cervical, colorectal, glioblastoma, hepatocellular, ovarian (HGSOC), head and neck, melanoma, and NSCLC. Samples were 53.9% primary tumor, 15.2% metastasis, 21.7% adjacent normal tissue, and 9.1% tumor-invaded lymph node. 10x 5′ and 3′ data. **One dissociation protocol for all samples, no cell sorting.** 611,750 cells after QC.
**Taxonomy level:** Level 1 (all major compartments) and Level 2 for T vs. NK, B vs. plasma, mast, pDC, cDC, monocyte/macrophage. Its 70 subtypes are finer than Level 2 and out of scope.

## Why it's in the knowledge base
- **Best current Level 1 marker panel.** Three markers per compartment for 10 major types, applied consistently across 9 cancer types (Fig. 1D).
- **Data comparable to the lab's.** Unsorted 10x data from one standardized protocol. A bulk RNA-seq comparison showed immune cells were only modestly over-represented, and to a similar degree across cancer types (Fig. S1B).
- **Documented annotation pitfalls** (below), which should become abstention or QC checks.

Out of scope and omitted here: the 70 subtypes, the TLS and type-1 immunity "hubs", the T-cell reactivity score, cell–cell interactions, and immunotherapy and survival associations.

## Marker evidence: Level 1 (human)
Exactly as shown in Fig. 1D. These are the 3 display markers per type; full lists are in the Shiny app.

| Level 1 label | Markers | Notes |
|---|---|---|
| T cell | CD3D, CD3E, TRAC | |
| NK cell | NCAM1, KLRC3, KLRC1 | Separated from T cells by lacking the T-cell genes |
| B cell | CD79A, CD79B, MS4A1 | Plasma cells were grouped under B cells in this paper (see Level 2) |
| Macrophage/monocyte | CD68, LYZ, AIF1 | Neutrophils fell inside this cluster |
| Dendritic cell | LILRA4, XCR1, CLEC9A | Display set covers pDC and cDC1. cDC2 markers in Level 2 table |
| Mast cell | MS4A2, TPSAB1, CPA3 | |
| Cancer/epithelial | EPCAM, KRT7, KRT18 | **Tissue-specific genes** were also used. No malignant-vs-normal method reported |
| Fibroblast | COL1A1, COL10A1, BGN | |
| Endothelial | CLDN5, PECAM1, VWF | |

Tissue-specific types were also found and should not be forced into the labels above: oligodendrocytes and microglia (glioblastoma), alveolar cells (lung), and hepatocytes (liver).

## Marker evidence: Level 2 (human)
| Level 2 label | Markers used in paper | Notes / distinguishing evidence | Where |
|---|---|---|---|
| Mast cell | MS4A2, TPSAB1, CPA3 | Methods misprint "TSPAB"; Fig. 1D shows TPSAB1 | Methods; Fig. 1D |
| pDC | LILRA4, CXCR3 | | Methods |
| cDC (cDC1/cDC2) | CLEC9A, XCR1 (cDC1); CD1C (cDC2) | Methods lists them together with migratory-DC genes | Methods |
| Migratory/mature DC | CCR7, CCL17, CCL19 | A **state** derived from cDC1 or cDC2, not its own lineage | Results; Fig. S3H |
| Langerhans-like DC | CD1A, CD207 | | Methods |
| DC3, AXL DC | Described as cDC2-related; no marker list in main text | Consistent with Caro 2026: treat as cDC2 family at Level 2 | Results; Fig. 3F |
| Classical monocyte | Shares CCR2 with monocyte-like macrophages | Monocyte and macrophage signatures form a **continuum** across subtypes, so there's no clean cutoff | Fig. 3C–E |
| Macrophage | Higher macrophage signature, lower monocyte signature | Early macrophages sit next to monocytes | Fig. 3E |
| Neutrophil | Within macrophage/monocyte cluster; described by CXCL8, IL1B, VEGFA, ADM | These are inflammatory/hypoxia genes, **not** clean lineage markers. Use another source for neutrophil rules | Results; Fig. 3C |
| B cell (follicular) | MHC class II, CD40, CD80, CD86; memory B: CD27+ | | Results; Fig. S3A |
| Plasmablast / plasma cell | Plasmablast: IGHM− ; plasma: IGHG1 (IgG) or IGHA1 (IgA); PRDM1 high in mature | | Results; Fig. S3A |
| CD8 T vs. CD4 T | Not listed as a rule in the main text | See FOXP3 caveat below | Fig. 2A |

## Annotation pitfalls the agent should check
1. **DCs and mast cells hide inside myeloid clusters.** They co-clustered with other myeloid cells and were only separated at higher clustering resolution using the markers above (Methods). *Guidance:* before labelling a whole myeloid cluster "macrophage", check for pDC, cDC, and mast markers within it.
2. **Neutrophils sit within the macrophage/monocyte compartment.** *Guidance:* don't assume a myeloid cluster is all monocyte/macrophage, and don't call neutrophils from inflammatory genes alone.
3. **FOXP3 does not imply CD4.** CD8+ regulatory T cells expressed CD3E, FOXP3, and CD8A but not CD4, plus ITGAE, NT5E, LAG3, FASLG, and GZMB, and lacked CD28 and IL7R (Fig. S2I). *Guidance:* call CD4 vs. CD8 from CD4/CD8A themselves, never from FOXP3.
4. **Technical artifacts form fake clusters.**
   - **Hemoglobin genes** (ambient RNA) drove clusters in T and B cells; the authors removed them from variable genes.
   - **Dissociation stress, interferon response, and cell cycle** created stress-high, IFN-high, and proliferating clusters until regressed out.
   - **Doublet clusters** expressed markers of two lineages and had higher-than-expected doublet rates (DoubletFinder).
   *Guidance:* a cluster defined mainly by hemoglobin, stress, or mixed-lineage genes should be flagged, not labelled.
5. **Monocyte/macrophage boundary is a continuum** (Fig. 3E), consistent with Caro 2026. Abstain when a cluster sits mid-gradient.

## Limits and caveats
- **Only 3 display markers per Level 1 type in the paper;** fuller lists are only in the Shiny app.
- **No negative markers stated.**
- **Malignant vs. normal epithelial cells weren't separated by a reported method;** cancer and epithelial cells were one class, defined partly by tissue-specific genes.
- **Fibroblasts and cancer cells weren't subclustered** because of patient-to-patient variability.
- **Not all treatment-naive:** cervical cancer samples and 38.7% of liver cancer patients had prior therapy.
- **Mixed tissue types:** ~22% adjacent normal tissue and ~9% lymph nodes. Proportions differ from tumor-only data.
- **Small sample numbers for some cancer types** (e.g., glioblastoma n = 8); the authors advise caution in per-cancer comparisons.

## Relevance to Project B
Use this as the **primary citation for Level 1 marker rules**. It's more complete than Luo 2022, which can serve as a second source. For Level 2, it supports the T vs. NK, B vs. plasma, mast, pDC, and cDC rules. It agrees with Caro 2026 that DC3 belongs to the cDC2 family and that the monocyte/macrophage boundary is blurry. Its pitfall list maps directly onto agent checks: look for DCs and mast cells inside myeloid clusters, never infer CD4 from FOXP3, and flag artifact-driven clusters.

---
**Review status:** Unreviewed · Drafted by Claude from the published PDF (uploaded by user) · Value: high for Level 1, moderate for Level 2 · Student check: pending (David Graham)
