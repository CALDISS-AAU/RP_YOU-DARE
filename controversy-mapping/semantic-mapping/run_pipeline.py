"""Pipeline for semantic mapping"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import warnings

import json
import pandas as pd

from modules.data_ingestion import sentences_to_chunks, ChunkConfig


## Input data
data_path = "/work/YOU-DARE/sentence_filtering/matched_data/DK/DK_lgb_matched.jl"
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
chunked_df = sentences_to_chunks(df, CONFIG_USE)

# TODO: Matias' magi
