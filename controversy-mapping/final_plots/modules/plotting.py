from __future__ import annotations
from pathlib import Path
import os
from dotenv import load_dotenv

from dataclasses import dataclass
import json
from typing import Any, Iterable, List, Optional, Sequence

import pandas as pd
import numpy as np
from collections import Counter

import plotly.express as px
import plotly.graph_objects as go

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


ACTOR_COLOUR_MAP_PATH = str(REPO_ROOT / "raw-data" / "mappings" / "actor_identifier_key" / "actor_colour_map" / "actor_value_colours.json")
ACTOR_IDENTIFIER_MAP_PATH = str(REPO_ROOT / "raw-data" / "mappings" / "actor_identifier_key" / "actor_identifier_key.csv")

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


def _build_actor_colour_map(country: str, actors: Sequence[str]):
    
    actor_colour_map_path = Path(ACTOR_COLOUR_MAP_PATH)
    
    with actor_colour_map_path.open() as f:
        actor_colours = json.load(f).get(country, {})

    actor_order = sorted({actor for actor in actors})
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


def _estimate_annotation_box(label: str, font_size: float) -> tuple[float, float]:
    width_px = max(90.0, len(str(label)) * font_size * 0.7 + 24)
    height_px = font_size * 1.9 + 14
    return width_px, height_px


def _annotation_box(label_x, label_y, box_width, box_height, xanchor, yanchor):
    if xanchor == "left":
        x0, x1 = label_x, label_x + box_width
    elif xanchor == "right":
        x0, x1 = label_x - box_width, label_x
    else:
        x0, x1 = label_x - box_width / 2, label_x + box_width / 2

    if yanchor == "bottom":
        y0, y1 = label_y, label_y + box_height
    elif yanchor == "top":
        y0, y1 = label_y - box_height, label_y
    else:
        y0, y1 = label_y - box_height / 2, label_y + box_height / 2

    return x0, y0, x1, y1


def _boxes_overlap(box_a, box_b, pad_x: float = 0.008, pad_y: float = 0.012) -> bool:
    ax0, ay0, ax1, ay1 = box_a
    bx0, by0, bx1, by1 = box_b
    return not (
        ax1 + pad_x < bx0
        or bx1 + pad_x < ax0
        or ay1 + pad_y < by0
        or by1 + pad_y < ay0
    )


def _place_actor_annotations(
    actor_with_umap_df: pd.DataFrame,
    actor_type_map: dict[str, str],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    resize_factor: float,
) -> list[dict[str, Any]]:
    if actor_with_umap_df.empty:
        return []

    x_span = max(x_max - x_min, 1e-9)
    y_span = max(y_max - y_min, 1e-9)
    font_size = 10 * resize_factor
    figure_width_px = 1920.0
    figure_height_px = 1080.0

    actor_label_df = actor_with_umap_df.copy().reset_index(drop=True)
    actor_label_df["display_label"] = actor_label_df["actor"].replace(actor_type_map)
    actor_label_df["x_norm"] = (actor_label_df["umap_1"] - x_min) / x_span
    actor_label_df["y_norm"] = (actor_label_df["umap_2"] - y_min) / y_span

    norm_points = actor_label_df[["x_norm", "y_norm"]].to_numpy(dtype=float)
    neighbour_distances = []
    for idx, point in enumerate(norm_points):
        others = np.delete(norm_points, idx, axis=0)
        if others.size == 0:
            neighbour_distances.append(np.inf)
        else:
            neighbour_distances.append(np.min(np.linalg.norm(others - point, axis=1)))

    actor_label_df["nearest_distance"] = neighbour_distances
    actor_label_df["label_length"] = actor_label_df["display_label"].astype(str).str.len()
    actor_label_df = actor_label_df.sort_values(
        ["nearest_distance", "label_length"],
        ascending=[True, False],
    ).reset_index(drop=True)

    placed_boxes = []
    annotations = []
    candidate_specs = [
        ("left", "bottom", 1, 1),
        ("right", "bottom", -1, 1),
        ("left", "top", 1, -1),
        ("right", "top", -1, -1),
        ("left", "middle", 1, 0),
        ("right", "middle", -1, 0),
        ("center", "bottom", 0, 1),
        ("center", "top", 0, -1),
    ]

    for row in actor_label_df.itertuples(index=False):
        box_width_px, box_height_px = _estimate_annotation_box(row.display_label, font_size)
        box_width = box_width_px / figure_width_px
        box_height = box_height_px / figure_height_px
        base_gap_x = max(0.01, box_width * 0.15)
        base_gap_y = max(0.015, box_height * 0.15)
        best_choice = None
        best_score = None

        for scale in range(1, 2):
            gap_x = base_gap_x * scale
            gap_y = base_gap_y * scale

            for xanchor, yanchor, direction_x, direction_y in candidate_specs:
                shift_x_px = direction_x * gap_x * figure_width_px
                shift_y_px = -direction_y * gap_y * figure_height_px
                label_x = row.x_norm + (shift_x_px / figure_width_px)
                label_y = row.y_norm - (shift_y_px / figure_height_px)
                box = _annotation_box(label_x, label_y, box_width, box_height, xanchor, yanchor)

                out_of_bounds = (
                    max(0.0, -box[0])
                    + max(0.0, -box[1])
                    + max(0.0, box[2] - 1.0)
                    + max(0.0, box[3] - 1.0)
                )
                overlaps = sum(_boxes_overlap(box, placed_box) for placed_box in placed_boxes)
                score = overlaps * 1000 + out_of_bounds * 100 + gap_x + gap_y

                if best_score is None or score < best_score:
                    best_score = score
                    best_choice = (xanchor, yanchor, shift_x_px, shift_y_px, box)

                if overlaps == 0 and out_of_bounds == 0:
                    break

            if best_score == gap_x + gap_y:
                break

        xanchor, yanchor, shift_x_px, shift_y_px, box = best_choice
        placed_boxes.append(box)

        annotations.append(
            dict(
                x=row.umap_1,
                y=row.umap_2,
                xref="x",
                yref="y",
                ax=shift_x_px,
                ay=shift_y_px,
                text=f"<b>{row.display_label}</b>",
                xanchor=xanchor,
                yanchor=yanchor,
                showarrow=True,
                arrowhead=0,
                arrowwidth=1,
                arrowcolor="black",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4,
                font=dict(size=font_size, family="DejaVu Sans", color="black"),
            )
        )

    return annotations


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
            "x_range": (float(annoreg.get("x_lim_lower")), float(annoreg.get("x_lim_upper"))),
            "y_range": (float(annoreg.get("y_lim_lower")), float(annoreg.get("y_lim_upper")))
        }

        regions.append(region_add)

    # split chunks in several lines lines
    df = chunks_with_umap_df.copy()
    #df['chunk'] = df['chunk'].apply(add_linebreaks)

    # correct actor values
    df["actor"] = df["actor"].replace(ACTOR_VALUES_CORRECT)
    actor_with_umap_df["actor"] = actor_with_umap_df["actor"].replace(ACTOR_VALUES_CORRECT)

    # exclude Project Legionary
    if country == "HU":
        actor_with_umap_df = actor_with_umap_df[actor_with_umap_df["actor"] != "Project Legionary"]
        df = df[df["actor"] != "Project Legionary"]

    # fix wrong actor name for HU
    if country == "HU":
        actor_with_umap_df["actor"] = actor_with_umap_df["actor"].replace({"Mi Hazánk": "Dúró Dóra (Mi Hazánk)"})
        actor_with_umap_df = actor_with_umap_df.groupby("actor").mean().reset_index()
        
    # derive colours and identifiers
    actor_colour_map = _build_actor_colour_map(country, df["actor"].unique().tolist())
    actor_identifier_map, actor_order = _build_actor_display_map(country)
    
    # filter actor order for actors present
    actor_order = [actor for actor in actor_order if actor in df["actor"].unique().tolist()]

    # settiings for hoverdata
    hover_data = {
        'umap_1': False,
        'umap_2': False,
        'actor': True,
        'entry_ID': True,
        #'chunk': True,
    }

    labels = {
        'actor': 'Actor',
        'entry_ID': 'Text ID',
        #'chunk': 'Text',
    }

    # scatter for actors
    fig_actor = px.scatter(
        df,
        x='umap_1',
        y='umap_2',
        color='actor',
        color_discrete_map=actor_colour_map,
        category_orders={'actor': actor_order},
        hover_data=hover_data,
        labels=labels,
        render_mode="svg",
        opacity=0.55,
    )

    
    for trace in fig_actor.data:
        old_name = trace.name
        if old_name in actor_identifier_map:
            new_name = actor_identifier_map[old_name]
            trace.name = new_name
            trace.legendgroup = new_name

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
                size=18,
                symbol='star-triangle-up',
                color='black',
                line=dict(
                    color=actor_with_umap_df['actor']
                    .map(actor_colour_map)
                    .fillna("black")
                    .tolist(),
                    width=2,
                ),
            ),
            #text=actor_with_umap_df['actor'].replace(actor_type_map),
            #textposition='top center',
            #textfont=dict(size=10 * resize_factor),
            name='Actors',
            showlegend=False,
        )
    )

    x_values_all = pd.concat([df["umap_1"], actor_with_umap_df["umap_1"]], ignore_index=True)
    y_values_all = pd.concat([df["umap_2"], actor_with_umap_df["umap_2"]], ignore_index=True)
    x_range = x_values_all.max() - x_values_all.min()
    y_range = y_values_all.max() - y_values_all.min()
    x_min, x_max = x_values_all.min() - (0.1 * x_range), x_values_all.max() + (0.1 * x_range)
    y_min, y_max = y_values_all.min() - (0.1 * y_range), y_values_all.max() + (0.1 * y_range)

    # add actor labels for mean positions
    for annotation in _place_actor_annotations(
        actor_with_umap_df=actor_with_umap_df,
        actor_type_map=actor_identifier_map,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        resize_factor=resize_factor,
    ):
        fig.add_annotation(**annotation)


    # actor-only legend
    fig.update_layout(
        #title=f"Semantic mapping for {country} - {theme}",
        #legend=dict(title=dict(text='Actor')),
    )

    # draw ellipses
    skipped_regions = []
    for r in regions:
        x0, x1 = r["x_range"]
        y0, y1 = r["y_range"]

        # only draw region if at least one point is inside
        mask = df["umap_1"].between(x0, x1) & df["umap_2"].between(y0, y1)
        if not mask.any():
            if x1 < x0:
                skipped_reason = f"X lower {x0} is higher than X upper {x1} which is invalid."
            elif y1 < y0:
                skipped_reason = f"Y lower {y0} is higher than Y upper {y1} which is invalid."
            else:
                skipped_reason = f"Provided x and y values are outside the range of the plot."
            skipped_regions.append(f"Region {r["label"]}: {skipped_reason}")
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
    
    # warn for skipped regions
    if skipped_regions:
        print(
            f"WARNING!: For {country}-{theme} skipped {len(skipped_regions)} with invalid input: {'\n'.join(skipped_regions)}"
        )
        
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
        font_family="DejaVu Sans"
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
        scale=5,
    )
    fig.write_image(
        str(pdf_path),
        format="pdf",
        width=1920,
        height=1080,
        scale=5,
    )

    print(f"Saved semantic map plots to {png_path} and {pdf_path}")
