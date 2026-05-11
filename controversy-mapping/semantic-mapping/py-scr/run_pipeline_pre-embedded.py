"""
Pipeline for semantic mapping
"""

from __future__ import annotations
from pathlib import Path
import os
from dotenv import load_dotenv

import argparse
import sys
import warnings
import pprint

import json
import pandas as pd
import numpy as np

from modules.data_ingestion import sentences_to_chunks,sentences_to_chunk_mp, ChunkConfig, read_embeddings_as_df
from modules.semantic_mapping_func import EmbeddingConfig, DimensionConfig

ENV_PATH = next(
    (
        parent / ".env"
        for parent in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
        if (parent / ".env").exists()
    ),
    None,
)
if ENV_PATH is None:
    raise FileNotFoundError("Could not locate .env")

load_dotenv(ENV_PATH)
REPO_ROOT = Path(os.environ.get("YOUDARE_REPO_ROOT", ".")).resolve()


## Embedding dir
EMBEDDINGS_IN_DIR = REPO_ROOT / "controversy-mapping" / "semantic-mapping" / "output" / "embeddings"

## Countries and themes
COUNTRIES = {
    "DK",
    "ES",
    "FR",
    "HU",
    "IT",
    "RO",
    "SWE",
    "UK"
}

THEMES = {
    "lgb",
    "migration", 
    "woke"
}

KEYS = {f"{country}_{theme}" for country in COUNTRIES for theme in THEMES}

def main():
    
    chunked_dfs = {}
    
    for key in KEYS:
        chunked_path = EMBEDDINGS_IN_DIR / f"{key}_chunked.parquet"
        embedding_path = EMBEDDINGS_IN_DIR / f"{key}_embeddings.npy"

        chunked_df_embeddings = read_embeddings_as_df(chunked_path, embedding_path)

        chunked_dfs[key] = chunked_df_embeddings

    # Doing by theme basis
    theme_dfs = {}
    for theme in ['lgb', 'migration', 'woke']:
        theme_dfs[theme] = pd.concat(
            [v for k, v in chunked_dfs.items() if k.endswith(theme)],
            ignore_index=True
        )


    DIM_CONFIG = DimensionConfig()

    for theme, theme_df in theme_dfs.items():
        # Stacking the embeddings
        embeddings = np.stack(theme_df['embedding'].values)
        # HDBSCAN for cluster labels 
        theme_dfs[theme]['cluster'] = DIM_CONFIG.cluster(embeddings)

        projections = DIM_CONFIG.reduce(embeddings)
        # saving the UMAP projections for plotting
        theme_dfs[theme]['umap_1'] = projections[:, 0]
        theme_dfs[theme]['umap_2'] = projections[:, 1]

        # getting actor embeddings - mean pooling per source
        actor_embeddings = (
        theme_df.groupby('source')['embedding']
        .apply(lambda x: np.stack (x).mean(axis=0))
        .reset_index()
        )
        actor_embeddings.columns=['source', 'embedding']


        actor_matrix = np.stack(actor_embeddings['embedding'].values)
        # Actor projections - like David Lynch wanted
        actor_projections = DIM_CONFIG.transform(actor_matrix)
        actor_embeddings['umap_1'] = actor_projections[:, 0]
        actor_embeddings['umap_2'] = actor_projections[:, 1]

        # Plotting
        DIM_CONFIG.plotter(theme_df , actor_df=actor_embeddings,theme=theme, output_path=str(REPO_ROOT / "controversy-mapping" / "semantic-mapping" / "plots" / "kgk" / f"{theme}_umap.html"))

if __name__ == "__main__":
    main()
