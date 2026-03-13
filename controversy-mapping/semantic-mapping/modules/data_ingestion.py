"""Embedding pipeline helpers."""

from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import Pool
import math
import ast
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

import pandas as pd
import numpy as np

@dataclass
class ChunkConfig:
    """
    Config class for setting up chunk.
    chunk_size: Threshold for chunksize. 
    Other parameters specifies expected names of columns in input data
    """
    chunk_size: int = 250
    text_id_col: str = "text_ID"
    sentence_id_col: str = "sentence_id"
    text_col: str = "text"
    matched_col: str = "matched"
    keyword_col: Optional[str] = None


def sentences_to_chunks(df, config: Optional[ChunkConfig] = None):
    """
    Convert sentence-level JSONL data into text chunks around matched sentences.

    For every row with matched == 1, build a chunk by concatenating sentences:
    - Start with the matched sentence.
    - Append forward sentences first, then backward sentences.
    - Concatenate with '.' between sentences until chunk_size characters is reached.
    - Never cross text_id boundaries.

    Duplicate chunks are removed when they contain the same set of matched sentences.

    Returns a DataFrame with the same columns as input, excluding:
    sentence_id, text, matched. Adds:
    - chunk_id (running id within each text_id, 1-based)
    - chunk (concatenated text)
    The matched keywords column is replaced with the unique keywords
    found among matched sentences in the chunk.
    """
    cfg = config or ChunkConfig() # load config or use defaults

    # check if all required columns are present
    required = [cfg.text_id_col, cfg.sentence_id_col, cfg.text_col, cfg.matched_col, cfg.keyword_col]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    # list of rows to fill in
    chunk_rows = []

    # output columns
    output_columns = _output_columns(df.columns, cfg)

    df[cfg.text_id_col] = df[cfg.text_id_col].apply(_safe_text) # ensures no null or missing

    # iterate over texts in dataframe using text id column
    for text_id, group_df in df.groupby(cfg.text_id_col, sort=False):
        # Sort by sentences in each text
        group_sorted = group_df.sort_values(
            cfg.sentence_id_col, kind="mergesort"
        ).reset_index(drop=True)

        # derive sentences as its own list
        sentences = group_sorted[cfg.text_col].tolist()

        # list of matched indicators
        matched_flags = (
            group_sorted[cfg.matched_col].fillna(0).astype(int).tolist()
        )

        # list of sentence ids
        sentence_ids = group_sorted[cfg.sentence_id_col].tolist()
        
        # list of keywords
        keyword_vals = (
            group_sorted[cfg.keyword_col].tolist() if cfg.keyword_col else [None] * len(group_sorted)
        )

        # set for keeping track of matched sentences
        seen_matched_sets = set()

        # starting id for chunks
        chunk_id = 1

        # iterate over sentences in text (by whether matched)
        for pos, is_matched in enumerate(matched_flags):
            # skip if not matching a keyword
            if is_matched != 1:
                continue
            
            # find what sentences to include
            included_positions, chunk_parts = _build_chunk_parts(
                pos,
                sentences,
                cfg.chunk_size,
            )

            # sentence ids for matched sentences (can differ from positions as empty lines are omitted from data)
            matched_sentence_ids = sorted(
                {sentence_ids[idx] for idx in included_positions if matched_flags[idx] == 1}
            )

            # keeping track of sets of matched sentences in chunks (avoid duplicate chunks)
            matched_set = tuple(matched_sentence_ids)
            # skip chunk if matched sentences are already in other chunk
            if matched_set in seen_matched_sets:
                continue
            seen_matched_sets.add(matched_set)

            # combine to chunk and combine keywords
            chunk_text = ". ".join(chunk_parts)
            chunk_keywords = _collect_chunk_keywords(
                included_positions,
                matched_flags,
                keyword_vals,
            )

            # output row
            anchor_row = group_sorted.iloc[pos].to_dict()
            out_row = _build_output_row(
                anchor_row,
                chunk_id,
                chunk_text,
                output_columns,
                cfg,
                chunk_keywords,
            )
            out_row[cfg.text_id_col] = text_id
            chunk_rows.append(out_row)
            chunk_id += 1

    # return empty df if no chunks
    if not chunk_rows:
        output_columns = df.columns
        out_df = pd.DataFrame(columns=output_columns)
    
    # output df
    out_df = pd.DataFrame(chunk_rows, columns=output_columns)

    return out_df


def sentences_to_chunk_mp(df, config: Optional[ChunkConfig] = None, n_workers: int = 2):
    """
    Multiprocessing wrapper for sentences_to_chunks.
    Splits dataframe into subset dataframes by unique text_id values and
    processes subsets in parallel.
    """
    cfg = config or ChunkConfig()

    if n_workers < 1:
        raise ValueError(f"n_workers must be >= 1, got {n_workers}")
    if cfg.text_id_col not in df.columns:
        raise KeyError(f"Missing required column: {cfg.text_id_col}")

    df_mp = df.copy()
    df_mp[cfg.text_id_col] = df_mp[cfg.text_id_col].apply(_safe_text)

    unique_text_ids = df_mp[cfg.text_id_col].drop_duplicates().tolist()
    if not unique_text_ids:
        return sentences_to_chunks(df_mp, cfg)

    n_workers = min(n_workers, len(unique_text_ids))
    split_size = math.ceil(len(unique_text_ids) / n_workers)
    text_id_splits = [
        unique_text_ids[idx : idx + split_size]
        for idx in range(0, len(unique_text_ids), split_size)
    ]

    subset_dfs = [
        df_mp[df_mp[cfg.text_id_col].isin(text_id_subset)].copy()
        for text_id_subset in text_id_splits
    ]

    with Pool(processes=n_workers) as pool:
        chunked_parts = pool.starmap(
            sentences_to_chunks,
            [(subset_df, cfg) for subset_df in subset_dfs],
        )

    non_empty_parts = [part for part in chunked_parts if not part.empty]
    if not non_empty_parts:
        return pd.DataFrame(columns=_output_columns(df.columns, cfg))
    return pd.concat(non_empty_parts, ignore_index=True)


## Read parquet + embeddings to df
def read_embeddings_as_df(chunked_path, emb_path) -> pd.DataFrame:
    chunked = pd.read_parquet(chunked_path)
    emb = np.load(emb_path)  # shape (n, dim)

    chunked["embedding"] = emb.astype(float).tolist()
    return chunked


def _safe_text(value: Any) -> str:
    """
    Ensures that text is a string
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _build_chunk_parts(start_pos, sentences, chunk_size):
    """
    Retrieves sentences to include in chunk.
    Expands contexts arround matched sentence until chunk_size is reached.
    """
    included_positions = [start_pos]
    chunk_parts = [sentences[start_pos]]
    current_len = len(chunk_parts[0])

    # starting context
    context = 1
    
    # retrieve chunk parts while len < chunk_size
    while current_len < chunk_size:
        if current_len >= chunk_size:
            break
        
        # expand forward
        forward_pos = start_pos + context
        if not forward_pos >= len(sentences):
            chunk_parts.append(sentences[forward_pos])
            included_positions.append(forward_pos)
            current_len += len(sentences[forward_pos])
            
            if current_len >= chunk_size:
                break
        
        # expand backwards
        backward_pos = start_pos - context
        if not backward_pos < 0:
            chunk_parts.append(sentences[backward_pos])
            included_positions.append(backward_pos)
            current_len += len(sentences[backward_pos])

        # break if outside text boundary
        if forward_pos >= len(sentences) and backward_pos < 0:
            break
        
        # increas context before next loop
        context += 1

    return included_positions, chunk_parts


def _collect_chunk_keywords(included_positions, matched_flags, keyword_vals):
    """
    Combine keywords present in chunk.
    """
    keywords = []
    for idx in included_positions:
        if matched_flags[idx] != 1:
            continue
        if keyword_vals[idx]:
            keywords.extend(keyword_vals[idx])

    if not keywords:
        return None
    unique_keywords = list(dict.fromkeys(keywords))
    return ", ".join(unique_keywords)


def _output_columns(columns, config):
    """
    Create list of output columns
    """
    drop_cols = {config.sentence_id_col, config.text_col, config.matched_col}
    kept = [col for col in columns if col not in drop_cols]
    return kept + ["chunk_id", "chunk"]


def _build_output_row(
    anchor_row,
    chunk_id,
    chunk_text,
    output_columns,
    config,
    chunk_keywords
    ):
    """
    Build row for output data frame with chunk text and relevant features/columns.
    """
    row = {}
    drop_cols = {config.sentence_id_col, config.text_col, config.matched_col}
    for col in output_columns:
        if col in {"chunk_id", "chunk"}:
            continue
        if col in drop_cols:
            continue
        if config.keyword_col and col == config.keyword_col:
            row[col] = chunk_keywords
        else:
            row[col] = anchor_row.get(col)

    row["chunk_id"] = chunk_id
    row["chunk"] = chunk_text
    return row