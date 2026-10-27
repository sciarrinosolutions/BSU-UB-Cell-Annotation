# Domínguez Conde 2022: Cross-tissue immune cell atlas and CellTypist

**Reference:** Domínguez Conde C*, Xu C*, Jarvis LB*, Rainbow DB*, Wells SB*, … Saeb-Parsy K, Jones JL, Teichmann SA. (2022). *Cross-tissue immune cell analysis reveals tissue-specific features in humans.* Science 376(6594): eabl5197. DOI: 10.1126/science.abl5197 (*co-first authors)
**Resource:** [CellTypist tool and models](https://www.celltypist.org) · [CellTypist code and tutorials](https://github.com/Teichlab/celltypist) · [Interactive atlas](https://www.tissueimmunecellatlas.org) · Analysis code: Zenodo 10.5281/zenodo.6334988 · Raw data: ArrayExpress E-MTAB-11536
**Open access:** yes, CC BY 4.0 (author manuscript in Europe PMC).
**Version note:** drafted from the author manuscript; figure numbers match the published version, but check against the final article if quoting.
**Species / tissue:** Human, **healthy** tissue from 12 deceased organ donors. 16 tissues: bone marrow, spleen, lymph nodes, blood, lung, liver, gut segments, thymus, muscle, omentum. Immune cells only; ~330,000 immune cells. 10x 5′ and 3′, with TCR and BCR sequencing.
**Taxonomy level:** Level 2 for immune lineages (T CD4/CD8, NK, B, plasma, monocyte, macrophage, DC subsets). Also a method-lessons source: **CellTypist**, an automated classifier that labels at two hierarchy levels. The agent doesn't run CellTypist; it learns from how CellTypist was built and where it struggled.

## Why it's in the knowledge base
1. **Lessons from CellTypist.** It's a logistic-regression classifier trained on 19 harmonised datasets from 20 tissues, with a high-hierarchy model (32 broad types) and a low-hierarchy model (91 types). Reported F1 was about 0.9 at both levels (Fig. 1C, Fig. S9). It shows that a two-level immune hierarchy, like Project B's, can be annotated accurately, and it documents where automated annotation struggled.
2. **Explicit Level 2 lymphoid markers,** including CD4 vs. CD8 (Fig. 4B), which Lodi 2025 lacked.
3. **Labelled doublet clusters** in each compartment, which show what mixed-lineage artifacts look like.

Out of scope: tissue distributions, tissue-resident subsets, TCR/BCR clonality, isotype usage.

## Marker evidence (human)
Genes as given in the text or on figure dot-plot axes. Figure-only genes are marked "dot plot". Check them against the published figure before citing as rules.

**Lymphoid (Fig. 4B; text)**
| Level 2 label | Markers | Notes | Where |
|---|---|---|---|
| T cell (any) | CD3D, CD3E (dot plot also CD3G) | | Fig. 4B |
| CD4 T | CD4, CD40LG (dot plot) | Naive/central memory CD4 and CD8 T cells are transcriptionally close (both CCR7, SELL high), so use CD4/CD8 genes, not naive-state genes | Fig. 4B; text |
| CD8 T | CD8A, CD8B (dot plot) | Memory CD8 subsets separate by CCR9, CX3CR1, CRTAM (states, out of scope) | Fig. 4B; text |
| Regulatory T (CD4) | FOXP3, CTLA4 | Finer than Level 2; see Lodi 2025: FOXP3 does not by itself imply CD4 | Text |
| MAIT | TRAV1-2, SLC4A10 | Invariant T cell; label as T at Level 2 unless the taxonomy splits it | Text |
| γδ T | (TCRγδ sequencing); a subset expresses ITGAD, CRTAM, IKZF2 | **Co-clustered with cytotoxic αβ T cells**; transcriptome alone was not decisive | Text; Fig. S22–23 |
| NK | FCGR3A (CD16) or NCAM1 (CD56) | Two NK clusters. **No productive TCR chains**, a useful negative check if TCR data exist | Text |
| ILC3 | PCDH9 (among others) | Small cluster **mixed with NK cells** | Text |
| B cell | MS4A1, CD19 (memory); TCL1A (naive) | | Text; Fig. 3B |
| Germinal center B | AICDA, BCL6 | | Text |
| Plasmablast / plasma cell | CD38, XBP1, SDC1; plasmablasts also MKI67 | | Text |

**Myeloid (Fig. 2B; text)**
| Level 2 label | Markers | Notes | Where |
|---|---|---|---|
| cDC1 (DC1) | XCR1, CLEC9A | | Text |
| cDC2 (DC2) | CD1C, CLEC10A | | Text |
| Migratory DC | CCR7, LAMP3 | A state of cDC1/cDC2 (see Caro 2026) | Text |
| Classical vs. non-classical monocyte | Differ in CD14, FCGR3A, CX3CR1 | Classical: CD14 high; non-classical: FCGR3A, CX3CR1 | Text |
| Macrophage | C1QA (dot plot); tissue subsets add other genes | CellTypist **resolved monocytes from macrophages** despite their continuum (text) | Fig. 2B; text |

## Doublets and mixed clusters: abstention triggers
- **Labelled doublet clusters in every compartment:** myeloid–T ("MNP/T doublets", expressing CD3E alongside myeloid genes), myeloid–B ("MNP/B"), and T–B ("T/B doublets") (Fig. 2A–B, Fig. 3A–B). *Guidance:* a cluster with strong markers from two lineages, such as CD3E plus C1QA, is presumptively a doublet until doublet scores say otherwise.
- **γδ T cells co-clustered with cytotoxic αβ T cells,** and ILC3 with NK cells. *Guidance:* at Level 2, call these "T cell" or "NK/ILC" and flag rather than force a finer label.
- **A mixed "T_CD4/CD8" cluster appears in Fig. 4A.** *Guidance:* don't split CD4 vs. CD8 on a cluster expressing both; flag it.

## Lessons from CellTypist for the agent's decisions (Project B interpretation, not stated in the paper)
- **Label clusters, not individual cells.** CellTypist's majority voting over clusters (Fig. 1C workflow) assigns one label per cluster, which matches how the agent works from cluster marker lists.
- **Expect weaker calls for cell types that are rare or poorly described.** CellTypist's accuracy depended strongly on how well a type was represented in training (Fig. S9C). The agent's equivalent is how well a type is covered by the knowledge base and literature; rare types deserve extra caution.
- **Some populations need a scientist even when an automated method is confident.** The authors still curated populations missing from the training set by hand, such as γδ T subsets. Flag these rather than force a label.
- **An immune-trained method can't label non-immune cells.** The version described covers immune cells only; the same applies to any evidence the agent uses, so check that a cluster's candidate labels come from the right Level 1 class.

## Limits and caveats
- **Healthy tissue, not tumor.** Lineage markers transfer, but tumor-specific states and proportions don't. Tumor-associated macrophages and DC3-like cells are underrepresented (see Caro 2026, Lodi 2025).
- **Immune cells only;** no epithelial, stromal, or endothelial labels.
- **Several marker genes come from dot-plot axes,** not tables. Confirm them against the published Fig. 2B, 3B, 4B before turning them into rules.
- **Two dissociation protocols were used across sites.** The authors report compositional differences weren't driven by protocol (Fig. S12).
- **Deceased organ donors,** some with trauma (e.g., one donor with lung contusions drove a macrophage subset).

## Relevance to Project B
A core Level 2 reference for **lymphoid** calls: T vs. NK, CD4 vs. CD8, B vs. plasma. It's a second source for the cDC1/cDC2/monocyte markers in Caro 2026. It also introduces **CellTypist**, whose two-level hierarchy and cluster-level labelling support the agent's design, and whose weak spots (rare types, γδ T cells, populations missing from training) show where the agent should be most cautious.

---
**Review status:** Unreviewed · Drafted by Claude from the Europe PMC author manuscript (uploaded by user) · Value: high for lymphoid Level 2 and method lessons · Revised 2026-10-22 for the lessons-not-tools approach · Student check: pending (David Graham)
