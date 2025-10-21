import json
import pandas as pd
import dateparser
import re
import os
import numpy as np
import traceback
import pathlib

class Doccano_Functions:
    def __init__(self):
        self.country = None
        self.source = None
        self.method = None

    def prepare_data_for_doccano(self, input_file_path: str, from_date=None, to_date=None, exclude_empty_dates=False, keywords=None, keyword_pairs=None):
        # if keywords is None:
        #     keywords = []
        # if keyword_pairs is None:
        #     keyword_pairs = [[]]

        # Prepares data #
        self.extract_info_from_input_file_path(input_file_path) # Extracts country and source from the input file path and saves these as instance variables
        data = self.import_data(input_file_path) # Imports the data on the input file path
        if not data:
            print("No data loaded.")
            return None

        # Dataframe setup and preparation #
        df = self.select_and_clean_relevant_columns(data) # Only include relevant and cleaned columns in the dataframe

        # Publication date fiddeling - standadising and filtering
        df = self.normalise_publication_dates(df)  # Normalise dates after cleaning
        if from_date or to_date:
            df = self.filter_dates(df, from_date, to_date, exclude_empty_dates)

        # --- Exit early if date filter yields zero rows ---
        if df.empty:
            print("No rows after date filtering; writing empty dataset.")
            empty_cols = ['text', 'link', 'source', 'publication date']
            if keywords:  # keep schema consistent if keywords were requested
                empty_cols.append('matched keywords')
            self.save_data(pd.DataFrame(columns=empty_cols))
            return df

        # Keywords matching
        df = self.match_on_keywords(df, keywords, keyword_pairs)

        # Saves data to jsonlines
        self.save_data(df)

        return df

    def extract_info_from_input_file_path(self, input_file_path: str):
        ''' Extracts the country and source from the path of the input file, and adds the source to the dataframe.
            Needs a path on the form:
                /work/YOU-DARE/scrapers/data/country/source_platform/...
        ''' 
        parts = input_file_path.strip('/').split('/')
        try:
            self.country = parts[4]  # 5th element is the country
            
            p = pathlib.Path(input_file_path)
            source_and_method = p.stem  # 'data_motstandsrorelsen_SPIDER'
            
            source_parts = source_and_method.split('_')
            method = source_parts[-1]  # 'SPIDER'

            platform_map = {
                'YT': 'YouTube',
                'SPIDER': 'website',
                'MANUAL': 'website',
                'TELEGRAM': 'telegram'
            }
            self.method = platform_map.get(method.upper(), 'unknown')

            print(f"Metadata extracted — Country: {self.country}")
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
            'article_text', # Spider
            'video_text', # YouTube
            'Message_text', # Telegram
            'Thread_text', # Merged telegram
            'thread_text', # Spider forum
            'article_sub_title', # Spider
            'video_sub_title', # YouTube
            'article_link', # Spider
            'video_link', # Youtube
            'post_link', # Spider forum
            'URL', # Telegram (all)
            'article_title', # Spider
            'video_title', # YouTube
            'post_title', # Spider forum
            'publication_date', # Everything but telegram
            'Timestamp', # Telegram
            'source', # Everything but telegram
            'Source', # Telegram
            'Display_name', # Telegram
        ]

        # From the full list, keep only the columns that are actually present in the input data
        available_columns = [col for col in relevant_columns if col in complete_df.columns]

        # Print the columns we’ll be working with
        print(f'Extracted columns: {available_columns}')

        # Create a copy of just the relevant data (to avoid modifying the original DataFrame or triggering warnings)
        df = complete_df[available_columns].copy()

        # Rename columns to standard format
        rename_map = {
            'article_text': 'text', # Websites / manual
            'video_text': 'text', # YouTube
            'Message_text': 'text', # Telegram posts
            'Thread_text': 'text', # Telegram combined
            'thread_text': 'text', # Forum
            'article_sub_title': 'sub_title', # Websites / manual
            'video_sub_title': 'sub_title', # YouTube
            'article_link': 'link', # Websites / manual
            'video_link': 'link', # YouTube
            'post_link': 'link', # Forum
            'URL': 'link', # Telegram
            'article_title': 'title', # Websites / manual
            'video_title': 'title', # YouTube 
            'post_title': 'title', # Forum
            'publication_date': 'publication date', # Websites / manual / YouTube
            'Timestamp': 'publication date', # Telegram
            'source': 'source', # Websites / manual / YouTube
            'Source': 'source', # Telegram
            'Display_name': 'source' # Telegram
        }

        # Only rename columns that are actually present
        columns_to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
        df.rename(columns=columns_to_rename, inplace=True)

        if 'title' in df.columns: # Ensure title is always a single string rather than potentially a list
            df['title'] = df['title'].apply(
                lambda x: ' '.join(map(str, x)) if isinstance(x, list)
                else ('' if pd.isna(x) else str(x))
            )

        if 'sub_title' in df.columns: # Ensure sub-title is always a single string rather than potentially a list
            df['sub_title'] = df['sub_title'].apply(
                lambda x: ' '.join(map(str, x)) if isinstance(x, list)
                else ('' if pd.isna(x) else str(x))
            )

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

        # Assigns source to dataset for output_file_name
        self.source = df['source'][0]

        # Return the cleaned-up, ready-for-export DataFrame
        return df

    def normalise_publication_dates(self, df):
        df['publication date'] = df['publication date'].apply(lambda s: None if (pd.isna(s) or (isinstance(s, str) and s.strip()=='')) else dateparser.parse(s, settings={'RETURN_AS_TIMEZONE_AWARE': False}))
        df['publication date'] = pd.to_datetime(df['publication date'], errors='coerce')
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
        
    def match_on_keywords(self, df, keywords, keyword_pairs, text_column='text'):
        df = df.copy()
        if keywords:
            keyword_regexes = [(kw, self.convert_to_regex(kw)) for kw in keywords]
            matched_keywords = []

            # iterate per row so we can mask the actor/source from the text before matching
            for _, row in df.iterrows():
                text = (row.get(text_column) or '')
                if self.method == "telegram":  # TILFØJELSE
                    text = '\n'.join([t[1] for t in re.findall(r'(Post_text|Comment_text)(.*?(?=---))', text, flags=re.DOTALL)]) or text  # TILFØJELSE

                # --- mask actor/source so it can't trigger matches ---
                actor = (row.get('source') or '').strip()
                text_for_match = text
                if actor:
                    try:
                        text_for_match = re.sub(re.escape(actor), ' ', text_for_match, flags=re.IGNORECASE)
                    except re.error as e:
                        print(f"Error masking actor '{actor}': {e}")

                matches = set()
                for original_kw, pattern in keyword_regexes:
                    try:
                        if re.search(pattern, text_for_match, flags=re.IGNORECASE):
                            matches.add(original_kw)
                    except re.error as e:
                        print(f"Bad regex for keyword '{original_kw}': {e}")

                matched_keywords.append(sorted(matches, key=str.lower))

                ## Insert functionality to remove keywords from pairs if not both (or more) keywords are present ##
                if keyword_pairs:
                    matched_keywords = self.check_keyword_pairs(keyword_pairs, matched_keywords)

            df['matched keywords'] = matched_keywords
            df = df[df['matched keywords'].map(len) > 0]  # keep only matched when keywords were provided

            # ✅ Early exit if nothing matched — don't try to build YAML
            if df.empty:
                print("No rows matched keywords; returning empty dataset.")
                return df  # let caller handle saving; your outer guard will write an empty .jl

            df['text'] = df.apply(self.build_yaml_keywords, axis=1)
            return df
        else:
            # no keywords provided: keep all rows and build YAML without the "Matched keywords" line
            df['text'] = df.apply(self.build_yaml, axis=1)
            print("No keywords provided. Returning original DataFrame.")
            return df

    def check_keyword_pairs(self, keyword_pairs, matched_keywords_list):
        ''' keyword_pairs : list of lists
            only keep words from keyword pairs in matched keywords if all words are present
        '''
        # for row in matched_keywords_list: # matched_keywords_list = list of list, row = list for specific observation
        #     unmatched_pair_words = set()
        #     matched_pairs = []
        #     if len(row) >=1: # Only look at non empty rows
        #         print(f'All matched keywords for this row: {row}')
        #         for pair in keyword_pairs: # keyword_pairs = list of list, pair = list
        #             if not set(pair).issubset(row):
        #                 for word in pair:
        #                     if word in row:
        #                         unmatched_pair_words.add(word)
        #             else:
        #                 matched_pairs.append(pair)
        #         print(f'unmatched words: {unmatched_pair_words}, matched pairs: {matched_pairs}')
        #         for word in list(unmatched_pair_words):
        #             row.remove(word)
        #         for pair in matched_pairs:
        #             if not set(pair).issubset(row):
        #                 row.append(pair)

        # Adds words from keyword pairs back into matched_keywords as single words rather than pairs
        for row in matched_keywords_list:
            unmatched_pair_words = set()
            matched_pair_words = set()
            if len(row) >=1:
                # print(row)
                for pair in keyword_pairs:
                    if not set(pair).issubset(row):
                        for word in pair:
                            if word in row:
                                unmatched_pair_words.add(word)
                    else:
                        for word in pair:
                            matched_pair_words.add(word)
                # print(f'unmatched words: {unmatched_pair_words}, matched pairs: {matched_pair_words}')
                for word in list(unmatched_pair_words):
                    row.remove(word)
                for word in list(matched_pair_words):
                    if word not in row:
                        row.append(word)
        
        return matched_keywords_list 

    def build_yaml(self, row):
        # Build the YAML header and attach to text
        return (
            f"---\n"
            f"Link: {row['link']}\n"
            f"Actor: {row['source']}\n"
            f"Publication date: {row['publication date']}\n"
            f"---\n"
            f"{row['text']}"
        )

    def build_yaml_keywords(self, row):
        # Join matched keywords into a comma-separated string
        keyword_string = ', '.join(row['matched keywords'])
        
        # Build the YAML header and attach to text
        return (
            f"---\n"
            f"Link: {row['link']}\n"
            f"Actor: {row['source']}\n"
            f"Matched keywords: {keyword_string}\n"
            f"Publication date: {row['publication date']}\n"
            f"---\n"
            f"{row['text']}"
        )

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
        output_path = f'{output_dir}/data_{self.country}_{self.source}_{self.method}_anno.jl'
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

    def get_all_dataset_paths(self, data_directory):
        list_of_all_datasets = []
        list_of_datasets_SPIDER = list(pathlib.Path(data_directory).rglob('*_SPIDER.jl'))
        list_of_datasets_MANUAL = list(pathlib.Path(data_directory).rglob('*_MANUAL.jl'))
        list_of_datasets_YT = list(pathlib.Path(data_directory).rglob('*_YT.jl'))
        list_of_datasets_TELEGRAM = list(pathlib.Path(data_directory).rglob('*_TELEGRAM.jl'))
        list_of_all_datasets = list_of_datasets_SPIDER + list_of_datasets_MANUAL + list_of_datasets_YT + list_of_datasets_TELEGRAM
        list_of_all_datasets = list(map(str, list_of_all_datasets))
        return list_of_all_datasets

    ### FOR MULTIPLE DATE RANGES ###
    def prepare_data_for_doccano_ranges(self, input_file_path: str, date_ranges, exclude_empty_dates=False, keywords=None):
        if keywords is None: keywords = []
        if not isinstance(date_ranges, (list, tuple)) or not date_ranges:
            print("date_ranges must be a non-empty list/tuple of (from_date, to_date) pairs."); return None
        self.extract_info_from_input_file_path(input_file_path)
        data = self.import_data(input_file_path)
        if not data: print("No data loaded."); return None
        df = self.select_and_clean_relevant_columns(data)
        df = self.normalise_publication_dates(df)
        df = self.filter_dates_multi(df, date_ranges, exclude_empty_dates)
        if df.empty:
            print("No rows after date filtering; writing empty dataset.")
            empty_cols = ['text','link','source','publication date']
            if keywords: empty_cols.append('matched keywords')
            self.save_data(pd.DataFrame(columns=empty_cols))
            return data
        df = self.match_on_keywords(df, keywords)
        self.save_data(df)
        return data

    def filter_dates_multi(self, df, date_ranges, exclude_empty_dates):
        """Union of inclusive ranges. Each item is (from_date, to_date); use None to open-end."""
        df = df.copy()
        df['publication date'] = pd.to_datetime(df['publication date'], format='%Y-%m-%d', errors='coerce')
        if df.empty: return df
        mask_any = pd.Series(False, index=df.index)
        for rng in date_ranges:
            if not isinstance(rng, (list, tuple)) or len(rng) != 2:
                print(f"Skipping invalid date range: {rng}"); continue
            f, t = rng
            m = pd.Series(True, index=df.index)
            if f: 
                fdt = pd.to_datetime(f, errors='coerce')
                if pd.notna(fdt): m &= (df['publication date'] >= fdt)
            if t:
                tdt = pd.to_datetime(t, errors='coerce')
                if pd.notna(tdt): m &= (df['publication date'] <= tdt)
            mask_any |= m
        final_mask = mask_any if exclude_empty_dates else (mask_any | df['publication date'].isna())
        df = df[final_mask].sort_values(by='publication date', ascending=False, na_position='last').copy()
        df['publication date'] = df['publication date'].dt.strftime('%Y-%m-%d')
        return df
    # Continue from here...