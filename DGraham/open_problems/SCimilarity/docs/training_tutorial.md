<!-- Converted from Genentech/scimilarity docs/notebooks/training_tutorial.ipynb (images and long outputs removed) -->

# Data preparation, model training, and building post-training structures

We have transitioned the SCimilarity codebase to the use of [TileDB](https://tiledb.com/) instead of the previously used [Zarr](https://zarr.dev/) to streamline dataloading, training, and building of post-training data structures. 

This tutorial is a high level workflow for training SCimilarity, including data structure requirement, dataloaders, and scripts to build post-training data structures.

The workflow is divided into the following sections:

 1. Process the data into CellArr TileDB format.
 2. Train using the TileDB dataloader.
 3. Build all post-training data structures, such as kNN indices and TileDB arrays.

## 1. Construct a TileDB store in CellArr format

To facilate random access for a cell corpus that is too large to fit into memory, we currently recommend a TileDB structure as used in [CellArr](https://github.com/CellArr/cellarr). The construction requires a collection of AnnData H5AD files which will be organized into TileDB arrays and dataframes by CellArr.

For more details on how to construct CellArr TileDB structures from AnnData H5AD files, please see the [CellArr documentation](https://cellarr.github.io/cellarr/) and the [tutorial](https://cellarr.github.io/cellarr/tutorial_cellxgene.html) to create CellArr objects from CELLxGENE datasets.

**Before you start creating a CellArr object, read the below sections on requirements and processing the AnnData.**

### 1.1 Processing the AnnData

We recommend you process the AnnData before constructing the CellArr. There are required `obs` columns that are described in the next section.

Some important requirements:

 1. `var.index` must be in gene symbols and not Ensemble IDs, you will need to map Ensemble ID to gene symbol.
 2. If you map Ensemble ID to gene symbol, you will need to consolidate counts in cases where multiple Ensemble IDs map to one gene symbol. We provide a utility function for this as `utils.consolidate_duplicate_symbols`.
 3. Please ensure that `var.index` contains only gene symbols as sometimes it can contain a mix of symbols and Ensemble IDs. 

An example of this process, assuming you have mapping tables, is shown below. Please note that this may need to be modified depending on the structure of your mapping table.

```python
def get_id2name(mapping_table_file: str):
    import pandas as pd

    id2name = pd.read_csv(mapping_table_file, delimiter="\t", index_col=0, dtype="unicode")["Gene name"]
    id2name = id2name.reset_index().drop_duplicates().set_index("Gene stable ID")["Gene name"]
    id2name = pd.concat([id2name, pd.Series(id2name.values, index=id2name.values).drop_duplicates()])
    return id2name

def convert_ids_to_names(adata):
    id2name = get_id2name()
    if not any(adata.var.index.isin(id2name.keys())) and "symbol" in adata.var.columns:
        adata.var = adata.var.set_index("symbol", drop=False)
    adata.var.index = adata.var.index.str.replace("'", "")
    adata.var.index = adata.var.index.str.replace('"', "")
    adata = adata[:, (adata.var.index.isin(id2name.keys())) & ~(adata.var.index.isnull())].copy()
    adata.var.index = id2name[adata.var.index]
    return adata

def clean_var(adata):
    from scimilarity.utils import consolidate_duplicate_symbols
    
    adata = convert_ids_to_names(adata)
    adata = consolidate_duplicate_symbols(adata)
    adata.var.index.name = "symbol"
    return adata
```

### 1.2 Required columns

We require specific columns to be present in the metadata by default, many of which are used for filtering cells. If you would like to change the default filter and/or what columns are required, you can do so with the `filter_condition` parameter in the dataloader class  `tiledb_data_models.CellMultisetDataModule`.

You may include any columns you wish in the metadata but the following columns are required by default:

 1. A string column for the study identifier, e.g., `datasetID`.
 2. A string column for sample identifier, e.g., `sampleID`.
 3. A string column for the cell type label identifier that contains the **cell ontology term identifier**, e.g., `cellTypeOntologyID`.
 4. A string column named `tissue` that contains the tissue annotation.
 5. A string column named `disease` that contains the disease annotation.
 6. An int column named `n_genes_by_counts` that contains the number of genes expressed, as produced by `scanpy.pp.calculate_qc_metrics`.
 7. An int column named `total_counts` that contains the number of UMIs, as produced by `scanpy.pp.calculate_qc_metrics`.
 8. An int column named `total_counts_mt` that contains the number of mitochondrial UMIs, as produced by `scanpy.pp.calculate_qc_metrics`.
 9. A float column named `pct_counts_mt` that contains the percentage of mitochondrial UMIs, as produced by `scanpy.pp.calculate_qc_metrics`.
 10. An int column named `predicted_doublets` that is `1` for doublet and `0` for not doublet, as produced by [scrublet](https://github.com/swolock/scrublet) or your choice of doublet detection tool.

**NOTE**: Not every column needs to have values. For example, some cells do not have cell type annotations, in which case you may leave it blank.

An example of this process is shown below. Please note that you may need to customize this based on the columns that exist in your data.

```python
# datasetID and sampleID are explicit as it is not trivial to infer it from obs column names
# Feel free to add cell type ontology ID, tissue, or disease if you wish to make those explicit per AnnData
def clean_obs(adata, datasetID, sampleID):
    # If you wish to use a doublet prediction tool other than scrublet, feel free
    # Though, we will require the "predicted_doublets" column as described previously
    import scrublet as scr
    import scanpy as sc

    # Determine between "MT-" and "mt-"
    mito_prefix = "MT-"
    if any(adata.var.index.str.startswith("mt-")) is True:
        mito_prefix = "mt-"

    # QC stats
    adata.var["mt"] = adata.var_names.str.startswith(mito_prefix)
    sc.pp.calculate_qc_metrics(
        adata,
        qc_vars=["mt"],
        percent_top=None,
        log1p=False,
        inplace=True,
        layer="counts",
    )
    obs = adata.obs.copy()

    obs.columns = [x[0].lower() + x[1:] for x in obs.columns] # lowercase first letter

    obs["datasetID"] = datasetID
    obs["sampleID"] = sampleID

    # Scrublet can fail, so we default to False in that case
    try:
        scrub = scr.Scrublet(adata.layers['counts'])
        doublet_scores, predicted_doublets = scrub.scrub_doublets(verbose=False)
        obs["doublet_score"] = doublet_scores
        obs["predicted_doublets"] = predicted_doublets.astype(int)
    except:
        obs["doublet_score"] = np.nan
        obs["predicted_doublets"] = 0
        pass

    # You will need to go through all columns that might contain cell type ontology
    # or convert cell type name to ontology (see: scimilarity.ontologies for helper functions)
    if "cellTypeOntologyID" not in obs.columns:
        obs["cellTypeOntologyID"] = ""

    # You will need to go through all columns that might contain tissue
    if "tissue" not in obs.columns and "meta_tissue" not in obs.columns:
        obs["tissue"] = ""
    elif "tissue" not in obs.columns and "meta_tissue" in obs.columns:
        obs = obs.rename(columns={"meta_tissue": "tissue"})

    # You will need to go through all columns that might contain disease
    if "disease" not in obs.columns and "meta_disease" not in obs.columns:
        obs["disease"] = ""
    elif "disease" not in obs.columns and "meta_disease" in obs.columns:
        obs = obs.rename(columns={"meta_disease": "disease"})

    columns = [
        "datasetID", "sampleID", "cellTypeOntologyID", "tissue", "disease",
        "n_genes_by_counts", "total_counts", "total_counts_mt", "pct_counts_mt",
        "doublet_score", "predicted_doublets",
    ]
    obs = obs[columns].copy()

    convert_dict = {
        "datasetID": str,
        "sampleID": str,
        "cellTypeOntologyID": str,
        "tissue": str,
        "disease": str,
        "n_genes_by_counts": int,
        "total_counts": int,
        "total_counts_mt": int,
        "pct_counts_mt": float,
        "doublet_score": float,
        "predicted_doublets": int,
    }
    adata.obs = obs.astype(convert_dict)
    return adata
```

### 1.3 Reason for required columns

First, the cell type ontology identifier is required because we utilize the cell ontology to determine ancestors or descendents during triplet mining. It is important that the cell type annotation is a controlled vocabulary that conforms to cell ontology.

Second, the CellArr cell corpus is a database of **all** cells, not just those which will be used in training. Cells not used in training are still used in cell search. The default behavior for the dataloader is to select for cells that can be used in training, as follows:

  - If the cell type annotation exists and is an ontology identifier
  - `total_counts` > 1000
  - `n_genes_by_counts` > 500
  - `pct_counts_mt` < 20
  - `predicted_doublets` == 0

These criteria can be customized in the dataloader, but the above are the defaults.

Lastly, this standardization of datasets makes it easier to create a CellArr object and provides expected columns for the dataloader. Feel free to add additional columns as you wish.

### 1.4 Select a gene space

CellArr will create tiledb structures that cover the union set of all genes in all your datasets. This is usually not efficient for the model, as only a subset of genes are well represented across studies, so we filter the gene space for model training.

An example of this process is shown below, utilizing the sample metadata to look at the gene vs study count distribution and select well represented genes. **You should save the gene order file so that it can be used for training.**

```python
def get_genes_vs_studies(cellarr_path):
    import os
    import tiledb
    import seaborn as sns
    from matplotlib import pyplot as plt

    plt.rcParams["pdf.fonttype"] = 42

    SAMPLEURI = "sample_metadata"

    # Get studies, one per row of a dataframe
    sample_tdb = tiledb.open(os.path.join(tiledb_base_path, SAMPLEURI), "r")
    sample_df = sample_tdb.query(attrs=["datasetID", "cellarr_cell_counts"]).df[:]
    sample_tdb.close()
    
    df = sample_df.groupby("datasetID", observed=True)["cellarr_cell_counts"].max().sort_values(ascending=False).reset_index()
    df = df[df.index.isin(df["datasetID"].drop_duplicates().index.values)]
    
    selected = []
    for idx, row in df.iterrows():
        datasetID = row["datasetID"]
        selected.append(sample_df[sample_df["datasetID"]==datasetID].index[0])
    print(len(selected))
    
    sample_tdb = tiledb.open(os.path.join(tiledb_base_path, SAMPLEURI), "r")
    genes_df = sample_tdb.df[sorted(selected)]
    sample_tdb.close()
    
    # Get all original genes from each study
    gene_counts = {}
    for idx, row in genes_df.iterrows():
        genes = row['cellarr_original_gene_set'].split(',')
        for g in genes:
            if g not in gene_counts:
                gene_counts[g] = 0
            gene_counts[g] += 1
    gene_counts = {k: v for k, v in sorted(gene_counts.items(), key=lambda item: item[1], reverse=False)}
    
    # Construct gene vs count dataframe and visualize
    gene = []
    count = []
    for k, v in gene_counts.items():
        gene.append(k)
        count.append(v)
    gene_counts_df = pd.DataFrame({"gene": gene, "count": count})    
    gene_counts_df = gene_counts_df.sort_values(by="count", ascending=False).reset_index(drop=True)
    
    fig, ax = plt.subplots(1)
    sns.barplot(ax=ax, x="gene", y="count", data=gene_counts_df)
    plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    plt.tight_layout()

    return gene_counts_df

def select_genes(gene_counts_df, min_studies, filename="scimilarity_gene_order.tsv"):
    gene_order = gene_counts_df[gene_counts_df["count"]>=min_studies]["gene"].values.tolist()
    gene_order = sorted(gene_order)
    with open(filename, "w") as f:
        f.write("\n".join(gene_order))
```

## 2. Training

We provide an example training script at `scripts/train.py` which you can customize to your specifications.

Training follows the `pytorch-lightning` paradigm:
 - Data module class `CellMultisetDataModule` from `tiledb_data_models`
 - Training module class `MetricLearning` from `training_models`

Training can be resumed if interrupted by using the checkpoints logged by `pytorch-lightning`. The training script already implements this by specifying the log directory. By default, we use `tensorboard` as our logger, but you can change this to your preferred logger.

Once training is complete, all files will be saved to the model directory given by the user. This includes csv files that contain the indices and metadata for cells that were used in training and validation.

## 3. Post-training structures

### 3.1 Embeddings tiledb

The first post-training structure to create is the embeddings TileDB, which will be used to create kNN indices.

We provide an example script at `scripts/build_embeddings.py` which embeds all cells in your CellArr objects and saves a TileDB array to `{model_path}/cellsearch/cell_embedding`.

### 3.2 Annotation kNN

The annotation kNN uses the embeddings TileDB and the training cells csv (`train_cells.csv.gz`) to create a `hnswlib` kNN index.

We provide an example script at `scripts/build_annotation_knn.py`. By default, the kNN index file will be saved to `{model_path}/annotation/labelled_kNN.bin` and the reference labels will be saved to `{model_path}/annotation/reference_labels.tsv`.

### 3.3 Cell search kNN

The cell search kNN uses the embeddings TileDB to create a `tiledb_vector_search` kNN index for all cells in your CellArr object.

We provide an example script at `scripts/build_cellsearch_knn.py`. By default, the kNN index will be saved to `{model_path}/cellsearch/full_kNN.bin`.

**NOTE**: Previously, we used `hnswlib` as the cell search kNN index. But as the data size grew, we transitioned to an on-disk kNN. The `CellQuery` class still defaults to an `hnswlib` index, but if you followed the process described in this tutorial, you should initialize `CellQuery` with:

`cq = CellQuery(model_path, knn_type="tiledb_vector_search")`

### 3.4 Cell search metadata

The `CellQuery` class includes a TileDB dataframe with cell metadata containing precomputed cell type predictions for all cells, as well as other metadata from the CellArr object.

We provide an example script at `scripts/build_cellsearch_metadata.py` that uses the CellArr object, embeddings TileDB, and annotation kNN to construct the TileDB dataframe containing the cell metadata.

This process will copy over cell metadata from the CellArr object into the model's cell metadata. Though this is somewhat inefficient in storage, we prefer the separation of the "raw" data contained in the CellArr object and the "processed" data in the model structures, as you may wish to train completely different models using the CellArr object.

**NOTE**: We often apply a safelist for cell type predictions for the cell metadata to remove cell types that are too general or too specific. The script as an option to use a safelist, given as a file with one gene per line. It is up to the user to decide if they wish to use this and select the cell types they wish to safelist.

## Conclusion

At this point you will have all the structures you need to run SCimilarity.

One advantage of using the CellArr structure is you can retrieve the original count data using `utils.adata_from_tiledb` based on indices in the cell metadata of the model, which is aligned with the CellArr index. This includes results from kNN cell search or from filters you may want to apply to the cell metadata (e.g., "get all regulatory T cells").

An example of how to search and then retrieve count data is shown below.

```python
def search_then_gather_cells(model_path, cellarr_path, adata, centroid_column_name):
    from scimilarity import CellQuery
    from scimilarity.utils import adata_from_tiledb 

    cq = CellQuery(model_path, knn_type="tiledb_vector_search")
    centroid_embedding, nn_idxs, nn_dists, results_metadata, qc_stats = cq.search_centroid_nearest(adata, centroid_column_name)
    
    results_adata = adata_from_tiledb(results_metadata["index"].values, tiledb_base_path=cellarr_path)

    #The above results are from the CellArr raw data, so augment the obs with `results_metadata` 
    for c in results_metadata.columns:
        if c not in results_adata.obs:
            results_adata.obs[c] = results_metadata[c].values
    return results_adata
```