"""
Detection of peaks/thematic salience using isolation forest anomaly detection. 
Code adjusted from Codes (OpenAI) output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import re
import pandas as pd
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

    return(new_df)
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