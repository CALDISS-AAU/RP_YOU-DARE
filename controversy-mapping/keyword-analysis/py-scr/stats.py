import os
import sys 
import numpy as np
import pandas as pd
import json
import datetime as dt
import dateparser
import seaborn
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
pio.templates.default = "plotly_white"
pio.renderers.default = "browser"

# Functions
sys.path.append("/work/YOU-DARE/doccano")
from functions.functions import Doccano_Functions
doccano = Doccano_Functions()

# Loading RAW data 
HUNGARY_data_directory = '/work/YOU-DARE/scrapers/data/Hungary'
FRANCE_data_directory = '/work/YOU-DARE/scrapers/data/France'
ITALY_data_directory = '/work/YOU-DARE/scrapers/data/Italy'
UK_data_directory = '/work/YOU-DARE/scrapers/data/United_Kingdom'
ROMANIA_data_directory = '/work/YOU-DARE/scrapers/data/Romania'
SPAIN_data_directory = '/work/YOU-DARE/scrapers/data/Spain'
SWEDEN_data_directory = '/work/YOU-DARE/scrapers/data/Sweden'
DENMARK_data_directory = '/work/YOU-DARE/scrapers/data/Denmark'



# 1) Get all dataset file paths
list_of_HUNGARY_dataset_paths = doccano.get_all_dataset_paths(HUNGARY_data_directory)
list_of_ITALY_dataset_paths = doccano.get_all_dataset_paths(ITALY_data_directory)
list_of_FRANCE_dataset_paths = doccano.get_all_dataset_paths(FRANCE_data_directory)
list_of_UK_dataset_paths = doccano.get_all_dataset_paths(UK_data_directory)
list_of_ROMANIA_dataset_paths = doccano.get_all_dataset_paths(ROMANIA_data_directory)
list_of_SPAIN_datasets_paths = doccano.get_all_dataset_paths(SPAIN_data_directory)
list_of_SWEDEN_dataset_paths = doccano.get_all_dataset_paths(SWEDEN_data_directory)
list_of_DENMARK_dataset_paths = doccano.get_all_dataset_paths(DENMARK_data_directory)

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
                chunksize=25_000
            )
            print(f"streaming {filename}")
        except ValueError as e:
            print(f"⚠️ Skipping file {filename}: {e}")
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

# Dataset lists
hu_web, hu_tg = load_data_raw(list_of_HUNGARY_dataset_paths)
swe_web, swe_tg = load_data_raw(list_of_SWEDEN_dataset_paths)
swe_web = clean_web(swe_web)
swe_tg_test = clean_tg(swe_tg)
dk_df = load_data_raw(list_of_DENMARK_dataset_paths)
ro_web, ro_tg = load_data_raw(list_of_ROMANIA_dataset_paths)
ro_web = clean_date(ro_web)
ro_tg = clean_tg(ro_tg)
fr_df = load_data_raw(list_of_FRANCE_dataset_paths)
uk_web, uk_tg = load_data_raw(list_of_UK_dataset_paths)
es_web, es_tg = load_data_raw(list_of_SPAIN_datasets_paths)
es_web = clean_date(es_web)
es_tg = clean_tg(es_tg)
it_web, it_tg = load_data_raw(list_of_ITALY_dataset_paths)
it_web = clean_date(it_web)
it_tg = clean_tg(it_tg)

# Cleaning
## UK ##
uk_web = clean_date(uk_web)
uk_tg = clean_tg(uk_tg)

# Loading annotated data
data = pd.read_csv('/work/YOU-DARE/controversy-mapping/keyword-analysis/data/work/SE_annotated_labels_flat.csv')

# Datetime formatting
data["publication date"] = pd.to_datetime(data["publication date"])
data['year'] = data['publication date'].dt.year

# Grouping by source & year
counts = data.groupby(["source", "year"]).size().reset_index(name="count")
label_counts = data.groupby(['source', 'year', 'label']).size().reset_index(name='count')

fig = px.histogram(
    data,
    x="publication date",
    color="year",
    text_auto=True,
    nbins=21,
    barmode="overlay",
    category_orders={"year": sorted(data["year"].unique())},
    color_discrete_sequence=px.colors.sequential.Inferno,
    labels={
        "publication date": "Publication Date",
        "year": "Year"
    },
    title="Annotated Texts per Year: Hungary"
)
fig.update_traces(opacity=0.75)
fig.update_xaxes(
    title_text="Date of Publication",
    tickangle=45,
    showgrid=True,
    gridcolor="lightgray"
)
fig.update_yaxes(
    title_text="Number of Texts",
    showgrid=True,
    gridcolor="lightgray"
)

fig.update_layout(
    title_font=dict(size=22, family="Arial", color="black"),
    font=dict(size=14),
    bargap=0.1,
    plot_bgcolor="white",
    legend_title_text="Publication Year",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(l=60, r=40, t=80, b=80)
)

fig.show()
fig.write_html('/work/YOU-DARE/controversy-mapping/keyword-analysis/res/HU_text_pr_year.html')


# Texts pr year pr. actor
fig = px.histogram(
    counts,
    x="year",
    y="count",
    color="source",
    barmode="group",
    text_auto=True,
    title="Annotated Texts per Source per Year: Sweden",
    color_discrete_sequence=px.colors.sequential.Inferno,
    labels={
        "year": "Publication Year",
        "count": "Number of Texts",
        "source": "Actors"
    }
)
fig.update_traces(opacity=0.9)

fig.update_xaxes(
    title_text="Publication Year",
    tickangle=0,
    showgrid=True,
    gridcolor="lightgray",
    dtick=1  # One tick per year
)

fig.update_yaxes(
    title_text="Number of Texts",
    showgrid=True,
    gridcolor="lightgray"
)

fig.update_layout(
    title_font=dict(size=22, family="Arial", color="black"),
    font=dict(size=14),
    bargap=0.15,
    plot_bgcolor="white",
    legend_title_text="Actors",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(l=60, r=40, t=80, b=80)
)
fig.show()
fig.write_html('/work/YOU-DARE/controversy-mapping/keyword-analysis/res/SE_text_year_actor.html')


### RAW data plots ###
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
    counts = df.groupby(["Display_name", "year"]).size().reset_index(name="count")
    counts["share"] = (
        counts["count"] /
        counts.groupby("Display_name")["count"].transform("sum")
    )
    return counts

# ITALY #
it_web_counts = create_counts_web(it_web)
it_tg_counts= create_counts_tg(it_tg)
# UK #
uk_web_counts = create_counts_web(uk_web)
uk_tg_counts = create_counts_tg(uk_tg)


matrix = uk_web_counts.pivot(
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
        text="<b>Normalized activity share by actor and year: United Kingdom<b>", # Main Title
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
fig.write_html('/work/YOU-DARE/controversy-mapping/keyword-analysis/res/Activity share_UK_web.html')