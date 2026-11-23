# SCimilarity (cell atlas foundation model + kNN)

**Rank on the Open Problems Immune Cell Atlas: #4 (scaled score 0.840), for the "kNN" variant, which is the "best" SCimilarity entry.**

| | SCimilarity (kNN) | SCimilarity (default) |
|---|---|---|
| Immune Cell Atlas scaled score | **0.840** | 0.788 |
| Immune Cell Atlas accuracy / macro F1 | 0.875 / 0.740 | 0.835 / 0.637 |
| Runtime / peak memory (Immune Cell Atlas) | 23 min / 55 GB | 29 min / 55 GB |
| Mean scaled score over 6 datasets | 0.449 | 0.390 |

The low mean is **not** poor accuracy. SCimilarity is human-only, so it is "not applicable" on the two mouse datasets (HypoMap, Mouse Pancreatic Islet) and scores 0 there. On the 4 human datasets it averages 0.673 (kNN), close to the other top methods. Tabula Sapiens is where it, like everyone else, does badly.

## How it works

SCimilarity is a **pretrained foundation model** from Genentech (Heimberg, Kuo et al., *Nature* 2025). It learns a 128-dimensional embedding in which **"distance = biological dissimilarity" across studies**.

1. **Architecture.** A fully connected encoder takes 28,231 genes (log-normalised counts in a fixed gene order) through layers of 1024 → 1024 → 1024 → **128** units. The output is normalised to unit length, so every cell lies on a 128-dimensional hypersphere. Training uses heavy dropout: 40% on the inputs and 50% on hidden layers.
2. **Training objective, two losses combined:**
   - **Triplet loss (supervised metric learning).** Each triplet is an *anchor* cell, a *positive* cell of the same Cell Ontology type **from a different study**, and a *negative* cell of a different type. The loss pulls the anchor and positive together and pushes the negative at least a margin away. Triplets whose labels are in an ancestor–descendant relationship in the Cell Ontology (for example "T cell" vs. "CD8 T cell") are excluded as ambiguous. Hard-triplet mining keeps only the most informative ones.
   - **Reconstruction (MSE) loss (unsupervised).** A decoder rebuilds the expression profile, so the embedding keeps finer state information. The chosen model weights reconstruction heavily (β = 0.001).
3. **Training data:** 7.9 million cells from 56 studies with 203 Cell Ontology labels, with 15 further studies (1.4 million cells) held out for testing. The full searchable reference is 23.4 million cells from 412 studies.
4. **Native annotation (the "default" variant):** embed a query cell, find its **50 nearest neighbours** in a prebuilt hnswlib index of the 7.9-million-cell annotated training set, and take their label. **No training on your data is needed.**
5. **Cell search:** the same embedding can find cells similar to any query profile or centroid across the 23.4-million-cell atlas, for example "where else does this macrophage state appear?"

Diagrams of each part are in `docs/model_training.png`, `docs/annotation_model.png`, `docs/query_model.png` and `docs/search_engine.png`. The details are in the paper's Methods ([Heimberg et al. 2025](https://doi.org/10.1038/s41586-024-08411-y)).

## How Open Problems ran it (two variants)

Sources: [`openproblems_implementation/scimilarity_knn/script.py`](openproblems_implementation/scimilarity_knn/script.py) and [`openproblems_implementation/scimilarity/script.py`](openproblems_implementation/scimilarity/script.py). Both use model v1.1.

- **Shared steps:** raw counts → gene symbols → `align_dataset` to SCimilarity's gene order (missing genes are zero-filled, with at least 5000 overlapping genes required) → `lognorm_counts` → 128-d embeddings. The model is **frozen**: no fine-tuning on the benchmark data.
- **kNN variant (the 0.840 result):** trains a scikit-learn `KNeighborsClassifier(n_neighbors=50)` on the *training donors'* SCimilarity embeddings **with the dataset's own labels**, then classifies the test donor. In effect, a pretrained embedding with a simple supervised classifier on top.
- **Default variant (0.788):** uses SCimilarity's built-in annotation, which returns its own Cell Ontology vocabulary. Benchmark code then maps those labels onto the dataset's labels: exact string matches first, then repeated linear-sum assignment on Jaccard distances computed from the training donors. Label-vocabulary mismatch costs about 0.05 in score and about 10 points of macro F1.
- Human datasets only. Mouse datasets exit as "not applicable".

## When it performs well

- **Human data with standard, Cell Ontology-style cell types**, especially common immune and tissue cell types that are well represented in its 56 training studies.
- **No usable reference** (default mode): it annotates out of the box against a 7.9-million-cell multi-study reference. The paper reports accuracy comparable to tissue-specific scANVI or CellTypist models, for example 86.5% on healthy kidney vs. 85.2% for scANVI and 90.4% for CellTypist.
- **Fine immune subsets supported by surface protein:** on a held-out CITE-seq dataset with 22 immune subsets, it scored 75.3% accuracy vs. 52.2% for scANVI and 59.1% for CellTypist.
- **Cross-study generalisation:** it is trained to put the same cell type from *different studies* together, so new datasets embed without retraining. Each cell is annotated on its own, with no clustering.
- **Exploration beyond labels:** cell search (finding similar states across 412 studies) and Integrated Gradients gene-importance scores, which recovered known markers with an average AUC of 0.84 against DE markers.

## When it struggles

- **Cancer cells: deliberately left out of training.** From the paper: "we deliberately withheld cancer cells and cell lines from training due to lack of clear cell type identity and these may not be well represented in the current model." This matters directly for our tumour use case. Immune and stromal cells *in* tumours are likely fine; malignant cells are not.
- **Fetal samples, granulocytes, haematopoietic stem and progenitor cells, and intermediate precursor states:** the authors report "poor performance" on these, because training data are mostly adult tissue and lineage commitment is ambiguous.
- **Label vocabulary.** Native annotation can only output Cell Ontology terms seen in training. Custom or finer labels need the kNN-on-embeddings approach, which still requires a labelled reference.
- **Closely related states:** monocytes vs. macrophages vs. DCs, NK vs. NKT vs. CD8 T cells, memory vs. naive T cells, CD56bright vs. CD56dim NK cells. The paper found every method, including SCimilarity, disagreed with author labels here.
- **Rare cell types with k = 50:** a type with only a handful of training cells near the query can be outvoted by abundant neighbours. This is our interpretation, and it fits SCimilarity's lower macro F1 (0.740) than scANVI's (0.797).
- **Non-human data, and data missing many of its 28,231 genes** (for example targeted panels): genes are zero-filled, and too little overlap fails the alignment check.
- **Compute:** about 55 GB of memory in the benchmark, and a model file to download (several GB).

## Relevance to our project

- **Promising:** it needs no per-dataset training, uses Cell Ontology labels (a standard vocabulary for an agent to reason over), and has a cell-search feature. An agent could query "which atlas cells look like this cluster?" as evidence for an annotation, and gene-attribution scores make the reasoning explainable.
- **Caution:** malignant cells weren't in training, so use it for the **immune and stromal compartments** of tumours. Myeloid states (monocyte, macrophage and DC boundaries) are a known weak spot for every method, and they're a focus of our group.

## Papers

Each paper links to its journal page by DOI. Where the journal version is paywalled, [`../papers.csv`](../papers.csv) gives a link to a free open-access copy (PMC, arXiv, a preprint or the author's copy).

| Paper | What it is |
|---|---|
| [Heimberg et al. 2025](https://doi.org/10.1038/s41586-024-08411-y) | **The SCimilarity paper** (*Nature* 638, 2025), PMC open access. Open Problems cites the 2023 bioRxiv preprint, 10.1101/2023.07.18.549537 |

## Files in this folder

| Path | What it is |
|---|---|
| `github/scimilarity_README.rst` | Genentech/scimilarity GitHub README |
| `docs/index.rst`, `docs/about.rst`, `docs/install.rst`, `docs/tutorials.rst` | Documentation site sources (including model download instructions) |
| `docs/cell_annotation_tutorial.md` | Official cell annotation tutorial (converted from notebook) |
| `docs/training_tutorial.md` | Official model training tutorial (converted from notebook) |
| `docs/*.png` | Official diagrams: model training, annotation, query and search engine |
| `openproblems_implementation/scimilarity_knn/` | Benchmark code for the **kNN variant** (best result) |
| `openproblems_implementation/scimilarity/` | Benchmark code for the default (native annotation) variant |

## Links

- Code: https://github.com/Genentech/scimilarity
- Docs: https://genentech.github.io/scimilarity/
- Paper: Heimberg G., Kuo T. et al. (2025) *Nature* 638:1085–1094. https://doi.org/10.1038/s41586-024-08411-y
- Open Problems implementations: https://github.com/openproblems-bio/task_label_projection/tree/f52ca0a9c28a6dc72520871de56ed3102c87c840/src/methods/scimilarity_knn
