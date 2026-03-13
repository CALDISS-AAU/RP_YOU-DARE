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

from modules.data_ingestion import sentences_to_chunks,sentences_to_chunk_mp, ChunkConfig
from modules.semantic_mapping_func import EmbeddingConfig, DimensionConfig


## Input data
LGB_paths = [
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/DK/DK_lgb_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/ES/ES_lgb_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/FR/FR_lgb_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/HU/HU_lgb_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/IT/IT_lgb_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/RO/RO_lgb_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/SWE/SWE_lgb_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/UK/UK_lgb_matched.jl"
]
Migration_paths = [
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/DK/DK_migration_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/ES/ES_migration_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/FR/FR_migration_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/HU/HU_migration_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/IT/IT_migration_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/RO/RO_migration_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/SWE/SWE_migration_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/UK/UK_migration_matched.jl"
]

woke_paths = [
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/DK/DK_woke_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/ES/ES_woke_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/FR/FR_woke_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/HU/HU_woke_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/IT/IT_woke_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/RO/RO_woke_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/SWE/SWE_woke_matched.jl",
    "/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/UK/UK_woke_matched.jl"
]

all_paths = LGB_paths + Migration_paths + woke_paths
def main():
    
    chunked_dfs = {}
    for data_path in all_paths:
        data_path = Path(data_path)

        with open(data_path, "r") as f:
                lines = f.read().splitlines()
        

        data_records = [json.loads(line) for line in lines]
        df = pd.DataFrame(data_records)

        # Derive country and theme from data_path
        path_elems = data_path.stem.split('_')
        country = path_elems[0]
        try:
            theme = path_elems[1]
        except IndexError:
            raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

        keyword_col = f'matched keywords - {theme}'

        # SET SETTINGS FOR CHUNKING
        CONFIG_USE=ChunkConfig(
            chunk_size = 250, # Størrelse på chunk. Inkluderer sætninger indtil denne grænse overstiges
            text_id_col = "text_ID", # navn på text id kolonne
            sentence_id_col = "sentence_id", # navn på sætningsid kolonne
            text_col = "text", 
            matched_col = "matched",
            keyword_col = keyword_col
        )

        # Chunk data
        chunked_df = sentences_to_chunk_mp(df, CONFIG_USE, n_workers=8)
        chunked_df = chunked_df.drop_duplicates(subset=['chunk'])
        chunked_df["country"] = country
        chunked_dfs[f"{country}_{theme}"] = chunked_df


    # Embedding configs
    EMB_CONFIG = EmbeddingConfig()
    # embeddings by theme
    for key, chunked_df in chunked_dfs.items():
        embeddings = EMB_CONFIG.get_embeddings(chunked_df['chunk'].tolist())
        chunked_dfs[key]['embedding'] = list(embeddings)

    


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
        DIM_CONFIG.plotter(theme_df , actor_df=actor_embeddings,theme=theme, output_path=f'/work/YOU-DARE/controversy-mapping/semantic-mapping/plots/{theme}_umap.html')

if __name__ == "__main__":
    main()
