import json
import os
from os.path import join
import pandas as pd
import random
from .functions.functions import Doccano_Functions

''' To run this script from bash do the following:
        python -m YOU-DARE.doccano.prep_script_FRANCE_additional
'''

# set random seed for sample
seed_no = 1763386108 # UNIX Epoch for when script was created

## init doccano class
doccano = Doccano_Functions()

# Step 1: Define all filtering parameters for the entire country
    # No keywords or dates used as they did not match any texts of the 3 actors - using random sample instead


# Step 2: Find all datasets that should be prepared for doccano
list_of_FR_dataset_paths = [
        "/work/YOU-DARE/scrapers/data/France/generation_zemmour_SPIDER/data_generation_zemmour_SPIDER.jl",
        "/work/YOU-DARE/scrapers/data/France/les_identitaires_SPIDER/data_les_identitaires_SPIDER.jl"
]

# Step 3: Prepare said datasets for doccano
for dataset_path in list_of_FR_dataset_paths:
        
        # prep source data
        prepped_df = doccano.prepare_data_for_doccano(dataset_path, save_data=False) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)

        # sample data
        sampled_df = prepped_df.sample(n=30, replace=False, random_state=seed_no)
        
        # save df
        doccano.save_data(sampled_df, custom_suffix="sampled")


# Thais d something
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

from_date = '2023-01-01'
to_date = '2025-10-01'

# dataset path
thais_dataset_path = '/work/YOU-DARE/scrapers/data/France/ThaisdEscufon_YT/ThaisdEscufon_YT.jl'

# 
doccano.prepare_data_for_doccano(thais_dataset_path, keywords=FR_keywords, from_date=from_date, to_date=to_date)