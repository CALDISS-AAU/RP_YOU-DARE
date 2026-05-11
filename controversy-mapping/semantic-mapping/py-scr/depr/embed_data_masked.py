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

from modules.data_ingestion import sentences_to_chunks,sentences_to_chunk_mp, ChunkConfig
from modules.semantic_mapping_func import EmbeddingConfig, DimensionConfig
from modules.matcher import mask_keywords

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


## Embeddings outdir
embeddings_out = REPO_ROOT / "controversy-mapping" / "semantic-mapping" / "output" / "embeddings_masked"
embeddings_out.mkdir(parents=True, exist_ok=True)


## Input data
LGB_paths = [
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "DK" / "DK_lgb_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "ES" / "ES_lgb_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "FR" / "FR_lgb_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "HU" / "HU_lgb_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "IT" / "IT_lgb_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "RO" / "RO_lgb_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "SE" / "SE_lgb_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "UK" / "UK_lgb_matched.jl")
]
Migration_paths = [
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "DK" / "DK_migration_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "ES" / "ES_migration_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "FR" / "FR_migration_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "HU" / "HU_migration_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "IT" / "IT_migration_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "RO" / "RO_migration_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "SE" / "SE_migration_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "UK" / "UK_migration_matched.jl")
]

woke_paths = [
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "DK" / "DK_woke_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "ES" / "ES_woke_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "FR" / "FR_woke_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "HU" / "HU_woke_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "IT" / "IT_woke_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "RO" / "RO_woke_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "SE" / "SE_woke_matched.jl"),
    str(REPO_ROOT / "controversy-mapping" / "data" / "matched_data" / "UK" / "UK_woke_matched.jl")
]

all_paths = LGB_paths + Migration_paths + woke_paths

def main():
    
    chunked_dfs = {}
    for c, data_path in enumerate(all_paths, start = 1):
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
        print(f"Chunking dataset {c} out of {len(all_paths)} datasets")
        chunked_df = sentences_to_chunk_mp(df, CONFIG_USE, n_workers=8)
        chunked_df = chunked_df.drop_duplicates(subset=['chunk'])
        chunked_df["country"] = country
        chunked_df['chunk_masked'] = chunked_df.apply(
            lambda row: mask_keywords(
                row['chunk'],
                [kw.strip() for kw in str(row[f'matched keywords - {theme}']).split(',') if kw.strip()] if pd.notna(row[f'matched keywords - {theme}']) else [],
                theme
                ),
                axis=1
                )

        # add to list
        chunked_dfs[f"{country}_{theme}"] = chunked_df


    # Embedding configs
    EMB_CONFIG = EmbeddingConfig()
    # embeddings by theme
    for key, chunked_df in chunked_dfs.items():
        print(f"Embedding dataset {key}")
        embeddings = EMB_CONFIG.get_embeddings(chunked_df['chunk_masked'].tolist())

        # force compact numeric dtype
        emb = np.asarray(embeddings, dtype=np.float32)

        # Store embeddings
        chunked_out = embeddings_out / f"{key}_chunked.parquet"
        emb_out = embeddings_out / f"{key}_embeddings.npy"

        chunked_df.to_parquet(chunked_out, index=False)
        np.save(emb_out, emb)

if __name__ == "__main__":
    main()
