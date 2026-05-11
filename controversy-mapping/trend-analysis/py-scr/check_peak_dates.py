from pathlib import Path
import os
from dotenv import load_dotenv

import pandas as pd
import json

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


peaks_used_dir = REPO_ROOT / "controversy-mapping" / "trend-analysis" / "output" / "version_for_annotation_march2026" / "peaks"

peaks_files = list(peaks_used_dir.rglob("*_peaks.json"))

dates_used_2025 = {}

for file in peaks_files:

    dates_2025 = []

    with open(file, 'r') as f:
        data = json.load(f)

    for k,v in data.items():
        last_date = v[1]

        if '2025' in v[1]:
            dates_2025.append(v[1])
    
    country = file.parts[-2]
    theme = file.parts[-1].split('_')[0]
    dates_used_2025[f"{country}-{theme}"] = dates_2025