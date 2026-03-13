"""
Pipeline for semantic mapping
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import warnings
import pprint
import json
import pandas as pd
import numpy as np

from modules.data_ingestion import read_embeddings_as_df
from modules.clustering import DimensionConfig

## Embedding dir
EMBEDDINGS_IN_DIR = Path("/work/YOU-DARE/controversy-mapping/semantic-mapping/output/bg-3_embeddings")

## Countries and themes
COUNTRIES = {
    "DK",
    "ES",
    "FR",
    "HU",
    "IT",
    "RO",
    "SE",
    "UK"
}

THEMES = {
    "lgb",
    "migration", 
    "woke"
}

KEYS = {f"{country}_{theme}" for country in COUNTRIES for theme in THEMES}

def makin_da_map(country, theme):
    
    key = f"{country}_{theme}"

    if key not in KEYS:
        raise ValueError(f"key {key} not a valid key. Expected one of: {', '.join(KEYS)}")

    # read data    
    chunked_path = EMBEDDINGS_IN_DIR / f"{key}_chunked.parquet"
    embedding_path = EMBEDDINGS_IN_DIR / f"{key}_embeddings.npy"

    chunked_df_embeddings = read_embeddings_as_df(chunked_path, embedding_path)

    # remove flashback
    if country == "SE":
        chunked_df_embeddings = chunked_df_embeddings[~chunked_df_embeddings['source'].str.contains('flashback', case = False)]

    DIM_CONFIG = DimensionConfig(
        # HDBSCAN PARAMETERS
        min_cluster_size = 40,
        min_samples = 1,
        metric = 'euclidean',
        cluster_selection_epsilon = 0.1,
        cluster_selection_method = 'leaf',
        ## UMAP
        build_algo = 'auto',
        n_neighbors = 50,
        n_components = 30,
        min_dist = 0.09,
        umap_metric = 'euclidean'
    )
    
    embeddings = np.stack(chunked_df_embeddings['embedding'].values)
    # HDBSCAN for cluster labels 
    chunked_df_embeddings['cluster'] = DIM_CONFIG.cluster(embeddings)
    chunked_df_embeddings['cluster'] = chunked_df_embeddings['cluster'].astype(str)

    projections = DIM_CONFIG.reduce(embeddings)
    # saving the UMAP projections for plotting
    chunked_df_embeddings['umap_1'] = projections[:, 0]
    chunked_df_embeddings['umap_2'] = projections[:, 1]

    # getting actor embeddings - mean pooling per actor
    actor_embeddings = (
        chunked_df_embeddings.groupby('actor')['embedding']
        .apply(lambda x: (lambda v: v / np.linalg.norm(v))(np.stack(x).mean(axis=0)))
        .reset_index()
    )
    actor_embeddings.columns=['actor', 'embedding']


    actor_matrix = np.stack(actor_embeddings['embedding'].values)
    # Actor projections - like David Lynch wanted
    actor_projections = DIM_CONFIG.transform(actor_matrix)
    actor_embeddings['umap_1'] = actor_projections[:, 0]
    actor_embeddings['umap_2'] = actor_projections[:, 1]

    # Plotting
    DIM_CONFIG.plotter(chunked_df_embeddings , actor_df=actor_embeddings,theme=theme, output_path=f'/work/YOU-DARE/controversy-mapping/semantic-mapping/plots/bg-3_embedding_plots/{country}_{theme}_umap.html')

# main function
def main():
    parser = argparse.ArgumentParser(description="Do a map.")
    parser.add_argument(
        "--country",
        required=True,
        choices=sorted(COUNTRIES),
        help="Country code to process."
    )
    parser.add_argument(
        "--theme",
        required=True,
        choices=sorted(THEMES),
        help="Theme to process."
    )
    args = parser.parse_args()
    makin_da_map(args.country, args.theme)

if __name__ == "__main__":
    main()
