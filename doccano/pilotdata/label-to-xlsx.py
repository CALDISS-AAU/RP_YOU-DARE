import json
import pandas as pd
from os.path import join

# JSON paths
data_dir = join('/home', 'kgk', 'caldiss-sharepoint', '[RP] YOU-DARE', 'data', 'doccano_strato_backup')

dk_labs_p = join(data_dir, 'dk_labels.json')
fr_labs_p = join(data_dir, 'fr_labels.json')

actual_labels_p = join(data_dir, '..', '..', 'wp2', 'labels', 'annotation_labels_doccano.json')

# read JSON labels
dk_labs = pd.read_json(dk_labs_p, orient = 'records')
fr_labs = pd.read_json(fr_labs_p, orient = 'records')

actual_labs = pd.read_json(actual_labels_p, orient='records')

# subset
dk_labs = dk_labs[['id', 'text']].rename(columns={'text': 'old label'})
fr_labs = fr_labs[['id', 'text']].rename(columns={'text': 'old label'})

actual_labs = actual_labs[['id', 'text']].rename(columns={'text': 'label'})

# export as xlsx
dk_labs.to_excel(join(data_dir, 'dklabs.xlsx'), index = False)
fr_labs.to_excel(join(data_dir, 'frlabs.xlsx'), index = False)
actual_labs.to_excel(join(data_dir, 'actuallabs.xlsx'), index = False)