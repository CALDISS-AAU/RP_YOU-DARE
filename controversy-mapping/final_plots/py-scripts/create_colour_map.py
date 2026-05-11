from pathlib import Path
import os
from dotenv import load_dotenv

import json

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

ENV_PATH = next(
    (
        parent / ".env"
        for parent in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
        if (parent / ".env").exists()
    ),
    None,
)
if ENV_PATH is None:
    raise FileNotFoundError("Could not locate .env")

load_dotenv(ENV_PATH)
REPO_ROOT = Path(os.environ.get("YOUDARE_REPO_ROOT", ".")).resolve()


mapping_p = REPO_ROOT / "raw-data" / "mappings" / "actor_mapping.json"
output_p = REPO_ROOT / "raw-data" / "mappings" / "actor_identifier_key" / "actor_colour_map" / "actor_value_colours.json"


def build_colour_mapping(mapping):
    colour_mapping = {}

    for top_level_key, nested_mapping in mapping.items():
        unique_values = list(dict.fromkeys(nested_mapping.values()))
        colors = plt.cm.tab20(np.linspace(0, 1, max(len(unique_values), 2)))[: len(unique_values)]

        colour_mapping[top_level_key] = {
            value: mcolors.to_hex(color) for value, color in zip(unique_values, colors)
        }

    return colour_mapping


with mapping_p.open() as f:
    mapping = json.load(f)

colour_mapping = build_colour_mapping(mapping)

with output_p.open("w") as f:
    json.dump(colour_mapping, f, indent=4, ensure_ascii=False)
