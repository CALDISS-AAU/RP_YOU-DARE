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

from modules.plotting_peaks import prepare_results_flagged, gen_streamgraph_peaks
from modules.peaks_table import create_peaks_table

# SET AGGREGATION LEVEL HERE
# Options: "D" - day, "W" - week, "2W" - biweekly, "ME" - month, "2ME" - bimonthly, "QE" - quarter, "YE" - year
AGG_FREQ_USE = "ME"

INDEXED_DATA_DIR = Path("/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data/")
FLAGGED_DIR = Path("/work/YOU-DARE/controversy-mapping/final_plots/input_data/D2.1 Timelines")
MAPS_OUT_DIR = Path("/work/YOU-DARE/controversy-mapping/final_plots/plots/peaks_deliverable")
#MAPS_OUT_DIR = Path("/work/YOU-DARE/controversy-mapping/final_plots/plots/peaks_test")

## Countries and themes
COUNTRIES = [
    "DK",
    "ES",
    "FR",
    "HU",
    "IT",
    "RO",
    "SE",
    "UK"
]

THEMES = [
    "lgb",
    "migration", 
    "woke"
]

KEYS = {f"{country}_{theme}" for country in COUNTRIES for theme in THEMES}


def generate(country, theme):
    """
    Generate peaks for deliverable.
    """

    key = f"{country}_{theme}"

    if key not in KEYS:
        raise ValueError(f"key {key} not a valid key. Expected one of: {', '.join(KEYS)}")

    # read data    
    indexed_data_path = INDEXED_DATA_DIR / country / f"{key}_indexed.jl"
    flagged_in_path = FLAGGED_DIR / country / "input_peaks-overview-annotation.xlsx"
    
    # output path
    plot_path_out = MAPS_OUT_DIR / f"{key}_peaks.png"

    # table dir
    peaks_table_dir = MAPS_OUT_DIR / "peaks_tables"
    peaks_table_dir.mkdir(parents=True, exist_ok=True)

    # prepare results and flagged
    results, flagged = prepare_results_flagged(
        data_path = indexed_data_path,
        flagged_path = flagged_in_path, 
        AGG_FREQ=AGG_FREQ_USE, 
        date_cutoff_start="2015-01-01",
        date_cutoff_end="2025-08-01"
        )
    #print(f"Results prepared for {country}-{theme}")

    # prepare table
    create_peaks_table(
        country, 
        flagged, 
        peaks_table_dir
        )

    #print(f"Table prepared for {country}-{theme}")

    # streamgraph
    gen_streamgraph_peaks(
        country,
        results, 
        flagged, 
        plot_path_out=plot_path_out,
        data_path=indexed_data_path, 
        AGG_FREQ=AGG_FREQ_USE
    )
    #print(f"Streamgraph prepared for {country}-{theme}")

# main function
def main():

    for country in COUNTRIES:
        for theme in THEMES:
            print(f"Generating for {country}-{theme}...")
            try:
                generate(country, theme)
                #print(f"Done")
            except Exception as e:
                print(f"Failed to generate for {country}-{theme}: \n {e}")

if __name__ == "__main__":
    main()
