# Open Problems label projection: top 5 methods on the Immune Cell Atlas

Background reading on the five best-scoring cell type annotation methods (scaled score > 0.80) on the **Immune Cell Atlas** dataset of the Open Problems label projection benchmark: https://openproblems.bio/benchmarks/label_projection/

| Folder | Method | Type |
|---|---|---|
| [`scANVI/`](scANVI/README.md) | scANVI | Semi-supervised deep generative model (VAE) with batch modelling |
| [`scANVI_scArches/`](scANVI_scArches/README.md) | scANVI + scArches | Pretrained scANVI reference, with query mapping by transfer learning |
| [`logistic_regression/`](logistic_regression/README.md) | Logistic regression | Linear classifier on 100 PCA components |
| [`SCimilarity/`](SCimilarity/README.md) | SCimilarity (kNN) | Pretrained human cell foundation model embedding, with a kNN classifier |
| [`multilayer_perceptron/`](multilayer_perceptron/README.md) | Multilayer perceptron | Two-hidden-layer neural network on 100 PCA components |
| [`_benchmark/`](#the-_benchmark-folder) | — | The benchmark itself: task code and full results |

Each method folder has a `README.md` covering how the method works, how Open Problems ran it, and when it performs well or poorly. Its "Papers" section links each relevant paper by DOI. It also holds:
- `github/`: README files
- `docs/`: user guides and tutorials, converted to Markdown
- `openproblems_implementation/`: the exact benchmark code

## Papers

The papers are linked by DOI rather than stored in the repository. [`papers.csv`](papers.csv) lists all 14 papers with:
- the full citation and journal DOI;
- a link to a free open-access copy: PMC, arXiv, a preprint, or an author or institutional repository. Use this when the journal version is paywalled;
- which method folders use the paper.

## The benchmark

- **Task:** a method trains on labelled cells from some samples (the reference) and predicts labels for cells from a **held-out sample** (the query).
- **Split:** the data processor randomly holds out **one batch** as the test set ([`_benchmark/openproblems_task/process_dataset/script.py`](_benchmark/openproblems_task/process_dataset/script.py)). For every CELLxGENE dataset the batch is **`donor_id`**, so every test is "annotate a new donor."
- **Immune Cell Atlas:** Domínguez Conde et al., *Science* 2022 (the CellTypist paper, [Domínguez Conde et al. 2022](https://doi.org/10.1126/science.abl5197)). About 360k immune cells from 16 tissues of 12 adult donors (healthy organ donors, not cancer), loaded from CELLxGENE Census (2023-07-25) with its Cell Ontology `cell_type` labels.
- **Metrics:** accuracy and F1 (macro, micro, weighted) ([Grandini et al. 2020](https://doi.org/10.48550/arXiv.2008.05756)).
  - **Macro F1** weights every cell type equally, so it's the one that shows how well **rare** types are handled.
  - Accuracy and micro F1 are the same number here.
- **Scaled score:** each metric is min–max scaled between the control methods: random labels and majority vote set the floor, and true labels give 1. The scaled metrics are then averaged. I recomputed this from the data embedded in the web page ([`_benchmark/label_projection_page_data.json`](_benchmark/label_projection_page_data.json)), and the result matches the site's > 0.80 cut-off for these five methods. Every method, dataset and metric is in [`_benchmark/label_projection_results_all.csv`](_benchmark/label_projection_results_all.csv).
- **Version:** these are the current website results (task commit `f52ca0a`, January 2025, 6 CELLxGENE datasets). The Open Problems paper ([Luecken et al. 2025](https://doi.org/10.1038/s41587-025-02694-w), *Nat Biotechnol* 2025, author manuscript) describes an **earlier** version with different datasets (pancreas, Tabula Muris Senis lung, CeNGEN, zebrafish).

## Top 5 at a glance (Immune Cell Atlas)

| Rank | Method | Scaled score | Accuracy | Macro F1 | Runtime | Peak memory | GPU | Mean score, 6 datasets |
|---|---|---|---|---|---|---|---|---|
| 1 | scANVI | **0.867** | 0.893 | **0.797** | 13 min | 65 GB | yes | 0.780 |
| 2 | scANVI + scArches | 0.858 | **0.904** | 0.726 | 31 min | 63 GB | yes | **0.793** |
| 3 | Logistic regression | 0.858 | 0.885 | 0.779 | **1 min** | 16 GB | no | 0.780 |
| 4 | SCimilarity (kNN) | 0.840 | 0.875 | 0.740 | 23 min | 55 GB | yes | 0.449* |
| 5 | Multilayer perceptron | 0.825 | 0.868 | 0.700 | 30 min | 15 GB | no | 0.767 |

\*SCimilarity is human-only and scores 0 ("not applicable") on the two mouse datasets. Its mean over the 4 human datasets is 0.673.

For comparison: Seurat TransferData 0.786, XGBoost 0.775, kNN 0.772, scGPT zero-shot 0.621. Geneformer, scGPT fine-tuned and scPRINT failed to run, and UCE scored near random.

### Scaled score on every dataset

| Method | DKD (human kidney) | GTEX v9 (human, 8 tissues) | HypoMap (mouse brain) | Immune Cell Atlas | Mouse Pancreas | Tabula Sapiens |
|---|---|---|---|---|---|---|
| scANVI | 0.945 | 0.769 | **0.995** | **0.867** | 0.947 | 0.155 |
| scANVI + scArches | 0.945 | **0.773** | 0.990 | 0.858 | **0.955** | 0.237 |
| Logistic regression | **0.946** | 0.770 | 0.990 | 0.858 | 0.949 | 0.166 |
| SCimilarity (kNN) | 0.942 | 0.732 | n/a | 0.840 | n/a | 0.179 |
| Multilayer perceptron | 0.939 | 0.655 | 0.993 | 0.825 | 0.931 | **0.261** |

Bold marks the best of these five. On DKD, XGBoost (0.948) is the best method overall.

## How they differ mechanically

| | scANVI | scANVI + scArches | Logistic regression | SCimilarity (kNN) | MLP |
|---|---|---|---|---|---|
| **Input** | Raw counts, all genes | Raw counts, all genes | 100 PCs of log-normalised data | Log-normalised counts in a fixed 28,231-gene order | 100 PCs of log-normalised data |
| **Model** | VAE; latent prior is a Gaussian mixture over cell types; classifier on the latent | Same model; reference frozen, new "adaptor" weights per query batch | Linear softmax classifier | Frozen pretrained encoder (triplet + reconstruction loss, 23M-cell corpus) → 128-d embedding → kNN, k=50 | 2 × 100 ReLU layers → softmax |
| **Batch handling** | Explicit (batch is an input to the encoder and decoder) | Explicit (query batch gets its own adaptors) | None | Implicit (trained to align the same type across studies) | None |
| **Sees test cells during training?** | **Yes**, unlabelled (transductive) | Only to fit the adaptors; the reference is fixed | No (but PCA was fit on all cells) | No (embedding is frozen) | No (but PCA was fit on all cells) |
| **Trained on this dataset?** | Yes, from scratch | Yes (reference), then the query | Yes | Only the kNN; the embedding is pretrained | Yes |
| **Output** | Label + probability | Label + probability | Label + probability | Label (+ neighbour votes) | Label + probability |
| **Detects novel types?** | No (not designed for it) | Partly (high uncertainty for unseen cells; threshold needed) | No | No (kNN mode); cell search can help | No |

## When to reach for which

| Situation | Best bet | Why |
|---|---|---|
| Quick, strong baseline; little compute | **Logistic regression** (or CellTypist) | About 1 min on CPU and within 0.01 of the best. The Open Problems paper found it beat Seurat and scANVI on all v1 datasets |
| Strong batch or donor effects; rare or subtle subtypes matter | **scANVI** | Models batch explicitly and has the best macro F1. Works with partial or seed labels |
| A fixed reference atlas, with new patients mapped one at a time | **scANVI + scArches** | No retraining of the reference, so mapping is fast and order-independent. Keeps disease-specific states separate (shown for COVID-19) |
| Human data with no good labelled reference | **SCimilarity** (native annotation) | Pretrained on 56 studies with Cell Ontology labels; zero-shot annotation and cell search |
| Non-linear boundaries, large balanced data | **MLP** | Beat the others on Tabula Sapiens, but needs tuning (early stopping, class weights) |

## Takeaways for our project (scRNA-seq annotation in cancer with AI agents)

1. **Simple methods are hard to beat.** On the Immune Cell Atlas, logistic regression on 100 PCs scored within 0.01 of the deep models, at roughly 1/12 to 1/28 of the runtime. An agent-based annotator should be benchmarked against it.
2. **The Immune Cell Atlas is healthy tissue, labelled with a logistic regression tool (CellTypist) plus curation.** This could favour linear classifiers. It's our interpretation and worth checking with Dr. Talkington. Results on tumour data may differ, and none of the six datasets is cancer.
3. **Rare types separate the methods more than accuracy does.** Accuracy spans only 0.87–0.90 across the top 5, but macro F1 spans 0.70–0.80. Our monocyte and T cell subtypes are where differences will show.
4. **None of these methods says "I don't know" by default.** All five always output a known label. For tumours, with malignant cells and tumour-specific states, we need an uncertainty or novelty step. scArches uncertainty and SCimilarity query coherence are starting points.
5. **SCimilarity left cancer cells out of training on purpose**, and reports weak performance on granulocytes and progenitors. Use it for the immune and stromal compartments.
6. **Tabula Sapiens breaks everything** (best score 0.32, Seurat). A held-out donor with tissues missing from training appears to be an unsolved case. That's our interpretation of the low scores, not something the site states.

## Caveats

- Each dataset was evaluated on **a single random held-out donor**, with no repeats, so differences of about 0.01 (for example scArches 0.8581 vs. LR 0.8578) aren't meaningful.
- Methods ran with **default or untuned settings**; see each folder's "How Open Problems ran it".
- For paywalled papers, the open copies in [`papers.csv`](papers.csv) are PMC author manuscripts, preprints or author-hosted copies, not the final journal version. The CSV notes which version each one is.

## The `_benchmark/` folder

| Path | What it is |
|---|---|
| `label_projection_results_all.csv` | Every method × dataset: raw metrics, scaled score, runtime, memory |
| `label_projection_page_data.json` | Raw data extracted from the benchmark web page (method info, dataset info, results) |
| `openproblems_task/README.md` | Task README (file formats, API) |
| `openproblems_task/process_dataset/` | Train/test split code |
| `openproblems_task/run_benchmark_main.nf` | Benchmark workflow listing every method that was run |

Papers for the benchmark:

| Paper | What it is |
|---|---|
| [Luecken et al. 2025](https://doi.org/10.1038/s41587-025-02694-w) | Open Problems paper (author's accepted manuscript); Supplementary Note 1.2 covers label projection |
| [Domínguez Conde et al. 2022](https://doi.org/10.1126/science.abl5197) | Source paper of the Immune Cell Atlas dataset (author manuscript) |
| [Grandini et al. 2020](https://doi.org/10.48550/arXiv.2008.05756) | Reference for the accuracy and F1 metrics |

Collected 2026-11-23 from the website and from `openproblems-bio/task_label_projection` at commit `f52ca0a9c28a6dc72520871de56ed3102c87c840`.
