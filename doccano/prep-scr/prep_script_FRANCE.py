from pathlib import Path
import os
from dotenv import load_dotenv

import json
from os.path import join
import pandas as pd
from .functions.functions import Doccano_Functions

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


''' To run this script from bash do the following:
        python -m YOU-DARE.doccano.prep_script_FRANCE
'''

## Read and prep pilotdata
in_p = str(REPO_ROOT / "doccano" / "pilotdata" / "data" / "FR_pilot_annotated.jsonl")

pilot_df = pd.read_json(in_p, orient = 'records', lines = True)
pilot_df_filter = pilot_df.loc[pilot_df['entities'].apply(lambda x: len(x) > 0)].reset_index()
pilot_df_select = pilot_df_filter[['link', 'text', 'entities', 'relations', 'Comments']].rename(columns = {'text': 'text_pilot'})

## Prepare labels mapping
labels_p = str(REPO_ROOT / "doccano" / "pilotdata" / "labels" / "FR-labels-mapping_rev.xlsx")

labels_df = pd.read_excel(labels_p)
labels_df['new label'] = labels_df['new label'].fillna(labels_df['old label']) # use old label if no new label specified

labels_mapping = dict(zip(labels_df['old label'], labels_df['new label']))

## init doccano class
doccano = Doccano_Functions()

# Step 1: Define all filtering parameters for the entire country
''' KEYWORDS:
        All keywords must be listed in a list
        The keywords are not case sensitive
        Keywords can be written in the following ways:
           - keyword : Catches keyword, KEYWORD, Keyword, KeYwOrD etc. (only the exact word)
           - *word   : Catches word, keyword, whats-the-word etc. (any word that ends with 'word')
           - key*    : Catches key, keyword, keylime etc. (any word that begins with 'key')
           - *ey*    : Catches ey, keyword, eye, hey etc. (any word that contains 'ey')
        Naming convention : COUNTRY_keywords
'''

FR_keywords = [
    'Genre',
    'sexualité',
    'sexe',
    'masculinité',
    'virilité',
    'LGBT',
    'homosexualité',
    'transtransgenre',
    'transidentité',
    'transition',
    'fluidité',
    'mère',
    'père',
    'parents',
    'parentalite',
    'famille',
    'enfants',
    'mariage',
    'démographie',
    'hormones',
    'PMA',
    'procréation médicalement assistée',
    'GPA',
    'gestation pour autrui',
    'femme',
    'laïcité',
    'religion',
    'voile',
    'burqua',
    'burkini',
    'séduction',
    'viande',
    'sport muscles',
    'violences sexuelles',
    'viol',
    'harcèlement',
    'harcèlement de rue',
    'féminisme',
    'féministes',
    'grand remplacement',
    'natalite',
    'etudes de genre',
    'salaire maternelle',
    'travail des femmes',
    'mères travailleuses',
    'woke',
    'wokisme',
    'travail des femmes',
    'avortement'
    ]


''' DATES:
        All dates must be on the form 'yyyy-mm-dd'
        Dates can be partial, e.g. 'yyyy-mm' or 'yyyy'
        What is included in the final dataset:
           - From_date:
              - 'yyyy-mm-dd' : This date is the first date that is included 
              - 'yyyy-mm'    : 'yyyy-mm-01' is the first date that is included
              - 'yyyy'       : 'yyyy-01-01' is the first date that is included
           - To_date:
              - 'yyyy-mm-dd' : This date is the last date that is included 
              - 'yyyy-mm'    : 'yyyy-mm-01' is the first date that is NOT included (e.g. to_date='2020-04' => '2020-03-31' IS included while '2020-04-01' IS NOT included)
              - 'yyyy'       : 'yyyy-01-01' is the first date that is NOT included (e.g. to_date='2020' => '2019-12-31' IS included while '2020-01-01' IS NOT included)
        Naming convention : COUNTRY_from_date and COUNTRY_to_date
        It is NOT a requirement to use both a from- and to-date
'''
from_date = '2023-01-01'
to_date = '2025-10-01'

# Step 2: Find all datasets that should be prepared for doccano
FR_data_directory = str(REPO_ROOT / "scrapers" / "data" / "France") # All datasets for the country
list_of_FR_dataset_paths = doccano.get_all_dataset_paths(FR_data_directory) # Finds all datasets within this folderstructure that ends with '_YT.jl', '_SPIDER.jl', '_MANUAL.jl' or '_TELEGRAM.jl'

# Step 3: Prepare said datasets for doccano
for dataset_path in list_of_FR_dataset_paths:
        
        # prep source data
        prepped_df = doccano.prepare_data_for_doccano(dataset_path, keywords=FR_keywords, from_date=from_date, to_date=to_date) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)

        # merge with pilotdata based on link (labels, entities, etc.)
        df_join = pd.merge(prepped_df, pilot_df_select, how = 'left', on = 'link')

        # determine span offset for labels
        try:
                df_join['text_len'] = df_join['text'].str.len()
        except KeyError:
                print(f"WARNING: The following dataset contains no text and no data has been saved: {dataset_path}")
                continue

        df_join['text_pilot_len'] = df_join['text_pilot'].str.len()
        df_join['span_offset'] = df_join['text_len'] - df_join['text_pilot_len']
        df_join = df_join.loc[~df_join['entities'].isna()].reset_index() # NAN values in entities causing issues with for loop

        # exit out if data frame empty (no existing labels - just use prepped_df)
        if df_join.shape[0] == 0:
                doccano.save_data(prepped_df)

        else:
                # update offset and change label to coding guide convention (based on research input)
                df_join['entities'] = df_join.apply(
                        lambda row: [
                                {**d, 
                                'start_offset': d['start_offset'] + row['span_offset'],
                                'end_offset': d['end_offset'] + row['span_offset'],
                                'label': labels_mapping.get(d['label'])
                                }
                                for d in row['entities']
                        ],
                axis = 1
                )
                
                df_join = df_join[['link', 'entities', 'relations', 'Comments']]

                # join on prepped again - all texts
                df_out = pd.merge(prepped_df, df_join, how = 'left', on = 'link')

                # save df
                doccano.save_data(df_out)







