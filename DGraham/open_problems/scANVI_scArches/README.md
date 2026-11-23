# scANVI + scArches (reference mapping by "architectural surgery")

**Rank on the Open Problems Immune Cell Atlas: #2 (scaled score 0.858, essentially tied with logistic regression). Best mean score over all 6 datasets (0.793).**

| | Immune Cell Atlas | Mean over all 6 datasets |
|---|---|---|
| Scaled score (0 = random, 1 = perfect) | **0.858** | **0.793** (best non-control method) |
| Accuracy | **0.904** (best of all methods) | |
| Macro F1 (sensitive to rare cell types) | 0.726 (4th of the top 5) | |
| Runtime / peak memory | 31 min / 63 GB (GPU) | |

The **highest accuracy** combined with a **lower macro F1** means it gets the abundant cell types right more often, but does worse on rare ones than scANVI or logistic regression.

## How it works

scArches is not a model of its own. It is a **transfer-learning recipe** that can be applied to any *conditional* autoencoder (scVI, scANVI, totalVI, trVAE and others). Here it is applied to scANVI, so the model itself is the one described in [`../scANVI/README.md`](../scANVI/README.md).

1. **Build the reference.** Train scVI, then scANVI, on the labelled reference only (the training donors). The batch (donor) enters the network as a one-hot vector **s** in the first layer of the encoder and decoder: `f1(x, s) = ReLU(Wx·x + Ws·s)`.
2. **Architectural surgery.** When a query arrives with new, unseen batches **s′**, scArches adds new randomly initialised input weights **W_s′** for those batches, called **"adaptors"**: `f1(x, s, s′) = ReLU(Wx·x + Ws·s + Ws′·s′)`. This is applied to both the encoder and the decoder.
3. **Fine-tune only the adaptors.** All reference weights are **frozen**, including the scANVI classifier. Only the adaptors are trained on the unlabelled query, which usually means 4–5 orders of magnitude fewer trainable parameters than training a full model. The reference's latent space doesn't move, so the query is **projected into** a fixed reference.
4. **Predict:** the frozen scANVI classifier labels each query cell from its latent **z**, and the label probabilities serve as uncertainty scores.

The math is in [`docs/scvi-tools_user_guide_transfer_learning_scArches.md`](docs/scvi-tools_user_guide_transfer_learning_scArches.md), and the full method and evaluation in [Lotfollahi et al. 2022](https://doi.org/10.1038/s41587-021-01001-7).

## How Open Problems ran it

Source: [`openproblems_implementation/scanvi_scarches/script.py`](openproblems_implementation/scanvi_scarches/script.py) and `config.vsh.yaml`

- Raw counts, all genes, `batch` = `donor_id`, one held-out donor as the query.
- Reference architecture: `n_latent=30`, `n_layers=2`, `n_hidden=128`, `dropout_rate=0.2`, layer norm, `encode_covariates=True`.
- The reference trains **scVI first** (early stopping, 90/10 train/validation split), then scANVI is initialised from it and trained (early stopping).
- Query step: `SCANVI.load_query_data(test, model)`, then training with `weight_decay=0.0`. Weight decay would otherwise shrink the frozen weights.
- **Query training defaults to `max_epochs=2`** in the config. The script's local-test block says 200, but the config default is what the benchmark used. So the adaptors get very little training, which may help explain the weaker rare-type performance.
- Unlike plain scANVI, the test cells **never influence the reference model**. This is a more realistic "new patient arrives" setting.

## When it performs well

- **Mapping new samples onto an existing, well-built reference** without retraining it. You can download a pretrained reference (for example from the scArches model zoo on Zenodo) and map your data in minutes. In Open Problems the runtime includes building the reference, which you'd only do once in practice.
- **Many queries over time.** Adaptors "commute": mapping order doesn't matter and the reference stays fixed, which suits a reference that keeps growing.
- **Sharing models without sharing data.** The reference model can be shared when the raw data can't (patient privacy).
- **Keeping biology that the reference doesn't have.** When the disease effect isn't seen in training, it isn't removed. COVID-19 query cells mapped onto a healthy reference kept their disease-specific states, such as monocyte-derived macrophages that are absent from the reference. Cells from an unseen tissue got high uncertainty scores (above 50% uncertainty → reported as "unknown"). See the paper's Figs. 4–5.
- **Abundant, well-defined cell types and consistently good accuracy across datasets.** It has the best mean score over the 6 Open Problems datasets.

## When it struggles

- **Small or narrow references.** The authors note that "a small reference along with a low number of studies leads to poor integration of query data while removing biological variation such as nuanced cell types." Reference quality limits everything.
- **Rare cell types.** It has the lowest macro F1 of the top 3 on the Immune Cell Atlas. The classifier is frozen, and the query adaptors (2 epochs here) can only shift the query into the reference space, not reshape the decision boundaries.
- **Query batch effects that adaptors can't absorb** (very different technology or chemistry). Only the first layer gets new parameters.
- **Novel cell types are not labelled novel by default.** The scANVI classifier still outputs a known label, and you have to threshold the uncertainty yourself.
- **It inherits the limits of the base model:** you get a latent space, not a corrected expression matrix, plus GPU or memory needs and hyperparameter sensitivity.
- **Tabula Sapiens:** every method fails there (0.237 scaled for scArches, though that's 2nd-best on that dataset).

## Relevance to our project

This is the closest fit to a **"map each new tumour sample onto a fixed immune reference"** workflow: a pretrained healthy immune reference, with each patient mapped as a query. The COVID result suggests disease-specific (for example tumour-associated) states would stay separate rather than be forced onto healthy ones in the *latent space*. The *labels* would still need an uncertainty threshold. Mapping order not mattering is useful for an agent that processes samples one at a time.

## Papers

Each paper links to its journal page by DOI. Where the journal version is paywalled, [`../papers.csv`](../papers.csv) gives a link to a free open-access copy (PMC, arXiv, a preprint or the author's copy).

| Paper | What it is |
|---|---|
| [Lotfollahi et al. 2022](https://doi.org/10.1038/s41587-021-01001-7) | **The scArches paper** (*Nat Biotechnol* 2022), PMC open access. Open Problems cites its preprint, 10.1101/2020.07.16.205997 |
| [Xu et al. 2021](https://doi.org/10.15252/msb.20209620) | The scANVI paper (the base model being transferred) |
| [Lopez et al. 2018](https://doi.org/10.1038/s41592-018-0229-2) | scVI base model |
| [Gayoso et al. 2022](https://doi.org/10.1038/s41587-021-01206-w) | scvi-tools library (the implementation the benchmark uses) |
| [Luecken et al. 2022](https://doi.org/10.1038/s41592-021-01336-8) | scIB integration benchmark |
| [Abdelaal et al. 2019](https://doi.org/10.1186/s13059-019-1795-z) | Annotation-classifier benchmark |

## Files in this folder

| Path | What it is |
|---|---|
| `github/scarches_README.rst` | theislab/scarches README |
| `github/scvi-tools_README.md` | scvi-tools README |
| `docs/scvi-tools_user_guide_transfer_learning_scArches.md` | The architectural-surgery math |
| `docs/scvi-tools_user_guide_scanvi.md`, `docs/scvi-tools_user_guide_scvi.md` | Base model math |
| `docs/tutorial_scarches_reference_mapping_scvi-tools.md` | Official scvi-tools reference mapping tutorial |
| `docs/tutorial_scanvi_surgery_pipeline_scarches.md` | scArches scANVI surgery tutorial (the procedure the benchmark followed) |
| `docs/tutorial_scvi_scanvi_harmonization.md`, `docs/tutorial_scanvi_classifier_fix.md` | Background tutorials (scANVI label transfer; the 1.1.0 bug fix) |
| `openproblems_implementation/scanvi_scarches/` | Exact benchmark code and config (commit `f52ca0a`) |

## Links

- Code: https://github.com/scverse/scvi-tools (implementation used) and https://github.com/theislab/scarches (original package and model zoo)
- Docs: https://docs.scvi-tools.org/en/stable/user_guide/background/transfer_learning.html and https://scarches.readthedocs.io
- Paper: Lotfollahi M. et al. (2022) *Nat Biotechnol* 40:121–130. https://doi.org/10.1038/s41587-021-01001-7
- Open Problems implementation: https://github.com/openproblems-bio/task_label_projection/tree/f52ca0a9c28a6dc72520871de56ed3102c87c840/src/methods/scanvi_scarches
