"""
Pipeline for semantic mapping
"""

from __future__ import annotations
from pathlib import Path
import os
from dotenv import load_dotenv

import argparse
import sys

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


sys.path.append(str(REPO_ROOT / "controversy-mapping" / "semantic-mapping"))

import warnings

import json
import pandas as pd
import numpy as np

from modules.data_ingestion import sentences_to_chunks,sentences_to_chunk_mp, ChunkConfig
from modules.semantic_mapping_func import LanguageDetectionConfig, TranslateConfig, EmbeddingConfig, DimensionConfig

## Embeddings outdir
embeddings_out = REPO_ROOT / "controversy-mapping" / "semantic-mapping" / "output" / "embeddings"
embeddings_out.mkdir(parents=True, exist_ok=True)

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

LANG_MAP = {
    'DK': 'dan_Latn',
    'SWE': 'swe_Latn',
    'SE': 'swe_Latn'
}

ENGLISH_ACTORS = ['Maniphesto', 'The Golden One']
ACTORS_TRANSLATE = ['Gym XIV']

all_paths = LGB_paths + Migration_paths + woke_paths
def main(year_cutoff_start=2015, year_cutoff_end=2026):
    
    chunked_dfs = {}
    for data_path in all_paths:
        data_path = Path(data_path)

        with open(data_path, "r") as f:
                lines = f.read().splitlines()
        

        data_records = [json.loads(line) for line in lines]
        df = pd.DataFrame(data_records)

        # filter date
        df["publication date"] = pd.to_datetime(df["publication date"], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD

        cutoff_date_start = pd.Timestamp(year=year_cutoff_start, month=1, day=1)
        cutoff_date_end = pd.Timestamp(year=year_cutoff_end, month=1, day=1)

        df = df[(df["publication date"] >= cutoff_date_start) & (df["publication date"] < cutoff_date_end)].reset_index(drop=True)


        # Derive country and theme from data_path
        path_elems = data_path.stem.split('_')
        country = path_elems[0]
        try:
            theme = path_elems[1]
        except IndexError:
            raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

        keyword_col = f'matched keywords'
        words_col = 'matched words'

        # SET SETTINGS FOR CHUNKING
        CONFIG_USE=ChunkConfig(
            chunk_size = 250, # Størrelse på chunk. Inkluderer sætninger indtil denne grænse overstiges
            text_id_col = "entry_ID", # navn på text id kolonne
            sentence_id_col = "sentence_id", # navn på sætningsid kolonne
            text_col = "text", 
            matched_col = "matched",
            keyword_col = keyword_col,
            words_col= words_col
        )

        # Chunk data
        chunked_df = sentences_to_chunk_mp(df, CONFIG_USE, n_workers=8)
        chunked_df = chunked_df.drop_duplicates(subset=['chunk'])
        chunked_df["country"] = country
        chunked_dfs[f"{country}_{theme}"] = chunked_df
    
    # language detection configs
    LangConfig = LanguageDetectionConfig()
    # language detection by theme
    for key, chunked_df in chunked_dfs.items():
        print(chunked_df.columns)
        chunked_df.loc[chunked_df['actor'].isin(ENGLISH_ACTORS), 'lang'] = 'en'

        mask = chunked_df['actor'].isin(ACTORS_TRANSLATE)

        if not any(mask):
            continue
        else:
            texts = chunked_df.loc[mask, "chunk"].astype(str).str[:500].tolist()
            chunked_df.loc[mask, "lang"] = [LangConfig.detect_lang(t)[0] for t in texts]
        
    # Translator configs
    Translator = TranslateConfig(src_lang='eng_Latn')
    for key, chunked_df in chunked_dfs.items():

        chunked_df["chunk_translated"] = chunked_df["chunk"]

        country = chunked_df['country'].iloc[0]
        if country in LANG_MAP:
            Translator.tgt_lang = LANG_MAP[country]
    # Only translate for supported languages
        else:

            print(f"Skipping unsupported country code: {country}")
            
        continue


        mask = chunked_df["lang"] == "en"

        texts = chunked_df.loc[mask, 'chunk'].tolist()

        if texts:
            translated = []
            texts_split = [texts[i:i + 10] for i in range(0, len(texts), 10)]
            for split in texts_split:
                translated_split = Translator.translate_sent(split)
                translated.extend(translated_split)
            chunked_df.loc[mask, 'chunk_translated'] = translated

    print("I translated!")


    # Embedding configs
    EMB_CONFIG = EmbeddingConfig()
    # embeddings by theme
    for key, chunked_df in chunked_dfs.items():
        embeddings = EMB_CONFIG.get_embeddings(chunked_df['chunk_translated'].tolist())

        # force compact numeric dtype
        emb = np.asarray(embeddings, dtype=np.float32)

        # Store embeddings
        chunked_out = embeddings_out / f"{key}_chunked.parquet"
        emb_out = embeddings_out / f"{key}_embeddings.npy"

        chunked_df.to_parquet(chunked_out, index=False)
        np.save(emb_out, emb)
    
    print("\033[92mSuccess:\033[0m \033[3mI embedded!\033[0m")

if __name__ == "__main__":
    main()
