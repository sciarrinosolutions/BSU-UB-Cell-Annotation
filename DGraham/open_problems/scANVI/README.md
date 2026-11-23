# scANVI (single-cell ANnotation using Variational Inference)

**Rank on the Open Problems Immune Cell Atlas: #1 (scaled score 0.867)**

| | Immune Cell Atlas | Mean over all 6 datasets |
|---|---|---|
| Scaled score (0 = random, 1 = perfect) | **0.867** | 0.780 |
| Accuracy | 0.893 | |
| Macro F1 (every cell type weighted equally, so it is sensitive to rare types) | **0.797** (best of all methods) | |
| Runtime / peak memory | 13 min / 65 GB (GPU) | |

Per-dataset numbers for every method are in [`../_benchmark/label_projection_results_all.csv`](../_benchmark/label_projection_results_all.csv). The scaled scores were recomputed from the page data the same way Open Problems computes them (see [`../README.md`](../README.md)).

## How it works

scANVI is the semi-supervised version of **scVI**, a variational autoencoder (VAE) for scRNA-seq counts. Both come from the Yosef lab and are distributed in **scvi-tools**.

1. **The generative model (the decoder).** Each cell *n* has a low-dimensional latent vector **z** (about 10–30 numbers). A neural network decoder maps **z** plus the cell's **batch** (here, the donor) to the expected expression of every gene. The observed counts are modelled with a negative binomial or zero-inflated negative binomial distribution, scaled by the cell's library size. Because batch is an input to the decoder, the latent **z** doesn't need to encode batch, so batch effects are factored out of **z**.
2. **The labels enter the prior.** In scVI the prior on **z** is a single standard Gaussian. In scANVI, **z** is generated from a cell type label **c** and a second latent **u**, which gives the latent space a **Gaussian mixture with one component per cell type**. Cells of the same type are encouraged to cluster together, even across batches.
3. **The encoder and classifier.** An encoder network maps a cell's counts to q(**z**|x). A **classifier** network then maps **z** to q(**c**|**z**), a probability for each cell type.
4. **Training** maximises the evidence lower bound (ELBO):
   - for **labelled** cells, using their label;
   - for **unlabelled** cells, summing over all possible labels weighted by the classifier;
   - plus an extra **classification loss** on labelled cells.

   This is why scANVI can use partly labelled data and "seed" labels (a few confidently marker-labelled cells).
5. **Prediction:** each cell gets the label with the highest probability from the classifier, applied to the mean of q(**z**|x). The probabilities can be used as uncertainty scores.

The math is in [`docs/scvi-tools_user_guide_scanvi.md`](docs/scvi-tools_user_guide_scanvi.md) and [`docs/scvi-tools_user_guide_scvi.md`](docs/scvi-tools_user_guide_scvi.md). The full derivation is in [Xu et al. 2021](https://doi.org/10.15252/msb.20209620), and the scVI base model in [Lopez et al. 2018](https://doi.org/10.1038/s41592-018-0229-2).

> **Version note:** scvi-tools 1.1.0 fixed a scANVI bug: the classifier had treated logits as probabilities, which hurt label transfer. Old results (before 2024) may understate scANVI. See [`docs/tutorial_scanvi_classifier_fix.md`](docs/tutorial_scanvi_classifier_fix.md). The benchmark pins `scvi-tools>=1.1.0`.

## How Open Problems ran it

Source: [`openproblems_implementation/scanvi/script.py`](openproblems_implementation/scanvi/script.py)

- Input is **raw counts** (`layers["counts"]`). No HVG subset was used in the benchmark run, because `--num_hvg` has no default, so all genes were kept.
- **Train and test cells are concatenated into one AnnData.** The test cells get the label `"Unknown"`, and one scANVI model is trained on everything. This makes it **transductive**: the held-out donor's cells shape the latent space during training, but their labels are never seen. It's exactly the semi-supervised setting scANVI was built for, and it's a key difference from scANVI+scArches.
- Architecture: `n_layers=2`, `encode_covariates=True`, layer norm instead of batch norm. These are the "scArches-style" settings.
- The scVI model is wrapped directly into scANVI (`SCANVI.from_scvi_model`) **without pretraining scVI first**, and trained with the default number of epochs. The scvi-tools tutorials pretrain scVI first, so tuning here could change results.
- `batch` = `donor_id`. One random donor is held out as the test set (see [`../_benchmark/openproblems_task/process_dataset/script.py`](../_benchmark/openproblems_task/process_dataset/script.py)).

## When it performs well

- **Many batches or donors with real technical differences.** Batch is modelled explicitly, so it shouldn't drive the classification. scANVI was among the top methods for integration in the scIB benchmark ([Luecken et al. 2022](https://doi.org/10.1038/s41592-021-01336-8)), especially for complex, multi-batch atlases.
- **Rare and subtle cell types.** It has the best macro F1 on the Immune Cell Atlas (0.797), ahead of logistic regression (0.779) and scArches (0.726). Xu et al. show it does especially well "where the differences between cell states are too subtle to be captured clearly by a transcriptome-wide similarity measure."
- **Partial, noisy or hierarchical labels.** It works when only some cells or datasets are labelled, including from a few marker-based seed labels ([`docs/tutorial_scanvi_seed_labeling.md`](docs/tutorial_scanvi_seed_labeling.md)). Xu et al. report it is "robust to mislabeling", and it supports a hierarchical label mode.
- **Large datasets.** It scales to millions of cells with mini-batch training on a GPU.
- **You want a probability per label** and a shared latent space for later analysis (UMAP, clustering, differential expression).

## When it struggles

- **Cell types not present in the reference.** The scANVI paper says plainly: "it was not designed to automatically identify previously unobserved labels." Every cell is forced into one of the training labels. Low confidence or poor mixing with the reference are only indirect hints.
- **Very heterogeneous splits where the test donor has tissues or cell types missing from training.** On Tabula Sapiens every method collapses (scANVI: 0.155 scaled, 0.17 accuracy). That's probably a property of the split, not of scANVI.
- **Compute.** It needs a GPU and used about 65 GB of RAM on the Immune Cell Atlas, versus about 1 minute and 16 GB for logistic regression, which scored nearly as well.
- **Small references.** Deep generative models need enough cells and batches to learn a good latent space. Simple classifiers can match or beat it on small or clean data. The Open Problems paper reports that "a simple logistic regression model outperforms more complex methods that explicitly model batch effects, such as Seurat or scANVI" on the four v1 datasets ([Luecken et al. 2025](https://doi.org/10.1038/s41587-025-02694-w)).
- **Hyperparameters and setup.** You need raw counts, a sensible batch key and enough training epochs. Results move with these choices, and the benchmark used mostly defaults.
- **Retraining for every new query.** In transductive mode the whole model is retrained each time new data arrives. scArches was built to avoid this (see [`../scANVI_scArches/`](../scANVI_scArches/README.md)).

## Relevance to our project

- **Pros:** It handles patient (batch) effects and returns calibrated-looking label probabilities that an agent could threshold, for example "uncertain, send to marker check." It works with partial or seed labels, so marker-derived labels from the agent could seed it.
- **Cons for cancer:** malignant cells and tumour-specific states usually aren't in healthy references, and scANVI won't flag them as novel by itself. A pipeline using it would need a separate novelty or uncertainty step.

## Papers

Each paper links to its journal page by DOI. Where the journal version is paywalled, [`../papers.csv`](../papers.csv) gives a link to a free open-access copy (PMC, arXiv, a preprint or the author's copy).

| Paper | What it is |
|---|---|
| [Xu et al. 2021](https://doi.org/10.15252/msb.20209620) | **The scANVI paper** (Xu, Lopez et al. 2021, *Mol Syst Biol*), open access |
| [Lopez et al. 2018](https://doi.org/10.1038/s41592-018-0229-2) | scVI, the base model (*Nat Methods* 2018), PMC author manuscript |
| [Gayoso et al. 2022](https://doi.org/10.1038/s41587-021-01206-w) | scvi-tools library paper (bioRxiv preprint of *Nat Biotechnol* 2022) |
| [Lotfollahi et al. 2022](https://doi.org/10.1038/s41587-021-01001-7) | scArches. Open Problems cites the scArches preprint (10.1101/2020.07.16.205997) as the reference for **both** scANVI entries |
| [Luecken et al. 2022](https://doi.org/10.1038/s41592-021-01336-8) | scIB integration benchmark, where scANVI is a top performer |
| [Abdelaal et al. 2019](https://doi.org/10.1186/s13059-019-1795-z) | Annotation benchmark (22 classifiers, including the older scVI) |

## Files in this folder

| Path | What it is |
|---|---|
| `github/scvi-tools_README.md` | scvi-tools GitHub README |
| `docs/scvi-tools_user_guide_scanvi.md`, `docs/scvi-tools_user_guide_scvi.md` | Model math and training details from the scvi-tools user guide |
| `docs/tutorial_scvi_scanvi_harmonization.md` | Official tutorial: integration and label transfer with scVI and scANVI |
| `docs/tutorial_scanvi_seed_labeling.md` | Official tutorial: annotating from a few marker-defined seed cells |
| `docs/tutorial_scanvi_classifier_fix.md` | The 1.1.0 classifier bug fix and how it changed results |
| `docs/tutorial_scanvi_surgery_pipeline_scarches.md` | The scArches tutorial that Open Problems links as scANVI's documentation |
| `openproblems_implementation/scanvi/` | Exact benchmark code and config (commit `f52ca0a`) |

Tutorials were converted from Jupyter notebooks to Markdown, without figures and long outputs.

## Links

- Code: https://github.com/scverse/scvi-tools
- Docs: https://docs.scvi-tools.org/en/stable/user_guide/models/scanvi.html
- Paper: Xu C., Lopez R. et al. (2021) *Mol Syst Biol* 17:e9620. https://doi.org/10.15252/msb.20209620 (preprint: https://doi.org/10.1101/532895)
- Open Problems implementation: https://github.com/openproblems-bio/task_label_projection/tree/f52ca0a9c28a6dc72520871de56ed3102c87c840/src/methods/scanvi
