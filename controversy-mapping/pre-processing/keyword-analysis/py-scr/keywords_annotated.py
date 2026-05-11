#!/usr/bin/env python3
from pathlib import Path
import os
from dotenv import load_dotenv

import pandas as pd
import numpy as np
import spacy
import stanza
from collections import Counter

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


# from spacy.lang.fr.stop_words import STOP_WORDS
# Stanza on my fat face
stanza.download("sv")


# data
SE_data = pd.read_csv(str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "data" / "work" / "SE_annotated_labels_flat.csv"))
ES_data = pd.read_csv(str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "data" / "work" / "ES_annotated_labels_flat.csv"))
FR_data = pd.read_csv(str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "data" / "work" / "FR_annotated_labels_flat.csv"))
HU_data = pd.read_csv(str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "data" / "work" / "HU_annotated_labels_flat.csv"))
RO_data = pd.read_csv(str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "data" / "work" / "RO_annotated_labels_flat.csv"))
UK_data = pd.read_csv(str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "data" / "work" / "UK_annotated_labels_flat.csv"))

'''
X: LGBTQ/Transgender/Homosexuality

    Homosexuality and LGBTQ+ issues

    Transpersons rights and trans-rights

    Gender transitioning minors/children

Y: Migration

    Great Replacement, Falling birth rates, demographic winter

    Remigration

Z: Gender

    Gender as ideology and academic freedom

    Gender equality, quotas

    Gender roles

    Gender Essentialism (there are only 2 sexes)
'''
# Label handling 
label_mapping = {
    'Homosexuality and LGBTQ+ issues': 'LGBTQ/Transgender/Homosexuality',
    'Transpersons rights and trans-rights': 'LGBTQ/Transgender/Homosexuality',
    'Gender transitioning minors/children': 'LGBTQ/Transgender/Homosexuality',
    'Great Replacement': 'Migration',
    'Falling birth rates': 'Migration',
    'demographic winter': 'Migration',
    'Remigration': 'Migration',
    'Gender as ideology and academic freedom': 'Gender',
    'Gender equality, quotas': 'Gender',
    'Gender roles': 'Gender',
    'Gender Essentialism': 'Gender'
}

# UK
UK_data['new_labels'] = UK_data['label'].map(label_mapping)
UK_Gender = UK_data.loc[UK_data['new_labels'] == 'Gender']
UK_Migration = UK_data.loc[UK_data['new_labels'] == 'Migration']
UK_LGBTQ = UK_data.loc[UK_data['new_labels'] == 'LGBTQ/Transgender/Homosexuality']

# RO
RO_data['new_labels'] = RO_data['label'].map(label_mapping)
RO_Gender = RO_data.loc[RO_data['new_labels'] == 'Gender']
RO_Migration = RO_data.loc[RO_data['new_labels'] == 'Migration']
RO_LGBTQ = RO_data.loc[RO_data['new_labels'] == 'LGBTQ/Transgender/Homosexuality']

# FR
FR_data['new_labels'] = FR_data['label'].map(label_mapping)
FR_Gender = FR_data.loc[FR_data['new_labels'] == 'Gender']
FR_Migration = FR_data.loc[FR_data['new_labels'] == 'Migration']
FR_LGBTQ = FR_data.loc[FR_data['new_labels'] == 'LGBTQ/Transgender/Homosexuality']

# SE
SE_data['new_labels'] = SE_data['label'].map(label_mapping)
SE_Gender = SE_data.loc[SE_data['new_labels'] == 'Gender']
SE_Migration = SE_data.loc[SE_data['new_labels'] == 'Migration']
SE_LGBTQ = SE_data.loc[SE_data['new_labels'] == 'LGBTQ/Transgender/Homosexuality']

# ES
ES_data['new_labels'] = ES_data['label'].map(label_mapping)
ES_Gender = ES_data.loc[ES_data['new_labels'] == 'Gender']
ES_Migration = ES_data.loc[ES_data['new_labels'] == 'Migration']
ES_LGBTQ = ES_data.loc[ES_data['new_labels'] == 'LGBTQ/Transgender/Homosexuality']

# HU
HU_data['new_labels'] = HU_data['label'].map(label_mapping)
HU_Gender = HU_data.loc[HU_data['new_labels'] == 'Gender']
HU_Migration = HU_data.loc[HU_data['new_labels'] == 'Migration']
HU_LGBTQ = HU_data.loc[HU_data['new_labels'] == 'LGBTQ/Transgender/Homosexuality']


nlp = spacy.load("en_core_web_trf")
nlp = spacy.load("ro_core_news_lg")
nlp = spacy.load("fr_dep_news_trf")
nlp = spacy.load("sv_core_news_lg")
nlp = spacy.load("es_dep_news_trf")

# Bigrams
# Add the merger to the pipeline
nlp.add_pipe("merge_noun_chunks")

# Make Hungarian Stanza Again
nlp = stanza.Pipeline(
    "sv",
    processors="tokenize,pos,lemma",
    tokenize_no_ssplit=True,
    use_gpu=True
)

# Functions
def get_label_nouns(dataframe, n=25):
    '''
    Being a baddie function that captures nouns from each sentence within a desired label uwu
    uses lemmatization for removing extra filth fr
    Parameters: can-do attitude, dataframe of your choice (all fax, no printer) & desired top n (int pweaz)
    '''
    counter = Counter()
    for doc in nlp.pipe(dataframe['span'].astype(str), batch_size=32, disable=['parser', 'ner']):
        nouns = [token.lemma_.lower() for token in doc if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop]

        counter.update(nouns)
    return counter.most_common(n)


def extract_pos(dataframe, n=40):
    counter = Counter()
    for doc in nlp.pipe(dataframe['span'].astype(str), batch_size=32, disable=['parser', 'ner']):
        POS_words = [f'{token.lemma_.lower()} ({token.pos_})' for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'PROPN'] and not token.is_stop]

        counter.update(POS_words)
    
    
    return counter.most_common(n)


# Stanza version plz no touch
def get_label_nouns_stanza(dataframe, n=25):
    counter = Counter()

    for text in dataframe["span"].astype(str):
        doc = nlp(text)

        nouns = [
            word.lemma.lower()
            for sent in doc.sentences
            for word in sent.words
            if word.upos in {"NOUN", "PROPN"}
        ]

        counter.update(nouns)

    return counter.most_common(n)

def extract_pos_stanza(dataframe, n=40):
    counter = Counter()

    for text in dataframe['span'].astype(str):
        doc = nlp(text)

        
        POS_words = [
            f"{word.lemma.lower()} ({word.upos})" 
            for sent in doc.sentences
            for word in sent.words
            if word.upos in {"NOUN", "VERB", "ADJ", "PROPN"}
        ]
        
        counter.update(POS_words)
    
    return counter.most_common(n)

def save_top_nouns(list, outfile):
    """
    Converts the Counter list of tuples into a CSV file.
    """
    df = pd.DataFrame(list, columns=['Nouns', 'Frequency'])
    df.to_csv(outfile, index=False, encoding='utf-8')
    return df

def save_top_pos(data_list, outfile):
    df = pd.DataFrame(data_list, columns=['Term_with_POS', 'Frequency'])
    df.to_csv(outfile, index=False, encoding='utf-8')
    print(f"Saved to {outfile}")

# UK
# Gender Nouns
top_gender_UK = get_label_nouns(UK_Gender)
save_top_nouns(top_gender_UK, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_gender_UK.csv"))
# Gender POS
Gender_POS_UK = extract_pos(UK_Gender)
save_top_pos(Gender_POS_UK, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Gender_POS_UK.csv"))
# Migration Nouns
top_migration = get_label_nouns(UK_Migration)
save_top_nouns(top_migration, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_migration_UK.csv"))
# Migration POS
Migration_POS_UK = extract_pos(UK_Migration)
save_top_pos(Migration_POS_UK, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Migration_POS_UK.csv"))
top_lgbtq = get_label_nouns(UK_LGBTQ)
save_top_nouns(top_lgbtq,str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_lgbtq_UK.csv"))
# LGTBQ POS
LGTBQ_POS_UK = extract_pos(UK_LGBTQ)
save_top_pos(LGTBQ_POS_UK, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "LGBTQ_POS_UK.csv"))

# FR
# Gender POS
Gender_POS_FR = extract_pos(FR_Gender)
save_top_pos(Gender_POS_FR, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Gender_POS_FR.csv"))
# Migration POS
Migration_POS_FR = extract_pos(FR_Migration)
save_top_pos(Migration_POS_FR, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Migration_POS_FR.csv"))
# LGBTQ POS
LGTBQ_POS_FR = extract_pos(FR_LGBTQ)
save_top_pos(LGTBQ_POS_FR, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "LGBTQ_POS_FR.csv"))

# NOUNS FR
top_gender_FR = get_label_nouns(FR_Gender)
save_top_nouns(top_gender_FR, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_gender_FR.csv"))
top_migration_FR = get_label_nouns(FR_Migration)
save_top_nouns(top_migration_FR, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_migration_FR.csv"))
top_lgbtq_FR = get_label_nouns(FR_LGBTQ)
save_top_nouns(top_lgbtq_FR, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_LGBTQ_FR.csv"))

# SWE
# Gender POS
Gender_POS_SE = extract_pos(SE_Gender)
save_top_pos(Gender_POS_SE, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Gender_POS_SE.csv"))
# Migration POS
Migration_POS_SE = extract_pos(SE_Migration)
save_top_pos(Migration_POS_SE, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Migration_POS_SE.csv"))
# LGBTQ POS
LGTBQ_POS_SE = extract_pos(SE_LGBTQ)
save_top_pos(LGTBQ_POS_SE, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "LGBTQ_POS_SE.csv"))

# SE NOUNS
top_gender_SE = get_label_nouns(SE_Gender)
save_top_nouns(top_gender_SE, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_gender_SWE.csv"))
top_migration_SE = get_label_nouns(SE_Migration)
save_top_nouns(top_migration_SE, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_migration_SWE.csv"))
top_lgbtq_SE = get_label_nouns(SE_LGBTQ)
save_top_nouns(top_lgbtq_SE, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_LGBTQ_SWE.csv"))

# ES
top_gender_ES = get_label_nouns(ES_Gender)
save_top_nouns(top_gender_ES, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_gender_ES.csv"))
top_migration_ES = get_label_nouns(ES_Migration)
save_top_nouns(top_migration_ES, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_migration_ES.csv"))
top_lgbtq_ES = get_label_nouns(ES_LGBTQ)
save_top_nouns(top_lgbtq_ES, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_LGBTQ_ES.csv"))

# Gender POS
Gender_POS_ES = extract_pos(ES_Gender)
save_top_pos(Gender_POS_ES, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Gender_POS_ES.csv"))
# Migration POS
Migration_POS_ES = extract_pos(ES_Migration)
save_top_pos(Migration_POS_ES, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Migration_POS_ES.csv"))
# LGBTQ POS
LGTBQ_POS_ES = extract_pos(ES_LGBTQ)
save_top_pos(LGTBQ_POS_ES, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "LGBTQ_POS_ES.csv"))

# HU
top_gender_HU = get_label_nouns_stanza(HU_Gender)
save_top_nouns(top_gender_HU, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_gender_HU.csv"))
top_migration_HU = get_label_nouns_stanza(HU_Migration)
save_top_nouns(top_migration_HU, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_migration_HU.csv"))
top_lgbtq_HU = get_label_nouns_stanza(HU_LGBTQ)
save_top_nouns(top_lgbtq_HU, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_LGBTQ_HU.csv"))

# Gender POS
Gender_POS_HU = extract_pos_stanza(HU_Gender)
save_top_pos(Gender_POS_HU, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Gender_POS_HU.csv"))
# Migration POS
Migration_POS_HU = extract_pos_stanza(HU_Migration)
save_top_pos(Migration_POS_HU, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Migration_POS_HU.csv"))
# LGBTQ POS
LGTBQ_POS_HU = extract_pos_stanza(HU_LGBTQ)
save_top_pos(LGTBQ_POS_HU, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "LGBTQ_POS_HU.csv")) 

# RO
top_gender_RO = get_label_nouns(RO_Gender)
save_top_nouns(top_gender_RO, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_gender_RO.csv"))
top_migration_RO = get_label_nouns(RO_Migration)
save_top_nouns(top_migration_RO, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_migration_RO.csv"))
top_lgbtq_RO = get_label_nouns(RO_LGBTQ)
save_top_nouns(top_lgbtq_RO, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "top_LGBTQ_RO.csv"))

# Gender POS
Gender_POS_RO = extract_pos(RO_Gender)
save_top_pos(Gender_POS_RO, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Gender_POS_RO.csv"))
# Migration POS
Migration_POS_RO = extract_pos(RO_Migration)
save_top_pos(Migration_POS_RO, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "Migration_POS_RO.csv"))
# LGBTQ POS
LGTBQ_POS_RO = extract_pos(RO_LGBTQ)
save_top_pos(LGTBQ_POS_RO, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "LGBTQ_POS_RO.csv"))

## BIGRAMS
def extract_pos_merged(dataframe, n=40, batch_size=64):
    counter = Counter()

    for doc in nlp.pipe(
        dataframe["span"].astype(str),
        batch_size=batch_size,
        disable=["ner"]
    ):
        for chunk in doc.noun_chunks:
            clean_chunk = " ".join(
                t.lemma_.lower()
                for t in chunk
                if t.pos_ not in {"DET", "PRON"}
            ).strip()

            if clean_chunk:
                counter[f"{clean_chunk} (NOUN)"] += 1

        for t in doc:
            if t.pos_ in {"VERB", "ADJ"} and not t.is_stop:
                counter[f"{t.lemma_.lower()} ({t.pos_})"] += 1

    return counter.most_common(n)


def extract_stanza_bigrams(df, text_col="span", n=40, window=2):
    counter = Counter()

    texts = df[text_col].astype(str)

    for text in texts:
        if not text.strip():
            continue

        doc = nlp(text)

        for sent in doc.sentences:
            words = [
                (w.lemma.lower(), w.upos)
                for w in sent.words
                if w.upos in {"NOUN", "VERB", "ADJ", "PROPN"} and w.lemma
            ]

            for i in range(len(words) - window + 1):
                w1, pos1 = words[i]
                w2, pos2 = words[i + 1]

                counter[f"{w1} ({pos1}) {w2} ({pos2})"] += 1

    return counter.most_common(n)



# UK
UK_bigrams_Gender = extract_stanza_bigrams(UK_Gender)
save_top_pos(UK_bigrams_Gender, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "UK_bigrams_Gender.csv"))
UK_bigrams_Migration = extract_stanza_bigrams(UK_Migration)
save_top_pos(UK_bigrams_Migration, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "UK_bigrams_Migration.csv"))
UK_bigrams_LGBTQ = extract_stanza_bigrams(UK_LGBTQ)
save_top_pos(UK_bigrams_LGBTQ, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "UK_bigrams_LGBTQ.csv"))

# FR
FR_bigrams_Gender = extract_stanza_bigrams(FR_Gender)
save_top_pos(FR_bigrams_Gender, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "FR_bigrams_Gender.csv"))
FR_bigrams_Migration = extract_stanza_bigrams(FR_Migration)
save_top_pos(FR_bigrams_Migration, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "FR_bigrams_Migration.csv"))
FR_bigrams_LGBQT = extract_stanza_bigrams(FR_LGBTQ)
save_top_pos(FR_bigrams_LGBQT, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "FR_bigrams_LGBQT.csv"))

# RO 
RO_bigrams_Gender = extract_stanza_bigrams(RO_Gender)
save_top_pos(RO_bigrams_Gender, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "RO_bigrams_Gender.csv"))
RO_bigrams_Migration = extract_stanza_bigrams(RO_Migration)
save_top_pos(RO_bigrams_Migration, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "RO_bigrams_Migration.csv"))
RO_bigrams_LGBQT = extract_stanza_bigrams(RO_LGBTQ)
save_top_pos(RO_bigrams_LGBQT, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "RO_bigrams_LGBQT.csv"))

# SE
SE_bigrams_Gender = extract_stanza_bigrams(SE_Gender)
save_top_pos(SE_bigrams_Gender, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "SE_bigrams_Gender.csv"))
SE_bigrams_Migration = extract_stanza_bigrams(SE_Migration)
save_top_pos(SE_bigrams_Migration, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "SE_bigrams_Migration.csv"))
SE_bigrams_LGBTQ = extract_stanza_bigrams(SE_LGBTQ)
save_top_pos(SE_bigrams_LGBTQ, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "SE_bigrams_LGBTQ.csv"))

# HU
HU_bigrams_Gender = extract_stanza_bigrams(HU_Gender)
save_top_pos(HU_bigrams_Gender, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "HU_bigrams_Gender.csv"))
HU_bigrams_Migration = extract_stanza_bigrams(HU_Migration)
save_top_pos(HU_bigrams_Migration, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "HU_bigrams_Migration.csv"))
HU_bigrams_LGBTQ = extract_stanza_bigrams(HU_LGBTQ)
save_top_pos(HU_bigrams_LGBTQ, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "HU_bigrams_LGBTQ.csv"))

# ES
ES_bigrams_Gender = extract_stanza_bigrams(ES_Gender)
save_top_pos(ES_bigrams_Gender, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "ES_bigrams_Gender.csv"))
ES_bigrams_Migration = extract_stanza_bigrams(ES_Migration)
save_top_pos(ES_bigrams_Migration, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "ES_bigrams_Migration.csv"))
ES_bigrams_LGTBTQ = extract_stanza_bigrams(ES_LGBTQ)
save_top_pos(ES_bigrams_LGTBTQ, str(REPO_ROOT / "controversy-mapping" / "keyword-analysis" / "keywords" / "ES_bigrams_LGTBTQ.csv"))