# Logistic regression (on PCA coordinates)

**Rank on the Open Problems Immune Cell Atlas: #3 (scaled score 0.858, tied with scANVI+scArches to three decimals). 2nd-best macro F1. 12–28× faster than the scANVI models.**

| | Immune Cell Atlas | Mean over all 6 datasets |
|---|---|---|
| Scaled score (0 = random, 1 = perfect) | **0.858** | 0.780 |
| Accuracy | 0.885 | |
| Macro F1 (sensitive to rare cell types) | 0.779 (2nd, behind scANVI's 0.797) | |
| Runtime / peak memory | **1.1 min / 16 GB (CPU only)** | |

Compare scANVI (13 min, 65 GB, GPU) and scANVI+scArches (31 min, 63 GB, GPU). Logistic regression got within 0.01 of both on a fraction of the compute.

## How it works

Multinomial logistic regression is a **linear classifier**. For each cell type *k* it learns a weight vector **w_k** and an intercept *b_k*. A cell with features **x** gets a score `s_k = w_k·x + b_k` for every type, and the **softmax** turns these scores into probabilities: `P(type k | x) = exp(s_k) / Σ_j exp(s_j)`. Training minimises the **cross-entropy** (log loss) over labelled cells, plus an L2 penalty that keeps the weights small. The decision boundaries between types are **straight hyperplanes** in feature space.

In this benchmark the features **x** aren't genes. They are each cell's **100-dimensional PCA coordinates**, centred and scaled, computed from log-CP10k-normalised expression. So the model works on a compressed summary of the main axes of variation.

### Exact settings (scikit-learn defaults)

Source: [`openproblems_implementation/logistic_regression/script.py`](openproblems_implementation/logistic_regression/script.py)

```python
classifier = sklearn.linear_model.LogisticRegression()       # all defaults
classifier.fit(input_train.obsm["X_pca"], input_train.obs["label"])
```

The defaults are: L2 penalty with `C=1.0` (inverse regularisation strength), the `lbfgs` solver, multinomial (softmax) loss, `max_iter=100`, and no class weighting (so abundant types dominate the loss). No hyperparameters were tuned.

- **No batch correction.** The model never sees the donor or batch variable.
- `X_pca` comes with the common dataset and is **computed before the train/test split**, so the PCA axes were fit on all cells, including the held-out donor. That's based on the task's file specifications in [`../_benchmark/openproblems_task/README.md`](../_benchmark/openproblems_task/README.md). This is mildly transductive and applies equally to the MLP, kNN and XGBoost methods.

The general theory is in [`docs/sklearn_user_guide_logistic_regression.rst`](docs/sklearn_user_guide_logistic_regression.rst). The reference Open Problems gives is a textbook, Hosmer, Lemeshow & Sturdivant (2013), *Applied Logistic Regression*, 3rd ed., Wiley. It isn't freely available, so it's not included.

## Why it does so well here

- **Clean, consistent labels within one study.** All donors in the Immune Cell Atlas were processed and annotated by one group with one pipeline, so batch effects between donors are modest. Explicit batch modelling (scANVI's main advantage) matters less.
- **PCA already captures the main cell type axes.** In scRNA-seq, the top principal components mostly separate cell types, and in that space many types are close to linearly separable.
- **The labels themselves were partly made by logistic regression.** This is our interpretation and needs checking. The Immune Cell Atlas is the dataset from the CellTypist paper ([Domínguez Conde et al. 2022](https://doi.org/10.1126/science.abl5197)). Its cell types were assigned with **CellTypist, an L2-regularised logistic regression** trained by SGD on immune reference data, followed by manual curation. A linear classifier may reproduce label boundaries that were partly drawn by a linear classifier, which could favour logistic regression on this dataset in particular.
- **Broad evidence that simple wins.** The Open Problems paper reports that on all four v1 datasets "a simple logistic regression model outperforms more complex methods that explicitly model batch effects, such as Seurat or scANVI, even when noise is added to the training data" ([Luecken et al. 2025](https://doi.org/10.1038/s41587-025-02694-w)). Abdelaal et al. 2019, comparing 22 classifiers, found a *general-purpose linear classifier* (SVM) "has overall the best performance" ([Abdelaal et al. 2019](https://doi.org/10.1186/s13059-019-1795-z)).

## When it performs well

- **References and queries from the same study or protocol, with modest batch effects.** It's in the top 3 of all 16 benchmarked method variants on 4 of 6 datasets: 2nd on DKD (0.946), GTEX v9 (0.770) and Mouse Pancreas (0.949), and 3rd on the Immune Cell Atlas (0.858). On HypoMap it scores 0.990, where all top methods are within 0.005.
- **Little compute or time, or many repeated runs.** A good baseline to try first, and cheap to retrain when labels change.
- **Interpretability.** Coefficients on PCs can be projected back to genes through the PCA loadings. CellTypist trains the same model directly on genes, which gives a direct gene × cell type weight matrix, effectively a learned marker list ([Domínguez Conde et al. 2022](https://doi.org/10.1126/science.abl5197), [`github/celltypist_README.md`](github/celltypist_README.md)).
- **Probabilities out of the box.** The softmax output can be thresholded to mark low-confidence cells.

## When it struggles

- **Large batch or technology differences between reference and query.** Nothing models batch. If the held-out donor's cells are shifted in PCA space, the hyperplanes misclassify them, and methods with explicit batch handling should win as the shift grows.
- **Rare cell types.** With no class weighting, the loss favours abundant types. PCA also gives little variance, and so few dimensions, to small populations. On GTEX v9 its macro F1 is 0.44 against 0.88 accuracy, meaning rare types are badly missed.
- **Non-linear or very subtle distinctions** (for example closely related T cell states) that a hyperplane in 100 PCs can't separate.
- **Novel cell types.** Softmax always picks one of the training labels, and probabilities on out-of-distribution cells can be overconfident.
- **Heterogeneous splits** like Tabula Sapiens (0.166), where the held-out donor seems to have tissues missing from training. Every method fails there.
- **Under-converged fits.** `max_iter=100` with lbfgs may stop early on large datasets. Raising it, or tuning `C`, could change results, and the benchmark didn't try.

## Relevance to our project

A **strong, cheap baseline** that any agent-based method must beat, and it beats or matches the deep models here. CellTypist's version, trained on genes, is directly useful to us. It has pretrained immune models (for example `Immune_All_Low.pkl`) with fine-grained monocyte and T cell types, outputs per-gene weights that could feed an agent's marker reasoning, and is already in our literature list (see `DSciarrino/annotation_explorer`). The main risk in tumours is batch and patient shift, plus malignant or unseen states that the softmax will silently force into a known label.

## Papers

Each paper links to its journal page by DOI. Where the journal version is paywalled, [`../papers.csv`](../papers.csv) gives a link to a free open-access copy (PMC, arXiv, a preprint or the author's copy).

| Paper | What it is |
|---|---|
| [Pedregosa et al. 2011](https://jmlr.org/papers/v12/pedregosa11a.html) | scikit-learn paper (the implementation used) |
| [Domínguez Conde et al. 2022](https://doi.org/10.1126/science.abl5197) | **CellTypist / Immune Cell Atlas paper**: logistic regression for immune annotation, and the source of this benchmark dataset |
| [Abdelaal et al. 2019](https://doi.org/10.1186/s13059-019-1795-z) | 22-classifier annotation benchmark (linear SVM best overall) |

## Files in this folder

| Path | What it is |
|---|---|
| `github/scikit-learn_README.rst` | scikit-learn GitHub README |
| `github/celltypist_README.md` | CellTypist GitHub README (logistic regression built for cell annotation) |
| `docs/sklearn_user_guide_logistic_regression.rst` | The logistic regression section of the scikit-learn user guide (math, solvers, regularisation) |
| `openproblems_implementation/logistic_regression/` | Exact benchmark code and config (commit `f52ca0a`) |

## Links

- Code: https://github.com/scikit-learn/scikit-learn
- Docs: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- Reference (cited by Open Problems): Hosmer D.W., Lemeshow S., Sturdivant R.X. (2013) *Applied Logistic Regression*, Wiley. Not open access.
- CellTypist: https://github.com/Teichlab/celltypist and https://www.celltypist.org
- Open Problems implementation: https://github.com/openproblems-bio/task_label_projection/tree/f52ca0a9c28a6dc72520871de56ed3102c87c840/src/methods/logistic_regression
