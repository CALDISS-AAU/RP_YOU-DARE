from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

import pandas as pd
import numpy as np
from cuml.manifold import UMAP
from cuml.cluster import HDBSCAN   
from collections import Counter

import plotly.express as px
import plotly.graph_objects as go

@dataclass
class DimensionConfig:
    # HDBSCAN PARAMETERS
    min_cluster_size: int = 10
    min_samples: int = 2
    metric: str = 'euclidean'
    cluster_selection_epsilon: float = 0.0
    cluster_selection_method: str = 'leaf'
    allow_single_cluster=False

    # UMAP PARAMETERS
    build_algo: str = 'auto'
    n_neighbors: int = 30
    n_components: int = 2
    min_dist: float = 0.1
    umap_metric: str = 'euclidean',


    def cluster(self, embeddings):
        clusterer = HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric=self.metric,
            cluster_selection_method=self.cluster_selection_method,
            output_type='numpy',
            cluster_selection_epsilon=self.cluster_selection_epsilon,
            allow_single_cluster=self.allow_single_cluster
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

    def plotter(self, df, actor_df, theme, output_path, by_actor=False):

        # split chunks in several lines lines
        df = df.copy()
        df['chunk'] = df['chunk'].apply(add_linebreaks)
        df['cluster'] = df['cluster'].astype(str)
        df = df.sort_values(['cluster'])

        # settiings for hoverdata
        hover_data = {
            'umap_1': False,
            'umap_2': False,
            'cluster': True,
            'actor': True,
            'text_ID': True,
            'chunk': True,
        }
        labels = {
            'cluster': 'Cluster',
            'actor': 'Actor',
            'text_ID': 'Text ID',
            'chunk': 'Text',
        }

        # scatter for clusters
        fig_cluster = px.scatter(
            df,
            x='umap_1',
            y='umap_2',
            color='cluster',
            hover_data=hover_data,
            labels=labels,
            render_mode="svg"
        )
        # scatter for actors
        fig_actor = px.scatter(
            df,
            x='umap_1',
            y='umap_2',
            color='actor',
            hover_data=hover_data,
            labels=labels,
            render_mode="svg"
        )

        # draw new figure
        fig = go.Figure()

        # which legend to show initially
        cluster_visible = not by_actor
        actor_visible = by_actor

        # add traces from scatters to new figure
        for trace in fig_cluster.data:
            trace.visible = cluster_visible
            fig.add_trace(trace)

        for trace in fig_actor.data:
            trace.visible = actor_visible
            fig.add_trace(trace)

        # add actors
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
                text=actor_df['actor'],
                textposition='top center',
                name='Actors'
            )
        )

        # stuff for legend
        cluster_count = len(fig_cluster.data)
        actor_count = len(fig_actor.data)
        always_on = [True]


        # buttons for legend toggling
        fig.update_layout(
            title=f"Text embeddings for {theme} UMAP",
            legend=dict(title=dict(text='Actor' if by_actor else 'Cluster')),
            updatemenus=[
                dict(
                    type='buttons',
                    direction='left',
                    x=0.5,
                    y=1.12,
                    buttons=[
                        dict(
                            label='Color by Cluster',
                            method='update',
                            args=[
                                {'visible': [True] * cluster_count + [False] * actor_count + always_on},
                                {'legend.title.text': 'Cluster'}
                            ]
                        ),
                        dict(
                            label='Color by Actor',
                            method='update',
                            args=[
                                {'visible': [False] * cluster_count + [True] * actor_count + always_on},
                                {'legend.title.text': 'Actor'}
                            ]
                        ),
                    ]
                )
            ]
        )

        # lock axis
        x_min, x_max = df["umap_1"].min() - (0.2 * abs(df["umap_1"].min())), df["umap_1"].max() + (0.2 * abs(df["umap_1"].max()))
        y_min, y_max = df["umap_2"].min() - (0.2 * abs(df["umap_2"].min())), df["umap_2"].max() + (0.2 * abs(df["umap_2"].max()))

        fig.update_xaxes(range=[x_min, x_max], autorange=False)
        fig.update_yaxes(range=[y_min, y_max], autorange=False)

        # write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_path)


def add_linebreaks(text):
    if len(text) < 50:
        return text

    white_spaces = [i for i, c in enumerate(text) if c.isspace()]

    num_breaks = len(text) // 75
    if num_breaks == 0:
        return text

    prev_break = 0
    text_return = ""

    for n in range(1, num_breaks + 1):
        target = n * 75
        candidates = [i for i in white_spaces if i > prev_break]
        if not candidates:
            break

        next_break = min(candidates, key=lambda i: abs(i - target))
        text_return += text[prev_break:next_break] + "<br>"
        prev_break = next_break

    text_return += text[prev_break:]
    return text_return