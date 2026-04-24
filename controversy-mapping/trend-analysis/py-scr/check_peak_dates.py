import pandas as pd
from pathlib import Path
import json

peaks_used_dir = Path("/work/YOU-DARE/controversy-mapping/trend-analysis/output/version_for_annotation_march2026/peaks")

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