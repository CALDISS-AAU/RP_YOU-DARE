from .functions.functions import Doccano_Functions

''' To run this scraper from bash do the following:
        python -m YOU-DARE.doccano.prep_script_SWEDEN
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
keywords_raw = """genus, kön*, maskulin*, feminin*, hormon*, norm, sex*, HBTQ*, pride, homosexu*, lesbisk*, bög, transperson*, transidentitet, transsexualitet, familj, föräld*, mamm*, mor, papp*, far, fäder, barn, gift, äktenskap, abort*, gravid*, hormon*, assisterad befruktning, befolkning*, demografi*, folkutbyte, födelsetal*, surrogatm*, föräldraledig*, samlag, perver*, antasta*, samtycke, trakasserier, våldtäkt*, övergrepp, oskuld, tjej, kille, killar*, flick, pojk, dam*, fru, tant*, kärring*, gubb*, heder*, incel, slöja, burka, slamp*, gender, sex*, masculine*, feminine*, hormone*, norm, sex*, LGBTQ*, pride, homosexu*, lesbian*, gay*, fag*, trans person*, trans identit*, transsexuality, family, parent*, mum*, mom*, mother, dad*, father*, child, marri*, marry, abortion*, pregnan*, hormon*, assisted reproduction, population*, demography*, replacement, birth rate*, surroga*, parental leave*, intercourse, perver*, molest*, consent*, harassment, rape*, raping, abuse*, virginity, girl, guy, girl, boy, lady*, wife, hag, gramp*, honor*, honour*, incel, veil, burqa, slut*"""
keywords_SE = [w.strip() for w in keywords_raw.split(",")]

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
SE_from_date = '2021-06-01'
SE_to_date = '2025-06-30'

# Step 2: Find all datasets that should be prepared for doccano
sweden_data_directory = '/work/YOU-DARE/scrapers/data/Sweden' # All datasets for the TEST-country (could also be e.g. '/work/YOU-DARE/scrapers/data/TEST_COUNTRY/Telegram' if one only want to prepare telegram datasets)
list_of_TEST_dataset_paths = doccano.get_all_dataset_paths(sweden_data_directory) # Finds all datasets within this folderstructure that ends with '_YT.jl', '_SPIDER.jl', '_MANUAL.jl' or '_TELEGRAM.jl'

# Step 3: Prepare said datasets for doccano
for dataset_path in list_of_TEST_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=keywords_SE, from_date=SE_from_date, to_date=SE_to_date) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)

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
keywords_2_raw = '''gender, sex*, masculine*, feminine*, hormone*, norm, sex*, LGBTQ*, pride, homosexu*, lesbian*, gay*, fag*, trans person*, trans identit*, transsexuality, family, parent*, mum*, mom*, mother, dad*, father*, child, marri*, marry, abortion*, pregnan*, hormon*, assisted reproduction, population*, demography*, replacement, birth rate*, surroga*, parental leave*, intercourse, perver*, molest*, consent*, harassment, rape*, raping, abuse*, virginity, girl, guy, girl, boy, lady*, wife, hag, gramp*, honor*, honour*, incel, veil, burqa, slut*'''
keywords_2 = [w.strip() for w in keywords_2_raw.split(",")]

### GOlden One YT ###
golden_one_dir = '/work/YOU-DARE/scrapers/data/Sweden/the_golden_one_YT' # Only the source_1 folder
list_of_golden_one_dataset_paths = doccano.get_all_dataset_paths(golden_one_dir ) 

for dataset_path in list_of_golden_one_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=keywords_2, from_date=SE_from_date, to_date=SE_to_date)

### GOLDEN ONE TELEGRAM ###
golden_one_TELEGRAM_path = '/work/YOU-DARE/scrapers/data/Sweden/Telegram/thegoldenone_TELEGRAM' # Full path to a specific dataset
list_of_golden_one_telegram_dataset_paths = doccano.get_all_dataset_paths(golden_one_TELEGRAM_path) 
for dataset_path in list_of_golden_one_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=keywords_2, from_date=SE_from_date, to_date=SE_to_date)

### GYM XIV OLD TELEGRAM ###
gym_xiv_old_dir = '/work/YOU-DARE/scrapers/data/Sweden/Telegram/GymXIV_OLD'
gym_xiv_dataset_paths = doccano.get_all_dataset_paths(gym_xiv_old_dir) 

for dataset_path in gym_xiv_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=keywords_2, from_date=SE_from_date, to_date=SE_to_date)


### GYM XIV NEW TELEGRAM
gym_xiv_new_dir = '/work/YOU-DARE/scrapers/data/Sweden/Telegram/GymXIV2_NEW'
gym_xiv_new_dataset_paths = doccano.get_all_dataset_paths(gym_xiv_new_dir) 

for dataset_path in list_of_golden_one_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=keywords_2, from_date=SE_from_date, to_date=SE_to_date)

# ### Aktivklubb sverige TELEGRAM ###
# Aktivklubb_dir = '/work/YOU-DARE/scrapers/data/Sweden/Telegram/AktivklubbSverige'
# list_aktivklubb_dataset_paths = doccano.get_all_dataset_paths(Aktivklubb_dir)

# for dataset_path in list_of_golden_one_dataset_paths:
#     doccano.prepare_data_for_doccano(dataset_path, keywords=keywords_SE, from_date=SE_from_date, to_date=SE_to_date)

