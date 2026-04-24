import os
import glob
import csv
import json

import pandas as pd
import dateparser
from docx import Document

RAW_DIR = "/work/YOU-DARE/raw-data/final_raw"
INDEXED_DIR = "/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data"

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

OUTPUT_CSV = "/work/YOU-DARE/documentation_tables/csv_tables_matched/matched_texts.csv"
OUTPUT_DOCX = "/work/YOU-DARE/documentation_tables/csv_tables_matched/matched_texts.docx"
OUTPUT_LOG = "/work/YOU-DARE/documentation_tables/csv_tables_matched/matched_texts_log.txt"
OUTPUT_DATE_LOG = "/work/YOU-DARE/documentation_tables/csv_tables_matched/matched_texts_date_log.csv"
OUTPUT_DATE_LOG_JSON = "/work/YOU-DARE/documentation_tables/csv_tables_matched/matched_texts_date_log_nested.json"
OUTPUT_DATE_LOG_TXT_DIR = "/work/YOU-DARE/documentation_tables/csv_tables_matched/date_logs_by_country"

# Inclusive date range
START_DATE = pd.Timestamp("2015-01-01")
END_DATE = pd.Timestamp("2025-07-31")

START_DATE_NORM = START_DATE.normalize()
END_DATE_NORM = END_DATE.normalize()

# Replace these with the actual two keys used in your jsonl files
DATE_SOURCE_KEYS = [
    "publication date",
    "timestamp",
    "publication_date"
]

DATE_ORDER_BY_PAIR = {
    ("Dansk Folkepartis Ungdom (DFU)", "Website"): "DMY",
    ("Casa Pound", "Website"): "DMY",
    ("I Rami Spogli", "Website"): "DMY",
    ("Pro Vita e Famiglia", "Website"): "DMY",
    ("Cultura Vieții", "Website"): "DMY",
    ("GB NEWS", "Website"): "DMY",
}

def unify_date_source_columns(
    df: pd.DataFrame,
    date_source_keys: list[str],
    unified_date_col: str = "__unified_publication_date__",
    unified_source_col: str = "__unified_date_source_key__",
) -> pd.DataFrame:
    df = df.copy()

    if "actor" not in df.columns:
        df["actor"] = None
    if "platform" not in df.columns:
        df["platform"] = None

    df[unified_date_col] = None
    df[unified_source_col] = None

    for key in date_source_keys:
        if key in df.columns:
            key_values = df[key]

            empty_unified_mask = (
                df[unified_date_col].isna()
                | (df[unified_date_col].astype(str).str.strip() == "")
            )

            non_empty_source_mask = (
                key_values.notna()
                & (key_values.astype(str).str.strip() != "")
            )

            mask = empty_unified_mask & non_empty_source_mask

            df.loc[mask, unified_date_col] = key_values[mask]
            df.loc[mask, unified_source_col] = key

    return df

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

        # Apply custom date order only for specific pairs
        date_order = date_order_by_pair.get((actor, platform))
        if date_order:
            settings['DATE_ORDER'] = date_order

        return dateparser.parse(s, settings=settings)

    df[col_name] = df.apply(parse_date, axis=1)
    df[col_name] = pd.to_datetime(df[col_name], errors='coerce')

    return df


def load_jsonl_to_df(filepath):
    records = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            try:
                obj = json.loads(line)
                records.append(obj)
            except json.JSONDecodeError:
                continue

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)

def to_json_safe_value(value):
    if value is None:
        return None

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value

# def prepare_and_filter_df(
#     df: pd.DataFrame,
#     date_source_keys: list[str],
#     date_order_by_pair: dict[tuple[str, str], str] | None = None,
# ) -> pd.DataFrame:
#     if df.empty:
#         return df.copy()

#     df = df.copy()

#     if "actor" not in df.columns:
#         df["actor"] = None
#     if "platform" not in df.columns:
#         df["platform"] = None

#     # Use a TEMP column so we do not overwrite an existing "publication date" column
#     unified_date_col = "__unified_publication_date__"
#     df[unified_date_col] = None

#     for key in date_source_keys:
#         if key in df.columns:
#             mask = df[unified_date_col].isna() | (
#                 df[unified_date_col].astype(str).str.strip() == ""
#             )
#             df.loc[mask, unified_date_col] = df.loc[mask, key]

#     # Parse the temp date column
#     df = normalise_publication_dates(
#         df,
#         col_name=unified_date_col,
#         date_order_by_pair=date_order_by_pair,
#     )

#     # Exclude Flashback
#     df = df[df["platform"] != "Flashback"]

#     # Keep only rows within the inclusive range
#     in_range_mask = (
#         df[unified_date_col].notna() &
#         (df[unified_date_col] >= START_DATE) &
#         (df[unified_date_col] <= END_DATE)
#     )
#     df = df[in_range_mask]

#     # Optional: rename parsed temp column back to publication date
#     df = df.rename(columns={unified_date_col: "publication date"})

#     return df

def prepare_and_filter_df(
    df: pd.DataFrame,
    date_source_keys: list[str],
    date_order_by_pair: dict[tuple[str, str], str] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    df = df.copy()

    unified_date_col = "__unified_publication_date__"

    df = unify_date_source_columns(
        df,
        date_source_keys=date_source_keys,
        unified_date_col=unified_date_col,
        unified_source_col="__unified_date_source_key__",
    )

    # Parse the temp date column
    df = normalise_publication_dates(
        df,
        col_name=unified_date_col,
        date_order_by_pair=date_order_by_pair,
    )

    # Exclude Flashback
    df = df[df["platform"] != "Flashback"]

    # Compare on normalized day so times do not accidentally exclude boundary dates
    normalized_day = df[unified_date_col].dt.normalize()

    in_range_mask = (
        normalized_day.notna()
        & (normalized_day >= START_DATE_NORM)
        & (normalized_day <= END_DATE_NORM)
    )

    df = df[in_range_mask]

    # Rename parsed temp column back to publication date
    df = df.rename(columns={unified_date_col: "publication date"})

    return df

# def collect_date_audit_rows():
#     audit_rows = []
#     raw_pattern = os.path.join(RAW_DIR, "*_YOUDARE-WEBDATA_combined.jsonl")

#     for filepath in sorted(glob.glob(raw_pattern)):
#         country = get_country_from_raw_filename(filepath)
#         if country not in COUNTRIES:
#             continue

#         df = load_jsonl_to_df(filepath)
#         if df.empty:
#             continue

#         unified_date_col = "__unified_publication_date__"
#         unified_source_col = "__unified_date_source_key__"
#         raw_value_col = "__unified_publication_date_raw__"

#         df = unify_date_source_columns(
#             df,
#             date_source_keys=DATE_SOURCE_KEYS,
#             unified_date_col=unified_date_col,
#             unified_source_col=unified_source_col,
#         )

#         # Preserve the raw chosen value exactly as it appears before parsing
#         df[raw_value_col] = df[unified_date_col]

#         df = normalise_publication_dates(
#             df,
#             col_name=unified_date_col,
#             date_order_by_pair=DATE_ORDER_BY_PAIR,
#         )

#         normalized_day = df[unified_date_col].dt.normalize()

#         status = pd.Series("UNPARSED_OR_EMPTY", index=df.index, dtype="object")

#         inside_mask = (
#             normalized_day.notna()
#             & (normalized_day >= START_DATE_NORM)
#             & (normalized_day <= END_DATE_NORM)
#         )
#         outside_mask = normalized_day.notna() & ~inside_mask

#         status.loc[inside_mask] = "INSIDE_RANGE"
#         status.loc[outside_mask] = "OUTSIDE_RANGE"

#         for _, row in df.iterrows():
#             parsed_dt = row[unified_date_col]
#             parsed_date = (
#                 parsed_dt.strftime("%Y-%m-%d")
#                 if pd.notna(parsed_dt)
#                 else ""
#             )
#             parsed_datetime = (
#                 parsed_dt.strftime("%Y-%m-%d %H:%M:%S")
#                 if pd.notna(parsed_dt)
#                 else ""
#             )

#             audit_rows.append({
#                 "Country": country_name(country),
#                 "Country code": country,
#                 "Source file": os.path.basename(filepath),
#                 "Actor": row.get("actor"),
#                 "Platform": row.get("platform"),
#                 "Date source key used": row.get(unified_source_col),
#                 "Raw date value": row.get(raw_value_col),
#                 "Standardised date": parsed_date,
#                 "Standardised datetime": parsed_datetime,
#                 "Range status": status.loc[row.name],
#             })

#     return audit_rows

def collect_date_audit_nested():
    nested = {}
    raw_pattern = os.path.join(RAW_DIR, "*_YOUDARE-WEBDATA_combined.jsonl")

    for filepath in sorted(glob.glob(raw_pattern)):
        country = get_country_from_raw_filename(filepath)
        if country not in COUNTRIES:
            continue

        df = load_jsonl_to_df(filepath)
        if df.empty:
            continue

        unified_date_col = "__unified_publication_date__"
        unified_source_col = "__unified_date_source_key__"
        raw_value_col = "__unified_publication_date_raw__"

        df = unify_date_source_columns(
            df,
            date_source_keys=DATE_SOURCE_KEYS,
            unified_date_col=unified_date_col,
            unified_source_col=unified_source_col,
        )

        # preserve original selected raw date string
        df[raw_value_col] = df[unified_date_col]

        df = normalise_publication_dates(
            df,
            col_name=unified_date_col,
            date_order_by_pair=DATE_ORDER_BY_PAIR,
        )

        normalized_day = df[unified_date_col].dt.normalize()

        status = pd.Series("UNPARSED_OR_EMPTY", index=df.index, dtype="object")

        inside_mask = (
            normalized_day.notna()
            & (normalized_day >= START_DATE_NORM)
            & (normalized_day <= END_DATE_NORM)
        )
        outside_mask = normalized_day.notna() & ~inside_mask

        status.loc[inside_mask] = "INSIDE_RANGE"
        status.loc[outside_mask] = "OUTSIDE_RANGE"

        country_bucket = nested.setdefault(country, {})

        for _, row in df.iterrows():
            actor = row.get("actor")
            platform = row.get("platform")

            actor_str = str(actor).strip() if pd.notna(actor) and str(actor).strip() else "UNKNOWN_ACTOR"
            platform_str = str(platform).strip() if pd.notna(platform) and str(platform).strip() else "UNKNOWN_PLATFORM"

            parsed_dt = row[unified_date_col]

            standardised_date = (
                parsed_dt.strftime("%Y-%m-%d")
                if pd.notna(parsed_dt)
                else None
            )
            standardised_datetime = (
                parsed_dt.strftime("%Y-%m-%d %H:%M:%S")
                if pd.notna(parsed_dt)
                else None
            )

            entry = {
                "raw_date": to_json_safe_value(row.get(raw_value_col)),
                "standardised_date": standardised_date,
                "standardised_datetime": standardised_datetime,
                "range_status": to_json_safe_value(status.loc[row.name]),
                "date_source_key": to_json_safe_value(row.get(unified_source_col)),
                "source_file": os.path.basename(filepath),
            }

            actor_bucket = country_bucket.setdefault(actor_str, {})
            platform_bucket = actor_bucket.setdefault(platform_str, [])
            platform_bucket.append(entry)

    return nested

# def sort_date_audit_nested(nested):
#     sorted_nested = {}

#     for country in sorted(nested.keys()):
#         sorted_nested[country] = {}

#         for pair_key in sorted(nested[country].keys()):
#             entries = nested[country][pair_key]

#             def sort_key(item):
#                 dt = pd.to_datetime(item["standardised_datetime"], errors="coerce")
#                 return (
#                     pd.isna(dt),  # False first, True last
#                     dt if pd.notna(dt) else pd.Timestamp.max,
#                     str(item.get("raw_date", "")),
#                 )

#             sorted_entries = sorted(entries, key=sort_key)
#             sorted_nested[country][pair_key] = sorted_entries

#     return sorted_nested

def sort_date_audit_nested(nested):
    sorted_nested = {}

    for country in sorted(nested.keys()):
        sorted_nested[country] = {}

        for actor in sorted(nested[country].keys()):
            sorted_nested[country][actor] = {}

            for platform in sorted(nested[country][actor].keys()):
                entries = nested[country][actor][platform]

                def sort_key(item):
                    dt = pd.to_datetime(item["standardised_datetime"], errors="coerce")
                    return (
                        pd.isna(dt),
                        dt if pd.notna(dt) else pd.Timestamp.max,
                        str(item.get("raw_date", "")),
                    )

                sorted_entries = sorted(entries, key=sort_key)
                sorted_nested[country][actor][platform] = sorted_entries

    return sorted_nested

def write_date_log(rows, output_file):
    if not rows:
        pd.DataFrame(columns=[
            "Country",
            "Country code",
            "Source file",
            "Actor",
            "Platform",
            "Date source key used",
            "Raw date value",
            "Standardised date",
            "Standardised datetime",
            "Range status",
        ]).to_csv(output_file, index=False, encoding="utf-8")
        return

    df = pd.DataFrame(rows)

    # Sort chronologically by parsed datetime; unparsed values go last
    df["__sort_datetime__"] = pd.to_datetime(
        df["Standardised datetime"],
        errors="coerce"
    )

    df = df.sort_values(
        by=["__sort_datetime__", "Country code", "Source file", "Raw date value"],
        na_position="last",
        kind="stable",
    )

    df = df.drop(columns=["__sort_datetime__"])

    df.to_csv(output_file, index=False, encoding="utf-8")
    
def write_date_log_nested_json(nested, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(nested, f, ensure_ascii=False, indent=2)

# def write_date_log_txt_by_country(nested, output_dir):
#     os.makedirs(output_dir, exist_ok=True)

#     for country in sorted(nested.keys()):
#         lines = []
#         lines.append(f"DATE LOG FOR {country} ({country_name(country)})")
#         lines.append("=" * 80)
#         lines.append("")
#         lines.append(
#             f"Included date range: {START_DATE_NORM.strftime('%Y-%m-%d')} to {END_DATE_NORM.strftime('%Y-%m-%d')}"
#         )
#         lines.append("")

#         for pair_key in sorted(nested[country].keys()):
#             lines.append(pair_key)
#             lines.append("-" * len(pair_key))

#             for item in nested[country][pair_key]:
#                 raw_date = item.get("raw_date", "")
#                 std_date = item.get("standardised_date", "")
#                 std_dt = item.get("standardised_datetime", "")
#                 range_status = item.get("range_status", "")
#                 source_key = item.get("date_source_key", "")
#                 source_file = item.get("source_file", "")

#                 indicator = {
#                     "INSIDE_RANGE": "[IN]",
#                     "OUTSIDE_RANGE": "[OUT]",
#                     "UNPARSED_OR_EMPTY": "[NA]",
#                 }.get(range_status, "[?]")

#                 lines.append(
#                     f"{indicator} raw='{raw_date}' | std_date='{std_date}' | std_dt='{std_dt}' | source_key='{source_key}' | file='{source_file}'"
#                 )

#             lines.append("")

#         output_file = os.path.join(output_dir, f"{country}_date_log.txt")
#         with open(output_file, "w", encoding="utf-8") as f:
#             f.write("\n".join(lines))

def write_date_log_txt_by_country(nested, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for country in sorted(nested.keys()):
        lines = []
        lines.append(f"DATE LOG FOR {country} ({country_name(country)})")
        lines.append("=" * 80)
        lines.append("")
        lines.append(
            f"Included date range: {START_DATE_NORM.strftime('%Y-%m-%d')} to {END_DATE_NORM.strftime('%Y-%m-%d')}"
        )
        lines.append("")

        for actor in sorted(nested[country].keys()):
            lines.append(actor)
            lines.append("-" * len(actor))

            for platform in sorted(nested[country][actor].keys()):
                lines.append(f"  Platform: {platform}")

                for item in nested[country][actor][platform]:
                    raw_date = item.get("raw_date", "")
                    std_date = item.get("standardised_date", "")
                    std_dt = item.get("standardised_datetime", "")
                    range_status = item.get("range_status", "")
                    source_key = item.get("date_source_key", "")
                    source_file = item.get("source_file", "")

                    indicator = {
                        "INSIDE_RANGE": "[IN]",
                        "OUTSIDE_RANGE": "[OUT]",
                        "UNPARSED_OR_EMPTY": "[NA]",
                    }.get(range_status, "[?]")

                    lines.append(
                        f"    {indicator} raw='{raw_date}' | std_date='{std_date}' | std_dt='{std_dt}' | source_key='{source_key}' | file='{source_file}'"
                    )

                lines.append("")

            lines.append("")

        output_file = os.path.join(output_dir, f"{country}_date_log.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

def get_country_from_raw_filename(filepath):
    filename = os.path.basename(filepath)
    return filename[:2]


def get_theme_from_indexed_filename(filepath):
    filename = os.path.basename(filepath)
    # Example: DK_lgb_indexed.jl -> lgb
    parts = filename.split("_")
    if len(parts) >= 3:
        return parts[1]
    return ""


def country_name(country_code):
    names = {
        "DK": "Denmark",
        "ES": "Spain",
        "FR": "France",
        "HU": "Hungary",
        "IT": "Italy",
        "RO": "Romania",
        "SE": "Sweden",
        "UK": "United Kingdom",
    }
    return names.get(country_code, country_code)


def format_theme(theme):
    theme_map = {
        "lgb": "LGB",
        "gender": "Gender",
        "migration": "Migration",
    }
    return theme_map.get(theme, theme)


def format_percentage(numerator, denominator):
    if denominator == 0:
        return "0.00%"
    percentage = (numerator / denominator) * 100
    return f"{percentage:.2f}%"


def collect_raw_totals():
    raw_totals = {}
    raw_original_totals = {}
    raw_pattern = os.path.join(RAW_DIR, "*_YOUDARE-WEBDATA_combined.jsonl")

    for filepath in sorted(glob.glob(raw_pattern)):
        country = get_country_from_raw_filename(filepath)
        if country not in COUNTRIES:
            continue

        original_count = count_valid_jsonl_rows(filepath)

        df = load_jsonl_to_df(filepath)
        df_filtered = prepare_and_filter_df(
            df,
            date_source_keys=DATE_SOURCE_KEYS,
            date_order_by_pair=DATE_ORDER_BY_PAIR,
        )

        filtered_count = len(df_filtered)

        raw_original_totals[country] = {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "count": original_count,
        }
        raw_totals[country] = filtered_count

    total_corpus = sum(raw_totals.values())
    total_raw_original = sum(item["count"] for item in raw_original_totals.values())

    return raw_totals, total_corpus, raw_original_totals, total_raw_original

def collect_indexed_counts():
    indexed_counts = []

    for country in COUNTRIES:
        country_dir = os.path.join(INDEXED_DIR, country)
        if not os.path.isdir(country_dir):
            continue

        indexed_pattern = os.path.join(country_dir, "*.jl")

        for filepath in sorted(glob.glob(indexed_pattern)):
            theme = get_theme_from_indexed_filename(filepath)

            df = load_jsonl_to_df(filepath)

            print("\n" + "="*60)
            print(f"DEBUG FILE: {filepath}")
            print(f"Columns: {list(df.columns)}")

            if not df.empty:
                print("Sample rows:")
                print(df.head(2).to_dict(orient="records"))

            # Check which date keys exist
            available_keys = [k for k in DATE_SOURCE_KEYS if k in df.columns]
            print(f"Available date keys: {available_keys}")

            # Check raw values before normalisation
            for key in available_keys:
                print(f"Sample values for {key}:")
                print(df[key].head(5).tolist())

            df_filtered = prepare_and_filter_df(
                df,
                date_source_keys=DATE_SOURCE_KEYS,
                date_order_by_pair=DATE_ORDER_BY_PAIR,
            )

            print(f"Rows BEFORE filtering: {len(df)}")
            print(f"Rows AFTER filtering: {len(df_filtered)}")

            # Optional: inspect parsed dates
            if not df_filtered.empty:
                print("Sample parsed dates:")
                print(df_filtered["publication date"].head(5))
            else:
                print("All rows removed after filtering!")

            matched_count = len(df_filtered)

            indexed_counts.append({
                "filepath": filepath,
                "filename": os.path.basename(filepath),
                "country": country,
                "theme": theme,
                "count": matched_count,
            })

    return indexed_counts


def build_rows(grouped_rows):
    rows = []

    for country in sorted(grouped_rows.keys()):
        for row in sorted(grouped_rows[country], key=lambda x: x["theme"]):
            rows.append({
                "Country": country_name(country),
                "Theme": format_theme(row["theme"]),
                "Number of matched texts": row["count"],
                "Share of texts (total corpus)": row["share_total"],
                "Share of texts (country total)": row["share_country"],
            })

    return rows


def write_csv(rows, output_file):
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Country",
                "Theme",
                "Number of matched texts",
                "Share of texts (total corpus)",
                "Share of texts (country total)",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_docx(rows, output_file):
    doc = Document()
    doc.add_heading("Matched texts", level=1)

    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"

    headers = [
        "Country",
        "Theme",
        "Number of matched texts",
        "Share of texts (total corpus)",
        "Share of texts (country total)",
    ]

    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        header_cells[i].text = header

    for row in rows:
        cells = table.add_row().cells
        cells[0].text = str(row["Country"])
        cells[1].text = str(row["Theme"])
        cells[2].text = str(row["Number of matched texts"])
        cells[3].text = str(row["Share of texts (total corpus)"])
        cells[4].text = str(row["Share of texts (country total)"])

    doc.save(output_file)

def count_valid_jsonl_rows(filepath):
    count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            try:
                json.loads(line)
                count += 1
            except json.JSONDecodeError:
                continue

    return count

def build_log(
    indexed_counts,
    raw_totals,
    total_raw,
    indexed_totals_by_country,
    total_indexed,
    raw_original_totals,
    total_raw_original,
):
    lines = []

    lines.append("MATCHED TEXTS LOG")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Date range included: {START_DATE.strftime('%d/%m/%Y')} - {END_DATE.strftime('%d/%m/%Y')}")
    lines.append(f"Date source keys checked: {', '.join(DATE_SOURCE_KEYS)}")
    lines.append("")

    lines.append("1. Indexed files and number of texts")
    lines.append("-" * 60)

    current_country = None
    for item in sorted(indexed_counts, key=lambda x: (x["country"], x["filename"])):
        country = item["country"]
        if country != current_country:
            current_country = country
            lines.append(f"\n{country} ({country_name(country)})")

        lines.append(f"  {item['filename']}: {item['count']}")

    lines.append("")
    lines.append("2. Total indexed texts per country")
    lines.append("-" * 60)
    for country in sorted(indexed_totals_by_country.keys()):
        lines.append(f"{country} ({country_name(country)}): {indexed_totals_by_country[country]}")

    lines.append("")
    lines.append("3. Raw files: total lines and lines after date filtering")
    lines.append("-" * 60)
    for country in sorted(raw_original_totals.keys()):
        original = raw_original_totals[country]
        filtered = raw_totals.get(country, 0)

        lines.append(f"{country} ({country_name(country)})")
        lines.append(f"  File: {original['filename']}")
        lines.append(f"  Total valid JSONL rows: {original['count']}")
        lines.append(f"  Rows after filtering: {filtered}")
        lines.append("")

    lines.append("4. Overall raw totals")
    lines.append("-" * 60)
    lines.append(f"Total valid raw rows overall: {total_raw_original}")
    lines.append(f"Total raw rows overall after filtering: {total_raw}")

    lines.append("")
    lines.append("5. Overall totals")
    lines.append("-" * 60)
    lines.append(f"Total indexed texts overall: {total_indexed}")
    lines.append(f"Total raw texts overall: {total_raw}")

    return "\n".join(lines)

# def main():
#     os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

#     raw_totals, total_raw, raw_original_totals, total_raw_original = collect_raw_totals()
#     indexed_counts = collect_indexed_counts()

#     grouped_rows = {}
#     indexed_totals_by_country = {}

#     for item in indexed_counts:
#         country = item["country"]
#         count = item["count"]
#         country_total = raw_totals.get(country, 0)

#         row = {
#             "theme": item["theme"],
#             "count": count,
#             "share_total": format_percentage(count, total_raw),
#             "share_country": format_percentage(count, country_total),
#         }

#         grouped_rows.setdefault(country, []).append(row)
#         indexed_totals_by_country[country] = indexed_totals_by_country.get(country, 0) + count

#     total_indexed = sum(indexed_totals_by_country.values())
#     rows = build_rows(grouped_rows)

#     write_csv(rows, OUTPUT_CSV)
#     write_docx(rows, OUTPUT_DOCX)

#     log_text = build_log(
#         indexed_counts=indexed_counts,
#         raw_totals=raw_totals,
#         total_raw=total_raw,
#         indexed_totals_by_country=indexed_totals_by_country,
#         total_indexed=total_indexed,
#         raw_original_totals=raw_original_totals,
#         total_raw_original=total_raw_original,
#     )

#     with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
#         f.write(log_text)

#     print(f"Wrote CSV table to: {OUTPUT_CSV}")
#     print(f"Wrote Word table to: {OUTPUT_DOCX}")
#     print(f"Wrote log file to: {OUTPUT_LOG}")

# if __name__ == "__main__":
#     main()

def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    raw_totals, total_raw, raw_original_totals, total_raw_original = collect_raw_totals()
    indexed_counts = collect_indexed_counts()

    date_audit_nested = collect_date_audit_nested()
    date_audit_nested = sort_date_audit_nested(date_audit_nested)

    grouped_rows = {}
    indexed_totals_by_country = {}

    for item in indexed_counts:
        country = item["country"]
        count = item["count"]
        country_total = raw_totals.get(country, 0)

        row = {
            "theme": item["theme"],
            "count": count,
            "share_total": format_percentage(count, total_raw),
            "share_country": format_percentage(count, country_total),
        }

        grouped_rows.setdefault(country, []).append(row)
        indexed_totals_by_country[country] = indexed_totals_by_country.get(country, 0) + count

    total_indexed = sum(indexed_totals_by_country.values())
    rows = build_rows(grouped_rows)

    write_csv(rows, OUTPUT_CSV)
    write_docx(rows, OUTPUT_DOCX)
    write_date_log_nested_json(date_audit_nested, OUTPUT_DATE_LOG_JSON)
    write_date_log_txt_by_country(date_audit_nested, OUTPUT_DATE_LOG_TXT_DIR)

    log_text = build_log(
        indexed_counts=indexed_counts,
        raw_totals=raw_totals,
        total_raw=total_raw,
        indexed_totals_by_country=indexed_totals_by_country,
        total_indexed=total_indexed,
        raw_original_totals=raw_original_totals,
        total_raw_original=total_raw_original,
    )

    with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
        f.write(log_text)

    print(f"Wrote CSV table to: {OUTPUT_CSV}")
    print(f"Wrote Word table to: {OUTPUT_DOCX}")
    print(f"Wrote log file to: {OUTPUT_LOG}")
    print(f"Wrote nested date JSON log to: {OUTPUT_DATE_LOG_JSON}")
    print(f"Wrote country date logs to: {OUTPUT_DATE_LOG_TXT_DIR}")

if __name__ == "__main__":
    main()