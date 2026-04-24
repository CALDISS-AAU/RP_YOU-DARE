import pandas as pd
import os
from os.path import join
import json

# PATHS
project_dir = join("/work", "YOU-DARE", "controversy-mapping", "keyword-analysis")
data_raw_dir = join(project_dir, "data", "raw")
data_work_dir = join(project_dir, "data", "work")

# datafiles
data_files = os.listdir(data_raw_dir)

# FUNCTION FOR FLATTENING
def flatten_data(jsonl_path, save_data=True, out_dir=data_work_dir, filename_out=None):

    # read jsonl file as list
    with open(jsonl_path, 'r') as f:
        lines = [json.loads(line) for line in f.read().splitlines()]

    # convert to data frame
    df = pd.DataFrame.from_records(lines)

    # filter empty (not labelled) and select cols
    col_keep = ['id', 'text', 'source', 'matched keywords', 'publication date', 'entities']
    df = df.loc[df['entities'].apply(lambda x: len(x) > 0), col_keep].rename(columns = {'id': 'text_id'})

    # un-nest entities (one row per label)
    df = df.explode('entities').reset_index(drop=True)

    # normalize entities to columns
    df = pd.merge(df, pd.json_normalize(df['entities']), how='left', left_index=True, right_index=True).rename(columns={'id': 'label_id'}).drop(columns=['entities'])

    # extract annotated text span
    df['span'] = df.apply(lambda r: r['text'][r['start_offset']:r['end_offset']], axis=1)

    # save data
    if save_data:
        if filename_out:
            file_out = join(out_dir, filename_out) + ".csv"
        else:
            filename_out = os.path.basename(jsonl_path).replace(".jsonl", "") + "_flat" + ".csv"
            file_out = join(out_dir, filename_out)

        if not file_out.endswith(".csv"):
            raise ValueError(f"Expects filename out to be .csv. Current filename ends with {file_out.split(".")[1]}")
        
        df.to_csv(file_out, index=False)

# CONVERT FILES
for file in data_files:

    file_path = join(data_raw_dir, file)

    flatten_data(file_path)
