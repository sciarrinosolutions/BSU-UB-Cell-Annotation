# Caro 2026: Pan-cancer atlas of tumor-associated dendritic cells (human)

**Reference:** Caro AA*, Kancheva D*, Hadadi E, Boeckx B, De Nolf C, Bardet PMR, Verstaen K, Li L, Oueslati L, Figueras-Duch N, Elkrim Y, Vandamme N, Deschoemaeker S, Blomme A, Close P, Janssens S, De Palma M, Lambrechts D, Coosemans A, Laoui D. (2026). *Pan-cancer single-cell atlases of mouse and human tumor-associated dendritic cells.* Nature Communications. DOI: 10.1038/s41467-026-73721-w (*equal contribution; corresponding author D. Laoui)
**Resource:** [Article](https://www.nature.com/articles/s41467-026-73721-w) · [Accepted manuscript (ORBi, open)](https://orbi.uliege.be/bitstream/2268/346789/1/s41467-026-73721-w_reference.pdf) · Interactive atlas: www.single-cell.be/Laouimmunology/TumorDCAtlas
**Open access:** yes, CC BY-NC-ND 4.0. The unedited PDF can be shared as-is; don't redistribute modified versions of it.
**Version note:** drafted from the "Article in Press" accepted manuscript, which is unedited. Check figure numbers against the final published version.
**Scope used for this page:** human data only, Level 2 labels only. The paper also contains a mouse atlas and fine-grained subsets and states; those are deliberately left out here.
**Species / tissue:** Human tumors from 10 cancer types (breast, colorectal, glioblastoma, hepatocellular, head and neck squamous, lung, melanoma, ovarian, pancreatic, renal), built from public scRNA-seq datasets.
**Taxonomy level:** Level 2, myeloid. Core source for **monocyte vs. macrophage vs. DC**, and for the DC types cDC1, cDC2, and pDC.

## What it does
The authors built a human mononuclear phagocyte (MNP) atlas of 61,432 cells (monocytes, macrophages, DCs, pDCs) from 10 cancer types. They then pulled out the DCs and re-clustered them. Every dataset was annotated with the same marker gene sets before integration (Methods). DC clusters were then checked with whole-signature scores from published fate-mapping and blood DC studies (Fig. 5E, Supp. Fig. 12I), and clusters were tested for statistical separation with sc-SHC.

## Key results relevant to Level 2
- **cDC2 is the most common DC type in human tumors** (Supp. Fig. 12D–E).
- **cDC1, pDC, and mature CCR7+ DCs have distinct signatures** and are straightforward to identify.
- **The hard boundary is cDC2-like cells vs. monocytes/macrophages.** One branch of the cDC2 family, called DC3, expresses several classic monocyte and macrophage genes (details below).
- **Mature (CCR7+) DCs lose their lineage markers.** Some mature DC clusters could not be traced back to cDC1 or cDC2 at all (Fig. 5D/F).

## Marker evidence for Level 2 annotation (human)
Gene lists are exactly as the paper gives them. The "per-dataset" sets come from the Methods, where they were used to annotate each dataset uniformly; the atlas sets come from Results, Fig. 5, and Supp. Fig. 11.

| Level 2 label | Positive markers | Distinguishing / caution | Where in paper |
|---|---|---|---|
| Monocyte (classical) | CD14, FCN1, VCAN; atlas also CFP, S100A8/9 | DC3 and its progenitor share CD14, FCN1, S100A9, VCAN (see warning) | Methods; Supp. Fig. 11 |
| Monocyte (non-classical) | FCGR3A, LST1, CX3CR1; atlas also CDKN1C | DC3 also expresses FCGR3A | Methods; Supp. Fig. 11 |
| Macrophage | C1QA/C1QB high, APOE, APOC1 | Immature macrophages sit between monocyte and macrophage signatures. DC3 also expresses C1QA/C1QC | Methods |
| cDC1 | CLEC9A, XCR1 | Clean lineage; mature cDC1 may lose these and show CCR7, LAMP3 instead | Methods; Fig. 5C |
| cDC2 | FCER1A, CD1C, HLA-DPB1 | The paper calls CD1C specific to human cDC2. CLEC10A marks a cDC2 branch (cDC2B) | Methods; Fig. 5C/F |
| pDC | LILRA4, IRF7; CLEC4C | The paper calls CLEC4C specific to human pDC | Methods; Fig. 5C |
| Mature DC (CCR7+) | CCR7, LAMP3 | Can derive from cDC1, cDC2, or DC3; lineage markers often lost | Methods; Fig. 5D/F |
| Any DC (general) | FLT3 | Supports DC identity across lineages | Fig. 5C |
| Proliferating cells | MKI67, STMN1 (TOP2A) | Not a cell type. Assign Level 2 label from co-expressed markers | Methods; Fig. 5F |

## Warning: cDC2-like cells that look like monocytes or macrophages
The paper defines human **DC3** (a cDC2-like DC) partly by **CD14, C1QA, C1QC, FCGR3A**, and its progenitor **Pro-DC3** by **FCN1, S100A9, VCAN, SELL** (Fig. 5D/F). These are the same genes used to call monocytes and macrophages. Even the authors couldn't separate DC3 from other cDC2 using single genes. They needed whole-signature scores from reference studies (Fig. 5E, Supp. Fig. 12I).

What this means for the rule table:
- **CD14, FCN1, VCAN, C1QA, or FCGR3A alone cannot decide monocyte vs. macrophage vs. DC.**
- **Check for DC identity first** (FCER1A, CD1C, HLA-DPB1, FLT3, CLEC10A). Call monocyte or macrophage only when those are low.
- **Abstain or flag for review** when DC markers and monocyte/macrophage markers are both strong in the same cluster.
- **Open question for Dr. Talkington:** at Level 2, should a DC3-like cluster be labelled "cDC2" or "DC (unresolved)"? The paper treats DC3 as a separate lineage, which the two-level taxonomy may not include.

## Other annotation guidance from the paper
- **Doublets mimic mixed identity.** After DC re-clustering, some clusters expressed C1QA/B, APOE, CD14, FCN1, VCAN. Because real DC3 cells express these genes, the authors removed only clusters that **also** had high doublet scores, unusually many detected genes, and large library sizes, i.e. likely DC–macrophage doublets. Upstream QC used scDblFinder for doublets and CellBender for ambient RNA.
- **Mature DCs without lineage markers.** For a CCR7+ LAMP3+ cluster lacking cDC1 or cDC2 markers, the paper's own approach is to leave the lineage unassigned. The agent can label it "DC" and note that its subtype is unresolved.
- **One cluster lacks the core cDC2 genes.** RORC DCs (RORC, ACY3, PRDM16, TMIGD2) lack FCER1A, CD1C, and PKIB, so the paper did not call them cDC2 (Fig. 5E). If one appears, flag it rather than forcing a cDC2 label.

## Limits and caveats
- **Built from DC-enriched or immune-sorted data.** Datasets pre-sorted for other populations, and whole-tumor data with too few DCs, were excluded. Cell-type proportions won't match unsorted tumor samples.
- **Abundance comparisons across cancer types are indicative only.** Several cancer types had few patients.
- **Most clusters in the paper are states** (ISG-, hypoxic-, heat-shock-, IL1B- and similar). They are out of scope here and should not be used as Level 2 labels.
- **This is a myeloid reference only.** It doesn't cover T, B, NK, or non-immune cells.

## Relevance to Project B
This is the primary current reference for the **human myeloid Level 2 split**. Use the marker table to draft rules for monocyte, macrophage, cDC1, cDC2, pDC, and mature DC. Its biggest contribution is evidence that the monocyte–macrophage–cDC2 boundary is genuinely blurry in tumors. So rules for that split should combine markers, require a positive DC marker before calling a DC, and allow abstention. Domínguez Conde 2022 and Lodi 2025 provide second-source markers for these myeloid types.

---
**Review status:** Unreviewed · Drafted by Claude from the accepted manuscript (Article in Press, ORBi copy); revised for human-only, Level 2 scope · Student check: pending (David Graham)
