import pandas as pd
import json
import pathlib
from datetime import datetime
import os
import re

def get_all_dataset_paths(data_directory):
    ''' Collects paths of all datasets ending with '*_YT' or '*_TELEGRAM' and returns these as a list.
        Takes a parent folder path as input 
        Returns list of all datasets within the input path
    '''
    list_of_all_datasets = []
    list_of_datasets_YT = list(pathlib.Path(data_directory).rglob('*_YT.jl'))
    list_of_datasets_TELEGRAM = list(pathlib.Path(data_directory).rglob('*_TELEGRAM.jl'))
    list_of_all_datasets = list_of_datasets_YT + list_of_datasets_TELEGRAM
    list_of_all_datasets = list(map(str, list_of_all_datasets))
    return list_of_all_datasets

def generate_folder_structure(output_folder, actor, date):
    ''' Generates folder structure within a given output folder based on actor and publication date
        Inputs:
            output_folder where the folder structure should be generated
            actor of jsonline
            date of publication for jsonline
        Returns full path in which jsonline belongs
    '''
    if pd.isna(date):
        output_folder_dir = f'{output_folder}/{actor}/no_date'
        if not os.path.exists(output_folder_dir):
            os.makedirs(output_folder_dir)
            print(f"Created directory: {output_folder_dir}")
        else:
            print(f"Directory {output_folder_dir} already exists")
        print('No publication date')
    else:
        year = date.year
        month_str = date.strftime('%B')

        output_folder_dir = f'{output_folder}/{actor}/{year}/{month_str}'
        if not os.path.exists(output_folder_dir):
            os.makedirs(output_folder_dir)
            print(f"Created directory: {output_folder_dir}")
        else:
            print(f"Directory {output_folder_dir} already exists")
    return output_folder_dir

def safe_name(s):
    s = str(s) if s is not None else "no_title"
    s = s.strip()
    s = s.replace("/", "_").replace("\\", "_")  # kill path separators
    s = re.sub(r'[<>:"|?*\n\r\t]', "_", s)      # other nasty chars
    return s or "no_title"

input_folder = '/work/YOU-DARE/scrapers/data/Spain' # Parent folder with all datasets for Spain
input_paths = get_all_dataset_paths(input_folder) # Generates list of all datasets within the spain-data folder
output_folder_clean = '/work/YOU-DARE/various_tasks/Spain_datadump/data_clean' # The final output-folder for the clean data
output_folder_meta = '/work/YOU-DARE/various_tasks/Spain_datadump/data_meta' # The final output-folder for the meta data / full jsonline

for file_path in input_paths:
    # Reads the dataset
    try:
        with open(file_path, 'r', encoding='utf-8') as input_file:
            data = [json.loads(line) for line in input_file]

    except Exception as e:
        print(f'Failed to load data from {file_path}. Error: {e}')
        continue

    # Extract relevant fields of information from dataset for folder generation and "clean" data
    for line in data:
        if file_path.endswith('_YT.jl'):
            datestring = line['publication_date']
            actor = line['source']
            link = line['video_link']
            title = line['video_title']
            text = line.get('video_text', "")
        elif file_path.endswith('post_TELEGRAM.jl'):
            datestring = line['Timestamp']
            actor = line['Display_name']
            link = line['URL']
            title = f'ID{line['Message ID']}'
            text = line['Message_text']
        elif file_path.endswith('archive_TELEGRAM.jl'):
            datestring = line['Timestamp']
            actor = line['source']
            link = line['URL']
            title = f'ID{link.split('/')[-1]}' # Extract the message ID from the URL
            text = line['Thread_text']
        else:
            continue
        
        date = pd.to_datetime(
            datestring,
            errors='coerce'
        )

        date_str = "no_date" if pd.isna(date) else date.strftime("%Y-%m-%d")
        
        title = safe_name(title)
        actor = safe_name(actor)

        # Generates folder structure based on the actor and date for each jsonline
        clean_data_dir = generate_folder_structure(output_folder_clean, actor, date)
        meta_data_dir = generate_folder_structure(output_folder_meta, actor, date)

        # Combines extracted columns to "clean" data
        clean_data = f'Actor: {actor}\nPublication date: {date_str}\nLink: {link}\nTitle/ID: {title}\nText: {text}'
        
        # Dumps data
        with open(f'{clean_data_dir}/{title}_{date_str}.txt', "w", encoding="utf-8") as f:
            f.write(clean_data)
        with open(f'{meta_data_dir}/{title}_{date_str}.txt', "w", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False))

