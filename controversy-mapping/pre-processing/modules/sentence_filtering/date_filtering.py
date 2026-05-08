import pandas as pd
import json
from pathlib import Path
import html
import random

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

cols_to_add_from_reduced = [
    'link', 
    'title', 
    'text'
]

# number_of_texts = 15 # Max number of texts pr peak pr topic pr country
number_of_texts_excel = 100 # Max number of texts pr peak pr topic pr country
number_of_characters_excel = 300 # Max number of characters from each text

input_data_folder = '/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data'
input_peaks_folder = '/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks' # '/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks'
reduced_data_folder = '/work/YOU-DARE/controversy-mapping/sentence_filtering/reduced_data/'
output_folder = '/work/YOU-DARE/controversy-mapping/trend-analysis/output/packages_for_researchers' # '/work/YOU-DARE/controversy-mapping/trend-analysis/output/packages_for_researchers'

# seed
random.seed(1770661406) # Unix Epoch Feb 09 19:23:26 2026 CET

log_counts = {}

def filter_dates(df, from_date, to_date):
    ''' Sorts and filtes data based on given arguments.
        - from_date: 'yyyy-mm-dd' this date is included in the final dataset
        - to_date: 'yyyy-mm-dd' this date is included in the final dataset
    '''
    df['publication date'] = pd.to_datetime(
        df['publication date'],
        format='%Y-%m-%d',
        errors='coerce'
    )

    # Filter by from_date and to_date if provided
    if from_date:
        from_dt = pd.to_datetime(from_date, errors='coerce') # Fills all invalid dates with NaT
        if pd.notna(from_dt):
            df = df[
                (df['publication date'].isna()) |  # keep NaT rows
                (df['publication date'] >= from_dt)  # apply filter only to real dates
            ]

    if to_date:
        to_dt = pd.to_datetime(to_date, errors='coerce') # Fills all invalid dates with NaT
        if pd.notna(to_dt):
            df = df[
                (df['publication date'].isna()) |  # keep NaT rows
                (df['publication date'] <= to_dt)  # apply filter only to real dates
            ]

    df['publication date'] = df['publication date'].dt.strftime('%Y-%m-%d')
    
    return df

def sample_even_by_actor_platform(df, n, actor_col="actor", platform_col="platform", random_state=None):
    if df.empty or n <= 0:
        return df.head(0).copy()
    if len(df) <= n:
        return df.copy()

    tmp = df.copy()

    tmp[actor_col] = tmp[actor_col].fillna("UNKNOWN_ACTOR")
    tmp[platform_col] = tmp[platform_col].fillna("UNKNOWN_PLATFORM")
    tmp["actor_platform_pair"] = list(zip(tmp[actor_col], tmp[platform_col]))

    # Shuffle rows once for randomness within each actor/platform pair
    tmp = tmp.sample(frac=1, random_state=random_state)

    # Build per-pair queues (row indices) in this shuffled order
    pair_to_idxs = tmp.groupby("actor_platform_pair").apply(
        lambda g: list(g.index),
        include_groups=False
    ).to_dict()

    # Randomize pair order (so who gets picked first is random)
    pairs = list(pair_to_idxs.keys())
    pairs = pd.Series(pairs).sample(frac=1, random_state=random_state).tolist()

    chosen = []

    # Round-robin selection
    while len(chosen) < n:
        progressed = False
        for pair in pairs:
            if pair_to_idxs[pair]:
                chosen.append(pair_to_idxs[pair].pop(0))
                progressed = True
                if len(chosen) == n:
                    break
        if not progressed:
            break

    return tmp.loc[chosen].drop(columns=["actor_platform_pair"])

def save_excel_sample(
    df_filtered,
    df_reduced,
    output_base,
    max_rows=number_of_texts_excel,
    text_n_chars=number_of_characters_excel,
    actor_col="actor",
    platform_col="platform",
    matched_words_col="matched words",
    random_state=42,
    output_filename="sampled_texts.xlsx"
):
    # Sample up to max_rows using the same round-robin logic
    df_excel = sample_even_by_actor_platform(
        df_filtered,
        max_rows,
    ).copy()

    if df_excel.empty:
        # Still write an empty file with the expected columns
        empty_df = pd.DataFrame(columns=["actor", "platform", "title", "link", "text", "matched words"])
        empty_df.to_excel(output_base / output_filename, index=False)
        return

    # Join title/link/text from reduced data using entry_ID
    reduced_cols = ["link", "title", "text"]
    df_excel[reduced_cols] = df_reduced.reindex(df_excel["entry_ID"])[reduced_cols].to_numpy()

    # Keep only requested output columns
    df_excel = df_excel[["actor", "platform", "title", "link", "text", "matched words"]].copy()

    # Prepare text and title
    df_excel["text"] = df_excel["text"].fillna("").astype(str).str.strip()
    df_excel["title"] = df_excel["title"].fillna("").astype(str).str.strip()

    # Remove title from beginning of text (if present)
    mask = df_excel["title"].ne("") & df_excel.apply(
        lambda x: x["text"].startswith(x["title"]),
        axis=1
    )

    df_excel.loc[mask, "text"] = df_excel.loc[mask].apply(
        lambda x: x["text"][len(x["title"]):].lstrip(" :-\n"),
        axis=1
    )

    # Clean and truncate text
    df_excel["text"] = (
        df_excel["text"]
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.slice(0, text_n_chars)
    )

    # Optional: clean other columns too
    for col in ["actor", "platform", "title", "link"]:
        df_excel[col] = df_excel[col].fillna("").astype(str)

    # Save Excel file
    df_excel.to_excel(output_base / output_filename, index=False)

# run sampling
for country in all_countries:
    log_counts[country] = {}
    reduced_data_path = f'{reduced_data_folder}/{country}_reduced.jl'
    with open(reduced_data_path, 'r', encoding='utf-8') as reduced:
        reduced_data = [json.loads(line) for line in reduced]

    df_reduced = pd.DataFrame(reduced_data).reset_index(drop=True)
    df_reduced = df_reduced.set_index('entry_ID')

    for theme in all_themes:
        log_counts[country][theme] = {}
        input_data_path = f'{input_data_folder}/{country}/{country}_{theme}_indexed.jl'
        input_peaks_path = f'{input_peaks_folder}/{country}/{theme}_peaks.json'

        with open(input_data_path, 'r', encoding='utf-8') as input_data:
            data = [json.loads(line) for line in input_data]

        with open(input_peaks_path, 'r', encoding='utf-8') as input_peaks:
            peaks = json.load(input_peaks)

        df = pd.DataFrame(data)
        
        df['theme'] = theme

        for peak_id, (from_date, to_date) in peaks.items():
            df_filtered = filter_dates(df, from_date, to_date)
            df_filtered['peak_ID'] = peak_id

            log_counts[country][theme][f"peak_{peak_id}"] = len(df_filtered)

            output_base = Path(output_folder) / country / theme / f"peak_{peak_id}" / "sampled_texts"
            output_base.mkdir(parents=True, exist_ok=True)

            save_excel_sample(
                df_filtered=df_filtered,
                df_reduced=df_reduced,
                output_base=output_base,
            )

log_path = Path(output_folder) / "sampling_log.json"

with open(log_path, "w", encoding="utf-8") as f:
    json.dump(log_counts, f, indent=4, ensure_ascii=False)