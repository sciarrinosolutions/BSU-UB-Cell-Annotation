# Multilayer perceptron (MLP, on PCA coordinates)

**Rank on the Open Problems Immune Cell Atlas: #5 (scaled score 0.825)**

| | Immune Cell Atlas | Mean over all 6 datasets |
|---|---|---|
| Scaled score (0 = random, 1 = perfect) | 0.825 | 0.767 |
| Accuracy | 0.868 | |
| Macro F1 (sensitive to rare cell types) | 0.700 (lowest of the top 5) | |
| Runtime / peak memory | 30 min / 15 GB (CPU only) | |

It has the same inputs as logistic regression, but is slower (30 min vs. 1 min) and slightly worse here. It does have the **best result of the top 5 on Tabula Sapiens** (0.261, 2nd overall), the hardest dataset.

## How it works

An MLP is a **feed-forward neural network**, essentially logistic regression with learned non-linear features in front of it.

1. **Input:** each cell's 100-dimensional PCA coordinates (centred and scaled, from log-CP10k expression). These are the same features logistic regression uses.
2. **Hidden layers:** two fully connected layers of 100 neurons each. Each neuron computes a weighted sum of the previous layer and applies **ReLU** (`max(0, x)`). Stacking these layers lets the network bend the decision boundaries, which a linear model can't.
3. **Output layer:** one unit per cell type with a **softmax**, giving class probabilities exactly as in logistic regression.
4. **Training:** minimise **cross-entropy loss** plus a small L2 weight penalty. Gradients come from **back-propagation** ([Rumelhart et al. 1986](https://doi.org/10.1038/323533a0); the review cited by Open Problems is [Hinton 1989](https://doi.org/10.1016/0004-3702(89)90049-0)). Weights are updated with the **Adam** optimiser ([Kingma & Ba 2015](https://doi.org/10.48550/arXiv.1412.6980)) on mini-batches.

### Exact settings

Source: [`openproblems_implementation/mlp/script.py`](openproblems_implementation/mlp/script.py) and `config.vsh.yaml`

```python
MLPClassifier(hidden_layer_sizes=(100, 100), max_iter=1000)   # other settings at scikit-learn defaults
```

The scikit-learn defaults are: ReLU activation, the `adam` solver, `learning_rate_init=0.001`, `alpha=1e-4` (L2 penalty), `batch_size=min(200, n_cells)`, and `early_stopping=False`. Training stops when the *training* loss improves by less than `tol=1e-4` for 10 epochs in a row, or after 1000 epochs.

- With no validation-based early stopping and a small L2 penalty, the network can **overfit the training donors**.
- It gets no batch information, like logistic regression. PCA is computed on all cells before the split.
- There is no hyperparameter tuning, and the random weight initialisation makes results vary somewhat from run to run.

The theory and practical tips (scaling, tuning `alpha`, choosing the solver) are in [`docs/sklearn_user_guide_neural_networks_supervised.rst`](docs/sklearn_user_guide_neural_networks_supervised.rst).

## When it performs well

- **Boundaries between cell types that are non-linear in PCA space,** which logistic regression can't draw. This is a plausible reason it beats LR on Tabula Sapiens (0.261 vs. 0.166) and matches it on HypoMap (0.993 vs. 0.990, against scANVI's 0.995).
- **Large, clean, well-balanced training sets.** With enough cells per type, the extra capacity can be used without overfitting.
- **Limited memory.** It used about 15 GB with no GPU, similar to logistic regression and far below scANVI's 65 GB.
- **A cheap, generic deep-learning baseline.** Neural-network annotators built for cells (for example ACTINN, which is in the Abdelaal benchmark) follow the same idea and were among the top classifiers in some of the experiments in [Abdelaal et al. 2019](https://doi.org/10.1186/s13059-019-1795-z).

## When it struggles

- **Rare cell types.** It has the lowest macro F1 of the top 5 on the Immune Cell Atlas (0.700), and 0.29 on GTEX v9 vs. 0.44 for LR. With unweighted cross-entropy, few examples and no early stopping, small classes are either ignored or memorised.
- **Shift between training and test donors.** Extra capacity can fit donor-specific quirks that don't carry over to the held-out donor. On GTEX v9 it falls to 10th place (0.655), while logistic regression is 2nd (0.770).
- **Compute vs. benefit.** It took 30 min vs. LR's 1 min on the Immune Cell Atlas, with a slightly worse score.
- **Hyperparameter sensitivity.** Layer sizes, `alpha`, learning rate and stopping rules all matter, and the benchmark used defaults. A tuned MLP, with validation early stopping and class weighting, would probably do better.
- **Interpretability.** Unlike LR there's no direct gene weight per cell type. You'd need post-hoc attribution methods.
- **Novel cell types.** Softmax always outputs one of the known labels, often with high confidence.

## Relevance to our project

Mostly useful as a **baseline**. It shows that adding non-linearity on top of PCA isn't enough to beat models that handle batch (scANVI) or that are linear and well regularised (LR). If we train our own classifier head, for example on top of foundation-model embeddings or agent-selected marker features, these lessons apply directly: validation early stopping across donors, class weighting for rare immune subsets, and a confidence threshold for unknowns.

## Papers

Each paper links to its journal page by DOI. Where the journal version is paywalled, [`../papers.csv`](../papers.csv) gives a link to a free open-access copy (PMC, arXiv, a preprint or the author's copy).

| Paper | What it is |
|---|---|
| [Hinton 1989](https://doi.org/10.1016/0004-3702(89)90049-0) | **The reference cited by Open Problems** (DOI 10.1016/0004-3702(89)90049-0), *Artificial Intelligence* 40:185–234. The author's copy, hosted on cs.toronto.edu |
| [Rumelhart et al. 1986](https://doi.org/10.1038/323533a0) | Back-propagation (*Nature* 323:533–536). The author's copy, hosted on cs.toronto.edu |
| [Kingma & Ba 2015](https://doi.org/10.48550/arXiv.1412.6980) | Adam optimiser (scikit-learn's default MLP solver), arXiv:1412.6980 |
| [Pedregosa et al. 2011](https://jmlr.org/papers/v12/pedregosa11a.html) | scikit-learn paper (the implementation used) |
| [Abdelaal et al. 2019](https://doi.org/10.1186/s13059-019-1795-z) | 22-classifier annotation benchmark, including neural-network methods |

## Files in this folder

| Path | What it is |
|---|---|
| `github/scikit-learn_README.rst` | scikit-learn GitHub README |
| `docs/sklearn_user_guide_neural_networks_supervised.rst` | scikit-learn user guide: MLP math, algorithms and tips |
| `openproblems_implementation/mlp/` | Exact benchmark code and config (commit `f52ca0a`) |

## Links

- Code: https://github.com/scikit-learn/scikit-learn
- Docs: https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html
- Reference: Hinton G.E. (1989) "Connectionist learning procedures." *Artificial Intelligence* 40:185–234. https://doi.org/10.1016/0004-3702(89)90049-0
- Open Problems implementation: https://github.com/openproblems-bio/task_label_projection/tree/f52ca0a9c28a6dc72520871de56ed3102c87c840/src/methods/mlp
