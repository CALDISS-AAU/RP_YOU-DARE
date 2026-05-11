from pathlib import Path
import os
from dotenv import load_dotenv

import sys 
import numpy as np
import pandas as pd
import json
import re
import datetime as dt
import dateparser
import seaborn
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

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


pio.templates.default = "plotly_white"
pio.renderers.default = "browser"

# Functions
sys.path.append(str(REPO_ROOT / "doccano"))
from functions.functions import Doccano_Functions
doccano = Doccano_Functions()

# load data function
def load_data_raw(dataset_list):
    """
    Takes a list of dataset file paths (returned by doccano functions)
    and concatenates them into a single DataFrame.

    Parameters:
    dataset_list: list of file paths

    Returns:
    web_df, tg_df
    """
    tg_frames = []
    web_frames = []
    
    for filename in dataset_list:
        fname = filename.lower()

        try:
            chunks = pd.read_json(
                filename,
                lines=True,
                encoding='utf-8',
                chunksize=15_000
            )
            print(f"streaming {filename}")
        except ValueError as e:
            print(f"Skipping file {filename}: {e}")
            continue

        # FIGURE OUT THE NAMES BITCH
        is_tg = "telegram" in fname
        is_yt = "yt" in fname
        is_web = "spider" in fname

        target = tg_frames if is_tg else web_frames

        # Append chunks to df
        for chunk in chunks:
            target.append(chunk)

    # Combine the results
    web_df = pd.concat(web_frames, ignore_index=True) if web_frames else pd.DataFrame()
    tg_df = pd.concat(tg_frames, ignore_index=True) if tg_frames else pd.DataFrame()
    
    print(f"\nWeb Dataframe: {web_df.shape}")
    print(f"\nTELEGRAM Dataframe: {tg_df.shape}")

    return web_df, tg_df

# Sanitize date and extract year for SPIDER or YT sources
def clean_date(df):
    df = df.copy()

    # Parse date bitch
    df["publication_date"] = df["publication_date"].apply(
        lambda x: dateparser.parse(str(x)) if pd.notna(x) else None
    )

    # Convert to pandas datetime, unify timezones
    df["publication_date"] = pd.to_datetime(
        df["publication_date"], errors="coerce", utc=True
    )

    # Extract year
    df["year"] = df["publication_date"].dt.year.astype("Int64")

    return df


def clean_tg(dataframe):
    dataframe['Timestamp'] = pd.to_datetime(
        dataframe.get('Timestamp'), errors='coerce', utc=True
    )
    dataframe['Edit_date'] = pd.to_datetime(
        dataframe.get('Edit_date'), errors='coerce', utc=True
    )

    dataframe['date_merged'] = (
        (dataframe['Timestamp'])
        .combine_first(dataframe['Edit_date'])
    )
    dataframe['year'] = dataframe['date_merged'].dt.year.astype('str')
    
    dataframe['Name'] = (
        (dataframe['Display-name'])
        .combine_first(dataframe['Display_name'])
    )
    
    drop_cols = [
        'Poop', 'Single_tear', 'Forwards', 'Views','Party',
        'Translation_confidence', 'Forwards_ER_reach', 'Exploding_head',
        'Forwards_ER_impressions', 'Scream', 'Starstruck', 'Vomit', 'Fire',
        'Thinking', 'Total_reactions', 'Angry', 'Translated_text', 'To',
        'Reply_ER_reach'
    ]

    dataframe = dataframe.drop(columns=[c for c in drop_cols if c in dataframe.columns], errors="ignore")

    return dataframe

def create_counts_web(df):
    df = df[df["year"].notna()]
    counts = df.groupby(["source", "year"]).size().reset_index(name="count")
    counts["share"] = (
        counts["count"] /
        counts.groupby("source")["count"].transform("sum")
    )
    return counts

def create_counts_tg(df):
    df = df[df["year"].notna()]
    counts = df.groupby(["Name", "year"]).size().reset_index(name="count")
    counts["share"] = (
        counts["count"] /
        counts.groupby("Name")["count"].transform("sum")
    )
    return counts



# Defining dataset dirs
HUNGARY_data_directory = str(REPO_ROOT / "scrapers" / "data" / "Hungary")
FRANCE_data_directory = str(REPO_ROOT / "scrapers" / "data" / "France")
ITALY_data_directory = str(REPO_ROOT / "scrapers" / "data" / "Italy")
UK_data_directory = str(REPO_ROOT / "scrapers" / "data" / "United_Kingdom")
ROMANIA_data_directory = str(REPO_ROOT / "scrapers" / "data" / "Romania")
SPAIN_data_directory = str(REPO_ROOT / "scrapers" / "data" / "Spain")
SWEDEN_data_directory = str(REPO_ROOT / "scrapers" / "data" / "Sweden")
DENMARK_data_directory = str(REPO_ROOT / "scrapers" / "data" / "Denmark")

# Get all dataset file paths
list_of_HUNGARY_dataset_paths = doccano.get_all_dataset_paths(HUNGARY_data_directory)
list_of_ITALY_dataset_paths = doccano.get_all_dataset_paths(ITALY_data_directory)
list_of_FRANCE_dataset_paths = doccano.get_all_dataset_paths(FRANCE_data_directory)
list_of_UK_dataset_paths = doccano.get_all_dataset_paths(UK_data_directory)
list_of_ROMANIA_dataset_paths = doccano.get_all_dataset_paths(ROMANIA_data_directory)
list_of_SPAIN_datasets_paths = doccano.get_all_dataset_paths(SPAIN_data_directory)
list_of_SWEDEN_dataset_paths = doccano.get_all_dataset_paths(SWEDEN_data_directory)
list_of_DENMARK_dataset_paths = doccano.get_all_dataset_paths(DENMARK_data_directory)

# Loading datasets
## HU ##
hu_web, hu_tg = load_data_raw(list_of_HUNGARY_dataset_paths)
orban_values = [
    'Viktor Orban - beszedek',
    'Viktor Orban - hirek',
    'Viktor Orban - interjuk'
]
hu_web['source'] = hu_web['source'].replace(orban_values, 'Viktor Orban')
## SWE ##
swe_web, swe_tg = load_data_raw(list_of_SWEDEN_dataset_paths)
## DK ##
dk_web, dk_tg = load_data_raw(list_of_DENMARK_dataset_paths)
## RO ##
ro_web, ro_tg = load_data_raw(list_of_ROMANIA_dataset_paths)
cultura_values = ['Cultura Vietii — /tag/demografia-este-destin/',
        'Cultura Vietii — /tag/restabilirea-ordinii-naturale/',
        'Cultura Vietii — demografie', 'Cultura Vietii — /tag/casatoria/',
        'Cultura Vietii — /tag/Mituri-despre-avort/',
        'Cultura Vietii — reproducere-asistata',
        'Cultura Vietii — esential',
        'Cultura Vietii — /tag/noua-era-intunecata/',
        'Cultura Vietii — /tag/bazele-conceptiei-sociale-ale-bisericii-ortodoxe/',
        'Cultura Vietii — /tag/probleme-fundamentale-de-bioetica/',
        'Cultura Vietii — /tag/omul-viitorului/',
        'Cultura Vietii — /tag/medicina-si-crestinism/',
        'Cultura Vietii — /tag/bioethica-militans/',
        'Cultura Vietii — /tag/video', 'Cultura Vietii — religie',
        'Cultura Vietii — educatie', 'Cultura Vietii — bioetica',
        'Cultura Vietii — sexualitate', 'Cultura Vietii — bunastarea-familiei']

ro_web['source'] = ro_web['source'].replace(cultura_values, 'Cultura Vietii')
## FR ##
fr_web, fr_tg = load_data_raw(list_of_FRANCE_dataset_paths)
## UK ##
uk_web, uk_tg = load_data_raw(list_of_UK_dataset_paths)
## ES ##
es_web, es_tg = load_data_raw(list_of_SPAIN_datasets_paths)
## IT ##
it_web, it_tg = load_data_raw(list_of_ITALY_dataset_paths)
blocco_values = [
    'Blocco Studentesco femminismo',
    'Blocco Studentesco genere',
    'Blocco Studentesco LGBT',
    'Blocco Studentesco aborto',
    'Blocco Studentesco virilita'
    ]

it_web['source'] = it_web['source'].replace(blocco_values, 'Blocco Studentesco')
# Cleaning
## UK ##
uk_web = clean_date(uk_web)
uk_tg = clean_tg(uk_tg)
## SWE ##
swe_web = clean_date(swe_web)
swe_tg = clean_tg(swe_tg)
## RO ##
ro_web = clean_date(ro_web)
ro_tg = clean_tg(ro_tg)
## IT ##
it_web = clean_date(it_web)
it_tg = clean_tg(it_tg)
## HU ##
hu_web = clean_date(hu_web)
hu_tg = clean_tg(hu_tg)
## ES ##
es_web = clean_date(es_web)
es_tg = clean_tg(es_tg)
## FR ##
fr_web = clean_date(fr_web)
fr_tg = clean_tg(fr_tg)
## DK ##
dk_web = clean_date(dk_web)

# Creating counts
# ITALY #
it_web_counts = create_counts_web(it_web)
it_tg_counts= create_counts_tg(it_tg)
# UK #
uk_web_counts = create_counts_web(uk_web)
uk_tg_counts = create_counts_tg(uk_tg)
# SWE #
swe_tg_counts = create_counts_tg(swe_tg)
swe_web_counts = create_counts_web(swe_web)
# HU #
hu_web_counts = create_counts_web(hu_web)
hu_tg_counts = create_counts_tg(hu_tg)
# RO #
ro_web_counts = create_counts_web(ro_web)
ro_tg_counts = create_counts_tg(ro_tg)
# ES #
es_web_counts = create_counts_web(es_web)
es_tg_counts = create_counts_tg(es_tg)
# FR #
fr_web_counts = create_counts_web(fr_web)
fr_tg_counts = create_counts_tg(fr_tg)
# DK # 
dk_web_counts = create_counts_web(dk_web)
### RAW data plots ###
matrix = hu_web_counts.pivot(
    index="source",
    columns="year",
    values="share"
).fillna(0)

fig = px.imshow(
    matrix,
    color_continuous_scale="Portland",
    text_auto=True,
    contrast_rescaling='infer',
    aspect="auto",
    labels=dict(color="Share")
)
fig.update_layout(
    plot_bgcolor='white',
    title=dict(
        text="<b>Normalized activity share by actor and year: Hungary<b>", # Main Title
        subtitle=dict(
            text="<i>Web Sources</i>", # Subtitle
            font=dict(
                color="gray", 
                size=15 # Subtitle font size
            ),
        ),
        x=0.5, # Center the title block
        xanchor='center'
    )
)

fig.show()
fig.write_html(str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "res" / "Activity share_HU_web.html"))