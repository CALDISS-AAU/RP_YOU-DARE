import json
from pathlib import Path
import pandas as pd

all_countries = [
    "DK",
    "ES",
    "FR",
    "HU",
    "IT",
    "RO",
    "SE",
    "UK",
]

all_themes = [
    "lgb",
    "migration",
    "woke",
]

input_dir = Path("/work/YOU-DARE/controversy-mapping/sentence_filtering/keyword_related_data/matched_words_xlsx_RETURNED")
output_dir = Path("/work/YOU-DARE/controversy-mapping/sentence_filtering/keyword_related_data/false_positives_lists")

output_dir.mkdir(parents=True, exist_ok=True)


for country in all_countries:
    excel_path = input_dir / f"{country}_matched_words.xlsx"

    false_positive_dict = {}

    for theme in all_themes:
        df = pd.read_excel(
            excel_path,
            sheet_name=theme,
        )

        false_words = (
            df.loc[df["False positive"].notna(), "Words"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s != ""]
            .unique()
            .tolist()
        )

        print(f"{country} | {theme}: {len(false_words)} false positives")
        
        false_positive_dict[theme] = sorted(false_words, key=str.lower)

    output_path = output_dir / f"{country}_false_positives_lists.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(false_positive_dict, f, ensure_ascii=False, indent=2)

    print(f"Saved {output_path}")