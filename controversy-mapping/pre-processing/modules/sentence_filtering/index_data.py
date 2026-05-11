from pathlib import Path
import os
from dotenv import load_dotenv

import pandas as pd
import json

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
    'ES',
    'FR',
    'HU',
    'IT',
    'RO',
    'SE',
    'UK'
]

all_themes = [
    'lgb',
    'migration',
    'woke'
]

input_folder = str(REPO_ROOT / "controversy-mapping" / "sentence_filtering" / "matched_data")

def merge_unique_keywords(series):
    seen = set()
    merged = []
    for sublist in series:
        for kw in sublist:
            if kw not in seen:
                seen.add(kw)
                merged.append(kw)
    return merged

for country in all_countries:
    output_folder = str(REPO_ROOT / "controversy-mapping" / "sentence_filtering" / "indexed_data" / f"{country}")
    for theme in all_themes:
        input_file_path = f'{input_folder}/{country}/{country}_{theme}_matched.jl'
        print(input_file_path)
        output_data_path = f'{output_folder}/{country}_{theme}_indexed.jl'
        matched_rows = []

        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            data = [json.loads(line) for line in input_file]

        df = pd.DataFrame(data)
        
        df_matched = df[df['matched'] == 1]
        df_matched = df_matched[['entry_ID', 'source', 'actor', 'platform', 'publication date', 'matched keywords', 'matched words']]

        df_matched = (
            df_matched
            .groupby('entry_ID', as_index=False)
            .agg({
                'source': 'first',
                'actor': 'first',
                'platform': 'first',
                'publication date': 'first',
                'matched keywords': merge_unique_keywords,
                'matched words': merge_unique_keywords
            })
        )

        Path(output_folder).mkdir(parents=True, exist_ok=True)
        df_matched.to_json(output_data_path, orient='records', lines=True, force_ascii=False)

        print(f'{country} {theme} - done!')
