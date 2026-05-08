import pandas as pd
import os

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

input_folder_path = '/work/YOU-DARE/controversy-mapping/sentence_filtering/matched_data'
input_file_ending = '_matched.jl'
output_folder_path = '/work/YOU-DARE/controversy-mapping/sentence_filtering/keyword_related_data/matched_words_xlsx'

for country in all_countries:
    output_file_path = f'{output_folder_path}/{country}_matched_words.xlsx'
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with pd.ExcelWriter(output_file_path) as writer:
        for theme in all_themes:
            input_file_path = f'{input_folder_path}/{country}/{country}_{theme}{input_file_ending}'

            df = pd.read_json(input_file_path, lines=True)

            words = (
                df['matched words']
                .explode()
                .dropna()
                .str.lower()
                .unique()
            )

            df_out = pd.DataFrame()
            df_out['Words'] = words
            df_out['False positive'] = None

            df_out.to_excel(writer, sheet_name=theme, index=False)

            print(f'Finished {country} {theme}')