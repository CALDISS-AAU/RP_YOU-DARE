"""Adapted from extract_words_peaks.py using Codex:
- uses spacy instead of stanza
- uses built-in stopwords from spacy models
- utilizes batch processing via spacy's nlp.pipe
- splits text processing within each peak across cpus using multiprocessing 
    - # NOTE: could probably be optimized further by extracting all texts across peaks first and then process using multiprocessing
"""

import json
import multiprocessing as mp
from collections import Counter
from pathlib import Path

import pandas as pd
import spacy

try:
    from tqdm.auto import tqdm
except Exception:
    # Fallback keeps script runnable if tqdm is not installed.
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else []

COUNTRIES=[
#    "RO", 
    "SWE"
#    "UK"
]

# Lookup dictionary for models - could be expanded.
SPACY_MODELS = {
    "RO": "ro_core_news_sm",
    "SWE": "sv_core_news_sm",
    "UK": "en_core_web_sm"
}

ALL_THEMES = [
    "lgb",
    "migration",
    "woke",
]

# Top level parameters
TOP_N = 4000 # number of terms to include
MAX_CHARS = 8000 # max length of text chunk (eases nlp processing)
BATCH_SIZE = 64 # number of texts in batch to process at a time
CPU_COUNT = 32 # NOTE: On UCloud, cores on machine type does not necessarily correspond to available cores. Also, not possible to extract number of cores via mp.cpu_count() (will just shows cores on the machine where the VM is running)

# data dirs
indexed_data_folder = "/work/YOU-DARE/controversy-mapping/sentence_filtering/indexed_data"
reduced_data_folder = "/work/YOU-DARE/controversy-mapping/sentence_filtering/reduced_data"
input_peaks_folder = "/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks"
output_data_folder = "/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks" 


def filter_dates(df: pd.DataFrame, from_date: str, to_date: str, remove_flashback=True) -> pd.DataFrame:
    """Filter by inclusive date interval while preserving rows with NaT dates."""
    filtered = df.copy()

    if remove_flashback:
        filtered = filtered[~filtered['source'].str.contains("flashback", case=False)].reset_index(drop=True)

    filtered["publication date"] = pd.to_datetime(
        filtered["publication date"],
        format="%Y-%m-%d",
        errors="coerce",
    )

    if from_date:
        from_dt = pd.to_datetime(from_date, errors="coerce")
        if pd.notna(from_dt):
            filtered = filtered[
                (filtered["publication date"].isna())
                | (filtered["publication date"] >= from_dt)
            ]

    if to_date:
        to_dt = pd.to_datetime(to_date, errors="coerce")
        if pd.notna(to_dt):
            filtered = filtered[
                (filtered["publication date"].isna())
                | (filtered["publication date"] <= to_dt)
            ]

    return filtered


def load_spacy_model(model_name):
    """Loads spacy model. Tries to download if model not present. Disables ner and parser"""
    try:
        nlp = spacy.load(model_name)
    except OSError:
        spacy.cli.download(model_name)
        nlp = spacy.load(model_name)
    for component in ("ner", "parser"):
        if component in nlp.pipe_names:
            nlp.remove_pipe(component)
    return nlp


def chunk_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Chunks text into max MAX_CHARS characters."""
    s = str(text).strip()
    if not s:
        return []
    if len(s) <= max_chars:
        return [s]

    chunks = [] # NOTE: "chunks" here refers to substrings of a full text; as in a text divided in chunks. Not a collection of texts to be processed in bulk, which is what "chunk" refers to elsewhere. Could be updated to avoid confusion.
    start = 0
    n_chars = len(s)

    while start < n_chars:
        end = min(start + max_chars, n_chars)
        if end < n_chars:
            cut = s.rfind("\n", start, end)
            if cut == -1:
                cut = s.rfind(" ", start, end)
            if cut > start + 200:
                end = cut
        piece = s[start:end].strip()
        if piece:
            chunks.append(piece)
        start = end

    return chunks


def extract_pos(
    texts: list[str],
    nlp,
    max_chars: int = MAX_CHARS,
    batch_size: int = BATCH_SIZE,
    show_progress: bool = False,
    progress_label: str = "spaCy",
    ) -> Counter:
    """Extract NOUN/VERB/ADJ/PROPN lemmas from a list of texts using spaCy pipe."""

    counter = Counter()

    # generator function to be passed to nlp.pipe
    def iter_pieces():
        text_iter = texts
        if show_progress: # enables progress bar
            text_iter = tqdm(
                texts,
                total=len(texts),
                desc=progress_label,
                unit="text",
                leave=False,
            )

        # generator
        for text in text_iter:
            yield from chunk_text(text, max_chars=max_chars)

    # processes texts via nlp.pipe using generator function
    for doc in nlp.pipe(iter_pieces(), batch_size=batch_size):
        for token in doc:
            if token.pos_ not in {"NOUN", "VERB", "ADJ", "PROPN"}:
                continue
            lemma = (token.lemma_ or token.text).strip().lower()
            if not lemma or lemma in nlp.Defaults.stop_words: # uses default stopwords in spacy model
                continue
            # Drop strings that are only punctuation and/or digits.
            if not any(ch.isalpha() for ch in lemma):
                continue
            counter[lemma] += 1

    return counter


def _extract_pos_worker(
    texts: list[str],
    model_name: str,
    max_chars: int,
    batch_size: int,
    ) -> Counter:
    """Worker-wrapper to be used for parallelization."""
    nlp = load_spacy_model(model_name)
    return extract_pos(
        texts=texts,
        nlp=nlp,
        max_chars=max_chars,
        batch_size=batch_size,
    )


def _split_list(items: list[str], n_parts: int) -> list[list[str]]:
    """Divide texts in lists in equal-size chunks to be split among cpu workers."""
    if not items:
        return []
    n_parts = max(1, min(n_parts, len(items)))
    chunk_size = (len(items) + n_parts - 1) // n_parts
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def _extract_pos_worker_star(args) -> Counter:
    """Wrapper to allow for additional arguements"""
    return _extract_pos_worker(*args)


def extract_pos_parallel(
    texts: list[str],
    spacy_model,
    top_n: int = TOP_N,
    max_chars: int = MAX_CHARS,
    batch_size: int = BATCH_SIZE,
    cpu_count=CPU_COUNT,
    progress_label: str = "POS extraction",
    ):
    """Function for handling texts: split among cpu workerks, run pos-extraction"""
    if not texts:
        return []

    n_procs = max(1, min(cpu_count, len(texts))) # number of available cpu workers
    chunks = _split_list(texts, n_procs) # divides texts between cpu workers
    # NOTE: "chunks" here refers to a subcollection of texts to be processed by the same cpu worker - not a chunk as in a substring of the full text. Other variable names could be used to avoid confusion. 

    # if only one batch of texts, no need for multiprocessing 
    if len(chunks) == 1: 
        nlp = load_spacy_model(spacy_model)
        return extract_pos(
            texts=chunks[0],
            nlp=nlp,
            max_chars=max_chars,
            batch_size=batch_size,
            show_progress=True,
            progress_label=progress_label,
        ).most_common(top_n)

    # arguements for mp-version of pos-extraction
    tasks = [
        (chunk, spacy_model, max_chars, batch_size)
        for chunk in chunks
    ]

    # counter to store results
    merged = Counter()
    # run mp pos-extraction
    with mp.get_context("spawn").Pool(processes=len(chunks)) as pool:
        results = pool.imap_unordered(_extract_pos_worker_star, tasks)
        for counter in tqdm( # tqdm for progress bar
            results,
            total=len(tasks),
            desc=f"{progress_label} workers",
            unit="worker",
            leave=False,
        ):
            merged.update(counter)

    return merged.most_common(top_n)



def _build_text_lookup(df_reduced: pd.DataFrame) -> dict:
    """Builds a simple lookup table from df_reduced: text_ID: text"""

    text_lookup = {}
    for text_id, text in enumerate(df_reduced["text"].tolist()):
        text_value = str(text) if pd.notna(text) else ""
        text_lookup[text_id] = text_value
        text_lookup[str(text_id)] = text_value
    return text_lookup


def _texts_from_ids(text_ids: list, text_lookup: dict):
    """Extract list of texts from lookup table from provided text ids"""
    texts = []

    for text_id in text_ids:

        value = text_lookup.get(int(text_id), text_lookup.get(str(text_id)))
        if not value:
            continue
        texts.append(value)

    return texts


def process_country(COUNTRY, THEMES=ALL_THEMES):
    """Main function for processing country"""

    SPACY_MODEL = SPACY_MODELS.get(COUNTRY)

    # read df reduced
    reduced_data_path = Path(reduced_data_folder) / f"{COUNTRY}_reduced.jl"
    df_reduced = pd.read_json(reduced_data_path, lines=True)

    # create look up table
    text_lookup = _build_text_lookup(df_reduced)

    # iter over themes - tqdm for progress bar
    for theme in tqdm(
        THEMES,
        total=len(THEMES),
        desc=f"{COUNTRY} themes",
        unit="theme",
    ):
        # read indexed data
        indexed_file_path = (
            Path(indexed_data_folder) / COUNTRY / f"{COUNTRY}_{theme}_indexed.jl"
        )
        df_indexes = pd.read_json(indexed_file_path, lines=True)

        # read theme peaks
        input_peaks_path = Path(input_peaks_folder) / COUNTRY / f"{theme}_peaks.json"
        with open(input_peaks_path, "r", encoding="utf-8") as input_peaks:
            peaks = json.load(input_peaks)

        peak_items = list(peaks.items())

        # iter over peaks - tqdm for progress bar
        for peak_id, (from_date, to_date) in tqdm(
            peak_items,
            total=len(peak_items),
            desc=f"{COUNTRY}/{theme} peaks",
            unit="peak",
            leave=False,
            ):

            # filter indexes by date - matched texts in peak period
            df_filtered = filter_dates(df_indexes, from_date, to_date)
            text_ids = df_filtered["text_ID"].tolist()
            texts = _texts_from_ids(text_ids, text_lookup)

            # extract words
            words = extract_pos_parallel(
                texts=texts,
                spacy_model=SPACY_MODEL,
                top_n=TOP_N,
                progress_label=f"{COUNTRY}/{theme}/peak {peak_id}",
            )

            # export
            output_data_dir = Path(output_data_folder) / COUNTRY / theme
            output_data_dir.mkdir(parents=True, exist_ok=True)
            output_data_path = output_data_dir / f"peak_{peak_id}_term_frequencies.csv"
            pd.DataFrame(words, columns=["term", "count"]).to_csv(
                output_data_path, index=False
            )

    return COUNTRY


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    for country in COUNTRIES:
        country = process_country(country)
        print(f"Finished {country}")