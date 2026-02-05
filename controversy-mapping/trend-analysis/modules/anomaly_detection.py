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
from sklearn.ensemble import IsolationForest


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


### TEMP FUNCTIONS
def use_telegram_source(url):
    name_re = re.compile(r'(?<=t.me/s/)\w+(?=/)')
    match = name_re.search(url)
    if match:
        name_use = match.group(0)
    else:
        name_use = ""
    return(name_use)

def fix_telegram_source(df):
    new_df = df.copy()
    new_df['link'] = new_df['link'].fillna('')
    
    filter_telegram_mask = new_df['link'].str.match(r'https://t.me')
    
    new_df.loc[filter_telegram_mask, 'source'] = new_df.loc[filter_telegram_mask, 'link'].apply(use_telegram_source)

    return new_df
###


def aggregate_counts(df, date_col = "publication date", freq = "D", weighted=False, weight_col="source_weight"):
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
        series["count"] = 1 / series[weight_col] # default count
    else:
        series["count"] = 1 # default count
    daily = series.groupby(date_col, as_index=True)["count"].sum() # count per day
    aggregated = daily.resample(freq).sum() # resample by specified frequency

    new_ts = aggregated.reset_index()
    
    # convert to expected data format
    ts_out = new_ts[[date_col, "count"]].copy()
    ts_out[date_col] = pd.to_datetime(ts_out[date_col])
    ts_out = ts_out.sort_values(date_col).set_index(date_col)
    ts_out["count"] = pd.to_numeric(ts_out["count"], errors="coerce")

    return ts_out


def detect_anomalies(ts, date_col = "publication date", config: Optional[AnomalyConfig] = None):
    """Return a dataframe with anomaly scores and flags from Isolation Forest.

    If config.contamination is None, default to 10 / n_samples.
    """

    cfg = config or AnomalyConfig() # load config or use defaults
    
    min_periods = cfg.min_periods
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
        contamination = min(0.5, 10 / n_samples)

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

# Main peak detection function
def find_peaks(
    data_path, 
    output_dir_peaks,
    REDUCED_DATA_DIR,
    CONFIG_USE, 
    AGG_FREQ, 
    USE_WEIGHTS,
    year_cutoff_start=2015,
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

    cutoff_date = pd.Timestamp(year=year_cutoff_start, month=1, day=1)

    df = df[df["publication date"] >= cutoff_date]

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
        
        if USE_WEIGHTS:

            # Calc weights
            source_counts = reduced_df.groupby('source').size()
            source_counts_logged = source_counts.apply(np.log)

            source_weights = source_counts_logged / source_counts_logged.sum()

            source_weights_df = pd.DataFrame(
                {
                    'source': source_weights.index,
                    'source_weight': source_weights.reset_index(drop=True)
                }
            )

            # Add weight
            df_with_weight = pd.merge(df, source_weights_df, how='left', on='source')

    except FileNotFoundError:
        warnings.warn(f"Reduced data file {reduced_data_path} not found! Peak detection performed unweighted, and vis of source-peaks skipped.")
        USE_WEIGHTS=False

    # aggregate by time frequency
    if USE_WEIGHTS:
        df_agg = aggregate_counts(df_with_weight, freq=AGG_FREQ, weighted=True)
    else:
        df_agg = aggregate_counts(df, freq=AGG_FREQ, weighted=False)

    # detect peaks
    results = detect_anomalies(
        df_agg,
        config=CONFIG_USE,
    )

    # filter peaks
    flagged = results[results["is_anomaly"]].reset_index(drop=True)
    flagged['peak_id'] = flagged.index + 1
    flagged['from_date'] = flagged['date'].dt.to_period("M").dt.start_time.dt.strftime("%Y-%m-%d")
    flagged['to_date'] = flagged['date'].dt.to_period("M").dt.end_time.dt.strftime("%Y-%m-%d")

    # set output path
    output_path = outputdir_peaks / country / f"{theme}_peaks.json"

    # ensure directories
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # convert to expected format
    peaks_out = flagged.set_index("peak_id")[["from_date", "to_date"]].apply(list, axis=1)
        
    # store as json
    #flagged.to_json(output_path, orient="records", lines=True, index=False, date_format="iso")
    peaks_out.to_json(
        output_path,
        orient="index"
    )

    # print to console
    print(f"Detected {len(flagged)} peaks for {country} - {theme}.")
    if not flagged.empty:
        print(
            flagged[["date", "count", "anomaly_score"]]
            .head(10)
            .to_string(index=False)
        )

    return results, flagged, USE_WEIGHTS

# simple plotting function
def simple_peak_plot(results, flagged, output_dir_vis, data_path, USE_WEIGHTS, AGG_FREQ):
    
    # Derive country and theme from data_path
    data_path = Path(data_path)
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # output dir for vis
    outputdir_vis = Path(output_dir_vis)

    # output path
    if USE_WEIGHTS:
        plot_path = outputdir_vis / country / f"{theme}_peaks_plot_weighted.png"
    else:
        plot_path = outputdir_vis / country / f"{theme}_peaks_plot.png"

    # ensure directories
    plot_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 5))
    plt.plot(results["date"], results["count"], color="steelblue", linewidth=1.5)
    if not flagged.empty:
        plt.scatter(
            flagged["date"],
            flagged["count"],
            color="crimson",
            s=35,
            zorder=3,
            label="Anomaly",
        )
    plt.title(f"Incidence Counts with Anomalies (freq={AGG_FREQ})")
    plt.xlabel("Date")
    if USE_WEIGHTS:
        plt.ylabel("Weighted count")
    else:
        plt.ylabel("Count")
    if not flagged.empty:
        plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    print(f"Saved plot to {plot_path}")