from pathlib import Path

import pandas as pd
from docx import Document


HEADERS = [
    "Country",
    "Theme",
    "Peak ID",
    "Start date",
    "End date",
    "No. actors engaged",
    "Number of matched texts",
]


def country_name(country_code):
    names = {
        "DK": "Denmark",
        "ES": "Spain",
        "FR": "France",
        "HU": "Hungary",
        "IT": "Italy",
        "RO": "Romania",
        "SE": "Sweden",
        "UK": "United Kingdom",
    }
    return names.get(country_code, country_code)


def format_theme(theme):
    theme_map = {
        "lgb": "LGB",
        "gender": "Gender",
        "migration": "Migration",
    }
    return theme_map.get(theme, theme)


def _find_table(doc, headers):
    for table in doc.tables:
        if not table.rows:
            continue

        row_headers = [cell.text.strip() for cell in table.rows[0].cells]
        if row_headers == list(headers):
            return table

    return None


def _create_table(doc, headers):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"

    header_cells = table.rows[0].cells
    for idx, header in enumerate(headers):
        header_cells[idx].text = header

    return table


def build_rows_from_flagged(country, flagged):
    
    # return if flagged is empty
    if flagged is None:
        return 

    # country label
    country_label = country_name(country)
    
    # create table rows
    rows = []

    for _, flagged_row in flagged.iterrows():
        row = {
                "Country": country_label,
                "Theme": format_theme(flagged_row["theme"]),
                "Peak ID": flagged_row["peak_id"],
                "Start date": flagged_row["from_date"],
                "End date": flagged_row["to_date"],
                "No. actors engaged": flagged_row["n_actors_engaged"],
                "Number of matched texts": flagged_row["n_texts_total"]
            }
        
        rows.append(row)

    return rows


def write_docx(country, rows, output_file, headers=HEADERS):
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document(output_path) if output_path.exists() else Document()
    if not output_path.exists():
        doc.add_heading(f"{country} - Annotated peaks", level=1)

    table = _find_table(doc, headers)
    if table is None:
        table = _create_table(doc, headers)

    for row in rows:
        cells = table.add_row().cells
        for idx, header in enumerate(headers):
            cells[idx].text = str(row.get(header, ""))

    doc.save(output_path)


def create_peaks_table(country, flagged, output_dir="."):
    output_file = Path(output_dir) / f"{country}_peaks-table.docx"
    rows = build_rows_from_flagged(country, flagged)
    
    if rows is None:
        return
        
    write_docx(country, rows, output_file, headers=HEADERS)
    return output_file
