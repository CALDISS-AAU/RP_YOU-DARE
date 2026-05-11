from pathlib import Path
import os
from dotenv import load_dotenv

import pandas as pd
import numpy as np
import json
import re

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


all_countries = [
    'DK',
    'FR',
    'ES',
    'HU',
    'IT',
    'RO',
    'SE',
    'UK'
]
full_datasets_folder_path = str(REPO_ROOT / "raw-data" / "final_raw")
full_datasets_file_ending = '_YOUDARE-WEBDATA_combined.jsonl'
reduced_datasets_folder_path = str(REPO_ROOT / "controversy-mapping" / "data" / "reduced_data")
reduced_datasets_file_ending = '_reduced.jl'

def import_data(input_file_path: str, country=''):
    ''' Imports a given jsonlines file for further processing '''
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            data = [json.loads(line) for line in input_file]
        print(f'Data loaded from {input_file_path} - {country}.')
        return data
    except Exception as e:
        print(f'Failed to load data from {input_file_path} - {country}. Error: {e}')
        return []

def _coalesce_columns(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    """Return first non-null value across candidate columns (row-wise) 
       and is used to unite e.g. aticle_title and video_title into one title column."""
    cols = [c for c in candidates if c in df.columns]
    if not cols:
        return pd.Series([pd.NA] * len(df), index=df.index)
    return df[cols].bfill(axis=1).iloc[:, 0]

def normalize_column(x):
    ''' Makes sure everything is a string rather than having unexpected lists ''' 
    # Missing values stay missing
    if x is None or x is pd.NA:
        return None
    if isinstance(x, float) and pd.isna(x):
        return None

    # List / array of authors
    if isinstance(x, (list, tuple, np.ndarray)):
        if len(x) == 0:
            return None
        # join with space, lowercase second+ if you want exact "Alice bob"
        return ' '.join(map(str, x))

    # Scalar value
    return str(x)

def remove_YAML(raw_text):
    """
    Cleans two different thread encodings:

    1) Telegram-like pattern:
       Keep everything between:
       - 'Post_text:' and the first '\n---' after it
       - each 'Comment_text:' and the first '\n---' after it

    2) Forum pattern (Flashback-style):
       Remove metadata blocks defined as:
       from '\n\n\n---\n' up to and including the next '\n---\n'
       (keep the text that comes after each metadata block)
    """
    # Preserve missing values
    if raw_text is None or raw_text is pd.NA:
        return None
    if isinstance(raw_text, float) and pd.isna(raw_text):
        return None

    text_content = raw_text if isinstance(raw_text, str) else str(raw_text)

    # Detect whether the text uses real newlines or escaped '\n'
    if r'\n---' in text_content:
        newline_pattern = r'\\n'
    else:
        newline_pattern = r'\n'

    delimiter_pattern = newline_pattern + r'---'

    # -------------------------
    # 1) Telegram pattern
    # -------------------------
    contains_telegram_structure = ('Post_text:' in text_content) or ('Comment_text:' in text_content)
    if contains_telegram_structure:
        telegram_post_text_pattern = rf'(?s)(?<=Post_text:\s).*?(?={delimiter_pattern})'
        telegram_comment_text_pattern = rf'(?s)(?<=Comment_text:\s).*?(?={delimiter_pattern})'

        post_text_match = re.search(telegram_post_text_pattern, text_content)
        extracted_post_text = post_text_match.group(0).strip() if post_text_match else ''

        extracted_comment_texts = [
            comment_text.strip()
            for comment_text in re.findall(telegram_comment_text_pattern, text_content)
        ]

        extracted_text_blocks = [block for block in [extracted_post_text, *extracted_comment_texts] if block]
        if extracted_text_blocks:
            return "\n\n".join(extracted_text_blocks)

        return text_content  # fallback if nothing was extracted

    # -------------------------
    # 2) Forum pattern
    # -------------------------
    # Metadata blocks are between: '\n\n\n---\n' and '\n---\n' (inclusive)
    triple_newline_pattern = newline_pattern * 3
    forum_text_pattern = rf'(?s){triple_newline_pattern}---{newline_pattern}.*?{newline_pattern}---{newline_pattern}'

    contains_forum_structure = ('POST:' in text_content or 'COMMENT:' in text_content) and '---' in text_content
    if contains_forum_structure:
        # Remove all metadata blocks, keep the remaining text chunks
        cleaned_forum_text = re.sub(forum_text_pattern, "\n", text_content)

        # Light cleanup (don’t over-normalize)
        cleaned_forum_text = cleaned_forum_text.strip()

        return cleaned_forum_text if cleaned_forum_text else text_content

    # If neither structure matches, return unchanged
    return text_content

def select_and_clean_relevant_columns(df: pd.DataFrame, country='') -> pd.DataFrame:
    # Keep only columns that might matter (optional, but fine)
    relevant_columns = [
        'publication_date','timestamp',
        'source','Source',
        'article_link','video_link','post_link','URL',
        'article_title','video_title','post_title',
        'article_text','video_text','thread_text',
        'platform', 'actor', 'entry_ID'
    ]
    available_columns = [c for c in relevant_columns if c in df.columns]
    reduced_df = df[available_columns].copy()

    # Remove Flashback rows before YAML/forum cleaning
    if 'platform' in reduced_df.columns:
        before_rows = len(reduced_df)
        reduced_df = reduced_df[reduced_df['platform'] != 'Flashback'].copy()
        after_rows = len(reduced_df)
        print(f"Removed {before_rows - after_rows} Flashback rows before text cleaning - {country}")

    # Build unified columns
    out = pd.DataFrame(index=reduced_df.index)

    out['publication date'] = _coalesce_columns(reduced_df, ['publication_date', 'timestamp'])
    out['source'] = _coalesce_columns(reduced_df, ['source', 'Source'])

    out['link'] = _coalesce_columns(reduced_df, ['article_link', 'video_link', 'post_link', 'URL'])
    out['title'] = _coalesce_columns(reduced_df, ['article_title', 'video_title', 'post_title'])
    out['text'] = _coalesce_columns(reduced_df, ['article_text', 'video_text', 'thread_text'])

    out['entry_ID'] = reduced_df['entry_ID'] #if 'entry_ID' in reduced_df.columns else pd.NA
    out['actor'] = reduced_df['actor'] #if 'actor' in reduced_df.columns else pd.NA
    out['platform'] = reduced_df['platform'] #if 'platform' in reduced_df.columns else pd.NA
    print(f'All columns has been coalesced - {country}')

    # Add title to beginning of text (only when both exist)
    title = out['title'].fillna('').astype(str).str.strip()
    text = out['text'].fillna('').astype(str).str.strip()

    out['text'] = np.where(
        (title != '') & (text != ''),
        title + "\n\n" + text,
        np.where(title != '', title, text)
    )
    print(f'Title has been added to the text - {country}')

    # Optional: make sure these are strings (and not lists)
    for col in ['entry_ID','actor','platform','publication date','source','link','title','text']:
        # out[col] = out[col].apply(lambda x: '' if pd.isna(x) else str(x))
        out[col] = out[col].apply(normalize_column)

    # Optional: drop rows with no text
    out = out[out.text != 'nan']
    out = out[out['text'].str.len() > 0].copy()

    column_order = [
        'entry_ID',
        'actor',
        'platform',
        'publication date',
        'source',
        'link',
        'title',
        'text'
    ]

    out = out[column_order]

    return out

def save_data(df, output_path, country=''):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_json(output_path, orient='records', lines=True)
        print(f'The data was saved successfully - {country}!')
    except Exception as e:
        print(f'Failed to save data - {country}. Error: {e}')

for country in all_countries:
    full_dataset_path = f'{full_datasets_folder_path}/{country}{full_datasets_file_ending}'
    reduced_dataset_path = f'{reduced_datasets_folder_path}/{country}{reduced_datasets_file_ending}'

    full_dataset = import_data(full_dataset_path, country=country) # Imports the data on the file path
    if not full_dataset:
        print("No data loaded.")

    full_df = pd.DataFrame(full_dataset)
    
    reduced_df = select_and_clean_relevant_columns(full_df, country=country)

    save_data(reduced_df, reduced_dataset_path, country=country)

    print(f'{full_dataset_path}\n{full_df.columns}\n{reduced_df.columns}\n{reduced_dataset_path}')
