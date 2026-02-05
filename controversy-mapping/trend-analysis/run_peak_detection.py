"""Run anomaly detection on trend data."""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import warnings

import numpy as np
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from modules.anomaly_detection import AnomalyConfig, find_peaks, simple_peak_plot

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

# function for processing
def process_data():
    # TODO: function for processing single dataset (path input) - possibly move to modules
    return

# main function
def main(CONFIG_USE=CONFIG_USE, AGG_FREQ=AGG_FREQ_USE, REDUCED_DATA_DIR=REDUCED_DATA_DIR):

    # TODO: Add function for visualize actors individually

    parser = argparse.ArgumentParser(description="Run anomaly detection.")
    datainput_group = parser.add_mutually_exclusive_group(required=False)
    datainput_group.add_argument(
        "--data-path",
        help="Path to input JSONL with one row per instance.",
    )
    datainput_group.add_argument(
        "--data-dir", 
        default="/work/YOU-DARE/sentence_filtering/indexed_data",
        help="Path to input directory with JSONL files."
    )
    parser.add_argument(
        "--use-weights",
        action="store_true",
        help="Apply source weights to counts"
        )
    parser.add_argument(
        "--output-dir-peaks",
        default="/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks",
        help="Directory for storing jsonlines with peaks"
    )
    parser.add_argument(
        "--output-dir-vis",
        default="/work/YOU-DARE/controversy-mapping/trend-analysis/output/packages_for_researchers",
        help="Directory for visualization (data packages for researchers)"
    )

    args = parser.parse_args()

    
    USE_WEIGHTS = args.use_weights

    if args.data_path:
        # use path

        # find peaks
        results, flagged, USE_WEIGHTS = find_peaks(
            data_path=args.data_path, 
            output_dir_peaks=args.output_dir_peaks,
            year_cutoff_start=2015,
            REDUCED_DATA_DIR=REDUCED_DATA_DIR,
            CONFIG_USE=CONFIG_USE, 
            AGG_FREQ=AGG_FREQ_USE, 
            USE_WEIGHTS=USE_WEIGHTS
            )
        
        # simple plot
        simple_peak_plot(
            results=results,
            flagged=flagged,
            output_dir_vis=args.output_dir_vis,
            data_path=args.data_path,
            AGG_FREQ=AGG_FREQ,
            USE_WEIGHTS=USE_WEIGHTS
        )

        
    elif args.data_dir:
        # use dir
        expected_file_pattern = re.compile(r'\w{2,3}_\w+_indexed\.jl', re.IGNORECASE)

        root_data_dir = Path(args.data_dir)

        # data files in dir
        jl_files = list(root_data_dir.rglob("*.jl"))

        # eligible data files
        data_paths = [p for p in jl_files if expected_file_pattern.search(str(p.stem)+".jl")]

        # print non-eligible
        non_eligible = [str(p) for p in jl_files if p not in data_paths]
        non_eligible_string = '\n'.join(non_eligible)
        if len(non_eligible) > 0:
            print(f"The following data files do not match pattern {{ctr}}_{{theme}}_indexed.jl:\n {non_eligible_string}")

        # run peak detection on files
        for data_path in data_paths:
            # find peaks
            results, flagged, USE_WEIGHTS = find_peaks(
                data_path=data_path, 
                output_dir_peaks=args.output_dir_peaks,
                year_cutoff_start=2015,
                REDUCED_DATA_DIR=REDUCED_DATA_DIR,
                CONFIG_USE=CONFIG_USE, 
                AGG_FREQ=AGG_FREQ_USE, 
                USE_WEIGHTS=USE_WEIGHTS
                )
            
            # simple plot
            simple_peak_plot(
                results=results,
                flagged=flagged,
                output_dir_vis=args.output_dir_vis,
                data_path=data_path,
                AGG_FREQ=AGG_FREQ,
                USE_WEIGHTS=USE_WEIGHTS
            )

    
    # plotly stuff
    # TODO: @MKAP: Har ikke pillet ved selve plotly delen. Lige nu virker den kun, hvis man kører funktionen på enkeltfil, så der skal gøres et eller andet, så det kan gøre i samme loop som resten
    if args.data_path:
        outputdir_vis = Path(args.output_dir_vis)

        # Derive country and theme from data_path
        data_path = Path(args.data_path)
        path_elems = data_path.stem.split('_')
        country = path_elems[0]
        try:
            theme = path_elems[1]
        except IndexError:
            raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")


        if USE_WEIGHTS:
            html_path = outputdir_vis / country / f"{theme}_peaks_plot_weighted.html"
        else:
            html_path = outputdir_vis / country / f"{theme}_peaks_plot.html"

        # ensure directories
        html_path.parent.mkdir(parents=True, exist_ok=True)

        fig = px.line(results, x="date", y="count", title=(f'<b>Incidence Counts with Anomalies(freq={AGG_FREQ})<b>'))
        fig.update_traces(
        line=dict(color="#4C72B0"),
        selector=dict(mode="lines")
        )
        if not flagged.empty:
            fig.add_scatter(
                x=flagged["date"],
                y=flagged["count"],
                mode="markers",
                name="Anomaly",
                marker=dict(color="#992F87", size=10)
            )

            fig.update_layout(
                plot_bgcolor="#F5F7FA",
                paper_bgcolor="#F5F7FA",
                )
        fig.write_html(html_path)
        print(f"Saved html plot to {html_path}")

# run main
if __name__ == "__main__":
    main()