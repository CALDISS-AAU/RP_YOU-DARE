import pandas as pd
import numpy as np
import dateparser
import os
import json
from docx import Document

COUNTRIES = [
    "DK",
    "ES",
    "FR",
    "HU",
    "IT",
    "RO",
    "SE",
    "UK",
]

DATE_ORDER_BY_PAIR = {
    ("Dansk Folkepartis Ungdom (DFU)", "Website"): "DMY",
    ("Casa Pound", "Website"): "DMY",
    ("I Rami Spogli", "Website"): "DMY",
    ("Pro Vita e Famiglia", "Website"): "DMY",
    ("Cultura Vieții", "Website"): "DMY",
    ("GB NEWS", "Website"): "DMY",
}

INFLUENCER_MAPPING_DIR = "/work/YOU-DARE/raw-data/mappings/actor_identifier_key/actor_identifier_key.csv"
OUTPUT_DIR = "/work/YOU-DARE/documentation_tables/csv_tables_anonymised"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# LOG_FILE = os.path.join(OUTPUT_DIR, "log.txt")
LOG_FILE = os.path.join(OUTPUT_DIR, "date_normalisation_log.json")
ACTOR_MAPPING_LOG_FILE = os.path.join(OUTPUT_DIR, "actor_mapping_log.json")

def _coalesce_columns(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    """Return first non-null value across candidate columns (row-wise)."""
    cols = [c for c in candidates if c in df.columns]
    if not cols:
        return pd.Series([pd.NA] * len(df), index=df.index)
    return df[cols].bfill(axis=1).iloc[:, 0]

def normalize_column(x):
    """Makes sure everything is a string rather than having unexpected lists."""
    if x is None:
        return None

    if isinstance(x, (list, tuple, np.ndarray)):
        if len(x) == 0:
            return None
        return " ".join(map(str, x))

    if pd.isna(x):
        return None

    return str(x)

def select_and_clean_relevant_columns(df: pd.DataFrame, country='') -> pd.DataFrame:
    relevant_columns = [
        'publication_date', 'timestamp',
        'platform',
        'actor'
    ]
    available_columns = [c for c in relevant_columns if c in df.columns]
    reduced_df = df[available_columns].copy()

    if 'platform' in reduced_df.columns:
        reduced_df = reduced_df[reduced_df['platform'] != 'Flashback'].copy()

    out = pd.DataFrame(index=reduced_df.index)

    out['publication date'] = _coalesce_columns(reduced_df, ['publication_date', 'timestamp'])
    out['actor'] = reduced_df['actor'] if 'actor' in reduced_df.columns else pd.NA
    out['platform'] = reduced_df['platform'] if 'platform' in reduced_df.columns else pd.NA

    for col in ['actor', 'platform', 'publication date']:
        out[col] = out[col].apply(normalize_column)

    out = out[['actor', 'platform', 'publication date']]
    return out


def normalise_publication_dates(
    df: pd.DataFrame,
    col_name: str = 'publication date',
    date_order_by_pair: dict[tuple[str, str], str] | None = None
) -> pd.DataFrame:
    df = df.copy()

    if date_order_by_pair is None:
        date_order_by_pair = {}

    def parse_date(row):
        s = row[col_name]
        actor = row['actor']
        platform = row['platform']

        if pd.isna(s) or (isinstance(s, str) and s.strip() == ''):
            return None

        settings = {
            'RETURN_AS_TIMEZONE_AWARE': False
        }

        date_order = date_order_by_pair.get((actor, platform))
        if date_order:
            settings['DATE_ORDER'] = date_order

        return dateparser.parse(s, settings=settings)

    df[col_name] = df.apply(parse_date, axis=1)
    df[col_name] = pd.to_datetime(df[col_name], errors='coerce')

    return df


def build_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=['actor', 'platform']).copy()

    df_table = (
        df.groupby(['actor', 'platform'], dropna=False)
          .agg(
              number_of_texts=('publication date', 'size'),
              date_from=('publication date', 'min'),
              date_to=('publication date', 'max')
          )
          .reset_index()
    )

    df_table['date_from'] = df_table['date_from'].dt.strftime('%Y-%m-%d')
    df_table['date_to'] = df_table['date_to'].dt.strftime('%Y-%m-%d')

    df_table = df_table.rename(columns={
        'actor': 'Actor',
        'platform': 'Platform',
        'number_of_texts': 'Number of texts',
        'date_from': 'Date from',
        'date_to': 'Date to'
    })

    return df_table


def write_word_table(df_table: pd.DataFrame, output_file: str, country: str):
    doc = Document()
    doc.add_heading(f"{country} data contents", level=1)

    table = doc.add_table(rows=1, cols=len(df_table.columns))
    table.style = "Table Grid"

    header_cells = table.rows[0].cells
    for i, col_name in enumerate(df_table.columns):
        header_cells[i].text = str(col_name)

    for _, row in df_table.iterrows():
        cells = table.add_row().cells
        for i, value in enumerate(row):
            if pd.isna(value):
                cells[i].text = ""
            else:
                cells[i].text = str(value)

    doc.save(output_file)


def build_date_examples_log(df_before: pd.DataFrame, df_after: pd.DataFrame, max_examples: int = 5) -> dict:
    """
    Build nested log:
    {actor: {platform: [{"before": ..., "after": ...}, ...]}}
    """
    temp = df_before.copy()
    temp['publication date after'] = df_after['publication date']

    temp['publication date after'] = temp['publication date after'].dt.strftime('%Y-%m-%d')
    temp = temp.dropna(subset=['actor', 'platform']).copy()

    log = {}

    for (actor, platform), group in temp.groupby(['actor', 'platform'], dropna=False):
        examples = []

        subset = group[['publication date', 'publication date after']].copy()
        subset = subset[
            subset['publication date'].notna() | subset['publication date after'].notna()
        ].head(max_examples)

        for _, row in subset.iterrows():
            before_val = row['publication date']
            after_val = row['publication date after']

            if pd.isna(before_val):
                before_val = None
            else:
                before_val = str(before_val)

            if pd.isna(after_val):
                after_val = None
            else:
                after_val = str(after_val)

            examples.append({
                "before": before_val,
                "after": after_val
            })

        if actor not in log:
            log[actor] = {}

        log[actor][platform] = examples

    return log

def influencer_mapping(
    df_table: pd.DataFrame,
    country: str,
    df_mapping: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """
    Replace influencer actor names in df_table['Actor'] with identifiers,
    based on country-specific rows in df_mapping where is_influencer == True.

    Also build a detailed QA log for:
    - all actors in original summary table
    - all actors in mapping file for this country
    - all influencer actors in mapping file
    - mappings actually applied
    - inconsistencies between summary data and mapping data
    """
    df_out = df_table.copy()

    # Clean Actor column in summary table
    df_out['Actor'] = df_out['Actor'].apply(normalize_column)
    df_out['Actor'] = df_out['Actor'].str.strip()

    # Store original actor names before replacement
    df_out['Actor original'] = df_out['Actor']

    # Country-specific mapping data (all actors)
    df_country_map_all = df_mapping[df_mapping['country'] == country].copy()

    df_country_map_all = df_country_map_all.dropna(subset=['actor'])
    df_country_map_all['actor'] = df_country_map_all['actor'].str.strip()

    if 'identifier' in df_country_map_all.columns:
        df_country_map_all['identifier'] = df_country_map_all['identifier'].apply(normalize_column)
        df_country_map_all['identifier'] = df_country_map_all['identifier'].str.strip()

    # Influencer-only subset for replacement
    df_country_map_inf = df_country_map_all[
        df_country_map_all['is_influencer'] == True
    ].copy()

    df_country_map_inf = df_country_map_inf.dropna(subset=['actor', 'identifier'])

    # Duplicate checks
    duplicate_all_actors = (
        df_country_map_all[df_country_map_all.duplicated(subset=['actor'], keep=False)]
        .sort_values('actor')
    )

    duplicate_influencer_actors = (
        df_country_map_inf[df_country_map_inf.duplicated(subset=['actor'], keep=False)]
        .sort_values('actor')
    )

    if not duplicate_influencer_actors.empty:
        raise ValueError(
            f"Duplicate influencer actor names found in mapping for country {country}: "
            f"{duplicate_influencer_actors['actor'].tolist()}"
        )

    # Build replacement dictionary from influencer rows only
    mapping_dict = df_country_map_inf.set_index('actor')['identifier'].to_dict()

    # Apply mapping only to influencer actors
    df_out['Actor'] = df_out['Actor'].map(mapping_dict).fillna(df_out['Actor'])

    # Build sets for QA
    summary_actors = sorted(df_out['Actor original'].dropna().unique().tolist())
    mapping_all_actors = sorted(df_country_map_all['actor'].dropna().unique().tolist())
    mapping_influencer_actors = sorted(df_country_map_inf['actor'].dropna().unique().tolist())
    mapping_influencer_identifiers = sorted(df_country_map_inf['identifier'].dropna().unique().tolist())

    # Which mappings were actually applied?
    applied_df = (
        df_out[df_out['Actor original'].isin(mapping_dict.keys())][['Actor original', 'Actor']]
        .drop_duplicates()
        .sort_values('Actor original')
    )

    applied_mappings = [
        {
            "actor": row['Actor original'],
            "identifier": row['Actor']
        }
        for _, row in applied_df.iterrows()
    ]

    # Inconsistencies
    actors_in_summary_not_in_mapping = sorted(set(summary_actors) - set(mapping_all_actors))
    actors_in_mapping_not_in_summary = sorted(set(mapping_all_actors) - set(summary_actors))
    influencer_actors_not_in_summary = sorted(set(mapping_influencer_actors) - set(summary_actors))
    influencer_actors_in_summary_but_not_mapped = sorted(
        (set(summary_actors) & set(mapping_influencer_actors))
        - set(applied_df['Actor original'].tolist())
    )

    # More detailed duplicate reporting
    duplicate_all_actor_rows = []
    if not duplicate_all_actors.empty:
        for actor_name, group in duplicate_all_actors.groupby('actor'):
            duplicate_all_actor_rows.append({
                "actor": actor_name,
                "rows": group[['id', 'actor', 'identifier', 'is_influencer']].fillna("").to_dict(orient='records')
            })

    country_log = {
        # "all_actors_in_summary_table": summary_actors,
        # "all_actors_in_mapping_file": mapping_all_actors,
        # "all_influencer_actors_in_mapping_file": mapping_influencer_actors,
        # "all_influencer_identifiers_in_mapping_file": mapping_influencer_identifiers,
        # "influencer_mappings_applied": applied_mappings,
        "inconsistencies": {
            "actors_in_summary_table_not_in_mapping_file": actors_in_summary_not_in_mapping,
            "actors_in_mapping_file_not_in_summary_table": actors_in_mapping_not_in_summary,
            "influencer_actors_in_mapping_file_not_in_summary_table": influencer_actors_not_in_summary,
            "influencer_actors_in_summary_table_but_not_mapped": influencer_actors_in_summary_but_not_mapped,
            "duplicate_actor_rows_in_mapping_file": duplicate_all_actor_rows
        }
    }
    
    # sort: normal actors first, "Influencer" last
    df_out['_influencer_flag'] = df_out['Actor'].str.contains('Influencer', case=False, na=False)
    df_out = df_out.sort_values(by=['_influencer_flag', 'Actor']).drop(columns='_influencer_flag')

    # Drop helper column before export
    df_out = df_out.drop(columns=['Actor original'])

    return df_out, country_log

df_mapping = pd.read_csv(INFLUENCER_MAPPING_DIR)

# Clean mapping dataframe
df_mapping.columns = df_mapping.columns.str.strip()

for col in ['id', 'country', 'actor', 'identifier']:
    if col in df_mapping.columns:
        df_mapping[col] = df_mapping[col].apply(normalize_column)
        df_mapping[col] = df_mapping[col].str.strip()

if 'is_influencer' in df_mapping.columns:
    df_mapping['is_influencer'] = (
        df_mapping['is_influencer']
        .astype(str)
        .str.strip()
        .str.lower()
        .map({'true': True, 'false': False})
    )

log_data = {}
actor_mapping_log_data = {}

for country in COUNTRIES:
    input_file = f"/work/YOU-DARE/raw-data/final_raw/{country}_YOUDARE-WEBDATA_combined.jsonl"
    output_csv = os.path.join(OUTPUT_DIR, f"{country}_data_contents.csv")
    output_docx = os.path.join(OUTPUT_DIR, f"{country}_data_contents.docx")

    df = pd.read_json(input_file, lines=True)

    df_reduced = select_and_clean_relevant_columns(df, country=country)

    df_before = df_reduced.copy()
    df_normalised = normalise_publication_dates(df_reduced, date_order_by_pair=DATE_ORDER_BY_PAIR)

    df_table = build_summary_table(df_normalised)

    df_table, actor_mapping_log_data[country] = influencer_mapping(
        df_table=df_table,
        country=country,
        df_mapping=df_mapping
    )

    df_table.to_csv(output_csv, index=False)
    write_word_table(df_table, output_docx, country)

    log_data[country] = build_date_examples_log(df_before, df_normalised, max_examples=5)

    print(f"Saved CSV: {output_csv}")
    print(f"Saved Word table: {output_docx}")

with open(LOG_FILE, 'w', encoding='utf-8') as f:
    json.dump(log_data, f, indent=2, ensure_ascii=False)

print(f"Log saved to: {LOG_FILE}")

with open(ACTOR_MAPPING_LOG_FILE, 'w', encoding='utf-8') as f:
    json.dump(actor_mapping_log_data, f, indent=2, ensure_ascii=False)

print(f"Actor mapping log saved to: {ACTOR_MAPPING_LOG_FILE}")
