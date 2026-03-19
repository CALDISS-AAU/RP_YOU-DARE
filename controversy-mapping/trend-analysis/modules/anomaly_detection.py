"""
Detection of peaks/thematic salience using isolation forest anomaly detection. 
Code adjusted from Codex (OpenAI) output.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union
import warnings

import numpy as np
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px
from scipy.signal import find_peaks

from sklearn.ensemble import IsolationForest

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .plotters import *

@dataclass
class AnomalyConfig:
    """
    Config class for specifying parameters for anamolay detection.
    """
    window: int = 1 # n "windows" to partition data into - default 1 - works well for this task as we are not looking at "local" relative peaks
    contamination: Optional[Union[float, str]] = None # share of time points expected to be anomalies/peaks - None (default) uses share 10/n_timepoints (10 peaks expected)
    n_estimators: int = 200 # default for forest estimator
    max_samples: Union[int, str] = "auto" # default for forest estimator
    random_state: int = 1770118482 
    min_periods: Optional[int] = 1 # min. number of time points to include
    score_std_cutoff: Optional[float] = None # cutoff for included peaks/anomalies - n standard deviations from 4th quartile of initially detected anomalies. Default None (include all)


def aggregate_counts(df, date_col = "publication date", freq = "D", weighted=False, weight_col="actor_weight", start_year=2015, end_year=2025):
    """
    Aggregate counts based on time frequency. "D" - day for default.
    Options: "D" - day, "W" - week, "2W" - biweekly, "ME" - month, "2ME" - bimonthly, "QE" - quarter, "YE" - year
    """

    if date_col not in df.columns: # check if date col is in data
        raise ValueError(
            f"Expected columns '{date_col}' not in {list(df.columns)}"
    )

    series = df.copy() # copy df
    series[date_col] = pd.to_datetime(series[date_col], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD
    series = series.sort_values(date_col) # sort
    if weighted:
        series['normal_count'] = 1 # default normal count
        series["count"] = 1 / series[weight_col] # default count
    else:
        series["count"] = 1 # default count
    daily = series.groupby(date_col, as_index=True)["count"].sum() # count per day
    aggregated = daily.resample(freq).sum() # resample by specified frequency
    full_index = pd.date_range(
        start=pd.Timestamp(f"{start_year}-01-01"),
        end=f"{end_year}-12-31",
        freq=freq,
    )
    aggregated = aggregated.reindex(full_index, fill_value=0)

    if weighted:
        daily_normal = series.groupby(date_col, as_index=True)["normal_count"].sum() # count per day
        aggregated_normal = daily_normal.resample(freq).sum() # resample by specified frequency
        aggregated_normal = aggregated_normal.reindex(full_index, fill_value=0)

    new_ts = aggregated.reset_index().rename(columns={"index": date_col})
    
    # convert to expected data format
    ts_out = new_ts[[date_col, "count"]].copy()
    ts_out[date_col] = pd.to_datetime(ts_out[date_col])
    ts_out["count"] = pd.to_numeric(ts_out["count"], errors="coerce")
    if weighted:
        ts_out['normal_count'] = normal_counts

    return ts_out

def detect_anomalies_scipy(ts, date_col="publication date", prominence=0.005, distance=1):
    ts = ts.sort_values(date_col).set_index(date_col)

    if ts.empty:
        raise ValueError("No samples available for anomaly detection.")

    total_count = ts["count"].sum()
    if total_count > 0:
        share = ts["count"] / total_count
    else:
        share = pd.Series(0.0, index=ts.index, dtype=float)

    peak_idx, peak_props = find_peaks(
        share.to_numpy(),
        prominence=prominence,
        distance=distance,
    )

    result = ts.copy()
    result["share"] = share
    result["date"] = result.index
    result["is_anomaly"] = False

    if len(peak_idx) > 0:
        peak_dates = result.index[peak_idx]
        result.loc[peak_dates, "is_anomaly"] = True

    return result.reset_index()


def detect_anomalies(ts, date_col = "publication date", config: Optional[AnomalyConfig] = None):
    """Return a dataframe with anomaly scores and flags from Isolation Forest.

    If config.contamination is None, default to 10 / n_samples.
    """

    cfg = config or AnomalyConfig() # load config or use defaults
    
    min_periods = cfg.min_periods
    ts = ts.sort_values(date_col).set_index(date_col)
    rolling = ts["count"].rolling(window=cfg.window, min_periods=min_periods) # rolling counts

    # derive features - uses mean, std and day of year
    features = pd.DataFrame(index=ts.index)
    features["count"] = ts["count"]
    rolling_mean = rolling.mean()
    baseline = rolling_mean.shift(1) # baseline for only keeping peaks (not downward anomalies)
    features["rolling_mean"] = rolling_mean
    features["rolling_std"] = rolling.std().fillna(0)
    features["day_of_year"] = features.index.dayofyear
    features = features.bfill().ffill() # fill missing - forward and backward fill

    n_samples = len(features)
    if n_samples == 0:
        raise ValueError("No samples available for anomaly detection.")

    # set contamination - expected "peaks"
    contamination = cfg.contamination
    if contamination is None:
        contamination = min(0.5, 15 / n_samples)

    # model setup
    model = IsolationForest(
        contamination=contamination,
        n_estimators=cfg.n_estimators,
        max_samples=cfg.max_samples,
        random_state=cfg.random_state,
    )
    # fit model
    model.fit(features)

    # predict
    predictions = model.predict(features)
    decision = model.decision_function(features)

    # df with results
    result = ts.copy()
    result["anomaly_score"] = -decision
    result["baseline"] = baseline
    result["date"] = result.index
    
    # initial anomaly flags (filtered for downward anomalies and below threshold peaks)
    is_anomaly = predictions == -1

    # keep only upward anomalies (peaks).
    upward = result["count"] > result["baseline"]
    is_anomaly = is_anomaly & upward.fillna(False)

    # exclude anomalies with scores below the top quartile of initial anomalies.
    initial_scores = result.loc[is_anomaly, "anomaly_score"]
    if not initial_scores.empty:
        q3_score = initial_scores.quantile(0.75)
        std_score = initial_scores.std(ddof=0)
        if cfg.score_std_cutoff:
            score_floor = q3_score - cfg.score_std_cutoff * std_score
            is_anomaly = is_anomaly & (result["anomaly_score"] >= score_floor)

    result["is_anomaly"] = is_anomaly

    return result.reset_index()

# Function for filtering adjacent peaks
def filter_adjacent_peak_ranges(flagged: pd.DataFrame) -> pd.DataFrame:
    """Keep only flagged ranges that dominate any immediately adjacent flagged range."""

    if flagged.empty:
        return flagged.copy()

    filtered = flagged.sort_values("date").reset_index(drop=True).copy()
    filtered["from_date"] = pd.to_datetime(filtered["from_date"])
    filtered["to_date"] = pd.to_datetime(filtered["to_date"])

    keep_mask = pd.Series(True, index=filtered.index)

    for idx in filtered.index:
        current_weight = filtered.at[idx, "share_weight"]
        current_from = filtered.at[idx, "from_date"]
        current_to = filtered.at[idx, "to_date"]

        prev_adjacent = idx > 0 and filtered.at[idx - 1, "to_date"] == current_from - pd.Timedelta(days=1)
        next_adjacent = idx < len(filtered) - 1 and filtered.at[idx + 1, "from_date"] == current_to + pd.Timedelta(days=1)

        if prev_adjacent and current_weight <= filtered.at[idx - 1, "share_weight"]:
            keep_mask.at[idx] = False
            continue

        if next_adjacent and current_weight <= filtered.at[idx + 1, "share_weight"]:
            keep_mask.at[idx] = False
       
    # filtered df
    filtered_peaks_df = filtered.loc[keep_mask].reset_index(drop=True)

    # convert dates back to strings
    filtered_peaks_df['from_date'] = filtered_peaks_df['from_date'].dt.strftime("%Y-%m-%d")
    filtered_peaks_df['to_date'] = filtered_peaks_df['to_date'].dt.strftime("%Y-%m-%d")

    return filtered_peaks_df

# Main peak detection function
def _find_peaks(
    data_path, 
    output_dir_peaks,
    output_dir_vis,
    CONFIG_USE, 
    AGG_FREQ, 
    year_cutoff_start=2015,
    remove_flashback=True,
    year_cutoff_end=2026 # exclusive
    ):

    # Paths
    data_path = Path(data_path)
    outputdir_peaks = Path(output_dir_peaks)

    # Derive country and theme from data_path
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # read data
    with open(data_path, "r") as f:
        lines = f.read().splitlines()

    data_records = [json.loads(line) for line in lines]
    df = pd.DataFrame(data_records)

    # cut-off date
    if "publication date" not in df.columns: # check if date col is in data
        raise ValueError(
            f"Expected columns 'publication date' not in {list(df.columns)}"
    )
    df["publication date"] = pd.to_datetime(df["publication date"], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD

    cutoff_date_start = pd.Timestamp(year=year_cutoff_start, month=1, day=1)
    cutoff_date_end = pd.Timestamp(year=year_cutoff_end, month=1, day=1)

    df = df[(df["publication date"] >= cutoff_date_start) & (df["publication date"] < cutoff_date_end)].reset_index(drop=True)

    # iter over actors and detect peaks
    results_all_df = pd.DataFrame()

    for actor in df['actor'].unique():
        df_actor = df[df['actor'] == actor]

        # n texts
        n_texts = df_actor.shape[0]

        # aggregate by time frequency
        df_agg = aggregate_counts(df_actor, freq=AGG_FREQ, weighted=False)

        # detect peaks
        results = detect_anomalies(
            df_agg,
            config=CONFIG_USE,
        )

        #results = detect_anomalies_scipy(
        #    df_agg)

        # add start and end
        results['from_date'] = results['date'].dt.to_period("M").dt.start_time.dt.strftime("%Y-%m-%d")
        results['to_date'] = results['date'].dt.to_period("M").dt.end_time.dt.strftime("%Y-%m-%d")

        # filter peaks
        flagged = results[results["is_anomaly"]].reset_index(drop=True)
        #if not flagged.empty:
            #flagged = filter_adjacent_peak_ranges(flagged)
            
        # add actor again
        results['actor'] = actor
        results['total_texts'] = n_texts

        # update anomaly
        results['is_anomaly'] = False
        results.loc[results['date'].isin(flagged['date']), 'is_anomaly'] = True

        # append
        results_all_df = pd.concat([results_all_df, results])

    # count actor engagement and collapse to one row per date
    flagged_all_df = results_all_df[results_all_df['is_anomaly']]
    flagged_all_df["share_texts"] = flagged_all_df["count"] / flagged_all_df["total_texts"]
    flagged_all_df["share_weight"] = flagged_all_df["share_texts"] * (flagged_all_df["total_texts"]/(flagged_all_df["total_texts"]+10))


    date_counts = (
        results_all_df.groupby("date")["count"]
        .sum()
        .to_frame(name="n_texts_total")
        .reset_index()
    )
    actor_counts = (
        flagged_all_df.groupby("date")
        .size()
        .to_frame(name="actors_engaged")
        .reset_index()
    )
    flagged_dates_df = pd.merge(
        flagged_all_df,
        actor_counts,
        how="left",
        on="date",
    )
    flagged_dates_df = pd.merge(
        flagged_dates_df,
        date_counts,
        how="left",
        on="date",
    )
    flagged_dates_df = (
        flagged_dates_df.sort_values("date")
        .groupby("date", as_index=False)
        .agg(
            {
                "count": "sum",
                "share_weight": "sum",
                "n_texts_total": "first",
                "from_date": "first",
                "to_date": "first",
                "actor": list,
                "actors_engaged": "first",
            }
        )
    )

    # final candidates
    candidate_peaks = filter_adjacent_peak_ranges(flagged_dates_df) # filter adjacent months
    candidate_peaks = candidate_peaks[candidate_peaks["n_texts_total"] > 5] # filter low counts
    candidate_peaks = candidate_peaks.sort_values(["actors_engaged", "count"], ascending=False) # sort by actors_engaged, then count
    candidate_peaks = candidate_peaks.iloc[0:15].reset_index(drop=True) # keep top 15
    candidate_peaks = candidate_peaks.sort_values("date").reset_index(drop=True) # sort by date
    candidate_peaks['peak_id'] = candidate_peaks.index + 1 # assign peak id
    candidate_peaks = (
        candidate_peaks[['peak_id', 'date', 'from_date', 'to_date', 'count', 'n_texts_total', 'actors_engaged', 'actor']]
        .rename(columns = {'actor': 'actors'})
    )
    candidate_peaks['is_peak'] = True

    # write output table
    gen_output_table(candidate_peaks, country, theme, output_dir_vis)

    # add peak id to full df
    results_all_df = pd.merge(
        results_all_df, 
        candidate_peaks[['date', 'peak_id', 'is_peak']],
        how='left',
        on='date'
    ).rename(columns={'is_anomaly': 'is_actor_anomaly'})
    results_all_df['is_peak'] = results_all_df['is_peak'].fillna(False)

    # set output path
    output_path = outputdir_peaks / country / f"{theme}_peaks.json"

    # ensure directories
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # convert to expected format
    peaks_out = candidate_peaks.set_index("peak_id")[["from_date", "to_date"]].apply(list, axis=1)
        
    # store as json
    #flagged.to_json(output_path, orient="records", lines=True, index=False, date_format="iso")
    peaks_out.to_json(
        output_path,
        orient="index"
    )

    # print to console
    print(f"Detected the following candidate peaks for {country} - {theme}.")
    if not candidate_peaks.empty:
        print(
            candidate_peaks[["from_date", "count", "n_texts_total", "actors_engaged"]]
            .head(15)
            .to_string(index=False)
        )

    return results_all_df, candidate_peaks

# output table for peaks
def gen_output_table(candidate_peaks, country, theme, output_dir_vis):

    # peaks output table (for analysis input) 
    output_table_df = (
        candidate_peaks[['peak_id', 'from_date', 'to_date', 'count', 'n_texts_total', 'actors_engaged', 'actors']]
        .rename(columns={
            'count': 'n_texts_actors',
            'n_texts_total': 'n_texts_total', 
            'actors_engaged': 'n_actors_engaged',
            'actors': 'actors_names'
            })
    )
    output_table_df['actors_names'] = output_table_df['actors_names'].str.join(", ")
    output_table_df['include_in_visualization'] = None
    output_table_df['title_short'] = None
    output_table_df['status'] = 'open'
    output_table_df = output_table_df[['peak_id', 'from_date', 'to_date', 'n_actors_engaged', 'actors_names', 'n_texts_actors', 'n_texts_total', 'include_in_visualization', 'title_short', 'status']]
    
    # output_path
    outpath = Path(output_dir_vis) / country / "input_peaks-overview-annotation.xlsx"

    # ensure directories
    outpath.parent.mkdir(parents=True, exist_ok=True)

    # write modes
    write_mode = "a" if outpath.exists() else "w"
    sheet_replace_mode = "replace" if outpath.exists() else None

    # write initial data to excel
    with pd.ExcelWriter(outpath, engine="openpyxl", mode=write_mode, if_sheet_exists=sheet_replace_mode) as writer:
        output_table_df.to_excel(writer, sheet_name=theme, index=False)

    # load workbook back
    wb = load_workbook(outpath)
    ws = wb[theme]

    # map colnames to letters
    header_map = {cell.value: cell.column for cell in ws[1]}
    status_col = get_column_letter(header_map["status"])
    include_col = get_column_letter(header_map["include_in_visualization"])

    # add status validation
    status_validation = DataValidation(
        type="list",
        formula1='"annotated,considered,skipped,open"',
        allow_blank=False,
    )
    status_validation.error = "Choose one of: annotated, considered, skipped, open"
    status_validation.prompt = "Select a status value"
    ws.add_data_validation(status_validation)
    status_validation.add(f"{status_col}2:{status_col}30") # applies to first 30 rows

    # add include validation
    include_validation = DataValidation(
        type="list",
        formula1='"YES,NO"',
        allow_blank=False,
    )
    include_validation.error = 'Choose either "YES" or "NO"'
    include_validation.prompt = "Include in visualization?"
    ws.add_data_validation(include_validation)
    include_validation.add(f"{include_col}2:{include_col}30") # applies to first 30 rows

    # save
    wb.save(outpath)

# data frame for counts per source
def count_by_source(
    data_path, 
    REDUCED_DATA_DIR,
    AGG_FREQ, 
    year_cutoff_start=2015,
    normalize=True,
    remove_flashback=True,
    source_to_actor_map=None,
    year_cutoff_end=2026 # exclusive
    ):

    # Paths
    data_path = Path(data_path)
    
    # Derive country and theme from data_path
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # read data
    with open(data_path, "r") as f:
        lines = f.read().splitlines()

    data_records = [json.loads(line) for line in lines]
    df = pd.DataFrame(data_records)

    # cut-off date
    if "publication date" not in df.columns: # check if date col is in data
        raise ValueError(
            f"Expected columns 'publication date' not in {list(df.columns)}"
    )
    df["publication date"] = pd.to_datetime(df["publication date"], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD

    cutoff_date_start = pd.Timestamp(year=year_cutoff_start, month=1, day=1)
    cutoff_date_end = pd.Timestamp(year=year_cutoff_end, month=1, day=1)

    df = df[(df["publication date"] >= cutoff_date_start) & (df["publication date"] < cutoff_date_end)].reset_index(drop=True)

    # read reduced data (for weights and source)
    reduced_data_path = REDUCED_DATA_DIR / f"{country}_reduced.jl"
    
    try:
        with open(reduced_data_path, "r") as f:
            lines = f.read().splitlines()
    
        data_records = [json.loads(line) for line in lines]
        reduced_df = pd.DataFrame(data_records)

        # add sources
        sources_in_data = reduced_df.loc[df['text_ID'].tolist(), 'source'].reset_index(drop=True)
        df['source'] = sources_in_data

        # filter flashback
        if country == "SWE" and remove_flashback:
            df['source'] = df['source'].fillna('').astype(str)
            df = df[~df['source'].str.contains("flashback", case=False)].reset_index(drop=True)

        # add actor 
        if source_to_actor_map:
            if country == "SWE":
                country_lookup = "SE"
            else:
                country_lookup = country
            df['actor'] = df['source'].replace(source_to_actor_map.get(country_lookup))
        else:
            df['actor'] = df['source']

    except FileNotFoundError:
        warnings.warn(f"Reduced data file {reduced_data_path} not found! Vis of source-peaks skipped.")
        USE_WEIGHTS=False

    # Count by source
    df_sources_count = pd.DataFrame()

    for actor in df['actor'].unique().tolist():

        df_source = df[df['actor'] == actor]

        df_agg = aggregate_counts(df_source, freq=AGG_FREQ, weighted=False)
        df_agg['actor'] = actor

        if normalize:
            df_agg['count_normalized'] = df_agg['count'] / df_agg['count'].sum()

        df_sources_count = pd.concat([df_sources_count, df_agg], axis=0, ignore_index=True)

    # rename
    df_sources_count = df_sources_count.rename(columns={"publication date": "date"})

    return df_sources_count