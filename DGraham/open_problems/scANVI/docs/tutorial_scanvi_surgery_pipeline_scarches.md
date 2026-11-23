<!-- Converted from theislab/scarches notebooks/scanvi_surgery_pipeline.ipynb (linked from Open Problems method info) (images and long outputs removed) -->

# Semi-supervised surgery pipeline with SCANVI

```python
try:
    from nbproject import header
    header()
except ModuleNotFoundError:
    print("If you want to see the header with dependencies, please install nbproject - pip install nbproject")
```

```text
<IPython.core.display.HTML object>
```

```python
import os
os.chdir('../')
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
```

```python
import scanpy as sc
import torch
import scarches as sca
from scarches.dataset.trvae.data_handling import remove_sparsity
import matplotlib.pyplot as plt
import numpy as np
import gdown
```

```python
sc.settings.set_figure_params(dpi=200, frameon=False)
sc.set_figure_params(dpi=200)
sc.set_figure_params(figsize=(4, 4))
torch.set_printoptions(precision=3, sci_mode=False, edgeitems=7)
```

### Set relevant anndata.obs labels and training length

Here we use the CelSeq2 and SS2 studies as query data and the other 3 studies as reference atlas.

```python
condition_key = 'study'
cell_type_key = 'cell_type'
target_conditions = ['Pancreas CelSeq2', 'Pancreas SS2']
```

### Download Dataset and split into reference dataset and query dataset

```python
url = 'https://drive.google.com/uc?id=1ehxgfHTsMZXy6YzlFKGJOsBKQ5rrvMnd'
output = 'pancreas.h5ad'
gdown.download(url, output, quiet=False)
```

```text
'pancreas.h5ad'
```

```python
adata_all = sc.read('pancreas.h5ad')
```

This line makes sure that count data is in the adata.X. Remember that count data in adata.X is necessary when using "nb" or "zinb" loss.

```python
adata = adata_all.raw.to_adata()
adata = remove_sparsity(adata)
source_adata = adata[~adata.obs[condition_key].isin(target_conditions)].copy()
target_adata = adata[adata.obs[condition_key].isin(target_conditions)].copy()
```

```python
source_adata
```

```text
AnnData object with n_obs × n_vars = 10294 × 1000
    obs: 'batch', 'study', 'cell_type', 'size_factors'
```

```python
target_adata
```

```text
AnnData object with n_obs × n_vars = 5387 × 1000
    obs: 'batch', 'study', 'cell_type', 'size_factors'
```

### Create SCANVI model and train it on fully labelled reference dataset

Preprocess reference dataset. Remember that the adata file has to have count data in adata.X for SCVI/SCANVI if not further specified

```python
sca.models.SCVI.setup_anndata(source_adata, batch_key=condition_key, labels_key=cell_type_key)
```

```text
[34mINFO    [0m Using batches from adata.obs[1m[[0m[32m"study"[0m[1m][0m                                               
[34mINFO    [0m Using labels from adata.obs[1m[[0m[32m"cell_type"[0m[1m][0m                                            
[34mINFO    [0m Using data from adata.X                                                             
[34mINFO    [0m Successfully registered anndata object containing [1;34m10294[0m cells, [1;34m1000[0m vars, [1;34m3[0m batches,
         [1;34m8[0m labels, and [1;34m0[0m proteins. Also registered [1;34m0[0m extra categorical covariates and [1;34m0[0m extra
         continuous covariates.                                                              
[34mINFO    [0m Please do not further modify adata until model is trained.
```

```python
vae = sca.models.SCVI(
    source_adata,
    n_layers=2,
    encode_covariates=True,
    deeply_inject_covariates=False,
    use_layer_norm="both",
    use_batch_norm="none",
)
```

```python
vae.train()
```

Create the SCANVI model instance with ZINB loss as default. Insert "gene_likelihood='nb'," to change the reconstruction loss to NB loss.

```python
scanvae = sca.models.SCANVI.from_scvi_model(vae, unlabeled_category = "Unknown")
```

```python
print("Labelled Indices: ", len(scanvae._labeled_indices))
print("Unlabelled Indices: ", len(scanvae._unlabeled_indices))
```

```text
Labelled Indices:  10294
Unlabelled Indices:  0
```

```python
scanvae.train(max_epochs=20)
```

```text
[34mINFO    [0m Training for [1;34m20[0m epochs.
```

### Create anndata file of latent representation and compute UMAP

```python
reference_latent = sc.AnnData(scanvae.get_latent_representation())
reference_latent.obs["cell_type"] = source_adata.obs[cell_type_key].tolist()
reference_latent.obs["batch"] = source_adata.obs[condition_key].tolist()
```

```python
sc.pp.neighbors(reference_latent, n_neighbors=8)
sc.tl.leiden(reference_latent)
sc.tl.umap(reference_latent)
sc.pl.umap(reference_latent,
           color=['batch', 'cell_type'],
           frameon=False,
           wspace=0.6,
           )
```

```text
<Figure size 1024x320 with 2 Axes>
```

One can also compute the accuracy of the learned classifier

```python
reference_latent.obs['predictions'] = scanvae.predict()
print("Acc: {}".format(np.mean(reference_latent.obs.predictions == reference_latent.obs.cell_type)))
```

```text
Acc: 0.9435593549640567
```

After pretraining the model can be saved for later use

```python
ref_path = 'ref_model/'
scanvae.save(ref_path, overwrite=True)
```

### Perform surgery on reference model and train on query dataset without cell type labels

If the cell types in 'target_adata' are equal to or a subset of the reference data cell types, one can just pass the adata without further preprocessing. It is also possible then to do semi-supervised training with scArches.

However if there are new cell types in 'target_adata' or if there is no '.obs' in the anndata for cell type labels (e.g. the data is unlabeled), one can only use scANVI in an unsupervised manner during surgery due to the nature of the classifier. 

In addition one has to preprocess 'target_adata' in the following way:

If there are new celltypes in there, save the original labels in other column and replace all labels with unlabeled category:

If there is no '.obs' column for cell types:

If 'target_adata' is in the right format, one can proceed with the surgery pipeline. Here we do the surgery unsupervised, but due to the overlapping cell types in query and reference data, one could also do supervised or semi-supervised surgery by setting the indices accordingly.

```python
model = sca.models.SCANVI.load_query_data(
    target_adata,
    ref_path,
    freeze_dropout = True,
)
model._unlabeled_indices = np.arange(target_adata.n_obs)
model._labeled_indices = []
print("Labelled Indices: ", len(model._labeled_indices))
print("Unlabelled Indices: ", len(model._unlabeled_indices))
```

```text
[34mINFO    [0m Using data from adata.X                                                             
[34mINFO    [0m Registered keys:[1m[[0m[32m'X'[0m, [32m'batch_indices'[0m, [32m'labels'[0m[1m][0m                                    
[34mINFO    [0m Successfully registered anndata object containing [1;34m5387[0m cells, [1;34m1000[0m vars, [1;34m5[0m batches, 
         [1;34m8[0m labels, and [1;34m0[0m proteins. Also registered [1;34m0[0m extra categorical covariates and [1;34m0[0m extra
         continuous covariates.                                                              
Labelled Indices:  0
Unlabelled Indices:  5387
```

```python
model.train(
    max_epochs=100,
    plan_kwargs=dict(weight_decay=0.0),
    check_val_every_n_epoch=10,
)
```

```text
[34mINFO    [0m Training for [1;34m100[0m epochs.
```

```python
query_latent = sc.AnnData(model.get_latent_representation())
query_latent.obs['cell_type'] = target_adata.obs[cell_type_key].tolist()
query_latent.obs['batch'] = target_adata.obs[condition_key].tolist()
```

```python
sc.pp.neighbors(query_latent)
sc.tl.leiden(query_latent)
sc.tl.umap(query_latent)
plt.figure()
sc.pl.umap(
    query_latent,
    color=["batch", "cell_type"],
    frameon=False,
    wspace=0.6,
)
```

```text
<Figure size 320x320 with 0 Axes>
```

```text
<Figure size 1024x320 with 2 Axes>
```

```python
surgery_path = 'surgery_model'
model.save(surgery_path, overwrite=True)
```

### Compute Accuracy of model classifier for query dataset and compare predicted and observed cell types

```python
query_latent.obs['predictions'] = model.predict()
print("Acc: {}".format(np.mean(query_latent.obs.predictions == query_latent.obs.cell_type)))
```

```text
Acc: 0.8815667347317616
```

```python
df = query_latent.obs.groupby(["cell_type", "predictions"]).size().unstack(fill_value=0)
norm_df = df / df.sum(axis=0)

plt.figure(figsize=(8, 8))
_ = plt.pcolor(norm_df)
_ = plt.xticks(np.arange(0.5, len(df.columns), 1), df.columns, rotation=90)
_ = plt.yticks(np.arange(0.5, len(df.index), 1), df.index)
plt.xlabel("Predicted")
plt.ylabel("Observed")
```

```text
Text(0, 0.5, 'Observed')
```

```text
<Figure size 640x640 with 1 Axes>
```

### Get latent representation of reference + query dataset and compute UMAP

```python
adata_full = source_adata.concatenate(target_adata)
full_latent = sc.AnnData(model.get_latent_representation(adata=adata_full))
full_latent.obs['cell_type'] = adata_full.obs[cell_type_key].tolist()
full_latent.obs['batch'] = adata_full.obs[condition_key].tolist()
```

```text
[34mINFO    [0m Input adata not setup with scvi. attempting to transfer anndata setup               
[34mINFO    [0m Using data from adata.X                                                             
[34mINFO    [0m Registered keys:[1m[[0m[32m'X'[0m, [32m'batch_indices'[0m, [32m'labels'[0m[1m][0m                                    
[34mINFO    [0m Successfully registered anndata object containing [1;34m15681[0m cells, [1;34m1000[0m vars, [1;34m5[0m batches,
         [1;34m8[0m labels, and [1;34m0[0m proteins. Also registered [1;34m0[0m extra categorical covariates and [1;34m0[0m extra
         continuous covariates.
```

```python
sc.pp.neighbors(full_latent)
sc.tl.leiden(full_latent)
sc.tl.umap(full_latent)
plt.figure()
sc.pl.umap(
    full_latent,
    color=["batch", "cell_type"],
    frameon=False,
    wspace=0.6,
)
```

```text
<Figure size 320x320 with 0 Axes>
```

```text
<Figure size 1024x320 with 2 Axes>
```

### Comparison of observed and predicted celltypes for reference + query dataset

```python
full_latent.obs['predictions'] = model.predict(adata=adata_full)
print("Acc: {}".format(np.mean(full_latent.obs.predictions == full_latent.obs.cell_type)))
```

```text
Acc: 0.9222626108028825
```

```python
sc.pp.neighbors(full_latent)
sc.tl.leiden(full_latent)
sc.tl.umap(full_latent)
plt.figure()
sc.pl.umap(
    full_latent,
    color=["predictions", "cell_type"],
    frameon=False,
    wspace=0.6,
)
```

```text
<Figure size 320x320 with 0 Axes>
```

```text
<Figure size 1024x320 with 2 Axes>
```