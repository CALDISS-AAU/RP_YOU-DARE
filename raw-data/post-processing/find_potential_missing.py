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


# find paths
combined_data_dir = REPO_ROOT / "raw-data"
data_files_paths = list(combined_data_dir.rglob("*.jl"))

# text columns to coalesce
text_columns = [
        'video_text',
        'article_text',
        'Message_text',
        'thread_text',
    ]

# function for finding short strings
def find_potential_missing(df, text_columns=text_columns, upper_str_len=13):
    
    relevant_text_cols = [col for col in text_columns if col in df.columns]

    if not relevant_text_cols:
        return []

    text_df = df[relevant_text_cols].fillna("")
    text_series = text_df[relevant_text_cols[0]].astype(str)
    for col in relevant_text_cols[1:]:
        text_series = text_series.str.cat(text_df[col].astype(str), sep="")

    potential_missing = text_series[text_series.str.len().between(1, upper_str_len)].unique().tolist()

    return(potential_missing)
    

# list of all candidates
potential_missing_all = []
chunk_size = 5000

# iter over filepaths
for file_p in data_files_paths:
    for chunk_df in pd.read_json(file_p, lines=True, chunksize=chunk_size):
        potential_missing_all.extend(find_potential_missing(chunk_df))


# find candidates - count > 1
candidate_counts = pd.Series(potential_missing_all).value_counts()
candidates = candidate_counts[candidate_counts > 1].index.tolist()

# printout resultse
if len(candidates) > 0:
    string_out = f"The following strings could be missing values: \n {'\n'.join(candidates)}"
    
else:
    string_out = "No candidate missing values found!"
    
print(string_out)

path_out = str(REPO_ROOT / "raw-data" / "post-processing" / "candidate-missing.txt")

with open(path_out, 'w') as f:
    f.write(string_out)
