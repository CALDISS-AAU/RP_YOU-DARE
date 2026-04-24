from .functions.functions import Doccano_Functions

''' To run this scraper from bash do the following:
        python -m YOU-DARE.doccano.prep_script_DENMARK
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
TEST_keywords = ["#metoo",
"abort",
"befolkningstal",
"biologi",
"børn",
"burqua",
"demografi",
"feminine",
"feminisme",
"feminister",
"flydende",
"fødselsrate",
"forældre",
"forældremyndighed",
"homoseksuelle",
"hormoner",
"identitetskrise",
"indvandrer",
"islam",
"islam",
"køn",
"kønsideologi",
"konspiration",
"kønsskifte",
"kønsstudier",
"kønsidentitet",
"kønsskifte",
"kriminelle",
"kvinde",
"kvindelige arbejde",
"kvinder",
"lgb",
"lgbtq",
"ligestilling",
"mandlig",
"maskulinitet",
"mor", 
"far",
"muslim",
"muslimer",
"migration",
"mænd",
"omsorg",
"opdragelse",
"pædofil",
"pædofili",
"race",
"religion",
"remigration",
"samtykkelov",
"seksuel undervisning",
"sekulær",
"sex",
"seksuel undervisning",
"sexualitet",
"sexchikane",
"sexforbrydelse",
"skilsmisse",
"social kontrol",
"sofie linde",
"tørklæde",
"trans",
"transkønnede",
"transpersoner",
"undertrykkelse",
"velfærdsstat",
"voldtægt",
"woke",
"wokeisme"]

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

# Step 2: Find all datasets that should be prepared for doccano
data_directory = '/work/YOU-DARE/scrapers/data/Denmark' # All datasets for the TEST-country (could also be e.g. '/work/YOU-DARE/scrapers/data/TEST_COUNTRY/Telegram' if one only want to prepare telegram datasets)
list_of_DK_dataset_paths = doccano.get_all_dataset_paths(data_directory) # Finds all datasets within this folderstructure that ends with '_YT.jl', '_SPIDER.jl', '_MANUAL.jl' or '_TELEGRAM.jl'

# Step 3: Prepare said datasets for doccano
for dataset_path in list_of_DK_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=TEST_keywords) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)