"""
Generating final maps for deliverable.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import warnings
import pprint
import json
import pandas as pd
import numpy as np

from modules.plotting import gen_semantic_map

## DATA DIRS
UMAP_IN_DIR = Path("/work/YOU-DARE/controversy-mapping/final_plots/input_data/used_positions_mar20/umap_positions") # Path to dir with chunk and actor UMAP coordinates
REGIONS_IN_DIR = Path("/work/YOU-DARE/controversy-mapping/final_plots/input_data/D2.1 Socio-symbolic maps") # Path to dir with regions to annotate
MAPS_OUT_DIR = Path("/work/YOU-DARE/controversy-mapping/final_plots/plots/socio-semantic-maps_deliverable")
#MAPS_OUT_DIR = Path("/work/YOU-DARE/controversy-mapping/final_plots/plots/socio-semantic-maps_test")
UMAP_CHUNKS_KEEP = Path("/work/YOU-DARE/controversy-mapping/final_plots/input_data/umap_chunks_keep/umap_chunks_keep.csv")

## Countries and themes
COUNTRIES = {
    "DK",
    "ES",
    "FR",
    "HU",
    "IT",
    "RO",
    "SE",
    "UK"
}

THEMES = {
    "lgb",
    "migration", 
    "woke"
}

KEYS = {f"{country}_{theme}" for country in COUNTRIES for theme in THEMES}


def generate(country, theme):
    """
    Generate semantic mapping for deliverable.
    """

    key = f"{country}_{theme}"

    if key not in KEYS:
        raise ValueError(f"key {key} not a valid key. Expected one of: {', '.join(KEYS)}")

    # read data    
    chunks_umap_path = UMAP_IN_DIR / country / f"{theme}_umap-coords.csv"
    actor_umap_path = UMAP_IN_DIR / country / f"{theme}_umap-actors-coords.csv"
    regions_annotate_path = REGIONS_IN_DIR / country / "input_semantic-map-annotation.xlsx"

    chunks_umap_df = pd.read_csv(chunks_umap_path)
    chunks_keep_df = pd.read_csv(UMAP_CHUNKS_KEEP)
    actor_umap_df = pd.read_csv(actor_umap_path)
    regions_annotate_df = pd.read_excel(regions_annotate_path, sheet_name=theme).dropna(subset=['x_lim_lower', 'x_lim_upper', 'y_lim_lower', 'y_lim_upper'])

    # filter to only include chunks in range 2015-01-01 - 2025-07-31 (see py-scripts/umap_filter.py)
    chunks_keep_use = chunks_keep_df[
        (chunks_keep_df["country"] == country) & (chunks_keep_df["theme"] == theme)
    ]["chunk_id"].tolist()
    chunks_umap_df = chunks_umap_df[chunks_umap_df["chunk_id"].isin(chunks_keep_use)]

    # convert regions to list of dicts
    regions_annotate = regions_annotate_df.to_dict(orient="records")

    # output path
    plot_path_out = MAPS_OUT_DIR / f"{key}_socio-semantic_map.png"

    # generate map
    gen_semantic_map(
        chunks_umap_df,
        actor_umap_df,
        regions_annotate,
        country=country,
        theme=theme,
        output_path=plot_path_out,
        resize_factor=2
        )

# main function
def main():

    for country in COUNTRIES:
        for theme in THEMES:
            try:
                generate(country, theme)
            except Exception as e:
                raise Exception(f"Failed to generate for {country}-{theme}: \n {e}")

if __name__ == "__main__":
    main()
