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

TRANSLATED_ACTORS = ['Maniphesto', 'The Golden One', 'Gym XIV']

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

    def plotter(self, df, actor_df, theme, output_path, by_actor=False, year_cutoff_start=2015, year_cutoff_end=2026, generate_input_sheet=True):

        # split chunks in several lines lines
        df = df.copy()
        df['chunk'] = df['chunk'].apply(add_linebreaks)
        df['cluster'] = df['cluster'].astype(str)
        df['actor'] = df['actor'].astype(str)
        df = df.sort_values(['cluster', 'actor'])

        # mark actors as translated
        df.loc[df['actor'].isin(TRANSLATED_ACTORS), 'actor'] = df.loc[df['actor'].isin(TRANSLATED_ACTORS), 'actor'].apply(lambda name: f"{name} [translated]")
        
        # filter date
        df["publication date"] = pd.to_datetime(df["publication date"], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD

        cutoff_date_start = pd.Timestamp(year=year_cutoff_start, month=1, day=1)
        cutoff_date_end = pd.Timestamp(year=year_cutoff_end, month=1, day=1)

        df = df[(df["publication date"] >= cutoff_date_start) & (df["publication date"] < cutoff_date_end)].reset_index(drop=True)

        # add year
        year_series = pd.to_datetime(df['publication date'], errors='coerce').dt.year
        df['year'] = year_series.astype('Int64').astype(str).replace('<NA>', 'Unknown')

        # fix publication date
        df["publication date"] = df["publication date"].dt.strftime("%Y-%m-%d")

        # settiings for hoverdata
        hover_data = {
            'umap_1': False,
            'umap_2': False,
            'cluster': True,
            'actor': True,
            'entry_ID': True,
            'chunk': True,
            'publication date': True,
            'matched words': True,
            'platform': True
        }

        labels = {
            'cluster': 'Cluster',
            'actor': 'Actor',
            'entry_ID': 'Text ID',
            'chunk': 'Text',
            'publication date': 'Publication date',
            'matched words': 'Matched keywords',
            'platform': 'Platform'
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
        # scatter for years
        fig_year = px.scatter(
            df,
            x='umap_1',
            y='umap_2',
            color='year',
            hover_data=hover_data,
            labels=labels,
            render_mode="svg"
        )

        cluster_color_map = {str(trace.name): trace.marker.color for trace in fig_cluster.data}
        cluster_order = [str(trace.name) for trace in fig_cluster.data]
        cluster_order.sort()
        actor_color_map = {str(trace.name): trace.marker.color for trace in fig_actor.data}
        actor_order = [str(trace.name) for trace in fig_actor.data]
        actor_order.sort()
        year_color_map = {str(trace.name): trace.marker.color for trace in fig_year.data}
        year_order = [str(trace.name) for trace in fig_year.data]
        year_order.sort()

        # draw new figure
        fig = go.Figure()

        # which legend to show initially
        cluster_visible = not by_actor
        actor_visible = by_actor

        trace_metadata = []
        actor_seen = set()
        cluster_seen = set()

        # one data-trace set (actor x cluster x year) to preserve visibility across mode switches
        for actor_name in actor_order:
            actor_subset = df[df['actor'] == actor_name]
            for cluster_name in cluster_order:
                cluster_subset = actor_subset[actor_subset['cluster'] == cluster_name]
                if cluster_subset.empty:
                    continue
                for year_name in year_order:
                    subset = cluster_subset[cluster_subset['year'] == year_name].copy()
                    if subset.empty:   
                        continue

                    showlegend_actor = actor_name not in actor_seen
                    showlegend_cluster = cluster_name not in cluster_seen
                    showlegend = showlegend_actor if actor_visible else showlegend_cluster
                    trace_name = actor_name if actor_visible else cluster_name
                    legend_group = actor_name if actor_visible else cluster_name
                    marker_color = actor_color_map[actor_name] if actor_visible else cluster_color_map[cluster_name]


                    platform_to_symbol = {
                        'YouTube': 'circle',
                        'Website': 'square',
                        'Telegram': 'cross'
                        }
                    subset['symbol'] = subset['platform'].map(platform_to_symbol)
                    fig.add_trace(
                        go.Scatter(
                            x=subset['umap_1'],
                            y=subset['umap_2'],
                            mode='markers',
                            marker=dict(color=marker_color, symbol=subset['symbol']),
                            name=trace_name,
                            legendgroup=legend_group,
                            showlegend=showlegend,
                            customdata=subset[['cluster', 'actor', 'platform', 'publication date', 'entry_ID', 'matched words', 'chunk']].to_numpy(), # TODO: Add matched words and platform here and to hovertemplate
                            hovertemplate='Cluster=%{customdata[0]}<br>Actor=%{customdata[1]}<br>Platform=%{customdata[2]}<br>Date=%{customdata[3]}<br>Text ID=%{customdata[4]}<br>Matched words=%{customdata[5]}<br>Text=%{customdata[6]}<extra></extra>'
                        )
                    )
                    trace_metadata.append(
                        {
                            'actor': actor_name,
                            'cluster': cluster_name,
                            'year': year_name
                        }
                    )
                    actor_seen.add(actor_name)
                    cluster_seen.add(cluster_name)
        
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
        actor_mode_showlegend = []
        cluster_mode_showlegend = []
        year_mode_showlegend = []
        actor_mode_names = []
        cluster_mode_names = []
        year_mode_names = []
        actor_mode_groups = []
        cluster_mode_groups = []
        year_mode_groups = []
        actor_mode_colors = []
        cluster_mode_colors = []
        year_mode_colors = []
        actor_seen = set()
        cluster_seen = set()
        year_seen = set()

        for trace_info in trace_metadata:
            actor_name = trace_info['actor']
            cluster_name = trace_info['cluster']
            year_name = trace_info['year']
            actor_mode_showlegend.append(actor_name not in actor_seen)
            cluster_mode_showlegend.append(cluster_name not in cluster_seen)
            year_mode_showlegend.append(year_name not in year_seen)
            actor_mode_names.append(actor_name)
            cluster_mode_names.append(cluster_name)
            year_mode_names.append(year_name)
            actor_mode_groups.append(actor_name)
            cluster_mode_groups.append(cluster_name)
            year_mode_groups.append(year_name)
            actor_mode_colors.append(actor_color_map[actor_name])
            cluster_mode_colors.append(cluster_color_map[cluster_name])
            year_mode_colors.append(year_color_map[year_name])
            actor_seen.add(actor_name)
            cluster_seen.add(cluster_name)
            year_seen.add(year_name)

        actor_mode_showlegend.append(True)
        cluster_mode_showlegend.append(True)
        year_mode_showlegend.append(True)
        actor_mode_names.append('Actors')
        cluster_mode_names.append('Actors')
        year_mode_names.append('Actors')
        actor_mode_groups.append('Actors')
        cluster_mode_groups.append('Actors')
        year_mode_groups.append('Actors')
        actor_mode_colors.append('yellow')
        cluster_mode_colors.append('yellow')
        year_mode_colors.append('yellow')

        # buttons for legend toggling
        fig.update_layout(
            title=f"Text embeddings for {theme} UMAP",
            uirevision='legend-state',
            legend=dict(
                title=dict(text='Actor' if by_actor else 'Cluster'),
                groupclick='togglegroup'
            ),
            updatemenus=[
                dict(
                    type='buttons',
                    direction='left',
                    x=0.5,
                    y=1.12,
                    active=1 if by_actor else 0,
                    buttons=[
                        dict(
                            label='Color by Cluster',
                            method='update',
                            args=[
                                {
                                    'showlegend': cluster_mode_showlegend,
                                    'name': cluster_mode_names,
                                    'legendgroup': cluster_mode_groups,
                                    'marker.color': cluster_mode_colors
                                },
                                {'legend.title.text': 'Cluster'}
                            ]
                        ),
                        dict(
                            label='Color by Actor',
                            method='update',
                            args=[
                                {
                                    'showlegend': actor_mode_showlegend,
                                    'name': actor_mode_names,
                                    'legendgroup': actor_mode_groups,
                                    'marker.color': actor_mode_colors
                                },
                                {'legend.title.text': 'Actor'}
                            ]
                        ),
                        dict(
                            label='Color by Year',
                            method='update',
                            args=[
                                {
                                    'showlegend': year_mode_showlegend,
                                    'name': year_mode_names,
                                    'legendgroup': year_mode_groups,
                                    'marker.color': year_mode_colors
                                },
                                {'legend.title.text': 'Year'}
                            ]
                        ),
                    ]
                )
            ]
        )

        # lock axis
        x_range = df["umap_1"].max() - df["umap_1"].min()
        y_range = df["umap_2"].max() - df["umap_2"].min()
        
        x_min, x_max = df["umap_1"].min() - (0.1 * x_range), df["umap_1"].max() + (0.1 * x_range)
        y_min, y_max = df["umap_2"].min() - (0.1 * y_range), df["umap_2"].max() + (0.1 * y_range)

        fig.update_xaxes(range=[x_min, x_max], autorange=False)
        fig.update_yaxes(range=[y_min, y_max], autorange=False)
        #fig.show()
        
        # write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_path)

        # generate input sheet
        if generate_input_sheet:
            gen_input_sheet(theme, output_path.parent)


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

def gen_input_sheet(theme, output_dir):

    input_df = pd.DataFrame(
        {
            "area_number": pd.Series(range(1,9)),
            "x_lim_lower": None,
            "x_lim_upper": None,
            "y_lim_lower": None,
            "y_lim_upper": None,
            "short_title": None
            }
    )

    outpath = Path(output_dir) / "input_semantic-map-annotation.xlsx"
    outpath.parent.mkdir(parents=True, exist_ok=True)

    write_mode = "a" if outpath.exists() else "w"
    sheet_replace_mode = "replace" if outpath.exists() else None

    with pd.ExcelWriter(outpath, engine="openpyxl", mode=write_mode, if_sheet_exists=sheet_replace_mode) as writer:
        input_df.to_excel(writer, sheet_name=theme, index=False)