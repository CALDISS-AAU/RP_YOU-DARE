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
keywords_raw = """"""
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
from_date = '2022-06-01'
to_date  = '2025-06-30'

# Step 2: Find all datasets that should be prepared for doccano
data_dir = '/work/YOU-DARE/scrapers/data/Italy' # All datasets for the TEST-country (could also be e.g. '/work/YOU-DARE/scrapers/data/TEST_COUNTRY/Telegram' if one only want to prepare telegram datasets)
list_of_IT_dataset_paths = doccano.get_all_dataset_paths(data_dir) # Finds all datasets within this folderstructure that ends with '_YT.jl', '_SPIDER.jl', '_MANUAL.jl' or '_TELEGRAM.jl'

# Exclude
drop = [
        '',
        '',
        '',
        '',
        '',
        ''
]

list_of_IT_dataset_paths = [path for path in list_of_UK_dataset_paths if path not in drop]

# Step 3: Prepare said datasets for doccano
# for dataset_path in list_of_IT_dataset_paths:
#     doccano.prepare_data_for_doccano(dataset_path, keywords=keywords, from_date=from_date) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)

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
### Gioventu Nazionale ###
gioventu_from_date = '2020-01-01'
gioventu_dir = '/work/YOU-DARE/scrapers/data/Italy/gioventu_nazionale_SPIDER'
list_of_gioventu_dataset_path = doccano.get_all_dataset_paths(gioventu_dir)

for dataset_path in list_of_gioventu_dataset_path:
    doccano.prepare_data_for_doccano(dataset_path, from_date=gioventu_from_date, to_date=to_date)

### Provita ###
provita_dir = '/work/YOU-DARE/scrapers/data/Italy/pro_vita_e_famiglia_playwright_SPIDER'
list_of_provita_dataset_path = doccano.get_all_dataset_paths(provita_dir)

for dataset_path in list_of_provita_dataset_path:
    doccano.prepare_data_for_doccano_ranges(dataset_path)

### Blocco Studentesco ###
blocco_dir = '/work/YOU-DARE/scrapers/data/Italy/blocco_studentesco_SPIDER'
blocco_keywords_raw = """genere, femminismo, LGBT, aborto, virilità"""
blocco_keywords = [w.strip() for w in blocco_keywords_raw.split(",")]
blocco_list_path = docca.get_all_dataset_paths(blocco_dir)

for dataset_path in blocco_list_path:
    doccano.prepare_data_for_doccano(dataset_path, keywords=blocco_keywords)

### Comunita' militante dei dodici raggi, Do.ra. ###
dodiciraggi_keywords_raw = """genere, sessualità, sesso, mascolinità, virilità, LGBT, omosessualità, trans, transgender, transidentità, transizione, fluidità, aborto, 194, mamma, papa', madre, padre, genitori genitore, genitorialità, famiglia, bambini, matrimonio, demografia, ormoni, PMA, Procreazione medicalmente assistita, GPA, gestazione per altri, utero, donna, donne, religione, cristiano, cristiana, secolarizzazione, Islam, islamizzazione, velo, burqa, violenze sessuali, stupro, molestie, femminismo, femministe, grande sostituzione, natalità, studi di genere, lavoro femminile, madri lavoratrici"""
dodiciraggi_keywords = [w.strip() for w in dodiciraggi_keywords_raw.split(",")]
dodiciraggi_dir = '/work/YOU-DARE/scrapers/data/Italy/Telegram/dodiciraggi'
dodiciraggi_list_path = doccano.get_all_dataset_paths(dodiciraggi_dir)

for dataset_path in dodiciraggi_list_path:
    doccano.prepare_data_for_doccano(dataset_path, keywords=dodiciraggi_keywords, from_date=from_date, to_date=from_date)

### Lealta Azione ###
lealta_azione_dir = '/work/YOU-DARE/scrapers/data/Italy/lealta_azione_YT'
lealta_keywords_raw = """genere, sessualità, sesso, mascolinità, virilità, LGBT, omosessualità, trans, transgender, transidentità, transizione, fluidità, aborto, 194, mamma, papa', madre, padre, genitori genitore, genitorialità, famiglia, bambini, matrimonio, demografia, ormoni, PMA, Procreazione medicalmente assistita, GPA, gestazione per altri, utero, donna, donne, religione, cristiano, cristiana, secolarizzazione, Islam, islamizzazione, velo, burqa, violenze sessuali, stupro, molestie, femminismo, femministe, grande sostituzione, natalità, studi di genere, lavoro femminile, madri lavoratrici"""
lealta_keywords = [w.strip() for w in lealta_keywords_raw.split(",")]
lealta_azione_dataset_list_path = doccano.get_all_dataset_paths(lealta_azione_dir)

for dataset_path in lealta_azione_dataset_list_path:
    doccano.prepare_data_for_doccano(dataset_path, keywords=lealta_keywords)

### Isabella Tovaglieri ###
isabella_dir = '/work/YOU-DARE/scrapers/data/Italy/isabella_tovaglieri_YT'
isabella_list_dataset_path = doccano.get_all_dataset_paths(isabella_dir)
isabella_from_date = '2024-01-01'
isabella_to_date = '2025-06-06'

isabella_kw_raw = """genere, sessualità, sesso, mascolinità, virilità, LGBT, LGBTQ, omosessualità, trans, transgender, transidentità, transessualita',  transizione, fluidità, aborto, 194 , mamma, papa', madre, padre, genitori, genitore, genitorialità, famiglia, bambini, matrimonio, demografia, ormoni, PMA, Procreazione, medicalmente, assistita, GPA,  gestazione per altri, donna, donne, religione, secolarizzazione, Islam, islamizzazione, velo, burqa, violenze, sessuali, stupro, molestie, femminismo,  femministe, grande, sostituzione, natalità, studi di genere, lavoro femminile, madri lavoratrici"""
isabella_kw = [w.strip() for w in isabella_kw_raw.split(',')]

for dataset_path in isabella_list_dataset_path:
        docanno.prepare_data_for_doccano(dataset_path, from_date=isabella_from_date, to_date=isabella_to_date, keywords=isabella_kw)

### Family day ###
fam_day_dir = '/work/YOU-DARE/scrapers/data/Italy/familyday_dynamic_SPIDER'
fam_day_list_dataset_path = doccano.get_all_dataset_paths(fam_day_dir)

fam_day_from_date = '2024-06-01'

for dataset_path in fam_day_list_dataset_path:
        docanno.prepare_data_for_doccano(dataset_path, from_date=fam_day_from_date, to_date=to_date)

### Casa Pound ###
cp_dir = '/work/YOU-DARE/scrapers/data/Italy/casa_pound_italia_SPIDER'
cp_dataset_path = doccano.get_all_dataset_paths(cp_dir)

cp_from_date = '2022-06-01'
cp_from_date = '2025-06-30'

cp_kw_raw = """genere, sessualità, sesso, mascolinità, virilità, LGBT, LGBTQ, omosessualità, trans, trasessualita',  transgender, transidentità, transizione, fluidità, aborto, 194, madre, padre, mamma, papà,  genitori, genitore, genitorialità, famiglia, bambini, matrimonio, demografia, ormoni, PMA, Procreazione medicalmente assistita, GPA,  gestazione per altri, donna, donne, religione, secolarizzazione, Islam, islamizzazione, velo, burqa, violenze sessuali, stupro, molestie, femminismo, femministe, grande sostituzione, natalità, studi di genere, lavoro femminile, madri lavoratrici"""
cp_kw = [w.strip for w in cp_kw_raw.split(',')]

for dataset_path in cp_dataset_path:
        docanno.prepare_data_for_doccano(dataset_path, from_date=cp_from_date, to_date=cp_from_date, keywords=cp_kw)

### La Rete dei Patrioti ###
lrdp_dir = '/work/YOU-DARE/scrapers/data/Italy/Telegram/retedeipatrioti'
lrdp_list_dataset_path = docanno.get_all_dataset_paths(lrdp_dir)

lrdp_kw_raw = """genere, sessualità, sesso, mascolinità, virilità, LGBT, LGBTQ, omosessualità, trans, transgender, transidentità, transizione, transessualita', fluidità, aborto, 194, ,madre, padre, mamma, papà, genitori, genitore, genitorialità, famiglia, bambini, matrimonio, demografia, ormoni, PMA, Procreazione medicalmente assistita, GPA,  gestazione per altri, donna, donne, religione, secolarizzazione, Islam, islamizzazione, velo, burqa, violenze sessuali, stupro, molestie, femminismo, femministe, grande sostituzione, natalità, studi di genere, lavoro femminile, madri lavoratrici"""
lrdp_kw = [w.strip() for w in lrdp_kw_raw.split(',')]

for dataset_path in lrdp_list_dataset_path:
        docanno.prepare_data_for_doccano(dataset_path, from_date=from_date, to_date=to_date, keywords=lrdp_kw)


### Yasmin Pani ###

yp_dir = '/work/YOU-DARE/scrapers/data/Italy/yasmin_pani_YT'
yp_list_dataset_path = doccano.get_all_dataset_paths(yp_dir)

yp_kw_raw = """schwa, asterischi, neutro, sessismo, incel, politicamente corretto, genere, sessualità, sesso, mascolinità, virilità LGBT, LGBTQ, omosessualità, trans, transgender, transidentità, trasnessualita', transizione, fluidità, aborto, 194, mamma, papa', madre, padre, mamma, papà, genitori, genitore, genitorialità, famiglia, bambini,  matrimonio, demografia, ormoni, PMA, Procreazione medicalmente assistita, GPA,  gestazione per altri, donna, donne, religione, secolarizzazione, Islam, islamizzazione, velo, burqa, violenze sessuali, stupro, molestie, femminismo, femministe, femminista, grande sostituzione, natalità, studi di genere, lavoro femminile, madri lavoratrici"""
yp_kw = [w.strip() for w in yp_kw_raw.split(',')]

for dataset_path in yp_list_dataset_path:
        docanno.prepare_data_for_doccano(dataset_path, from_date=from_date, to_date=to_date, keywords=yp_kw)

### La Fionda ###
la_fionda_dir = '/work/YOU-DARE/scrapers/data/Italy/Telegram/lafionda'
la_fionda_dataset_path = doccano.get_all_dataset_paths(la_fionda_dir)

la_fionda_from_date = '2024-06-01'

for dataset_path in la_fionda_dataset_path:
        doccano.prepare_data_for_doccano(dataset_path, from_date=la_fionda_from_date, to_date=to_date)

### Il Redpillatore ###
redpill_dir = '/work/YOU-DARE/scrapers/data/Italy/redpillatore_IT_SPIDER'
repill_dataset_list_path = doccano.get_all_dataset_paths(redpill_dir)

for dataset_path in repill_dataset_list_path:
        doccano.prepare_data_for_doccano(dataset_path)

### Uomini e Donne in Movimento ###
uomini_dir = '/work/YOU-DARE/scrapers/data/Italy/uominiedonne_static_SPIDER'

uomini_dataset_list_path = doccano.get_all_dataset_paths(uomini_dir)

for dataset_path in uomini_dataset_list_path:
        doccano.prepare_data_for_doccano(dataset_path, from_date=from_date, to_date=to_date)

### I Rami Spogli ###
rami_spogli_dir = '/work/YOU-DARE/scrapers/data/Italy/rami_spogli_SPIDER'

rami_spogli_list_dataset_path = doccano.get_all_dataset_paths(rami_spogli_dir)

for dataset_path in rami_spogli_list_dataset_path:
        doccano.prepare_data_for_doccano(dataset_path)

### Essere Uomo ###
essere_uomo_dir = './YOU-DARE/scrapers/data/Italy/essere_uomo_YT'

essere_uomo_dataset_list_path = doccano.get_all_dataset_paths(essere_uomo_dir)

for dataset_path in essere_uomo_dataset_list_path:
        doccano.prepare_data_for_doccano(dataset_path, from_date=la_fionda_from_date, to_date=to_date)