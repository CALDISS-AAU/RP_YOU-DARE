"""Adapted from extract_words_peaks.py using Codex:
- uses spacy instead of stanza
- uses built-in stopwords from spacy models
- utilizes batch processing via spacy's nlp.pipe
- splits text processing within each peak across cpus using multiprocessing 
    - # NOTE: could probably be optimized further by extracting all texts across peaks first and then process using multiprocessing
"""
from pathlib import Path
import os
from dotenv import load_dotenv

import json
import multiprocessing as mp
from collections import Counter
import re

import pandas as pd
import spacy

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


# pip install huspacy
import huspacy

# for translation
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, NllbTokenizer

try:
    from tqdm.auto import tqdm
except Exception:
    # Fallback keeps script runnable if tqdm is not installed.
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else []


COUNTRIES=[
    #"DK",
    # "ES",
    # "FR",
    # "HU",
    "IT",
    # "RO", 
    # "SE",
    "UK"
]

EXCLUDE_PATTERNS = [
    # re.compile(r'https?:\\/\\/(?:\w+\.)?twitter\.com\\/\S+|pic.twitter.com\\/[a-zA-Z]*?\d+\w?')
    # re.compile(r'https?:\\/\\/(?:\w+\.)?twitter\.com\\/\S+|pic.twitter.com\\/[a-zA-Z]*?\d+\w?', re.IGNORECASE),
    re.compile(r'https?://(?:\w+\.)|pic.twitter.com/[a-zA-Z]*?\d+\w?', re.IGNORECASE)
]

# Lookup dictionary for models
SPACY_MODELS = {
    "DK": "da_core_news_sm",   # Danish
    "ES": "es_core_news_sm",   # Spanish
    "FR": "fr_core_news_sm",   # French
    "HU": "hu_core_news_md",   # Hungarian # requires huspacy + huspacy.download("hu_core_news_md")
    "IT": "it_core_news_sm",   # Italian
    "RO": "ro_core_news_sm",   # Romanian
    "SE": "sv_core_news_sm",   # Swedish
    "UK": "en_core_web_sm"     # English
}

ALL_THEMES = [
    "lgb",
    "migration",
    "woke",
]

ENGLISH_SPEAKING_ACTORS = {
    'DK': {'Maniphesto'},
    'SE': {'Gym XIV', 'The Golden One'}
}

LANG_MAP = {
    'DK': 'dan_Latn',
    'SE': 'swe_Latn'
}

# Top level parameters
TOP_N = 4000 # number of terms to include
MAX_CHARS = 8000 # max length of text chunk (eases nlp processing)
BATCH_SIZE = 64 # number of texts in batch to process at a time
CPU_COUNT = 32 # NOTE: On UCloud, cores on machine type does not necessarily correspond to available cores. Also, not possible to extract number of cores via mp.cpu_count() (will just shows cores on the machine where the VM is running)

# data dirs
indexed_data_folder = str(REPO_ROOT / "controversy-mapping" / "data" / "indexed_data")
reduced_data_folder = str(REPO_ROOT / "controversy-mapping" / "data" / "reduced_data")
input_peaks_folder = str(REPO_ROOT / "controversy-mapping" / "trend-analysis" / "output" / "peaks")
output_data_folder = str(REPO_ROOT / "controversy-mapping" / "trend-analysis" / "output" / "peaks") 


# Translation stuff
class TranslateConfig:
    def __init__(
        self,
        model_name: str = "facebook/nllb-200-distilled-1.3B",
        src_lang: str = "eng_Latn",
        tgt_lang: str = "dan_Latn",
        device: str | None = None,
    ):
        # auto-detect device
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device

        self.tokenizer = NllbTokenizer.from_pretrained(model_name, src_lang=src_lang)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, use_safetensors=True).to(self.device)
        
    def translate_sent(self, sentences):
        if isinstance(sentences, str):
            sentences = [sentences]
    
        inputs = self.tokenizer(
            sentences,
            return_tensors="pt",
            padding=True,
            truncation=True).to(self.device)
        
        with torch.no_grad():
            translated = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(self.tgt_lang)
            )

        translation = self.tokenizer.batch_decode(
            translated,
            skip_special_tokens=True
            )
            
        return translation


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

def ensure_spacy_model(model_name):
    """Download/install model once if missing."""
    try:
        spacy.load(model_name)
    except OSError:
        if model_name.startswith("hu"):
            huspacy.download(model_name)
        else:
            spacy.cli.download(model_name)

def load_spacy_model(model_name):
    """Load an already installed spaCy model and remove unused pipes."""
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
    exclude_patterns=None,
    ) -> tuple[Counter, Counter]:
    """Extract NOUN/VERB/ADJ/PROPN lemmas from a list of texts using spaCy pipe.
    
    Returns:
        included_counter: counted lemmas kept for final frequencies
        excluded_counter: counted lemmas excluded by regex patterns
    """

    included_counter = Counter()
    excluded_counter = Counter()

    def iter_pieces():
        text_iter = texts
        if show_progress:
            text_iter = tqdm(
                texts,
                total=len(texts),
                desc=progress_label,
                unit="text",
                leave=False,
            )

        for text in text_iter:
            yield from chunk_text(text, max_chars=max_chars)

    for doc in nlp.pipe(iter_pieces(), batch_size=batch_size):
        for token in doc:
            if token.pos_ not in {"NOUN", "VERB", "ADJ", "PROPN"}:
                continue

            lemma = (token.lemma_ or token.text).strip().lower()

            if not lemma or lemma in nlp.Defaults.stop_words:
                continue

            if not any(ch.isalpha() for ch in lemma):
                continue

            if should_exclude_lemma(lemma, exclude_patterns=exclude_patterns):
                excluded_counter[lemma] += 1
                continue

            included_counter[lemma] += 1

    return included_counter, excluded_counter


def _extract_pos_worker(
    texts: list[str],
    model_name: str,
    max_chars: int,
    batch_size: int,
    exclude_patterns,
    ) -> tuple[Counter, Counter]:
    nlp = load_spacy_model(model_name)
    return extract_pos(
        texts=texts,
        nlp=nlp,
        max_chars=max_chars,
        batch_size=batch_size,
        exclude_patterns=exclude_patterns,
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
    exclude_patterns=None,
    ):
    """Process texts in parallel and return both included and excluded term counts."""
    if not texts:
        return [], []

    n_procs = max(1, min(cpu_count, len(texts)))
    chunks = _split_list(texts, n_procs)

    if len(chunks) == 1:
        nlp = load_spacy_model(spacy_model)
        included_counter, excluded_counter = extract_pos(
            texts=chunks[0],
            nlp=nlp,
            max_chars=max_chars,
            batch_size=batch_size,
            show_progress=True,
            progress_label=progress_label,
            exclude_patterns=exclude_patterns,
        )
        return included_counter.most_common(top_n), excluded_counter.most_common()

    tasks = [
        (chunk, spacy_model, max_chars, batch_size, exclude_patterns)
        for chunk in chunks
    ]

    merged_included = Counter()
    merged_excluded = Counter()

    with mp.get_context("spawn").Pool(processes=len(chunks)) as pool:
        results = pool.imap_unordered(_extract_pos_worker_star, tasks)
        for included_counter, excluded_counter in tqdm(
            results,
            total=len(tasks),
            desc=f"{progress_label} workers",
            unit="worker",
            leave=False,
        ):
            merged_included.update(included_counter)
            merged_excluded.update(excluded_counter)

    return merged_included.most_common(top_n), merged_excluded.most_common()


def _build_text_lookup(df_reduced: pd.DataFrame) -> dict:
    """Build lookup table from df_reduced: entry_ID -> {'text': ..., 'actor': ...}."""

    text_lookup = {}
    for entry_id, text, actor in zip(
        df_reduced["entry_ID"],
        df_reduced["text"],
        df_reduced["actor"],
    ):
        if pd.isna(entry_id):
            continue

        text_lookup[str(entry_id)] = {
            "text": str(text) if pd.notna(text) else "",
            "actor": str(actor).strip() if pd.notna(actor) else "",
        }

    return text_lookup

def _texts_from_ids_by_language(
    entry_ids: list,
    text_lookup: dict,
    english_actors: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Split texts into english-model texts and default-model texts based on actor."""

    english_actors = english_actors or set()
    english_texts = []
    default_texts = []

    for entry_id in entry_ids:
        record = text_lookup.get(str(entry_id))
        if not record:
            continue

        text = record.get("text", "")
        actor = record.get("actor", "")

        if not text:
            continue

        if actor in english_actors:
            english_texts.append(text)
        else:
            default_texts.append(text)

    return english_texts, default_texts
    
def should_exclude_lemma(lemma: str, exclude_patterns=None) -> bool:
    """Return True if lemma matches any exclusion regex."""
    if not lemma:
        return True

    if exclude_patterns is None:
        exclude_patterns = EXCLUDE_PATTERNS

    return any(pattern.search(lemma) for pattern in exclude_patterns)

def process_country(COUNTRY, THEMES=ALL_THEMES):
    """Main function for processing country"""

    SPACY_MODEL = SPACY_MODELS.get(COUNTRY)
    ensure_spacy_model(SPACY_MODEL)

    if COUNTRY in ENGLISH_SPEAKING_ACTORS:
        ensure_spacy_model("en_core_web_sm")

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
            entry_ids = df_filtered["entry_ID"].tolist()

            english_actors = ENGLISH_SPEAKING_ACTORS.get(COUNTRY, set())
            english_texts, default_texts = _texts_from_ids_by_language(
                entry_ids,
                text_lookup,
                english_actors=english_actors,
            )

            merged_words = Counter()
            merged_excluded = Counter()

            # translate english texts
            if english_texts:
                Translator = TranslateConfig(src_lang='eng_Latn')
                if country in LANG_MAP:
                    Translator.tgt_lang = LANG_MAP[country]
                    translated_texts = []
                    texts_split = [english_texts[i:i + 10] for i in range(0, len(english_texts), 10)]
                    for split in texts_split:
                        translated_split = Translator.translate_sent(split)
                        translated_texts.extend(translated_split)

                    default_texts.extend(translated_texts) # add to default texts
                    english_texts = None # Set to none to ensure evaluation for presence of english-language texts is skipped after translation
            # Only translate for supported languages
                else:
                    print(f"Skipping unsupported country code: {country}")

            # default country-language texts
            if default_texts:
                words, excluded_words = extract_pos_parallel(
                    texts=default_texts,
                    spacy_model=SPACY_MODEL,
                    top_n=TOP_N,
                    progress_label=f"{COUNTRY}/{theme}/peak {peak_id} [{COUNTRY}]",
                    exclude_patterns=EXCLUDE_PATTERNS,
                )
                merged_words.update(dict(words))
                merged_excluded.update(dict(excluded_words))

            # english-language texts
            if english_texts:
                words_en, excluded_words_en = extract_pos_parallel(
                    texts=english_texts,
                    spacy_model="en_core_web_sm",
                    top_n=TOP_N,
                    progress_label=f"{COUNTRY}/{theme}/peak {peak_id} [EN]",
                    exclude_patterns=EXCLUDE_PATTERNS,
                )
                merged_words.update(dict(words_en))
                merged_excluded.update(dict(excluded_words_en))

            words = merged_words.most_common(TOP_N)
            excluded_words = merged_excluded.most_common()

            # export
            output_data_dir = Path(output_data_folder) / COUNTRY / theme
            output_data_dir.mkdir(parents=True, exist_ok=True)
            output_data_path = output_data_dir / f"peak_{peak_id}_term_frequencies.csv"
            pd.DataFrame(words, columns=["term", "count"]).to_csv(
                output_data_path, index=False
            )

            if excluded_words:  # only write if not empty
                excluded_output_path = output_data_dir / f"peak_{peak_id}_excluded_terms.txt"
                with excluded_output_path.open("w", encoding="utf-8") as f:
                    for term, count in excluded_words:
                        f.write(f"{term}\t{count}\n")

    return COUNTRY


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    for country in COUNTRIES:
        country = process_country(country)
        print(f"Finished {country}")
