"""What this will do:
- Replaces __standardising_data, save_datasets_countries and telegram_prep functions/scripts
- Reads data directly from scrapers/data
- Determines platform and correct path to use from naming conventions - flags potential duplicates, missed datafiles
- Fixes telegram data using function in modules
- Standardizes data (like already done in standardising_data.py) - without intermediary data storage
    - one function per platform
- Adds platform variable/key
- Adds actor variable/key
- Writes to final_raw/{cntr}_YOUDARE-WEBDATA_combined.jsonl as a combined jsonl - streams one dataset at the time (also avoid including irrelevant keys from other platforms)
"""

'''
source ./YOU-DARE/environment/bin/activate
cd ./YOU-DARE/raw-data/data_combiner
python -m run_combiner --country "SE"
'''

# TODO: Perform standardization according to platform
    # Telegram - source from filepath (add path as input)
    # YouTube -> simple keys check NOTE: some rows without video_text - raises error? 
    # Websites -> re-use existing standardization features from standardising_data.py
        # - exclude date resolving
    

import argparse
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import json
from functools import partial

from modules.standardizers import telegram_to_threads, standardize_yt, standardize_web, standardize_flashback # NOTE: standardize_web and standardize_flashback are unfinished functions - returns None
from modules.pathresolver import determine_datafile_platform
from modules.readers import read_telegram, read_jsonl_chunks

COMBINED_OUT_DIR = "/work/YOU-DARE/raw-data/final_raw"
SCRAPER_DATA_DIR = "/work/YOU-DARE/scrapers/data"
SOURCE_ACTOR_MAPPING_P = "/work/YOU-DARE/raw-data/mappings/actor_mapping.json"
LOG_DIR = "/work/YOU-DARE/raw-data/data_combiner/logs"

# mapping country abv to scraping data subdir
COUNTRY_MAP = { # ISO 3166 alpha-2 pls
    "DK": "Denmark", 
    "FR": "France",
    "IT": "Italy",
    "HU": "Hungary", 
    "UK": "United_Kingdom",
    "SE": "Sweden",
    "RO": "Romania", 
    "ES": "Spain",
    "TEST": "__TEST_COUNTRY"
   }


# processor pipelines
PROCESSOR_PIPELINES = {
    "YouTube": {"reader": read_jsonl_chunks, "standardizer": standardize_yt},
    "Website": {"reader": read_jsonl_chunks, "standardizer": standardize_web}, # TODO must return list[dict[str, Any]] (jsonl)
    "Flashback": {"reader": read_jsonl_chunks, "standardizer": standardize_flashback}, # TODO must return list[dict[str, Any]] (jsonl)
    "Telegram": {"reader": read_telegram, "standardizer": telegram_to_threads},
}

# function for processing data subdir based on country abv input
def process_dir(country, replace_data = True, chunksize = 10000, included_filetypes = [".jl", ".csv"]):
    """
    Processes possible data paths in a scrapers data subdirectory.
    The proper processing function is determined via pathresolver, which returns the platform of the data.
    Based on platform, the appropriate reader and standardizer from PROCESSOR_PIPELINES is used.
    Sources other than Telegram are processed in chunks (read as generator) and streamed to outfile.
    Actor and platform variables are added.
    Logs processed paths, failed paths and skipped subdirs for tracking potentially overlooked data.
    
    Args:
        - Country: alpha-2 country code - determines proper subdir based on COUNTRY_MAP
        - replace_data: whether to append to existing combined data file or replace. Writes to COMBINED_OUT_DIR. (default:True)
        - included_filetypes: what file-endings to include as potential data paths (default: .jl, .csv)
    """

    # identify scrapers data subdir
    cntr_data_dir = COUNTRY_MAP.get(country)

    if cntr_data_dir is None:
        raise ValueError(f"No data dir found for country {country}. Expected one of {', '.join(list(COUNTRY_MAP.keys()))}")

    # read source-to-actor mapping
    with open(SOURCE_ACTOR_MAPPING_P, 'r') as f:
        source_actor_map=json.load(f)
    cntr_source_actor_map = source_actor_map.get(country)

    if cntr_source_actor_map is None:
        print(f"WARNING! No source-to-actor mapping found for country {country}! Check {SOURCE_ACTOR_MAPPING_P}.")

    # find potential data paths based on file endings
    country_dir = Path(SCRAPER_DATA_DIR) / cntr_data_dir
    potential_data_paths = [p for p in country_dir.rglob("*") if p.suffix.lower() in included_filetypes]

    # combined data file to write to
    datafile_out = f"{country}_YOUDARE-WEBDATA_combined.jsonl"
    datapath_out = Path(COMBINED_OUT_DIR) / datafile_out
    datapath_out.parent.mkdir(parents=True, exist_ok=True)

    # clear existing data file if replace_data==True
    if replace_data:
        datapath_out.write_text("", encoding="utf-8")

    # logfiles
    log_dir_out = Path(LOG_DIR) / country
    log_dir_out.mkdir(parents=True, exist_ok=True)

    paths_processed_p = log_dir_out / f"{country}_paths_processed.txt"
    failed_paths_p = log_dir_out / f"{country}_failed_paths.txt"
    skipped_subdirs_p = log_dir_out / f"{country}_skipped_subdirs.txt"

    ## reset logfiles
    paths_processed_p.write_text("", encoding="utf-8")
    failed_paths_p.write_text("", encoding="utf-8")
    skipped_subdirs_p.write_text("", encoding="utf-8")

    ## open for writing
    paths_processed_out = open(paths_processed_p, 'a', encoding='utf-8')
    failed_paths_out = open(failed_paths_p, 'a', encoding='utf-8')
    skipped_subdirs_out = open(skipped_subdirs_p, 'a', encoding='utf-8')

    # tracking stuff
    seen_telegram_paths = set()
    seen_dirs = {}
    actor_platform_abvs = {}

    # iter over potential data paths
    print(f"Processing {len(potential_data_paths)} potential data paths...")
    for p in tqdm(potential_data_paths, desc="Datapaths"):

        # use function from pathresolver - detmines platform based on filename and parent directories and keeps track of seen dirs and paths
        path_payload, platform = determine_datafile_platform(
            p,
            seen_paths=seen_telegram_paths,
            seen_dirs=seen_dirs,
        )

        if platform is None: # function returns None if path does not conform to expected pattern or if data is already added (assumption: one platform datafile per directory)
            continue

        # Telegram => payload is {"posts": Path, "replies": Path?}
        # Others   => payload is Path
        # Depending on platform, uses the appropriate processing function
            # if failed for any reason, appends path and error to file in log directory

        # retrieve processing pipeline (reader, standardizer) based on platform
        processing_pipeline = PROCESSOR_PIPELINES.get(platform)

        if processing_pipeline is None:
            raise ValueError(f"No parsing function for platform: {platform}.")

        # set chunksize if platform not telegram
        if platform == "Telegram":
            data_reader = processing_pipeline["reader"]
        else:
            data_reader = partial(processing_pipeline["reader"], chunksize = chunksize) # chunksize only option for none Telegram

        # failure state (turns True if exception if raised)
        processing_failed = False

        # iter over data chunks using reader (telegram uses full dfs)
        for chunk_id, data_chunk in enumerate(tqdm(data_reader(path_payload), desc=f"Chunks {p.stem}")):
            try:
                if platform == "Telegram":
                    standardised_data_chunk = processing_pipeline.get("standardizer")(data_chunk[0], data_chunk[1], path_payload) # 0=posts, 1=replies
                else:
                    standardised_data_chunk = processing_pipeline.get("standardizer")(data_chunk, path_payload)
            
            except Exception as e:
                print(f"WARNING: Processing failed for path {p} at chunk {chunk_id}. Tried to parse as {platform} data. Appended to {failed_paths_out}. Parsing failed with error: \n {e}")
                failed_out = f"{str(p)} - {chunk_id}: {str(e)}"
                
                failed_paths_out.write(failed_out + "\n")
                
                # flag that processing failed
                processing_failed = True
                standardised_data_chunk = None
                break
                

            # add final variables and stream to file
            if standardised_data_chunk is not None:
                # convert to df
                standardised_data_df = pd.DataFrame.from_records(standardised_data_chunk)
                
                # add actor
                if cntr_source_actor_map:
                    standardised_data_df['actor'] = standardised_data_df['source'].replace(cntr_source_actor_map)

                    actor = standardised_data_df['actor'].tolist()[0] # assumes one source per chunk; or same actor
                else:
                    actor = None

                # add platform
                standardised_data_df['platform'] = platform

                # rownumbers for ids
                ids = pd.Series(standardised_data_df.index + 1)
                
                # actor-platform abv for id
                if actor:
                    actor_alphanum = ''.join([c for c in actor if c.isalnum()]) # ensures alphanumeric characters
                    actor_abv = (actor_alphanum[0] + actor_alphanum[len(actor)//2] + actor_alphanum[-1]).upper()
                else:
                    actor_abv = "UNKNOWN"

                if platform:
                    platform_abv = platform[0].upper()
                else:
                    platform_abv = "UNKNOWN"
                
                name_for_id = f"{country}-{actor_abv}-{platform_abv}"
                
                # tracking last used row number
                if name_for_id in actor_platform_abvs:
                    ids_offset = actor_platform_abvs[name_for_id]
                    actor_platform_abvs[name_for_id] += ids.max()
                else:
                    ids_offset = 0
                    actor_platform_abvs[name_for_id] = ids.max()

                # add id
                standardised_data_df['entry_ID'] = ids.apply(lambda n: f"{name_for_id}-{str(ids_offset + n)}")
                ## place id first
                standardised_data_df = standardised_data_df[['entry_ID'] + [c for c in standardised_data_df.columns if c != 'entry_ID']]
                # stream to output file
                standardised_data_df.to_json(datapath_out, orient='records', lines=True, mode='a', force_ascii=False) # append mode, force ascii=False to ensure utf-8 - pandas also automatially converts to NaN/None to null

        
        # write to processed paths
        if not processing_failed:
            if platform == "Telegram":
                paths_out = '\n'.join(str(path_value.stem) for path_value in path_payload.values())
                paths_processed_out.write(paths_out + '\n')
            else:
                paths_processed_out.write(path_payload.stem + '\n')
                

    # check for skipped subdirs - potentially over-looked data files
    excluded_parent_suffixes = ("m4a_files", "transcribed", "memberlists")
    all_parents = {
        p.parent.resolve(strict=False)
        for p in potential_data_paths
        if not any(
            p.parent.name.lower().endswith(suffix)
            for suffix in excluded_parent_suffixes
        )
    }
    unseen_parents = sorted(str(parent) for parent in (all_parents - set(seen_dirs)))
    if unseen_parents:
        print(f"WARNING: no datafiles processed from the following parent directories:\n{'\n'.join(unseen_parents)}")
        skipped_subdirs_out.write('\n'.join(unseen_parents))

    # close log files
    paths_processed_out.close()
    skipped_subdirs_out.close()
    failed_paths_out.close()

# main function
def main():
    parser = argparse.ArgumentParser(description="Combine and standardize scraper data for a country.")
    parser.add_argument(
        "--country",
        required=True,
        choices=sorted(COUNTRY_MAP.keys()),
        help="ISO alpha-2 country code to process.",
    )
    args = parser.parse_args()
    process_dir(args.country)


if __name__ == "__main__":
    main()