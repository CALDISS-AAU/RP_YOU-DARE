"""Run anomaly detection on the simulated incidence data."""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import warnings

import numpy as np
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from modules.anomaly_detection import AnomalyConfig, aggregate_counts, detect_anomalies, fix_telegram_source

# SET SETTINGS FOR ANOMALY DETECTION HERE
CONFIG_USE=AnomalyConfig(
            window=1, # n "windows" to partition data into - default 1 - works well for this task as we are not looking at "local" relative peaks
            score_std_cutoff=None, # cutoff for included peaks/anomalies - n standard deviations from 4th quartile of initially detected anomalies. Default None (include all)
            # negative values: includes less than top quartile
            # positive values: includes more than top quartil
            # None: Includes all detected anomalies/peaks
            contamination=None # share of time points expected to be anomalies/peaks - None (default) uses share 10/n_timepoints (10 peaks expected)
        )

# SET AGGREGATION LEVEL HERE
# Options: "D" - day, "W" - week, "2W" - biweekly, "ME" - month, "2ME" - bimonthly, "QE" - quarter, "YE" - year
AGG_FREQ_USE = "ME"

# PATH TO REDUCED DATA (for weights)
REDUCED_DATA_DIR = Path("/work/YOU-DARE/sentence_filtering/reduced_data")

# main function
def main(CONFIG_USE=CONFIG_USE, AGG_FREQ=AGG_FREQ_USE):

    parser = argparse.ArgumentParser(description="Run anomaly detection.")
    parser.add_argument(
        "--data-path",
        help="Path to input JSONL with one row per instance.",
    )
    parser.add_argument(
        "--use-weights",
        action="store_true",
        help="Apply source weights to counts"
        )

    args = parser.parse_args()

    data_path = Path(args.data_path)
    USE_WEIGHTS = args.use_weights

    # Derive country and theme from data_path
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    if len(path_elems)>1:
        theme = path_elems[1]

    # read data
    with open(data_path, "r") as f:
        lines = f.read().splitlines()
    
    data_records = [json.loads(line) for line in lines]
    df = pd.DataFrame(data_records)

    # read reduced data (for weights)
    if USE_WEIGHTS:
        reduced_data_path = REDUCED_DATA_DIR / f"{country}_reduced.jl"

        try:
            with open(reduced_data_path, "r") as f:
                lines = f.read().splitlines()
        
            data_records = [json.loads(line) for line in lines]
            reduced_df = pd.DataFrame(data_records)

            ### TEMP FIX OF SOURCE
            reduced_df = fix_telegram_source(reduced_df)
            
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
            sources_in_data = reduced_df.loc[df['text_ID'].tolist(), 'source'].reset_index(drop=True)

            df['source'] = sources_in_data
            df_with_weight = pd.merge(df, source_weights_df, how='left', on='source')

        except FileNotFoundError:
            warnings.warn(f"Reduced data file {reduced_data_path} not found! Peak detection performed unweighted.")
            USE_WEIGHTS=False

    # aggregate by time frequency
    agg_freq = AGG_FREQ
    if USE_WEIGHTS:
        df_agg = aggregate_counts(df_with_weight, freq=agg_freq, weighted=True)
    else:
        df_agg = aggregate_counts(df, freq=agg_freq, weighted=False)

    # detect peaks
    results = detect_anomalies(
        df_agg,
        config=CONFIG_USE,
    )

    # filter peaks
    flagged = results[results["is_anomaly"]]

    # set output path
    if USE_WEIGHTS:
        output_path = Path("output") / f"{data_path.stem}_weighted_peaks.jsonl"
    else:
        output_path = Path("output") / f"{data_path.stem}_peaks.jsonl"

    # store as jsonl
    output_path.parent.mkdir(parents=True, exist_ok=True)
    flagged.to_json(output_path, orient="records", lines=True, index=False, date_format="iso")

    # print to console
    print(f"Detected {len(flagged)} anomalies.")
    if not flagged.empty:
        print(
            flagged[["date", "count", "anomaly_score"]]
            .head(10)
            .to_string(index=False)
        )

    # simple plot
    # TODO: Update or omit plotting functions (possibly doing that elsewhere)
    if USE_WEIGHTS:
        plot_path = Path("output") / f"{data_path.stem}_weighted_peaks_plot.png"
        html_path = Path("output") / f"{data_path.stem}_weighted_plotly_peaks.html"
    else:
        plot_path = Path("output") / f"{data_path.stem}_peaks_plot.png"
        html_path = Path("output") / f"{data_path.stem}_plotly_peaks.html"

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
    plt.title(f"Incidence Counts with Anomalies (freq={agg_freq})")
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

    fig = px.line(results, x="date", y="count", title=(f'Incidence Counts with Anomalies(freq={agg_freq})'))
    fig.update_traces(line= dict(color="#992F87"))
    if not flagged.empty:
        fig.add_scatter(
            x=flagged["date"],
            y=flagged["count"],
            mode="markers",
            name="Anomaly",
            marker=dict(color="#4C72B0", size=10)
        )
    fig.write_html(html_path)
    print(f"Saved html plot to {html_path} and chewed some bubblegum")
if __name__ == "__main__":
    main()