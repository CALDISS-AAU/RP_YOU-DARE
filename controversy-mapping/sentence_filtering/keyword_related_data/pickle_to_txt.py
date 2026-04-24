import pickle 
from pathlib import Path
import json

input_data_folder = '/work/YOU-DARE/controversy-mapping/sentence_filtering/keyword_related_data/keyword_pickels'
output_data_folder = '/work/YOU-DARE/controversy-mapping/sentence_filtering/keyword_related_data/keyword_lists'

all_countries = [
    'DK',
    'ES',
    'FR',
    'HU',
    'IT',
    'RO',
    'SE',
    'UK'
]

all_themes = [
    'lgb',
    'migration',
    'woke'
]

relevant_sub_dicts = [
    'lgb_core',
    'woke_core',
    'woke_extended_1',
    'woke_extended_2',
    'migr_core',
    'remigr_core',
    'replace_dict'
]

for country in all_countries:
    country_data = {}
    for theme in all_themes:
        input_data_path = f'{input_data_folder}/{country}/{country}_{theme}_dictionaries.pkl'
        output_data_path = f'{output_data_folder}/{country}_keywords_lists.txt'

        with open(input_data_path, 'rb') as f:
            input_data = pickle.load(f)
            print(input_data)

        # keywords = [kw for sub_dict in input_data.values() for kw in sub_dict]
        keywords = [
            kw
            for sub_name, sub_dict in input_data.items()
            if sub_name in relevant_sub_dicts
            for kw in sub_dict
        ]

        country_data[theme] = keywords
        
        Path(output_data_folder).mkdir(parents=True, exist_ok=True)
        with open(output_data_path, 'w', encoding='utf-8') as output:
            json.dump(country_data, output, ensure_ascii=False, indent=2)