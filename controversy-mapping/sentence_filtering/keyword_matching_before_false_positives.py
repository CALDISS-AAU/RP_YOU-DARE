import pandas as pd
import json
import re
from pathlib import Path
import dateparser
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

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

datasets_folder_path = '/work/YOU-DARE/controversy-mapping/sentence_filtering/reduced_data/'
datasets_file_ending = '_reduced.jl'
keyword_lists_folder_path = '/work/YOU-DARE/controversy-mapping/sentence_filtering/keyword_related_data/keyword_lists/'
keyword_lists_file_ending = '_keywords_lists.txt'
matched_datasets_folder_path = '/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data/'
matched_datasets_file_ending = '_matched.jl'

english_speaking_actors = {
    'DK': {'Maniphesto'},
    'SE': {'Gym XIV', 'The Golden One'}
}

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

def import_keywords(input_file_path: str, country=''):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            keyword_lists = json.load(input_file)
        print(f'Keyword lists loaded from {input_file_path} - {country}.')
        return keyword_lists
    except Exception as e:
        print(f'Failed to load keyword lists from {input_file_path} - {country}. Error: {e}')
        return {}

def split_text_into_sentences(df, country=''):
    rows = []

    for _, row in df.iterrows():
        text = row.get('text') or ''
        if not isinstance(text, str) or not text.strip():
            continue

        sentences = re.split(r'\n+|\.', text)
        for i, sent in enumerate(sentences, start=1):
            new_row = row.copy()
            new_row['text'] = sent
            new_row['sentence_id'] = i
            rows.append(new_row)

    df_split = pd.DataFrame(rows)
    print(f'Text has been split into sentences - {country}')
    return df_split

def normalise_publication_dates(df, col_name='publication date'):
    df[col_name] = df[col_name].apply(
        lambda s: None if (pd.isna(s) or (isinstance(s, str) and s.strip() == ''))
        else dateparser.parse(s, settings={'RETURN_AS_TIMEZONE_AWARE': False})
    )
    df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
    df[col_name] = df[col_name].dt.strftime('%Y-%m-%d')
    return df

def convert_to_regex(keyword):
    pattern = keyword.strip()

    starts = pattern.startswith('*')
    ends = pattern.endswith('*')

    if starts:
        pattern = pattern[1:]
    if ends:
        pattern = pattern[:-1]

    pattern = re.escape(pattern)
    pattern = pattern.replace(r'\*', r'\w*')

    if starts and ends:
        return pattern
    elif starts:
        return r'\w*' + pattern + r'(?:\b|(?=\s|\.|,|$))'
    elif ends:
        return r'\b' + pattern + r'\w*'
    else:
        return r'\b' + pattern + r'(?:\b|(?=\s|\.|,|$))'

def compile_keyword_regexes(keywords, label=''):
    compiled_regexes = []

    for kw in keywords:
        pattern = convert_to_regex(kw)
        try:
            rgx = re.compile(pattern, flags=re.IGNORECASE)
            compiled_regexes.append((kw, rgx))
        except re.error as e:
            print(f"Bad regex for keyword '{kw}' ({label}): {e}")

    return compiled_regexes

def match_on_keywords_by_actor(
    df,
    category,
    local_keywords,
    english_keywords,
    english_actor_set,
    text_column='text',
    actor_column='actor',
    country=''
):
    df = df.copy()

    local_compiled = compile_keyword_regexes(local_keywords, label=f'{country}-{category}-local')
    english_compiled = compile_keyword_regexes(english_keywords, label=f'{country}-{category}-english')

    matched_keywords = []
    matched_words = []

    for _, row in df.iterrows():
        text = row.get(text_column) or ''
        actor = str(row.get(actor_column) or '').strip()

        if actor in english_actor_set:
            compiled_regexes = english_compiled
        else:
            compiled_regexes = local_compiled

        matches = set()
        matches_words = []

        for original_kw, rgx in compiled_regexes:
            if rgx.search(text):
                matches.add(original_kw)
                matches_words.extend(m.group(0).strip() for m in rgx.finditer(text))

        matched_words.append(sorted(set(matches_words), key=str.lower))
        matched_keywords.append(sorted(matches, key=str.lower))

    df['matched keywords'] = matched_keywords
    df['matched words'] = matched_words
    print(f'Keywords have been matched for {category} - {country}')
    return df

def save_data(df, output_path, country=''):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_json(output_path, orient='records', lines=True)
        print(f'The data was saved successfully - {country}!')
    except Exception as e:
        print(f'Failed to save data - {country}. Error: {e}')

def process_country(country: str):
    print(f'Processing {country}')

    keyword_lists_dir = f'{keyword_lists_folder_path}{country}{keyword_lists_file_ending}'
    keyword_lists_local = import_keywords(keyword_lists_dir, country=country)

    keyword_lists_uk_dir = f'{keyword_lists_folder_path}UK{keyword_lists_file_ending}'
    keyword_lists_uk = import_keywords(keyword_lists_uk_dir, country='UK')

    english_actor_set = english_speaking_actors.get(country, set())

    dataset_dir = f'{datasets_folder_path}{country}{datasets_file_ending}'

    dataset = import_data(dataset_dir, country=country)
    if not dataset:
        raise RuntimeError(f"No data loaded for {country}")

    df = pd.DataFrame(dataset)
    df = normalise_publication_dates(df)
    df_split = split_text_into_sentences(df, country=country)
    df_split = df_split[df_split.text != 'nan']
    df_split = df_split.dropna(subset=['publication date'])

    for category, local_keywords in keyword_lists_local.items():
        english_keywords = keyword_lists_uk.get(category, [])

        df_category = match_on_keywords_by_actor(
            df_split,
            category=category,
            local_keywords=local_keywords,
            english_keywords=english_keywords,
            english_actor_set=english_actor_set,
            country=country
        )

        kw_col = 'matched keywords'
        flag_col = 'matched'

        df_category[flag_col] = df_category[kw_col].apply(
            lambda x: 1 if isinstance(x, list) and len(x) > 0 else 0
        )

        df_category[kw_col] = df_category[kw_col].apply(
            lambda x: x if isinstance(x, list) and len(x) > 0 else None
        )

        id_cols = ['entry_ID', 'sentence_id']
        other_cols = [c for c in df_category.columns if c not in id_cols]
        df_category = df_category[id_cols + other_cols]

        matched_dataset_dir = f"{matched_datasets_folder_path}/{country}/{country}_{category}{matched_datasets_file_ending}"
        save_data(df_category, matched_dataset_dir, country=country)

    print(f'{country} has been processed')
    return country

if __name__ == "__main__":
    max_workers = min(len(all_countries), 8)

    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(process_country, ctr): ctr for ctr in all_countries}

        for future in as_completed(futures):
            ctr = futures[future]
            try:
                done = future.result()
                print(f'Finished {done}')
            except Exception as e:
                print(f'Failed {ctr} ({e})')