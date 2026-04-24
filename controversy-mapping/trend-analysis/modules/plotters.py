"""
Detection of peaks/thematic salience using isolation forest anomaly detection. 
Code adjusted from Codex (OpenAI) output.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union
import warnings

import numpy as np
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px

from .anomaly_detection import *

# main plotting function
def gen_streamgraph_peaks(results, flagged, output_dir_vis, data_path, AGG_FREQ):
    """Generate a streamgraph of smoothed within-actor monthly weights and peak labels."""

    required_cols = {"date", "actor", "count", "total_texts"}
    missing_cols = required_cols.difference(results.columns)
    if missing_cols:
        raise ValueError(f"Expected columns {sorted(required_cols)} in results, missing {sorted(missing_cols)}")

    if results.empty:
        warnings.warn("No results available for streamgraph plotting.")
        return None

    def _gaussian_smooth(values: np.ndarray, sigma: float = 2) -> np.ndarray:
        if values.size <= 1:
            return values.astype(float)

        radius = max(1, int(np.ceil(3 * sigma)))
        x_vals = np.arange(-radius, radius + 1, dtype=float)
        kernel = np.exp(-(x_vals ** 2) / (2 * sigma ** 2))
        kernel /= kernel.sum()
        padded = np.pad(values.astype(float), (radius, radius), mode="edge")
        return np.convolve(padded, kernel, mode="valid")

    # Derive country and theme from data_path
    data_path = Path(data_path)
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # plot path
    plot_path = Path(output_dir_vis) / country / theme / f"{theme}_streamgraph_peaks.png"
    plot_path.parent.mkdir(parents=True, exist_ok=True)

    # complete df with all months in date range
    plot_df = results.copy()
    plot_df["date"] = pd.to_datetime(plot_df["date"])

    actors = sorted(plot_df["actor"].dropna().unique().tolist())
    dates = pd.date_range(plot_df["date"].min(), plot_df["date"].max(), freq=AGG_FREQ)

    full = pd.MultiIndex.from_product(
        [dates, actors],
        names=["date", "actor"],
    ).to_frame(index=False)

    ## total texts per actor (total is repeated for each row)
    actor_totals = (
        plot_df[["actor", "total_texts"]]
        .drop_duplicates(subset=["actor"])
        .rename(columns={"total_texts": "actor_total_texts"})
    )

    ## merge
    plot_df = (
        full.merge(
            plot_df[["date", "actor", "count", "peak_id", "is_peak"]],
            on=["date", "actor"],
            how="left",
        )
        .merge(actor_totals, on="actor", how="left")
    )

    ## fill missing
    plot_df["count"] = plot_df["count"].fillna(0)
    plot_df["share_texts"] = np.where( # weight based on share of texts
        plot_df["actor_total_texts"] > 0,
        plot_df["count"] / plot_df["actor_total_texts"],
        0,
    )
    plot_df["weight"] = plot_df["share_texts"] * (plot_df["actor_total_texts"]/(plot_df["actor_total_texts"]+10))


    # pivot wider
    weight_wide = (
        plot_df.pivot(index="date", columns="actor", values="weight")
        .fillna(0)
        .sort_index()
    )

    # smooth weights using gaussian smooth
    smoothed_weights = pd.DataFrame(
        {
            actor: _gaussian_smooth(weight_wide[actor].to_numpy(dtype=float))
            for actor in weight_wide.columns
        },
        index=weight_wide.index,
    )

    #actor_order = smoothed_weights.sum(axis=0).sort_values(ascending=False).index.tolist()
    #smoothed_weights = smoothed_weights[actor_order]
    actor_order = weight_wide.sum(axis=0).sort_values(ascending=False).index.tolist()
    smoothed_weights = weight_wide[actor_order]

    # values to plot
    x_values = smoothed_weights.index.to_pydatetime()
    stacked_values = smoothed_weights.to_numpy().T
    total_weights = stacked_values.sum(axis=0)
    baseline = -total_weights / 2 # Shifts start of height in the negative (half of height below 0)

    # draw plot
    fig, ax = plt.subplots(figsize=(14, 8))
    colors = plt.cm.tab20(np.linspace(0, 1, max(len(actor_order), 2)))[:len(actor_order)]

    lower = baseline.copy()
    for actor, actor_weights, color in zip(actor_order, stacked_values, colors):
        upper = lower + actor_weights
        ax.fill_between(
            x_values,
            lower,
            upper,
            label=actor,
            color=color,
            alpha=0.95,
            linewidth=0.5,
        )
        lower = upper

    # extract peaks
    if flagged is not None and not flagged.empty and {"date", "peak_id"}.issubset(flagged.columns):
        peak_df = flagged[["date", "peak_id"]].copy()
    else:
        peak_df = plot_df.loc[plot_df["is_peak"].fillna(False), ["date", "peak_id"]].copy()

    # datetime
    peak_df["date"] = pd.to_datetime(peak_df["date"])

    # add peak dots
    y_padding = max(total_weights.max() * 0.04, 0.002)
    upper_envelope = total_weights / 2

    for _, peak in peak_df.iterrows():
        peak_idx = smoothed_weights.index.get_indexer([peak["date"]])
        if peak_idx.size == 0 or peak_idx[0] < 0:
            continue

        x_peak = peak["date"].to_pydatetime()
        y_peak = upper_envelope[peak_idx[0]]# + y_padding
        ax.scatter(x_peak, y_peak, color="black", s=22, zorder=5)
        ax.text(
            x_peak,
            y_peak + y_padding*0.2,
            f"{int(peak['peak_id'])}\n({peak['date'].strftime('%Y-%m')})",
            ha="center",
            va="bottom",
            fontsize=9,
            color="black",
        )
        ax.axvline(
            x_peak,
            color="black",
            linestyle="--",
            linewidth=0.8,
            alpha=0.45,
            zorder=4
        )

    # labels
    ax.set_title(f"Timeline peaks based on actor engagement \n{country} - {theme}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Weights")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.margins(x=0)

    # adjust ticks
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True, title="Actor")

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    
    # save
    fig.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved streamgraph plot to {plot_path}")

    return plot_path

# simple plotting function
def simple_peak_plot(results, flagged, output_dir_vis, data_path, USE_WEIGHTS, AGG_FREQ):
    
    # Derive country and theme from data_path
    data_path = Path(data_path)
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # output dir for vis
    outputdir_vis = Path(output_dir_vis)

    # output path
    if USE_WEIGHTS:
        plot_path = outputdir_vis / country / theme / f"{theme}_peaks_plot_weighted.png"
    else:
        plot_path = outputdir_vis / country / theme / f"{theme}_peaks_plot.png"

    # ensure directories
    plot_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 5))
    plt.plot(results["date"], results["count"], color="steelblue", linewidth=1.5)
    if not flagged.empty:
        plt.scatter(
            flagged["date"],
            flagged["count"],
            color="crimson",
            s=35,
            zorder=3,
            label="Anomaly",
        )
    plt.title(f"Incidence Counts with Anomalies (freq={AGG_FREQ})")
    plt.xlabel("Date")
    if USE_WEIGHTS:
        plt.ylabel("Weighted count")
    else:
        plt.ylabel("Count")
    if not flagged.empty:
        plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    print(f"Saved plot to {plot_path}")

# plotly function
def plotly_peaks(results, flagged, output_dir_vis, data_path, USE_WEIGHTS, AGG_FREQ):

    # Derive country and theme from data_path
    data_path = Path(data_path)
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # output dir for vis
    outputdir_vis = Path(output_dir_vis)

    # output path
    plot_path = outputdir_vis / country / theme / f"{theme}_peaks_plot.html"

    # ensure directories
    plot_path.parent.mkdir(parents=True, exist_ok=True)

    # add row index (for peak counts)
    flagged['peakid'] = flagged.index + 1

    # Create plots
    if USE_WEIGHTS:
        fig = px.line(
        results, 
        x="date", 
        y="count", 
        custom_data=["normal_count"]
        )

        fig.update_layout(
            title=f'<b>Weighted text counts with peaks (freq={AGG_FREQ})<b>',
            title_subtitle=dict(text=f"By: {theme} & {country}")
        )

        fig.update_traces(
        line=dict(color="#4C72B0"),
        selector=dict(mode="lines"),
        hovertemplate=(
            "Date: %{x}<br>"
            "Weighted count: %{y}<br>"
            "Raw count: %{customdata[0]}<extra></extra>"
            ) 
        ) 

        if not flagged.empty:
            fig.add_scatter(
                x=flagged["date"],
                y=flagged["count"], 
                customdata=flagged["normal_count"],
                mode="markers+text",
                text=flagged['peakid'],
                textposition='top center',
                name="Trend Peaks",
                marker=dict(color="#992F87", size=10)
            )

            fig.update_traces(
            selector=dict(mode="markers+text"),
            hovertemplate=(
                "Date: %{x}<br>"
                "Weighted count: %{y}<br>"
                "Raw count: %{customdata}<extra></extra>"
                ) 
            ) 

        fig.update_yaxes(
                title_text='Weighted counts',
                showgrid=True,
                gridcolor='lightgray'
            )

        fig.update_xaxes(
            title_text='Time',
            showgrid=True,
            gridcolor='lightgray'
        )

        fig.update_layout(
            plot_bgcolor="#F5F7FA",
            paper_bgcolor="#F5F7FA",
            )

    else:
        fig = px.line(
        results, 
        x="date", 
        y="count", 
        )

        fig.update_layout(
            title=f'<b>Text counts with peaks (freq={AGG_FREQ})<b>',
            title_subtitle=dict(text=f"By: {theme} & {country}")
        )

        fig.update_traces(
        line=dict(color="#4C72B0"),
        selector=dict(mode="lines"),
        hovertemplate=(
            "Date: %{x}<br>"
            "Count: %{y}<br><extra></extra>"
            ) 
        ) 

        if not flagged.empty:
            fig.add_scatter(
                x=flagged["date"],
                y=flagged["count"], 
                mode="markers+text",
                text=flagged['peakid'],
                textposition='top center',
                name="Trend Peaks",
                marker=dict(color="#992F87", size=10)
            )

            fig.update_traces(
            selector=dict(mode="markers+text"),
            hovertemplate=(
                "Date: %{x}<br>"
                "Count: %{y}<br><extra></extra>"
                ) 
            ) 

        fig.update_yaxes(
                title_text='Counts',
                showgrid=True,
                gridcolor='lightgray'
            )

        fig.update_xaxes(
            title_text='Time',
            showgrid=True,
            gridcolor='lightgray'
        )

        fig.update_layout(
            plot_bgcolor="#F5F7FA",
            paper_bgcolor="#F5F7FA",
            )
        
    
    fig.write_html(plot_path)
    print(f"Saved html plot to {plot_path}")

# actor plot
def plotly_peaks_by_actor(df_by_source, flagged, output_dir_vis, data_path, USE_WEIGHTS, AGG_FREQ):

    # Derive country and theme from data_path
    data_path = Path(data_path)
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # output dir for vis
    outputdir_vis = Path(output_dir_vis)

    # output path
    plot_path = outputdir_vis / country / theme / f"{theme}_actor-activity_plot.html"

    # ensure directories
    plot_path.parent.mkdir(parents=True, exist_ok=True)

    # create complete df
    dates = pd.date_range(df_by_source['date'].min(), df_by_source['date'].max(), freq=AGG_FREQ)

    full = pd.MultiIndex.from_product(
        [dates, df_by_source['actor'].unique()],
        names=['date', 'actor']
    ).to_frame(index=False)
    
    df_by_source = (full.merge(df_by_source, on=['date', 'actor'], how='left').assign(count_normalized=lambda d: d['count_normalized'].fillna(0)))

    # Create plot
    fig = px.line(
        df_by_source, 
        x="date", 
        y="count_normalized", 
        color='actor',
        custom_data=["count"]) 
    
    fig.update_yaxes(
        title_text='Normalized counts',
        showgrid=True,
        gridcolor='lightgray'
    )

    fig.update_xaxes(
        title_text='Time',
        showgrid=True,
        gridcolor='lightgray'
    )

    fig.update_layout(
        title=f"<b>Normalized text count by actor (freq={AGG_FREQ}) - vertical lines indicate peaks</b>",
        title_subtitle=dict(text=f"By: {theme} & {country}")
    )
    
    fig.update_traces(
        selector=dict(mode="lines"),
        hovertemplate="Count: %{customdata[0]}<extra></extra>"
    )
    
    if not flagged.empty:
        for i, date in enumerate(flagged["date"].tolist(), start=1):
            fig.add_vline(x=date, line_dash="dot")
            fig.add_annotation(
                x=date,
                y=1.05,
                text=f"Peak {i}",
                textangle=-90,
                showarrow=False,
                xanchor='left',
                yanchor='bottom',
                font=dict(color='gray', size=11)
            )

    fig.update_layout(
        plot_bgcolor="#F5F7FA",
        paper_bgcolor="#F5F7FA",
        )

    fig.write_html(plot_path)
    print(f"Saved actor plot to {plot_path}")