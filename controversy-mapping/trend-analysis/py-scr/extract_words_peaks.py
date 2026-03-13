# pip install pandas wordcloud stanza stopwordsiso

import os 
import json
import pandas as pd 
import wordcloud
import matplotlib.pyplot as plt
# import spacy
import stanza
from pathlib import Path
from stopwordsiso import stopwords
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

COUNTRY_LANG = {
    # "DK": "da",   # Danish
    # "ES": "es",   # Spanish
    # "FR": "fr",   # French
    # "HU": "hu",   # Hungarian
    # "IT": "it",   # Italian
    # # "RO": "ro",   # Romanian # Vil ikke køre
    "SWE": "sv",  # Swedish
    "UK": "en",   # English
}
all_countries = list(COUNTRY_LANG)

all_themes = [
    'lgb',
    'migration',
    'woke'
]

# Maybe as a sexy function??!
#pip install stopwordsiso
def get_stopwords(lang):
    word_list = stopwords(lang)
    return word_list

# Functions for data processing
def filter_dates(df, from_date, to_date):
    ''' Sorts and filtes data based on given arguments.
        - from_date: 'yyyy-mm-dd' this date is included in the final dataset
        - to_date: 'yyyy-mm-dd' this date is included in the final dataset
    '''
    df['publication date'] = pd.to_datetime(
        df['publication date'],
        format='%Y-%m-%d',
        errors='coerce'
    )

    # Filter by from_date and to_date if provided
    if from_date:
        from_dt = pd.to_datetime(from_date, errors='coerce') # Fills all invalid dates with NaT
        if pd.notna(from_dt):
            df = df[
                (df['publication date'].isna()) |  # keep NaT rows
                (df['publication date'] >= from_dt)  # apply filter only to real dates
            ]

    if to_date:
        to_dt = pd.to_datetime(to_date, errors='coerce') # Fills all invalid dates with NaT
        if pd.notna(to_dt):
            df = df[
                (df['publication date'].isna()) |  # keep NaT rows
                (df['publication date'] <= to_dt)  # apply filter only to real dates
            ]

    df['publication date'] = df['publication date'].dt.strftime('%Y-%m-%d')
    
    return df

# Functions for loading the best models eva
# Stanza on the ground
def load_stanza(language: str, use_gpu: bool = True):
    return stanza.Pipeline(
        language,
        processors="tokenize,pos,lemma,ner",
        tokenize_no_ssplit=True,
        use_gpu=use_gpu,
    )

# def extract_pos_stanza(dataframe, stop_words_list, nlp, n=4000):
#     counter = Counter()

#     for text in dataframe['text'].astype(str):
#         doc = nlp(text)

#         POS_words = [
#             word.lemma.lower()
#             for sent in doc.sentences
#             for word in sent.words
#             if word.upos in {"NOUN", "VERB", "ADJ", "PROPN"}
#         ]
#         POS_words_filtered = [w for w in POS_words if w not in stop_words_list]
        
#         counter.update(POS_words_filtered)
    
#     return counter.most_common(n)

# def extract_pos_stanza(dataframe, stop_words_list, nlp, n=4000):
#     counter = Counter()

#     for i, text in enumerate(dataframe['text'].astype(str)):
#         try:
#             doc = nlp(text)
#         except Exception as e:
#             raise RuntimeError(
#                 f"Stanza failed on row {i}, "
#                 f"text_ID={dataframe.iloc[i]['text_ID']}, "
#                 f"chars={len(text)}"
#             ) from e

#         POS_words = [
#             word.lemma.lower()
#             for sent in doc.sentences
#             for word in sent.words
#             if word.upos in {"NOUN", "VERB", "ADJ", "PROPN"}
#         ]
#         counter.update(w for w in POS_words if w not in stop_words_list)

#     return counter.most_common(n)

def chunk_text(s: str, max_chars: int = 8000):
    s = str(s).strip()
    if not s:
        return []
    if len(s) <= max_chars:
        return [s]

    chunks = []
    start = 0
    n = len(s)

    while start < n:
        end = min(start + max_chars, n)

        # try to cut at a newline or space to avoid mid-word splits
        if end < n:
            cut = s.rfind("\n", start, end)
            if cut == -1:
                cut = s.rfind(" ", start, end)
            if cut > start + 200:  # avoid tiny leftovers
                end = cut

        chunk = s[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end

    return chunks


# def extract_pos_stanza(dataframe, stop_words_list, nlp, n=4000, max_chars=8000):
#     counter = Counter()

#     for i, text in enumerate(dataframe["text"].astype(str)):
#         for piece in chunk_text(text, max_chars=max_chars):
#             try:
#                 doc = nlp(piece)
#             except Exception as e:
#                 raise RuntimeError(
#                     f"Stanza failed on row {i}, text_ID={dataframe.iloc[i]['text_ID']}, "
#                     f"chars={len(text)} (chunk_chars={len(piece)})"
#                 ) from e

#             pos_words = [
#                 word.lemma.lower()
#                 for sent in doc.sentences
#                 for word in sent.words
#                 if word.upos in {"NOUN", "VERB", "ADJ", "PROPN"}
#             ]
#             counter.update(w for w in pos_words if w not in stop_words_list)

#     return counter.most_common(n)

def extract_pos_stanza(dataframe, stop_words_list, nlp, n=4000, max_chars=8000):
    counter = Counter()

    for i, text in enumerate(dataframe["text"].astype(str)):
        for piece in chunk_text(text, max_chars=max_chars):
            try:
                doc = nlp(piece)
            except Exception as e:
                raise RuntimeError(
                    f"Stanza failed on row {i}, text_ID={dataframe.iloc[i]['text_ID']}, "
                    f"chars={len(text)} (chunk_chars={len(piece)})"
                ) from e

            for sent in doc.sentences:
                for w in sent.words:
                    if w.upos not in {"NOUN", "VERB", "ADJ", "PROPN"}:
                        continue

                    try:
                        lemma = (w.lemma if w.lemma is not None else w.text).lower()
                    except Exception as e:
                        print(
                            "Bad token:",
                            "row=", i,
                            "text_ID=", dataframe.iloc[i]["text_ID"],
                            "upos=", w.upos,
                            "text=", repr(w.text),
                            "lemma=", repr(w.lemma),
                        )
                        raise

                    if lemma in stop_words_list:
                        continue

                    counter[lemma] += 1

    return counter.most_common(n)


# Generate cloud
def generate_cloud(text, theme, outfile):
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        max_words=100,
        colormap='coolwarm'
        ).generate(
            text
            )
    # BABY PLOT ME ONE MORE TIME
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  
    plt.title(f"{theme}: Word cloud")
    plt.show()
    plt.savefig(outfile)

# Actual functionality
indexed_data_folder = '/work/YOU-DARE/sentence_filtering/indexed_data'
reduced_data_folder = '/work/YOU-DARE/sentence_filtering/reduced_data/'
input_peaks_folder = '/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks'
output_data_folder = '/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks'

def process_country(country: str, language: str):
    stop_words = get_stopwords(language)
    nlp = load_stanza(language, use_gpu=True)

    # Load reduced dataset to get full texts
    reduced_data_path = f'{reduced_data_folder}/{country}_reduced.jl'
    with open(reduced_data_path, 'r', encoding='utf-8') as reduced:
        reduced_data = [json.loads(line) for line in reduced]
    df_reduced = pd.DataFrame(reduced_data)
            
    for theme in all_themes:
        indexed_file_path = f'{indexed_data_folder}/{country}/{country}_{theme}_indexed.jl'
        with open(indexed_file_path, 'r', encoding='utf-8') as input_file:
            data = [json.loads(line) for line in input_file]
        df_indexes = pd.DataFrame(data)
        df_indexes['theme'] = theme
        df_indexes['matched keywords'] = df_indexes[f'matched keywords - {theme}']
        df_indexes = df_indexes.drop([f'matched keywords - {theme}'], axis=1)
        
        input_peaks_path = f'{input_peaks_folder}/{country}/{theme}_peaks.json'
        with open(input_peaks_path, 'r', encoding='utf-8') as input_peaks:
            peaks = json.load(input_peaks)
        for peak_id, (from_date, to_date) in peaks.items():
            df_filtered = filter_dates(df_indexes, from_date, to_date)
            df_filtered['peak_ID'] = peak_id

            df_filtered['text'] = df_reduced.loc[
                df_filtered['text_ID'],
                'text'
            ].to_numpy()
        
            print(country, language, theme, peak_id, len(df_filtered), df_filtered.columns)

            lens = df_filtered["text"].astype(str).str.len()
            print("peak", peak_id, "rows", len(df_filtered), "max_chars", int(lens.max()), "p99_chars", int(lens.quantile(0.99)))
            # words = extract_pos_stanza(df_filtered, stop_words, nlp)
            # print(words)
            try:
                words = extract_pos_stanza(df_filtered, stop_words, nlp)
            except Exception as e:
                print("⚠️ FAILED PEAK")
                print("country:", country)
                print("theme:", theme)
                print("peak:", peak_id)
                print("error:", e)
                continue

            output_data_dir = f'{output_data_folder}/{country}/{theme}'
            Path(output_data_dir).mkdir(parents=True, exist_ok=True)

            output_data_path = f'{output_data_dir}/peak_{peak_id}_term_frequencies.csv'
            pd.DataFrame(words, columns=["term", "count"]).to_csv(output_data_path, index=False)

    return country

# Runs each country in parallel
if __name__ == "__main__": 
    mp.set_start_method("spawn", force=True)
    max_workers = 1#min(len(all_countries), 8) # one worker pr country

    # Loads stanza model
    for language in set(COUNTRY_LANG.values()):
        stanza.download(language) 

    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(process_country, country, COUNTRY_LANG[country]): country
            for country in all_countries
        }

        for future in as_completed(futures):
            country = futures[future]
            try:
                future.result()
                print(f"Finished {country}")
            except Exception as e:
                print(f"Failed {country} ({e})")