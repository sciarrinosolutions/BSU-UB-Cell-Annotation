# Luo 2022: Pan-cancer single-cell atlas of cancer-associated fibroblasts

**Reference:** Luo H*, Xia X*, Huang L-B*, An H, Cao M, Kim GD, Chen H-N, Zhang W-H, Shu Y, Kong X, … Caulin C, Park J, Xu H. (2022). *Pan-cancer single-cell analysis reveals the heterogeneity and plasticity of cancer-associated fibroblasts in the tumor microenvironment.* Nature Communications 13:6619. DOI: 10.1038/s41467-022-34395-2 · PMCID: PMC9636408 (*equal contribution)
**Resource:** [Full text (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9636408/) · [Interactive atlas](https://gist-fgl.github.io/sc-caf-atlas/) · [Code](https://github.com/Xiaxy-XuLab/PanCAF) · Integrated matrix: GEO GSE210347
**Open access:** yes, CC BY 4.0.
**Species / tissue:** Human. 226 samples (148 primary tumor, 53 adjacent, 25 normal) from 164 donors across 10 solid cancer types, from 12 studies. All 10x Genomics, **no cell sorting**. 855,271 cells after QC.
**Taxonomy level:** Level 1 (all major compartments) and Level 2 for **fibroblast** and **endothelial** only. Paper's main topic, CAF subtypes, is finer than Level 2 and out of scope.

## Why it's in the knowledge base
Two things only:
1. Level 1 compartment markers from a large, unsorted human tumor dataset.
2. Four populations with mixed lineage signals, which are documented abstention triggers.

Everything else in the paper is out of scope for annotation: CAF subtypes and states, trajectories, cell–cell interactions, and immunotherapy and survival associations.

## Marker evidence (human)
Gene lists exactly as the paper gives them.

| Label | Markers used in paper | Notes | Where |
|---|---|---|---|
| Epithelial (Level 1) | EPCAM, KRT19 | Unlike other compartments, epithelial clusters split by cancer type and by tumor vs. normal | Fig. 1c; Supp. Fig. S1d, S2 |
| Fibroblast (Level 1/2) | DCN, COL1A1; ACTA2, ACTG2 | ACTA2 is shared with pericytes and some endothelial-transition cells (see below) | Fig. 1c, 1e |
| Endothelial (Level 1/2) | VWF, PECAM1 | | Fig. 1c, 1e |
| Lymphocyte (Level 1) | CD3D, CD3E | Covers T cells. NK and B were subclustered separately (supplementary figures) | Fig. 1c, 1e |
| Myeloid (Level 1) | CD68, CD14 | Also expressed by some fibroblasts (CAFap, below) | Fig. 1c, 1e |
| Plasma cell (Level 1/2) | IGHG1, JCHAIN | | Fig. 1c, 1e |
| Tumor-associated macrophage | APOE (subsets marked by C1QC or SPP1) | Finer than Level 2; APOE was in ~90% of TAMs | Fig. 1h; Fig. 6 text |

Normal vs. cancer-associated fibroblasts were separated by **tissue of origin**, not by single markers. That's a state distinction; at Level 2, both are "fibroblast."

## Mixed-identity populations: abstention triggers
These cells carry markers from two Level 1 compartments. A simple marker rule would mislabel them.

| Population | What it expresses | Risk for the agent | Where |
|---|---|---|---|
| Antigen-presenting CAF (CAFap) | Fibroblast ACTA2 **plus** HLA-DRA, CD74, and macrophage genes CD68, CD163, CD14; transcriptionally closer to monocyte/macrophage clusters than other fibroblasts | Could be called macrophage, or fibroblast–macrophage doublet. ~10–14% of α-SMA+ stromal cells were CD163+ by imaging in 3 cancer types | Fig. 4a–d; Supp. Fig. S7 |
| Endothelial-to-mesenchymal CAF (CAFEndMT) | Fibroblast RGS5, ACTA2 **plus** endothelial PLVAP, VWF; also ESM1 | Could be called endothelial or fibroblast. **Authors say these may be pericytes**, which they did not separate | Fig. 5a–c; Discussion |
| Peripheral-nerve-like CAF (CAFPN) | MPZ, S100B, PLP1, LGI4 (nerve/Schwann genes) | Clustered with fibroblasts but expresses a nerve program; likely not a true fibroblast | Fig. 4g |
| CD3+ dendritic cells | DC and pDC clusters with CD3D, CD3E | T-cell markers in DCs. Imaging found CD3+ CD11c+ CD86+ cells at 3–13% of CD11c+ myeloid cells | Supp. Fig. S1g–j |

**Agent guidance (Project B interpretation, not stated in the paper):**
- When a cluster scores high on two Level 1 compartments, check doublet scores and library size first.
- If it isn't a doublet, **flag for review** rather than picking the higher-scoring label.
- Don't call T cell from CD3D/CD3E alone if the cluster also has a strong DC signature.
- Don't call macrophage from CD68/CD14/CD163 alone if fibroblast genes (DCN, COL1A1, ACTA2) are high.
- If the taxonomy includes pericytes, this paper can't separate them from fibroblasts; another source is needed.

## Limits and caveats
- **The authors warn that canonical markers may not be restricted to one cell type** and recommend corroborating evidence (Discussion).
- **Pericytes were not separated from fibroblasts.**
- **Only two markers per compartment and no negative markers;** this is a thin basis for rules on its own.
- **QC was simple:** Scrublet for doublets, plus fixed cutoffs (fewer than 200 or more than 6,000 detected genes, more than 20% mitochondrial content). No ambient-RNA correction was reported, which could contribute to some mixed signals.
- **Batch correction was fastMNN,** and clustering was done on the corrected space.
- **Mixed-identity populations were inferred from trajectories,** with limited imaging validation in 3 cancer types. Their origin is not established.

## Relevance to Project B
A secondary source. Use it to (1) cite Level 1 compartment markers alongside a stronger primary source, and (2) document known cross-lineage mimics, so the agent abstains instead of forcing a label. It's not useful for immune Level 2 splits; use the T-cell, myeloid (Caro 2026), and B/NK references for those. If the taxonomy has a pericyte or smooth-muscle label, look for a dedicated stromal source.

---
**Review status:** Unreviewed · Drafted by Claude from PMC full text · Value: moderate (Level 1 markers + abstention triggers) · Student check: pending (David Graham)
