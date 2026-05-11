from __future__ import annotations

from dataclasses import dataclass
import ast
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

import pandas as pd
import numpy as np
import torch
import fasttext
import transformers
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, NllbTokenizer
from sentence_transformers import SentenceTransformer
import huggingface_hub
from cuml.manifold import UMAP
from cuml.cluster import HDBSCAN
from collections import Counter

import plotly.express as px
import plotly.graph_objects as go

class LanguageDetectionConfig:
    def __init__(
        self,
        fast_model : str = "lid.176.bin",

    ):
        self.lang_model = fasttext.load_model(fast_model)
    
    def detect_lang(self, text: str):
        label, prob = self.lang_model.predict(text)
        lang = label[0].replace('__label__', "")
        return lang, prob[0]


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

class EmbeddingConfig:
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        max_seq_length: int = 512,
        batch_size: int = 64,
        dtype=torch.bfloat16,
    ):
        self.batch_size = batch_size

        self.model = SentenceTransformer(
            model_name,
            model_kwargs={
                "dtype": dtype,
                "use_safetensors": True
                },
        )
        self.model.max_seq_length = max_seq_length

    def get_embeddings(self, sentences):
        pool = self.model.start_multi_process_pool()
        embeddings = self.model.encode_multi_process(
            sentences = [f"Represent this sentence for retrieval: {s}" for s in sentences],
            pool=pool,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        self.model.stop_multi_process_pool(pool)
        return embeddings


@dataclass
class DimensionConfig:
    # HDBSCAN PARAMETERS
    min_cluster_size: int = 10
    min_samples: int = 2
    metric: str = 'euclidean'
    cluster_selection_method: str = 'eom'

    # UMAP PARAMETERS
    build_algo: str = 'nn_descent'
    n_neighbors: int = 50
    n_components: int = 2
    min_dist: float = 0.15
    umap_metric: str = 'euclidean'

    def cluster(self, embeddings):
        clusterer = HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric=self.metric,
            cluster_selection_method=self.cluster_selection_method,
            output_type='numpy'
        )
        return clusterer.fit_predict(embeddings)

    def reduce(self, embeddings):
        self._reducer = UMAP(
            n_neighbors=self.n_neighbors,
            n_components=self.n_components,
            min_dist=self.min_dist,
            metric=self.umap_metric,
            build_algo=self.build_algo,
            output_type='numpy',
            build_kwds={
                'nnd_do_batch': True,
                'nnd_n_clusters': 4
            }
        )
        return self._reducer.fit_transform(embeddings)
    
    def transform(self, embeddings):
        if self._reducer is None:
            raise ValueError("Must call reduce() before transform()")

        return self._reducer.transform(embeddings)

    def plotter(self, df, actor_df, theme, output_path):

        fig = px.scatter(
            df,
            x='umap_1',
            y='umap_2',
            color='cluster',
            hover_data=['chunk'],
            title=f"Text embeddings for {theme} UMAP"
        )

        fig.add_trace(
            go.Scatter(
                x=actor_df['umap_1'],
                y=actor_df['umap_2'],
                mode='markers+text',
                marker=dict(
                    size=14,
                    symbol='star-triangle-up',
                    color='yellow'
                ),
                text=actor_df['source'],
                textposition='top center',
                name='Actors'
            )
        )
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_path)
