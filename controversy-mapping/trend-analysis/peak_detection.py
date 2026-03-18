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

from modules.anomaly_detection import AnomalyConfig, find_peaks
from modules.plotters import gen_streamgraph_peaks

# SET SETTINGS FOR ANOMALY DETECTION HERE
CONFIG_USE=AnomalyConfig(
            window=10, # n "windows" to partition data into - default 1 - works well for this task as we are not looking at "local" relative peaks
            score_std_cutoff=None, # cutoff for included peaks/anomalies - n standard deviations from 4th quartile of initially detected anomalies. Default None (include all)
            # negative values: includes less than top quartile
            # positive values: includes more than top quartil
            # None: Includes all detected anomalies/peaks
            contamination=0.5 # share of time points expected to be anomalies/peaks - None (default) uses share 15/n_timepoints (15 peaks expected)
        )

# SET AGGREGATION LEVEL HERE
# Options: "D" - day, "W" - week, "2W" - biweekly, "ME" - month, "2ME" - bimonthly, "QE" - quarter, "YE" - year
AGG_FREQ_USE = "ME"

# main function
def main(CONFIG_USE=CONFIG_USE, AGG_FREQ=AGG_FREQ_USE):

    parser = argparse.ArgumentParser(description="Run peak detection.")
    datainput_group = parser.add_mutually_exclusive_group(required=False)
    datainput_group.add_argument(
        "--data-path",
        help="Path to input JSONL with one row per instance.",
    )
    datainput_group.add_argument(
        "--data-dir", 
        default="/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data",
        help="Path to input directory with JSONL files."
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

    # use path
    if args.data_path: 

        # find peaks
        results, flagged = find_peaks(
            data_path=args.data_path, 
            output_dir_peaks=args.output_dir_peaks,
            output_dir_vis=args.output_dir_vis,
            year_cutoff_start=2015,
            CONFIG_USE=CONFIG_USE, 
            AGG_FREQ=AGG_FREQ, 
            )
        
        # streamgraph peaks plot
        gen_streamgraph_peaks(
            results=results, 
            flagged=flagged, 
            output_dir_vis=args.output_dir_vis,
            data_path=args.data_path, 
            AGG_FREQ=AGG_FREQ_USE
        )

    # use dir
    elif args.data_dir:
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
            results, flagged = find_peaks(
            data_path=data_path, 
            output_dir_peaks=args.output_dir_peaks,
            output_dir_vis=args.output_dir_vis,
            year_cutoff_start=2015,
            CONFIG_USE=CONFIG_USE, 
            AGG_FREQ=AGG_FREQ, 
            )
            
            # streamgraph peaks plot
            gen_streamgraph_peaks(
                results=results, 
                flagged=flagged, 
                output_dir_vis=args.output_dir_vis,
                data_path=data_path, 
                AGG_FREQ=AGG_FREQ_USE
            )
                

# run main
if __name__ == "__main__":
    main()