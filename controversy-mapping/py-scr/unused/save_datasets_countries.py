# Packages
import os
import sys 
import numpy as np
import pandas as pd
import json
import dateparser
import json
from pathlib import Path
import time
import glob

# Loading dataset lists
FRANCE_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/France/*.j*',
    recursive = True
)

HUNGARY_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/Hungary/*.j*',
    recursive=True
    )

ITALY_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/Italy/*.jl',
    recursive=True
    )

DENMARK_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/Denmark/*.jl',
    recursive=True
)

UK_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/United_Kingdom/*.jl',
    recursive=True
)

SWEDEN_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/Sweden/*.jl',
    recursive=True
)

ROMANIA_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/Romania/*.jl',
    recursive=True
)

SPAIN_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/__standardised_data/Spain/*.jl',
    recursive=True
)


# def load_data_raw(dataset_list):
#     """
#     Takes a list of dataset file paths (returned by doccano functions)
#     and concatenates them into a single DataFrame.

#     Parameters:
#     dataset_list: list of file paths

#     Returns:
#     web_df, tg_df, yt_df, manual_df
#     """
#     tg_frames = []
#     yt_frames = []
#     web_frames = []
#     manual_frames = []
    
#     for filename in dataset_list:
#         fname = filename.lower()

#         try:
#             chunks = pd.read_json(
#                 filename,
#                 lines=True,
#                 encoding='utf-8',
#                 chunksize=10_000
#             )
#             print(f"streaming {filename}")
#         except ValueError as e:
#             print(f"⚠️ Skipping file {filename}: {e}")
#             continue

#         # FIGURE OUT THE NAMES BITCH
#         if "telegram" in fname:
#             target = tg_frames
#         elif "spider" in fname:
#             target = web_frames
#         elif "yt" in fname:
#             target = yt_frames
#         else:
#             target = manual_frames


#         # Append chunks to df
#         for chunk in chunks:
#             target.append(chunk)

#     # Combine the results
#     web_df = pd.concat(web_frames, ignore_index=True).insert(4, 'platform', 'web') if web_frames else pd.DataFrame()
#     tg_df = pd.concat(tg_frames, ignore_index=True).insert(4, 'platform', 'telegram') if tg_frames else pd.DataFrame()
#     yt_df = pd.concat(yt_frames, ignore_index=True).insert(4, 'platform', 'youtube') if yt_frames else pd.DataFrame()
#     manual_df = pd.concat(manual_frames, ignore_index=True).insert(4, 'platform', 'manual') if manual_frames else pd.DataFrame()

    
#     print(f"\nWeb Dataframe: {web_df.shape}")
#     print(f"\nTELEGRAM Dataframe: {tg_df.shape}")
#     print(f"\nYOUTUBE Dataframe: {yt_df.shape}")
#     print(f"\nMANUAL Dataframe: {manual_df.shape}")

#     web_df = web_df.astype(str)
#     tg_df = tg_df.astype(str)
#     yt_df = yt_df.astype(str)
#     manual_df = manual_df.astype(str)

#     return web_df, tg_df, yt_df, manual_df

def load_data_raw_jsonlines(dataset_list, output_file_name):
    """
    Takes a list of dataset file paths (returned by doccano functions)
    adds a platform key extracted from name conventions
    merges and writes to a full jsonlines object in output_path

    Parameters:
    dataset_list: list of file paths
    output_path: a path to desired output folder

    
    """
    out_dir = Path("/work/YOU-DARE/raw-data")
    out_dir.mkdir(exist_ok=True)
    full_output_path = out_dir / output_file_name

    # Open out file
    with open(full_output_path, "w", encoding='utf-8') as outfile:

        for filename in dataset_list:
            fname = filename.lower()
        
        # Determine platform name
            if "telegram" in fname: platform = 'telegram'
            elif "spider" in fname: platform = 'website'
            elif "yt" in fname: platform = 'youtube'
            else: platform = 'manual'

            with open(filename, 'r', encoding='utf-8') as infile:
                    for line in infile:
                        if line.strip():
                            # Load
                            record = json.loads(line)
                            # Add platform
                            record['platform'] = platform
                            # Write to outfile
                            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")


# def append_jsonl_raw(in_path, out_path, key='web'):
#     with open(in_path, "r", encoding="utf-8") as fin, \
#          open(out_path, "a", encoding="utf-8") as fout:
#         for line in fin:
#             in_path['platform'] = 'web'
#             fout.append(line)

## IT ##
load_data_raw_jsonlines(ITALY_dir, 'IT_data_combined.jl')
# load_data_raw_jsonlines(list_of_ITALY_dataset_paths, 'IT_data_combined.jl')

## HU ##
start = time.perf_counter()
load_data_raw_jsonlines(HUNGARY_dir, 'HU_data_combined.jl')
end = time.perf_counter()
print(f"Elapsed time: {end - start:.2f} seconds")

## FR ##
# perform magic
start = time.perf_counter()
load_data_raw_jsonlines(FRANCE_dir, 'FR_data_combined.jl')
end = time.perf_counter()
print(f"Elapsed time: {end - start:.2f} seconds")
## SWE ##
load_data_raw_jsonlines(SWEDEN_dir, 'SWE_data_combined.jl')

## ES ##
load_data_raw_jsonlines(SPAIN_dir, 'ES_data_combined.jl')


## RO ##
load_data_raw_jsonlines(ROMANIA_dir, 'RO_data_combined.jl')

# DK #
load_data_raw_jsonlines(DENMARK_dir, 'DK_data_combined.jl')

## UK ##
load_data_raw_jsonlines(UK_dir, 'UK_data_combined.jl')
# uk_web, uk_tg, uk_yt, uk_manual = load_data_raw(list_of_UK_dataset_paths)
# modernity_web, modernity_tg, modernity_yt, modernity_manual = load_data_raw(modernity_list)

# dump_and_save(
#     uk_web,
#     uk_tg,
#     uk_yt,
#     uk_manual,
#     'UK_data.json'
# )
# uk_combined_path = '/work/YOU-DARE/raw-data/UK_data_combined.jl'
# append_jsonl_raw(
#     in_path=modernity,
#     out_path=uk_combined_path
# )