"""
Detection of peaks/thematic salience using isolation forest anomaly detection. 
Code adjusted from Codex (OpenAI) output.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union, Sequence
import warnings

import numpy as np
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px

ACTOR_COLOUR_MAP_PATH = "/work/YOU-DARE/raw-data/mappings/actor_identifier_key/actor_colour_map/actor_value_colours.json"
ACTOR_IDENTIFIER_MAP_PATH = "/work/YOU-DARE/raw-data/mappings/actor_identifier_key/actor_identifier_key.csv"

ACTOR_VALUES_CORRECT = {
        "Rasmus Munch": "Rasmus Munch Søndergaard",
        "Retten Til Liv": "Retten til Liv",
        "Toroczkai László": "László Toroczkai",
        "Active news": "Activenews"
}

HU_ACTORS_RENAME = {
    "Dúró Dóra (Mi Hazánk)": "Dóra Dúró",
    "Novák Előd (Mi Hazánk)": "Előd Novák",
    "LH": "Legio Hungaria (LH)",
    "Incze Béla": "Béla Incze",
    "Budaházy Edda": "Edda Budaházy",
    "Budaházy György": "György Budaházy",
    "Influencer 2": "Influencer 1" # Project Legionary (original Influencer 1 omitted from analysis)
}

# actor-colour map
def _build_actor_colour_map(country: str, actors: Sequence[str]):
    
    actor_colour_map_path = Path(ACTOR_COLOUR_MAP_PATH)
    
    with actor_colour_map_path.open() as f:
        actor_colours = json.load(f).get(country, {})

    actor_order = sorted({actor for actor in actors if pd.notna(actor)})
    filtered_actor_colours = {
        actor: actor_colours[actor] for actor in actor_order if actor in actor_colours
    }

    missing_actors = [actor for actor in actor_order if actor not in filtered_actor_colours]
    fallback_palette = px.colors.qualitative.Plotly

    for idx, actor in enumerate(missing_actors):
        filtered_actor_colours[actor] = fallback_palette[idx % len(fallback_palette)]

    return filtered_actor_colours


def _build_actor_display_map(country: str) -> dict[str, str]:
    actor_type_map_path = Path(ACTOR_IDENTIFIER_MAP_PATH)
    actor_type_df = pd.read_csv(actor_type_map_path)

    # fix Marion Marechal
    actor_type_df.loc[actor_type_df["actor"] == "Marion Marechal", "identifier"] = "Marion Marechal"
    actor_type_df.loc[actor_type_df["actor"] == "Marion Marechal", "is_influencer"] = False
    
    actor_type_df = actor_type_df.loc[actor_type_df["country"] == country, ["actor", "identifier"]]

    # fix HU actor names
    if country == "HU":
        actor_type_df["identifier"] = actor_type_df["identifier"].replace(HU_ACTORS_RENAME)

    # sort to have influencer last
    actor_type_df = actor_type_df.sort_values(
        by="identifier",
        key=lambda s: list(zip(s.str.startswith("Influencer"), s))
    )

    # order of actors
    actor_order = actor_type_df["actor"].to_list()
    
    # convert to dict
    actor_display_map = actor_type_df.set_index("actor")["identifier"].to_dict()

    return actor_display_map, actor_order

# filter flagged
def filter_flagged(flagged_path, country, theme, cutoff_date_start, cutoff_date_end):

    # Path
    flagged_path = Path(flagged_path)
    
    # read data
    flagged_in = pd.read_excel(flagged_path, sheet_name=theme)

    # filter for annotated
    flagged = flagged_in.loc[flagged_in['include_in_visualization'].astype('str').str.lower().str.strip() == 'yes', :]
    
    # convert date
    flagged["date"] = pd.to_datetime(flagged["to_date"], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD
    
    # filter for included period
    flagged_filtered = flagged[(flagged["date"] >= cutoff_date_start) & (flagged["date"] < cutoff_date_end)].reset_index(drop=True)

    # warning for excluded annotated peaks
    if flagged.shape[0] > flagged_filtered.shape[0]:

        peaks_removed = list(set(flagged["peak_id"].to_list()) - set(flagged_filtered["peak_id"].to_list()))

        print(f"WARNING!: For {country} - {theme} the following peaks were annotated but excluded because they were outside the period of study:\n {peaks_removed}")
        
    if flagged_filtered.empty:
        return None

    flagged_filtered = flagged_filtered.sort_values("date").reset_index(drop=True)
    flagged_filtered["peak_id"] = flagged_filtered.index+1 # reset index counter

    # add theme
    flagged_filtered["theme"] = theme
    
    return flagged_filtered

# Aggregate couts
def aggregate_counts(df, date_col = "publication date", freq = "D"):
    """
    Aggregate counts based on time frequency. "D" - day for default.
    Options: "D" - day, "W" - week, "2W" - biweekly, "ME" - month, "2ME" - bimonthly, "QE" - quarter, "YE" - year
    """

    if date_col not in df.columns: # check if date col is in data
        raise ValueError(
            f"Expected columns '{date_col}' not in {list(df.columns)}"
    )

    series = df.copy() # copy df
    series[date_col] = pd.to_datetime(series[date_col], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD
    series = series.sort_values(date_col) # sort
    series["count"] = 1 # default count
    daily = series.groupby(date_col, as_index=True)["count"].sum() # count per day
    aggregated = daily.resample(freq).sum() # resample by specified frequency
    full_index = pd.date_range(
        start=aggregated.index.min(),
        end=aggregated.index.max(),
        freq=freq,
    )
    aggregated = aggregated.reindex(full_index, fill_value=0)

    new_ts = aggregated.reset_index().rename(columns={"index": date_col})
    
    # convert to expected data format
    ts_out = new_ts[[date_col, "count"]].copy()
    ts_out[date_col] = pd.to_datetime(ts_out[date_col])
    ts_out["count"] = pd.to_numeric(ts_out["count"], errors="coerce")
    
    return ts_out

## aggregate df
def prepare_results_flagged(
    data_path,
    flagged_path, 
    AGG_FREQ, 
    date_cutoff_start="2015-01-01",
    date_cutoff_end="2025-08-01" # exclusive
    ):

    # Paths
    data_path = Path(data_path)
    
    # Derive country and theme from data_path
    path_elems = data_path.stem.split('_')
    country = path_elems[0]
    try:
        theme = path_elems[1]
    except IndexError:
        raise IndexError(f"Filename {data_path.stem} does not match expected pattern {{ctr}}_{{theme}}_matched.jl. No theme found")

    # read data
    with open(data_path, "r") as f:
        lines = f.read().splitlines()

    data_records = [json.loads(line) for line in lines]
    df = pd.DataFrame(data_records)

    # cut-off date
    if "publication date" not in df.columns: # check if date col is in data
        raise ValueError(
            f"Expected columns 'publication date' not in {list(df.columns)}"
    )
    df["publication date"] = pd.to_datetime(df["publication date"], format="%Y-%m-%d") # convert to datetime - expects YYYY-MM-DD

    cutoff_date_start = pd.to_datetime(date_cutoff_start, format="%Y-%m-%d")
    cutoff_date_end = pd.to_datetime(date_cutoff_end, format="%Y-%m-%d")

    df = df[(df["publication date"] >= cutoff_date_start) & (df["publication date"] < cutoff_date_end)].reset_index(drop=True)

    # iter over actors and detect peaks
    results_all_df = pd.DataFrame()

    for actor in df['actor'].unique():
        # exclude Project Legionary
        if actor == "Project Legionary":
            continue

        df_actor = df[df['actor'] == actor]

        # n texts
        n_texts = df_actor.shape[0]

        # aggregate by time frequency
        df_agg = aggregate_counts(df_actor, freq=AGG_FREQ)

        # add date
        df_agg['date'] = df_agg['publication date'].dt.to_period("M").dt.end_time.dt.strftime("%Y-%m-%d")
        
        # add actor and total texts
        df_agg['actor'] = actor
        df_agg['total_texts'] = n_texts

        # append
        results_all_df = pd.concat([results_all_df, df_agg])

    # retrieve flagged
    flagged = filter_flagged(flagged_path, country, theme, cutoff_date_start, cutoff_date_end)

    return results_all_df, flagged

# main plotting function
def gen_streamgraph_peaks(country, results, flagged, plot_path_out, data_path, AGG_FREQ):
    """Generate a streamgraph of smoothed within-actor monthly weights and peak labels."""

    required_cols = {"date", "actor", "count", "total_texts"}
    missing_cols = required_cols.difference(results.columns)
    if missing_cols:
        raise ValueError(f"Expected columns {sorted(required_cols)} in results, missing {sorted(missing_cols)}")

    if results.empty:
        raise ValueError("No results available for streamgraph plotting. No plot generated")
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
    plot_path_out.parent.mkdir(parents=True, exist_ok=True)

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
            plot_df[["date", "actor", "count"]],
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
    actors_included = weight_wide.sum(axis=0).sort_values(ascending=False).index.tolist()
    
    # colours and actor order
    actor_display_map, actor_order = _build_actor_display_map(country)
    actor_order = [actor for actor in actor_order if actor in actors_included]
    actor_colour_map = _build_actor_colour_map(country, actor_order)
    colors = [actor_colour_map[actor] for actor in actor_order]
    smoothed_weights = weight_wide[actor_order]

    # values to plot
    x_values = smoothed_weights.index.to_pydatetime()
    stacked_values = smoothed_weights.to_numpy().T
    total_weights = stacked_values.sum(axis=0)
    baseline = -total_weights / 2 # Shifts start of height in the negative (half of height below 0)

    # draw plot
    fig, ax = plt.subplots(figsize=(12, 7))

    lower = baseline.copy()
    for actor, actor_weights, color in zip(actor_order, stacked_values, colors):
        upper = lower + actor_weights
        ax.fill_between(
            x_values,
            lower,
            upper,
            label=actor_display_map.get(actor, actor),
            color=color,
            alpha=0.95,
            linewidth=0.5,
        )
        lower = upper

    # extract peaks
    if flagged is not None and not flagged.empty and {"date", "peak_id"}.issubset(flagged.columns):
        peak_df = flagged[["date", "peak_id"]].copy()

        # datetime
        peak_df["date"] = pd.to_datetime(peak_df["date"])

        # add peak dots
        y_padding = max(total_weights.max() * 0.04, 0.002)
        upper_envelope = total_weights / 2

        # sort peak_df by date
        peak_df = peak_df.sort_values('date', ascending=True)

        for peak_id, peak in peak_df.iterrows():
            peak_idx = smoothed_weights.index.get_indexer([peak["date"]])
            if peak_idx.size == 0 or peak_idx[0] < 0:
                continue

            x_peak = peak["date"].to_pydatetime()
            y_peak = upper_envelope[peak_idx[0]]# + y_padding
            ax.scatter(x_peak, y_peak, color="black", s=22, zorder=5)
            ax.text(
                x_peak,
                y_peak + y_padding*0.2,
                #f"{int(peak_id+1)}\n({peak['date'].strftime('%Y-%m')})", # Peak ID + date
                f"{int(peak_id+1)}", # only peak ID
                ha="center",
                va="bottom",
                fontsize=12,
                color="black",
                fontname="DejaVu Sans",
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
    #ax.set_title(f"Timeline peaks based on actor engagement \n{country} - {theme}")
    #ax.set_xlabel("Time", fontname="Liberation Sans")
    #ax.set_ylabel("Weights")
    #ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7], bymonthday=-1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.margins(x=0.01, y=0.10)
    ax.set_yticks([])
    ax.tick_params(axis="y", left=False, labelleft=False)

    # adjust ticks
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
        frameon=True,
        #title="Actor",
        ncol=max(1, min(4, len(actor_order))),
        prop={"family": "DejaVu Sans"},
        title_fontproperties={"family": "DejaVu Sans"},
    )

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontname="DejaVu Sans")
    plt.tight_layout(rect=(0, 0.08, 1, 1))
    
    # write to PNG and PDF
    Path(plot_path_out).parent.mkdir(parents=True, exist_ok=True)
    png_path = Path(plot_path_out).with_suffix(".png")
    pdf_path = Path(plot_path_out).with_suffix(".pdf")

    fig.savefig(png_path, dpi=300, bbox_inches="tight", format="png")
    fig.savefig(pdf_path, dpi=300, bbox_inches="tight", format="pdf")
    
    plt.close(fig)
    print(f"Saved streamgraph plot to {png_path} and {pdf_path}")

    return plot_path_out
