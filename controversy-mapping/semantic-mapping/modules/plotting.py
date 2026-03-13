from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

import pandas as pd
import numpy as np
from collections import Counter

import plotly.express as px
import plotly.graph_objects as go

from .clustering import add_linebreaks


def gen_semantic_map(
    chunks_with_umap_df, 
    actor_with_umap_df, 
    regions_annotate,
    country,
    theme, 
    output_path, 
    resize_factor=2
    ):
    """
    Generate final semantic map for deliverable.
    Args:
        chunks_with_umap_df: data frame of chunks to be mapped along with x and y coordinates from UMAP and actor.
        actor_with_umap_df: data frame of x and y coordinates for mean embeddings of actors.
        regions_annotate: list of regions to annotate. Expects dictionaries with keys label, x_start, x_end, y_start, y_end.
        country: Country map is for.
        theme: Theme map is for.
        output_path: Path for storing pdf/png.
        resize_factor: scaling up elements (fonts, geoms, etc.).
    """

    # prepare regions
    regions = []
    
    for c, annoreg in enumerate(regions_annotate, start = 1):
        
        region_add = {
            "label": str(c),
            "x_range": (int(annoreg.get("x_start")), annoreg.get("x_end")),
            "y_range": (int(annoreg.get("y_start")), annoreg.get("y_end"))
        }

        regions.append(region_add)

    # split chunks in several lines lines
        df = chunks_with_umap_df.copy()
        df['chunk'] = df['chunk'].apply(add_linebreaks)
        
        # settiings for hoverdata
        hover_data = {
            'umap_1': False,
            'umap_2': False,
            'actor': True,
            'text_ID': True,
            'chunk': True,
        }

        labels = {
            'actor': 'Actor',
            'text_ID': 'Text ID',
            'chunk': 'Text',
        }

        # scatter for actors
        fig_actor = px.scatter(
            df,
            x='umap_1',
            y='umap_2',
            color='actor',
            hover_data=hover_data,
            labels=labels,
            render_mode="svg",
            #opacity=0.35,
        )

        # draw new figure
        fig = go.Figure()

        # add traces from scatters to new figure
        for trace in fig_actor.data:
            fig.add_trace(trace)

        # add actors
        fig.add_trace(
            go.Scatter(
                x=actor_with_umap_df['umap_1'],
                y=actor_with_umap_df['umap_2'],
                mode='markers+text',
                marker=dict(
                    size=14,
                    symbol='star-triangle-up',
                    color='yellow'
                ),
                text=actor_with_umap_df['actor'],
                textposition='top center',
                textfont=dict(size=10 * resize_factor),
                name='Actors'
            )
        )

        # actor-only legend
        fig.update_layout(
            #title=f"Semantic mapping for {country} - {theme}",
            legend=dict(title=dict(text='Actor')),
        )

        # draw ellipses
        for r in regions:
            x0, x1 = r["x_range"]
            y0, y1 = r["y_range"]

            # only draw region if at least one point is inside
            mask = df["umap_1"].between(x0, x1) & df["umap_2"].between(y0, y1)
            if not mask.any():
                continue

            fig.add_shape(
                type="circle",  # use "rect" if box instead
                xref="x",
                yref="y",
                x0=x0,
                x1=x1,
                y0=y0,
                y1=y1,
                fillcolor="rgba(0,0,0,0)",
                line=dict(color="rgba(64,64,64,0.95)", width=5, dash="dash"),
                layer="above",
                opacity=0.6
            )

            fig.add_annotation(
                x=(x0 + x1) / 2,
                y=y1,
                xref="x",
                yref="y",
                text=f"<b>{r['label']}</b>",
                showarrow=False,
                yshift=10,
                bgcolor="rgba(255,255,255,0.85)",
                font=dict(size=14 * resize_factor),
            )

        # lock axis
        x_range = df["umap_1"].max() - df["umap_1"].min()
        y_range = df["umap_2"].max() - df["umap_2"].min()
        
        x_min, x_max = df["umap_1"].min() - (0.1 * x_range), df["umap_1"].max() + (0.1 * x_range)
        y_min, y_max = df["umap_2"].min() - (0.1 * y_range), df["umap_2"].max() + (0.1 * y_range)

        # changes to axis
        fig.update_xaxes(
            range=[x_min, x_max],
            autorange=False,
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="black",
            linewidth=2,
            mirror=True,
            showticklabels=False,
            ticks="",
        )
        fig.update_yaxes(
            range=[y_min, y_max],
            autorange=False,
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="black",
            linewidth=2,
            mirror=True,
            showticklabels=False,
            ticks="",
        )

        # re-scale elements        
        fig.update_traces(
            marker=dict(size=6 * resize_factor),
            selector=dict(mode="markers")
        )

        fig.update_layout(
            font=dict(size=12 * resize_factor),
            legend=dict(font=dict(size=11 * resize_factor)),
            title=dict(font=dict(size=16 * resize_factor)),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_family="DejaVu Serif"
        )

        # write to PNG and PDF
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        png_path = Path(output_path).with_suffix(".png")
        pdf_path = Path(output_path).with_suffix(".pdf")
        fig.write_image(
            str(png_path), 
            format="png",
            width=1920,
            height=1080,
            scale=1,
        )
        fig.write_image(
            str(pdf_path),
            format="pdf",
            width=1920,
            height=1080,
            scale=1,
        )
