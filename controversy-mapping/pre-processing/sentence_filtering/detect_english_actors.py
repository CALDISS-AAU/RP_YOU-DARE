from pathlib import Path
import os
from dotenv import load_dotenv

import json

import langid
import pandas as pd


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
    'SE'
]

input_dir = REPO_ROOT / "controversy-mapping" / "data" / "reduced_data"
input_file_ending = '_reduced.jl'

output_path = REPO_ROOT / "controversy-mapping" / "data" / "english_actor_detection" / "english_actor_summary.txt"
output_path.parent.mkdir(parents=True, exist_ok=True)


def import_data(input_file_path: Path, country: str = '') -> list[dict]:
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            data = [json.loads(line) for line in input_file]
        print(f'Data loaded from {input_file_path} - {country}.')
        return data
    except Exception as e:
        print(f'Failed to load data from {input_file_path} - {country}. Error: {e}')
        return []


def is_text_english(text: str, min_chars: int = 50) -> bool | None:
    """
    Returns:
        True  -> text detected as English
        False -> text detected as not English
        None  -> text too short / missing / unusable
    """
    if not isinstance(text, str):
        return None

    text = text.strip()
    if not text:
        return None

    if len(text) < min_chars:
        return None

    try:
        lang, _score = langid.classify(text)
        return lang == 'en'
    except Exception:
        return None


def process_country(country: str) -> pd.DataFrame:
    input_file_path = input_dir / f'{country}{input_file_ending}'
    data = import_data(input_file_path, country=country)

    empty_cols = [
        'country',
        'actor',
        'platform',
        'english_count',
        'not_english_count',
        'total_classified_texts',
        'english_share_texts',
        'english_char_count',
        'not_english_char_count',
        'total_classified_chars',
        'english_share_chars',
        'mean_english_text_length',
        'mean_not_english_text_length'
    ]

    if not data:
        return pd.DataFrame(columns=empty_cols)

    df = pd.DataFrame(data)

    required_columns = ['actor', 'platform', 'text']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f'{country} is missing required columns: {missing_columns}')

    df = df.copy()
    df['text'] = df['text'].fillna('').astype(str)
    df['text_length'] = df['text'].str.len()
    df['is_english'] = df['text'].apply(is_text_english)

    df = df[df['is_english'].notna()].copy()

    if df.empty:
        return pd.DataFrame(columns=empty_cols)

    rows = []

    for (actor, platform), group in df.groupby(['actor', 'platform']):
        english_mask = group['is_english'] == True
        not_english_mask = group['is_english'] == False

        english_count = int(english_mask.sum())
        not_english_count = int(not_english_mask.sum())
        total_classified_texts = english_count + not_english_count

        english_char_count = int(group.loc[english_mask, 'text_length'].sum())
        not_english_char_count = int(group.loc[not_english_mask, 'text_length'].sum())
        total_classified_chars = english_char_count + not_english_char_count

        english_share_texts = (
            english_count / total_classified_texts
            if total_classified_texts > 0 else None
        )

        english_share_chars = (
            english_char_count / total_classified_chars
            if total_classified_chars > 0 else None
        )

        mean_english_text_length = (
            float(group.loc[english_mask, 'text_length'].mean())
            if english_count > 0 else None
        )

        mean_not_english_text_length = (
            float(group.loc[not_english_mask, 'text_length'].mean())
            if not_english_count > 0 else None
        )

        if english_share_texts is not None and english_share_texts >= 0.5:
            rows.append({
                'country': country,
                'actor': actor,
                'platform': platform,
                'english_count': english_count,
                'not_english_count': not_english_count,
                'total_classified_texts': total_classified_texts,
                'english_share_texts': english_share_texts,
                'english_char_count': english_char_count,
                'not_english_char_count': not_english_char_count,
                'total_classified_chars': total_classified_chars,
                'english_share_chars': english_share_chars,
                'mean_english_text_length': mean_english_text_length,
                'mean_not_english_text_length': mean_not_english_text_length
            })

    summary = pd.DataFrame(rows)

    if summary.empty:
        return pd.DataFrame(columns=empty_cols)

    summary = summary.sort_values(
        by=[
            'english_share_chars',
            'english_share_texts',
            'english_char_count',
            'english_count',
            'actor',
            'platform'
        ],
        ascending=[False, False, False, False, True, True]
    )

    return summary


def main() -> None:
    output_dict = {}

    for country in all_countries:
        print(f'Processing {country}...')
        country_summary = process_country(country)

        if country_summary.empty:
            output_dict[country] = []
            continue

        output_dict[country] = [
            {
                'actor': row['actor'],
                'platform': row['platform'],
                'english_count': int(row['english_count']),
                'not_english_count': int(row['not_english_count']),
                'total_classified_texts': int(row['total_classified_texts']),
                'english_share_texts': round(float(row['english_share_texts']), 3),
                'english_char_count': int(row['english_char_count']),
                'not_english_char_count': int(row['not_english_char_count']),
                'total_classified_chars': int(row['total_classified_chars']),
                'english_share_chars': round(float(row['english_share_chars']), 3),
                'mean_english_text_length': (
                    round(float(row['mean_english_text_length']), 1)
                    if pd.notna(row['mean_english_text_length']) else None
                ),
                'mean_not_english_text_length': (
                    round(float(row['mean_not_english_text_length']), 1)
                    if pd.notna(row['mean_not_english_text_length']) else None
                )
            }
            for _, row in country_summary.iterrows()
        ]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_dict, f, ensure_ascii=False, indent=2)

    print(f'Saved results to {output_path}')


if __name__ == '__main__':
    main()
