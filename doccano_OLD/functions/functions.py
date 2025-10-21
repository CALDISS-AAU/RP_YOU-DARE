import json
import pandas as pd
import dateparser
import re
import os
import numpy as np
import traceback



class Doccano_Functions:
    def __init__(self):
        self.country = None
        self.source = None

    def prepare_data_for_doccano(self, input_file_path: str, from_date=None, to_date=None, exclude_empty_dates=False, keywords=[]):
        # Prepares data #
        self.extract_info_from_input_file_path(input_file_path) # Extracts country and source from the input file path and saves these as instance variables
        data = self.import_data(input_file_path) # Imports the data on the input file path
        if not data:
            print("No data loaded.")
            return None

        # Dataframe setup and preparation #
        df = self.select_and_clean_relevant_columns(data) # Only include relevant and cleaned columns in the dataframe
        df['source'] = self.source  # Append source_platform as a column

        # Publication date fiddeling - standadising and filtering
        df = self.normalise_publication_dates(df)  # Normalise dates after cleaning
        if from_date or to_date:
            df = self.filter_dates(df, from_date, to_date, exclude_empty_dates)

        # Keywords matching
        if keywords:
            df = self.match_on_keywords(df, keywords)

        # Saves data to jsonlines
        self.save_data(df)

        return data

    def extract_info_from_input_file_path(self, input_file_path: str):
        ''' Extracts the country and source from the path of the input file, and adds the source to the dataframe.
            Needs a path on the form:
                /work/YOU-DARE/scrapers/data/country/source_platform/...
        ''' 
        parts = input_file_path.strip('/').split('/') # Splits the path
        try:
            self.country = parts[4] # Assigns the 5th element to the instance variable 'country'
            source_and_method = parts[5] 
            source_parts = source_and_method.split('_') # Splits the 6th element at '_'
            method = source_parts[-1] # Assigns the last element of the source to 'method'
            raw_source = '_'.join(source_parts[:-1]) # Joins the rest of the source back together

            # Assigns relevant platforms to the used method
            platform_map = {
                'YT': 'YouTube',
                'SPIDER': 'website',
                'MANUAL': 'website',
                'TELEGRAM': 'telegram'
            }
            platform = platform_map.get(method.upper(), 'unknown')
            self.source = f"{raw_source}_{platform}" # Combines the original source excluding the method with the relevant plantform and assigns it to the instance variable 'source'

            print(f"Metadata extracted — Country: {self.country}, Source: {self.source}")
        except IndexError as e:
            print(f"Invalid input path format: {input_file_path}. Error: {e}")

    def import_data(self, input_file_path: str):
        ''' Imports a given jsonlines file for further processing '''
        try:
            with open(input_file_path, 'r', encoding='utf-8') as input_file:
                data = [json.loads(line) for line in input_file]
            print(f'Data loaded from {input_file_path}.')
            return data
        except Exception as e:
            print(f'Failed to load data from {input_file_path}. Error: {e}')
            return []

    def select_and_clean_relevant_columns(self, data):
        ''' 
            Processes a dataset by:
            - Keeping only relevant columns
            - Merging the *_title and *_sub_title into the *_text
            - Removing the *_sub_title column afterward
            - Adding an empty 'publication_date' column if it's missing
        '''
        
        # Convert the input data (list of dicts) into a pandas DataFrame
        complete_df = pd.DataFrame(data)

        # Relevant columns for Doccano
        relevant_columns = [
            'publication_date',
            'article_text',
            'video_text',
            'article_link',
            'video_link',
            'article_title',
            'video_title', 
            'article_sub_title',
            'Message_text',
            'Timestamp',
            'URL'
        ]

        # From the full list, keep only the columns that are actually present in the input data
        available_columns = [col for col in relevant_columns if col in complete_df.columns]

        # Print the columns we’ll be working with
        print(f'Extracted columns: {available_columns}')

        # Create a copy of just the relevant data (to avoid modifying the original DataFrame or triggering warnings)
        df = complete_df[available_columns].copy()

        # Rename columns to standard format
        rename_map = {
            'article_text': 'text',
            'video_text' : 'text',
            'Message_text' : 'text',
            'article_sub_title': 'sub_title',
            'video_sub_title': 'sub_title',
            'article_link': 'link',
            'video_link': 'link',
            'URL': 'link',
            'article_title': 'title',
            'video_title': 'title',
            'publication_date': 'publication date',
            'Timestamp': 'publication date'
        }

        # Only rename columns that are actually present
        columns_to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
        df.rename(columns=columns_to_rename, inplace=True)

        # Add title and subtitle to the beginning of the article text if 'text' exists
        if 'text' in df.columns: # Relevant in cases were no transcriptions has been matched to associated data rows
            if 'title' in df.columns:
                if 'sub_title' in df.columns:
                    # Prepend title and subtitle (with spacing) before the main article text
                    df['text'] = (
                        df['title'].fillna('') + '\n' +               # Title
                        df['sub_title'].fillna('') + '\n\n' +         # Subtitle
                        df['text'].fillna('')                         # Main text
                    )
                else:
                    # Only title exists — prepend it before the main text
                    df['text'] = (
                        df['title'].fillna('') + '\n\n' +
                        df['text'].fillna('')
                    )
        # else:
        #     df['text'] = ''

        # Drop sub_title
        if 'sub_title' in df.columns:
            df.drop(columns='sub_title', inplace=True)

        # Ensure 'publication_date' exists
        if 'publication date' not in df.columns:
            # If missing, add an empty column (to keep a consistent schema)
            df['publication date'] = None

        # Return the cleaned-up, ready-for-export DataFrame
        return df

    def normalise_publication_dates(self,df):
        df['publication date'] = df['publication date'].apply(
            lambda s: pd.NaT 
                if pd.isna(s) # If no publication date then it stays NaN/null (pd.NaT)
                else dateparser.parse(
                    s, 
                    settings={'RETURN_AS_TIMEZONE_AWARE': False} # Return a datetime.datetime without any timezones no matter the input
                ) 
            ) # publication date is now true datetime always

        # Format to yyyy-mm-dd
        df['publication date'] = df['publication date'].dt.strftime('%Y-%m-%d')
        return df

    def filter_dates(self, df, from_date, to_date, exclude_empty_dates):
        ''' Sorts and filtes data based on given arguments.
            - from_date: 'yyyy-mm-dd' this date is included in the final dataset
            - to_date: 'yyyy-mm-dd' this date is included in the final dataset
            - exclude_empty_dates: False (default)/True excludes empty dates
        '''
        df['publication date'] = pd.to_datetime(
            df['publication date'],
            format='%Y-%m-%d',
            errors='coerce'
        )

        # Sort by date descending, with NaT (missing dates) placed at the end
        df = df.sort_values(by='publication date', ascending=False, na_position='last')

        # Filter by from_date and to_date if provided
        if from_date:
            from_dt = pd.to_datetime(from_date, errors='coerce') # Fills all invalid dates with NaT
            if pd.notna(from_dt):
                df = df[
                    (df['publication date'].isna()) |  # keep NaT rows
                    (df['publication date'] >= from_dt)  # apply filter only to real dates
                ]

        if to_date:
            to_dt = pd.to_datetime(to_date, errors='coerce') # Fills all invalid dates with NaT
            if pd.notna(to_dt):
                df = df[
                    (df['publication date'].isna()) |  # keep NaT rows
                    (df['publication date'] <= to_dt)  # apply filter only to real dates
                ]

        # Optionally drop rows with empty publication dates
        if exclude_empty_dates:
            df = df[df['publication date'].notna()]

        df['publication date'] = df['publication date'].dt.strftime('%Y-%m-%d')
        
        return df
        
    def match_on_keywords(self, df, keywords, text_column='text'):
        if len(keywords)==0:
            print("No keywords provided. Returning original DataFrame.")
            return df

        # Convert wildcard patterns to regex
        keyword_regexes = [(kw, self.convert_to_regex(kw)) for kw in keywords]
        
        matched_keywords = []

        if 'text' in df.columns:
            for text in df[text_column].fillna(''):
                matches = set()
                for original_kw, pattern in keyword_regexes:
                    if re.search(pattern, text, flags=re.IGNORECASE):
                        matches.add(original_kw)
                matched_keywords.append(sorted(matches, key=str.lower))

            df = df.copy()
            df['matched keywords'] = matched_keywords

            # Keep only rows where at least one keyword matched
            df = df[df['matched keywords'].map(len) > 0]

        return df

    def convert_to_regex(self, keyword):
        pattern = keyword.strip()
        if pattern.startswith('*') and pattern.endswith('*'):
            return re.escape(pattern.strip('*'))
        elif pattern.startswith('*'):
            return r'\w*' + re.escape(pattern.strip('*')) + r'(\s|\.|\,)'
        elif pattern.endswith('*'):
            return r'\s' + re.escape(pattern.strip('*')) + r'\w*'
        else:
            return r'\s' + re.escape(pattern) + r'(\s|\.|\,)'

    def save_data(self, df):
        output_dir = f'/work/YOU-DARE/doccano/data/{self.country}'
        output_path = f'{output_dir}/data_{self.country}_{self.source}_anno.jl'
        os.makedirs(output_dir, exist_ok=True)
        try:
            df.to_json(output_path, orient='records', lines=True)
            # with open(output_path, 'w', encoding='utf-8') as f:
            #     for record in df.to_dict(orient='records'):
            #         json_line = json.dumps(record, ensure_ascii=False, separators=(',', ':'))
            #         f.write(json_line + '\n')
                    
            print('The data was saved successfully!')
        except Exception as e:
            print(f'Failed to save data. Error: {e}')


    # Continue from here...

class Transcriber_data_Functions:
    def add_transcribed_text_to_video_data(self, dataset_path, transcriptions_dir):
        """
        Convenience function to:
        1. Extract text from transcription files.
        2. Merge with the videos dataset.
        
        Output is saved in the same folder as the videos dataset with a name
        matching the folder name.

        Args:
            dataset_path (str): Full path to 'videos.jl'.
            transcriptions_dir (str): Directory containing raw transcription .json files.
        """
        # Step 1: Create intermediate file path for extracted text
        temp_transcript_path = os.path.join(transcriptions_dir, 'combined_text_dataset.jl')

        # Step 2: Generate text dataset
        self.make_text_dataset_from_transcriptions(transcriptions_dir, temp_transcript_path)

        # Step 3: Merge with original dataset
        self.merge_datasets_on_audio_name(dataset_path, temp_transcript_path)

    def extract_text_from_jsonl(self, file_path):
        all_texts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    segments = data.get('segments', [])
                    for segment in segments:
                        text = segment.get('text')
                        if text:
                            all_texts.append(text)
        except Exception as e:
            print(f'Failed to load data from {input_file_path}. Error: {e}')
            return []

        full_text = ' '.join(all_texts)
        return full_text

    def make_text_dataset_from_transcriptions(self, transcriptions_dir, output_path):
        """
        Processes transcription JSON files in a directory and writes a JSONL file with
        'file_name' (cleaned to match original metadata) and 'text' fields.
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as out_file:
                for file_name in os.listdir(transcriptions_dir):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(transcriptions_dir, file_name)
                        full_text = self.extract_text_from_jsonl(file_path)

                        # Clean the filename to strip model/language suffix
                        cleaned_name = os.path.splitext(file_name)[0]

                        out_file.write(json.dumps({
                            'file_name': cleaned_name,
                            'video_text': full_text
                        }) + '\n')
        except Exception as e:
            print(f'Failed to process transcriptions from {transcriptions_dir}. Error: {e}')
            return []
    
    def merge_datasets_on_audio_name(self, dataset_path, transcript_path):
        """
        Merges metadata and transcription datasets based on normalized audio file names,
        and saves the result to a .jl file named after the dataset's parent folder.
        """
        try:
            # Step 1: Load transcriptions into a normalized lookup dictionary
            transcription_lookup = {}
            with open(transcript_path, 'r', encoding='utf-8') as tf:
                for line in tf:
                    data = json.loads(line)
                    key = data['file_name'].strip().lower()
                    transcription_lookup[key] = data['video_text']

            # Step 2: Merge with dataset entries
            merged_data = []
            unmatched_files = []
            with open(dataset_path, 'r', encoding='utf-8') as df:
                for line in df:
                    entry = json.loads(line)
                    raw_name = entry.get('video_id')
                    normalized_name = raw_name.strip().lower() if raw_name else None

                    if normalized_name and normalized_name in transcription_lookup:
                        entry['video_text'] = transcription_lookup[normalized_name]
                        # print(f"Matched: {raw_name}")
                    else:
                        unmatched_files.append(raw_name)
                        # print(f"No match for: {raw_name}")

                    merged_data.append(entry)

            # Step 3: Determine output path
            folder_path = os.path.dirname(dataset_path)
            parent_folder_name = os.path.basename(folder_path)
            output_path = os.path.join(folder_path, f'{parent_folder_name}.jl')

            # Step 4: Write merged output
            with open(output_path, 'w', encoding='utf-8') as out_file:
                for item in merged_data:
                    out_file.write(json.dumps(item) + '\n')

            print(f'Merged file saved to: {output_path}')
            if unmatched_files:
                print(f"\nUnmatched entries: {len(unmatched_files)}")
                for f in unmatched_files: # print's the name of all unmatched files
                    print(f" - {f}")

        except Exception as e:
            print(f'Failed to merge datasets. Error: {e}\n\n\n')
            



    # Continue from here...