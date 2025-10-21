from .functions.functions import Doccano_Functions, Transcriber_data_Functions
from .functions.YT_name_FIXER import JLFileRenamer
import pathlib

''' To run this scraper from bash do the following:
        python -m YOU-DARE.doccano.prep_script
'''

doccano = Doccano_Functions()
transcriber_prep = Transcriber_data_Functions()
# file_renamer = JLFileRenamer()

def get_all_dataset_paths(data_directory):
    list_of_all_datasets = []
    list_of_datasets_SPIDER = list(pathlib.Path(data_directory).rglob('*_SPIDER.jl'))
    list_of_datasets_MANUAL = list(pathlib.Path(data_directory).rglob('*_MANUAL.jl'))
    list_of_datasets_YT = list(pathlib.Path(data_directory).rglob('*_YT.jl'))
    list_of_datasets_TELEGRAM = list(pathlib.Path(data_directory).rglob('*_TELEGRAM.jl'))
    list_of_all_datasets = list_of_datasets_SPIDER + list_of_datasets_MANUAL + list_of_datasets_YT + list_of_datasets_TELEGRAM
    list_of_all_datasets = list(map(str, list_of_all_datasets))
    return list_of_all_datasets

def generate_YT_datasets(data_directory):
    list_of_YouTube_datasets = list(pathlib.Path(data_directory).rglob('*_YT'))
    list_of_YouTube_datasets = list(map(str, list_of_YouTube_datasets))
    
    for directory in list_of_YouTube_datasets:
        dataset_path = f'{directory}/videos.jl'
        transcriptions_dir = f'{directory}/transcribed'
        print(f'dataset: {dataset_path}, directory: {transcriptions_dir}')
        transcriber_prep.add_transcribed_text_to_video_data(dataset_path, transcriptions_dir)

    print(list_of_YouTube_datasets)

### Denmark ###
danish_keywords = [
    '*MeToo',
    'Abort',
    'Befolkningstal',
    'Biologi',
    'Børn',
    'Burqua',
    'Demografi',
    'Feminine', 
    'Feminisme',
    'Feminister', 
    'Flydende',
    'Fødselsrate',
    'Forældre',
    'Forældremyndighed', 
    'Homoseksuelle', 
    'Hormoner',
    'Identitetskrise', 
    'Indvandrer', 
    'Islam',
    'Køn',
    'Kønsideologi',
    'Konspiration',
    'Kønsskifte', 
    'Kønsstudier',
    'Kønsidentitet',
    'Kønsskifte',
    'Kriminelle', 
    'Kvinde',
    'kvindelige arbejde',
    'kvinder', 
    'LGB',
    'LGBTQ',
    'Ligestilling',
    'Mandlig',
    'Maskulinitet',
    'Mor', 
    'Far',
    'Muslim', 
    'Muslimer',
    'Migration', 
    'Mænd',
    'Omsorg',
    'Opdragelse', 
    'Pædofil',
    'Pædofili',
    'Race',
    'Religion', 
    'Remigration', 
    'Samtykkelov',
    'Seksual undervisning', 
    'Sekulær',
    'Sex',
    'Sexualitet', 
    'Sexchikane',
    'Sexforbrydelse',
    'Skilsmisse',
    'Social kontrol',
    'Sofie Linde',
    'Tørklæde',
    'Trans', 
    'Transkønnede', 
    'Transpersoner', 
    'Undertrykkelse',
    'Velfærdsstat', 
    'voldtægt',
    'Woke',
    'Wokeisme',
]
danish_data_directory = '/work/YOU-DARE/scrapers/data/Denmark' # All datasets for Denmark
generate_YT_datasets(danish_data_directory)
print(f'\n\n\n#### All youtube-datasets has been generated ####\n\n\n')
list_of_Danish_dataset_paths = get_all_dataset_paths(danish_data_directory)

for dataset_path in list_of_Danish_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=danish_keywords)

### France ###
french_keywords = [
    'genre',
    'sexualité', 
    'sexe', 
    'masculinité', 
    'virilité', 
    'LGBT', 
    'homosexualité', 
    'trans', 
    'transgenre', 
    'transidentité', 
    'transition', 
    'fluidité', 
    'mère', 
    'père', 
    'Parents', 
    'parentalité', 
    'famille', 
    'enfants', 
    'mariage', 
    'démographie', 
    'hormones', 
    'PMA',
    'Procréation médicalement assistée',  
    'GPA',
    'Gestation pour autrui', 
    'femme', 
    'laïcité', 
    'sécularisation',  
    'voile', 
    'burqua', 
    'burkini', 
    'séduction', 
    'viande', 
    'sport',  
    'muscles', 
    'violences sexuelles', 
    'viol', 
    'harcèlement', 
    'harcèlement de rue', 
    'féminisme', 
    'féministes', 
    'grand remplacement', 
    'natalité', 
    'études de genre', 
    'salaire maternelle', 
    'travail des femmes', 
    'mères travailleuses', 
]
french_data_directory = '/work/YOU-DARE/scrapers/data/France' # All datasets for France
generate_YT_datasets(french_data_directory)
list_of_French_dataset_paths = get_all_dataset_paths(french_data_directory)

for dataset_path in list_of_French_dataset_paths:
    doccano.prepare_data_for_doccano(dataset_path, keywords=french_keywords)