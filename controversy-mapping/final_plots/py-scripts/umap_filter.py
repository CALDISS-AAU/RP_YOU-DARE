from pathlib import Path
import os
from dotenv import load_dotenv


import pandas as pd


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


UMAP_DIR = REPO_ROOT / "controversy-mapping" / "semantic-mapping" / "output" / "embeddings"
DATE_FROM = pd.Timestamp("2015-01-01")
DATE_TO = pd.Timestamp("2025-07-31")
PATH_OUT = REPO_ROOT / "controversy-mapping" / "final_plots" / "input_data" / "umap_chunks_keep" / "umap_chunks_keep.csv"

def build_umap_filter_df():
    combined_df = pd.DataFrame(columns=["country", "theme", "chunk_id"])

    for parquet_path in UMAP_DIR.glob("*.parquet"):
        parts = parquet_path.stem.split("_")
        country = parts[0]
        theme = parts[1]

        df = pd.read_parquet(parquet_path)
        df["publication date"] = pd.to_datetime(df["publication date"])
        df = df[
            (df["publication date"] >= DATE_FROM)
            & (df["publication date"] <= DATE_TO)
        ].copy()
        df["country"] = country
        df["theme"] = theme
        df = df[["country", "theme", "chunk_id"]]

        combined_df = pd.concat([combined_df, df], ignore_index=True)

    return combined_df


combined_df = build_umap_filter_df()

# write to csv
PATH_OUT.parent.mkdir(parents=True, exist_ok=True)
combined_df.to_csv(PATH_OUT, index=False)