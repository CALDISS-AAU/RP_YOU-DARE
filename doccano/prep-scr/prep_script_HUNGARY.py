from pathlib import Path
import os
from dotenv import load_dotenv

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


''' To run this scraper from bash do the following:
        python -m YOU-DARE.doccano.prep_script_HUNGARY
'''

doccano = Doccano_Functions()

### TEST_COUNTRY ###
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
HUNGARY_keywords_raw = """
    *LMBT*, *LGBT*, *gender*, pride*, nő*, férfi*, transz*, homo*, nemi*, nemek*, 
    *femini*, maszkulin*, abortusz*, fiú*, lány*, anya*, apa*, anyá*, apá*, szex*, 
    szivárvány*, leszbi*, meleg*, buzi*, csaj*, hetero*, pedofil*, normalitás*, normál*, 
    biológia*, macsó*, performatív*, deviáns*, devianci*,
    társadalmi, nem*, biológiai
"""
HUNGARY_keywords = [w.strip() for w in HUNGARY_keywords_raw.split(",")]

HUNGARY_keyword_pairs = [
    ['társadalmi', 'nem*'], 
    ['biológiai', 'nem*']
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

HUNGARY_from_date = '2010-01-01'

# Step 2: Find all datasets that should be prepared for doccano
HUNGARY_data_directory = str(REPO_ROOT / "scrapers" / "data" / "Hungary") # All datasets for the TEST-country (could also be e.g. str(REPO_ROOT / "scrapers" / "data" / "TEST_COUNTRY" / "Telegram") if one only want to prepare telegram datasets)
list_of_HUNGARY_dataset_paths = doccano.get_all_dataset_paths(HUNGARY_data_directory) # Finds all datasets within this folderstructure that ends with '_YT.jl', '_SPIDER.jl', '_MANUAL.jl' or '_TELEGRAM.jl'
print(f'Keywords: {HUNGARY_keywords}\nKeyword pairs: {HUNGARY_keyword_pairs}\nAll {len(list_of_HUNGARY_dataset_paths)} directories: {list_of_HUNGARY_dataset_paths}')

# Step 3: Prepare said datasets for doccano
for dataset_path in list_of_HUNGARY_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=HUNGARY_keywords, keyword_pairs=HUNGARY_keyword_pairs, from_date=HUNGARY_from_date) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)

