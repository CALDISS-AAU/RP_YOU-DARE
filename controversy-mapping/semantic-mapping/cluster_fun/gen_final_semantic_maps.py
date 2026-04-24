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
UMAP_IN_DIR = Path("/work/YOU-DARE/controversy-mapping/semantic-mapping/output/umap_positions") # Path to dir with chunk and actor UMAP coordinates
REGIONS_IN_DIR = Path("/work/YOU-DARE/controversy-mapping/semantic-mapping/plots/semantic-maps_analyze") # Path to dir with regions to annotate
MAPS_OUT_DIR = Path("/work/YOU-DARE/controversy-mapping/semantic-mapping/plots/semantic-maps_deliverable") # Path to dir for output

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
    actor_umap_df = pd.read_csv(actor_umap_path)
    regions_annotate_df = pd.read_excel(regions_annotate_path, sheet_name=theme)

    # convert regions to list of dicts
    regions_annotate = regions_annotate_df.to_dict(orient="records")

    # output path
    plot_path_out = MAPS_OUT_DIR / country / f"{key}_semantic_map.png"

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
            generate(country, theme)

if __name__ == "__main__":
    main()