from .functions.functions import Doccano_Functions

''' To run this scraper from bash do the following:
        python -m YOU-DARE.doccano.prep_script_SPAIN
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
SPAIN_keywords_raw = """*real*; *biológ*; *biolog*; *natural*; binari*; *sex*; ideología de género; dos sexos; matern*; niñ*; casa*; cuidados; derecho*; custodia*; *género*; *genero*; *masculi*; fuer*; cuerpo; múscul*; muscul*; *femen*; *femin*; madre*; padre*; *sensib*; *afect*; dulce; dulzura; gay; lesbi*; maric*; boller*; trans*; lobb*; pecado; dios; iglesia*; católic; catolic*; mezquita*; wok*; *igual*; médic*; medic*; enferm*; hormon*; baño*; lavabo*; adolescen*; cárcel*; carcel*; prisión*; prision*; preso*; *famil*; matrim*; hetero*; homo*; descend*; herenci*; hered*; legítim*; legitim*; deber*; violen*; consen*; viola*; agresi*; dañ*; víctim*; victim*; domést*; domest*; cuota*; misógin*; misogin*; misandr*; zorr*; puta*; *vergüenz*; *verguenz*; mentir*; verdad*; asesin*; mantenid*; charo; charidad; ofendid*; fals*; discrimina*; brecha*; *abort*; vida*; neonato*; concepció*; concepcio*; reproduc*; *vitro; subrog*; mora*; moro*; *migrant*; extranjer*; *jamón*; *jamon*; patera*; delincuen*; musulm*; islam*; abuel*; *landia; barriga*; vientre*; conej*; rata*; *democr*; escuela*; coleg*; *doctrin*; escolar*; hombre*; mujer*; *coloni*; imperi*; universi*; profesor*; guarr*; piojo*; pater*; patriarc*; matriarc*; incel*; alfa*; beta*; hipergamia; mach*; ruin*; crist*; papá*; papa*; mamá*; mama*; laic*; *conquist*; españ*; europ*; *reemplaz*; *natal*; invasi*; invierno demográfico; invierno demografico; nacimient*; nacid*; bebe*; cruzada*; verja*; fronter*; melill*; ceut*; amenaz*; muro*; *patria*; *legal*; blanc*; negr*; marruecos; marroquí*; marroqui*; áfrica*; africa*; terroris*"""
SPAIN_keywords = [w.strip() for w in SPAIN_keywords_raw.split(";")]
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
SPAIN_from_date = '2017-01-01'
SPAIN_to_date = '2025-06-30'

# Step 2: Find all datasets that should be prepared for doccano
SPAIN_data_directory = '/work/YOU-DARE/scrapers/data/Spain' # All datasets for the TEST-country (could also be e.g. '/work/YOU-DARE/scrapers/data/TEST_COUNTRY/Telegram' if one only want to prepare telegram datasets)
list_of_SPAIN_dataset_paths = doccano.get_all_dataset_paths(SPAIN_data_directory) # Finds all datasets within this folderstructure that ends with '_YT.jl', '_SPIDER.jl', '_MANUAL.jl' or '_TELEGRAM.jl'

# Step 3: Prepare said datasets for doccano
for dataset_path in list_of_SPAIN_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=SPAIN_keywords, from_date=SPAIN_from_date, to_date=SPAIN_to_date) # Prepares all datasets for doccano - OnLy required argument is a input_file_path (for more info hold over the function or have a look at the function here: /work/YOU-DARE/doccano/functions/functions.py)

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
### CATALUNYAAC TELEGRAM ###
CATALUNYAAC_keywords_raw = """*real*;*biològ*; *biolog*; *natural*; binari*; *sex*; ideologia de gènere; dos sexes; matern*; nen*; casa*; cures; dret*; custòdi*; *gènere*; *genere*; *masculí*; *masculi*; fort*; força; forces; cos; múscul*; muscul*; *femen*; *femin*; mare*; pare*; sensib*; *afect*; dolç*; gay; lesbi*; maric*; mariet*; boller*; trans*; lobb*; pecat*; deu; divi*; diví; esglesi*; catòlic*; catolic*; mesquit*; wok*; *igual*; mèdic*; medic*; malalt*; hormon*; bany*; lavabo*; adolescen*; càrcel*; carcel*; preso*; *famíl*; *famil*; matrim*; hetero; homo*; descend*; herenci*; hereu*; herev*; legítim*; legitim*; deure*; violèn*; violen*; consen*; viola*; agressi*; dany*; víctim*; victim*; domèst*; domest*; quot*; misogin*; misandr*; zorr*; puta; putes; *vergony*; mentid*; veritat*; assassi*; manting*; charo; charitat; charidad; ofendid*; ofes*; fals*; discrimina*; bretx*; *avort*; vida; nounat*; concepció*; concepcio*; reproduc*; *vitro; subrog*; mora*; moro*; *migrant*; estranger*; *pernil*; *jamón*; *jamon*; patera*; delinquèn*; delinquen*; musulm*; islam*; avi*; *landia; panx*; ventre*; conill*; rata*; *democr*; escola*; col·leg*; *doctrin*; escolar*; home*; dona; dones; *coloni*; imperi*; universi*; professor*; guarr*; piojo*; pater*; patriarc*; matriarc*; incel*; alfa*; beta*; hipergamia; mascl*; ruin*; crist*; papa*; mama*; laic*; *conquest*; espany*; europ*; catalu*; català*; catala*; *reemplaç*; *natal*; invasi*; hivern demogràfic; hivern demografic; naixement*; nascu*; bebe*; croad*; reixat*; fronter*; melill*; ceut*; amenaç*; muro*; *pàtria*; *patria*; *legal*; blanc*; negr*; marroc; marroquí*; marroqui*; àfrica*; africa*; terroris*"""
CATALUNYAAC_keywords = [w.strip() for w in CATALUNYAAC_keywords_raw.split(";")]

CATALUNYAAC_data_directory = '/work/YOU-DARE/scrapers/data/Spain/Telegram/catalunyaac' # Only the single source folder
list_of_CATALUNYAAC_dataset_paths = doccano.get_all_dataset_paths(CATALUNYAAC_data_directory) 

for dataset_path in list_of_CATALUNYAAC_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=CATALUNYAAC_keywords, from_date=SPAIN_from_date, to_date=SPAIN_to_date)

### ANTHONY COREY SANCHEZ YOUTUBE ###
ANTHONY_COREY_SANCHEZ_keywords_raw = """*real*;*biològ*; *biolog*; *natural*; binari*; *sex*; ideologia de gènere; dos sexes; matern*; nen*; casa*; cures; dret*; custòdi*; *gènere*; *genere*; *masculí*; *masculi*; fort*; força; forces; cos; múscul*; muscul*; *femen*; *femin*; mare*; pare*; sensib*; *afect*; dolç*; gay; lesbi*; maric*; mariet*; boller*; trans*; lobb*; pecat*; deu; divi*; diví; esglesi*; catòlic*; catolic*; mesquit*; wok*; *igual*; mèdic*; medic*; malalt*; hormon*; bany*; lavabo*; adolescen*; càrcel*; carcel*; preso*; *famíl*; *famil*; matrim*; hetero; homo*; descend*; herenci*; hereu*; herev*; legítim*; legitim*; deure*; violèn*; violen*; consen*; viola*; agressi*; dany*; víctim*; victim*; domèst*; domest*; quot*; misogin*; misandr*; zorr*; puta; putes; *vergony*; mentid*; veritat*; assassi*; manting*; charo; charitat; charidad; ofendid*; ofes*; fals*; discrimina*; bretx*; *avort*; vida; nounat*; concepció*; concepcio*; reproduc*; *vitro; subrog*; mora*; moro*; *migrant*; estranger*; *pernil*; *jamón*; *jamon*; patera*; delinquèn*; delinquen*; musulm*; islam*; avi*; *landia; panx*; ventre*; conill*; rata*; *democr*; escola*; col·leg*; *doctrin*; escolar*; home*; dona; dones; *coloni*; imperi*; universi*; professor*; guarr*; piojo*; pater*; patriarc*; matriarc*; incel*; alfa*; beta*; hipergamia; mascl*; ruin*; crist*; papa*; mama*; laic*; *conquest*; espany*; europ*; catalu*; català*; catala*; *reemplaç*; *natal*; invasi*; hivern demogràfic; hivern demografic; naixement*; nascu*; bebe*; croad*; reixat*; fronter*; melill*; ceut*; amenaç*; muro*; *pàtria*; *patria*; *legal*; blanc*; negr*; marroc; marroquí*; marroqui*; àfrica*; africa*; terroris*"""
ANTHONY_COREY_SANCHEZ_keywords = [w.strip() for w in ANTHONY_COREY_SANCHEZ_keywords_raw.split(";")]

ANTHONY_COREY_SANCHEZ_data_directory = '/work/YOU-DARE/scrapers/data/Spain/antony_sanchez_YT' # Only the single source folder
list_of_ANTHONY_COREY_SANCHEZ_dataset_paths = doccano.get_all_dataset_paths(ANTHONY_COREY_SANCHEZ_data_directory)

for dataset_path in list_of_ANTHONY_COREY_SANCHEZ_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=ANTHONY_COREY_SANCHEZ_keywords, from_date=SPAIN_from_date, to_date=SPAIN_to_date)

### LA CATALUNYA WOKE YOUTUBE ###
LA_CATALUNYA_WOKE_keywords_raw = """*real*;*biològ*; *biolog*; *natural*; binari*; *sex*; ideologia de gènere; dos sexes; matern*; nen*; casa*; cures; dret*; custòdi*; *gènere*; *genere*; *masculí*; *masculi*; fort*; força; forces; cos; múscul*; muscul*; *femen*; *femin*; mare*; pare*; sensib*; *afect*; dolç*; gay; lesbi*; maric*; mariet*; boller*; trans*; lobb*; pecat*; deu; divi*; diví; esglesi*; catòlic*; catolic*; mesquit*; wok*; *igual*; mèdic*; medic*; malalt*; hormon*; bany*; lavabo*; adolescen*; càrcel*; carcel*; preso*; *famíl*; *famil*; matrim*; hetero; homo*; descend*; herenci*; hereu*; herev*; legítim*; legitim*; deure*; violèn*; violen*; consen*; viola*; agressi*; dany*; víctim*; victim*; domèst*; domest*; quot*; misogin*; misandr*; zorr*; puta; putes; *vergony*; mentid*; veritat*; assassi*; manting*; charo; charitat; charidad; ofendid*; ofes*; fals*; discrimina*; bretx*; *avort*; vida; nounat*; concepció*; concepcio*; reproduc*; *vitro; subrog*; mora*; moro*; *migrant*; estranger*; *pernil*; *jamón*; *jamon*; patera*; delinquèn*; delinquen*; musulm*; islam*; avi*; *landia; panx*; ventre*; conill*; rata*; *democr*; escola*; col·leg*; *doctrin*; escolar*; home*; dona; dones; *coloni*; imperi*; universi*; professor*; guarr*; piojo*; pater*; patriarc*; matriarc*; incel*; alfa*; beta*; hipergamia; mascl*; ruin*; crist*; papa*; mama*; laic*; *conquest*; espany*; europ*; catalu*; català*; catala*; *reemplaç*; *natal*; invasi*; hivern demogràfic; hivern demografic; naixement*; nascu*; bebe*; croad*; reixat*; fronter*; melill*; ceut*; amenaç*; muro*; *pàtria*; *patria*; *legal*; blanc*; negr*; marroc; marroquí*; marroqui*; àfrica*; africa*; terroris*"""
LA_CATALUNYA_WOKE_keywords = [w.strip() for w in LA_CATALUNYA_WOKE_keywords_raw.split(";")]

LA_CATALUNYA_WOKE_data_directory = '/work/YOU-DARE/scrapers/data/Spain/la_catalunya_woke_YT' # Only the single source folder
list_of_LA_CATALUNYA_WOKE_dataset_paths = doccano.get_all_dataset_paths(LA_CATALUNYA_WOKE_data_directory)

for dataset_path in list_of_LA_CATALUNYA_WOKE_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=LA_CATALUNYA_WOKE_keywords, from_date=SPAIN_from_date, to_date=SPAIN_to_date)

### VOX YOUTUBE ###
VOX_ranges = [
   #(from, to),
    ('2017-03-01','2017-03-31'),
    ('2017-06-15','2017-07-14'),
    ('2018-03-01','2018-03-31'),
    ('2018-06-15','2018-07-14'),
    ('2019-03-01','2019-07-14'),
    ('2019-10-10','2019-12-10'),
    ('2020-03-01','2020-03-31'),
    ('2020-06-15','2020-07-14'),
    ('2021-03-01','2021-03-31'),
    ('2021-06-15','2021-07-14'),
    ('2022-03-01','2022-03-31'),
    ('2022-06-15','2022-07-14'),
    ('2023-03-01','2023-03-31'),
    ('2023-06-15','2023-08-23'),
    ('2024-03-01','2024-03-31'),
    ('2024-05-09','2024-07-14'),
    ('2025-03-01','2025-03-31'),
    ('2025-06-15','2025-07-14'),
]

VOX_data_directory = '/work/YOU-DARE/scrapers/data/Spain/vox_espana_YT' # Only the single source folder
list_of_VOX_dataset_paths = doccano.get_all_dataset_paths(VOX_data_directory)

for dataset_path in list_of_VOX_dataset_paths:
    doccano.prepare_data_for_doccano_ranges(dataset_path, date_ranges=VOX_ranges, keywords=SPAIN_keywords)