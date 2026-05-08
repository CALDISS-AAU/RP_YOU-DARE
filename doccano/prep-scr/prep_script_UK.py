from .functions.functions import Doccano_Functions

''' To run this scraper from bash do the following:
        python -m YOU-DARE.doccano.prep_script_UK
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
keywords_raw = """gender, women, masculinity, femininity, transgender, transwomen, LGBTQ+, gay, lesbian, abortion, reproduction, sexuality, sex, family, parents, mother, father, natality, transgender rights, rape, sexual violence, women's safety, children safety"""
keywords = [w.strip() for w in keywords_raw.split(",")]

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
from_date = '2010-01-01'

# Step 2: Find all datasets that should be prepared for doccano
data_dir = '/work/YOU-DARE/scrapers/data/United_Kingdom' # All datasets for the TEST-country (could also be e.g. '/work/YOU-DARE/scrapers/data/TEST_COUNTRY/Telegram' if one only want to prepare telegram datasets)
list_of_UK_dataset_paths = doccano.get_all_dataset_paths(data_dir) # Finds all datasets within this folderstructure that ends with '_YT.jl', '_SPIDER.jl', '_MANUAL.jl' or '_TELEGRAM.jl'

# Exclude
drop = [
        '/work/YOU-DARE/scrapers/data/United_Kingdom/modernity_individual_links_SPIDER/data_modernity_individual_links_including_duplicates_SPIDER.jl',
        '/work/YOU-DARE/scrapers/data/United_Kingdom/lotus_eaters/lotus_eaters_news_SPIDER/data_lotus_eaters_news_SPIDER.jl',
        '/work/YOU-DARE/scrapers/data/United_Kingdom/lotus_eaters/lotus_eaters_analysis_SPIDER/data_lotus_eaters_analysis_SPIDER.jl',
        '/work/YOU-DARE/scrapers/data/United_Kingdom/lotus_eaters/lotus_eaters_entertainment_SPIDER/data_lotus_eaters_entertainment_SPIDER.jl',
        '/work/YOU-DARE/scrapers/data/United_Kingdom/mansworld_magazine/manworlds_magazine_essay_SPIDER/data_manworlds_magazine_essay_SPIDER.jl',
        '/work/YOU-DARE/scrapers/data/United_Kingdom/mansworld_magazine/manworlds_magazine_interview_SPIDER/data_manworlds_magazine_interview_SPIDER.jl'
]

list_of_UK_dataset_paths = [path for path in list_of_UK_dataset_paths if path not in drop]

# Step 3: Prepare said datasets for doccano
for dataset_path in list_of_UK_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=keywords, from_date=from_date) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)

# Step 4: Repeat step 1 to 3 for all datasets with special requirements, either using a specific sub-folder or a specific path
''' KEYWORDS:
        All keywords for this specific source must be listed, hence if the specific keywords for this source is an addition to the general keywords the two lists of keywords need to be joined
        Keywords are still not case sensitive and partial keywords can still be written using *
        Naming convention : NAME_OF_SOURCE_keywords
        New keywords does not need to be listed if only the dates change. If this is the case keep the argument keywords=TEST_keywords when preparing the data for doccano
''' 

''' DATES:
        The format of the provided dates has not changed
        Naming convention : NAME_OF_SOURCE_from_date and NAME_OF_SOURCE_to_date
        New dates does not need to be listed if only the keywords, or one of the dates, change. If this is the case keep the arguments from_date=TEST_from_date and/or to_date=TEST_to_date when preparing the data for doccano
'''

