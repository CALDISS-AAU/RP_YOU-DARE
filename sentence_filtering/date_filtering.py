import pandas as pd
import json
from pathlib import Path
import html

all_countries = [
    'DK',
    'ES',
    'FR',
    'HU',
    'IT',
    'RO',
    'SWE',
    'UK'
]

all_themes = [
    'lgb',
    'migration',
    'woke'
]

cols_to_add_from_reduced = [
    'link', 
    'title', 
    'text'
]

number_of_texts = 15 # Max number of texts pr peak pr topic pr country

input_data_folder = '/work/YOU-DARE/sentence_filtering/indexed_data_OG_lan_ONLY'
input_peaks_folder = '/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks'
reduced_data_folder = '/work/YOU-DARE/sentence_filtering/reduced_data/'
output_folder = '/work/YOU-DARE/controversy-mapping/trend-analysis/output/packages_for_researchers'

def filter_dates(df, from_date, to_date):
    ''' Sorts and filtes data based on given arguments.
        - from_date: 'yyyy-mm-dd' this date is included in the final dataset
        - to_date: 'yyyy-mm-dd' this date is included in the final dataset
    '''
    df['publication date'] = pd.to_datetime(
        df['publication date'],
        format='%Y-%m-%d',
        errors='coerce'
    )

    # Filter by from_date and to_date if provided
    if from_date:
        from_dt = pd.to_datetime(from_date, errors='coerce') # Fills all invalid dates with NaT
        if pd.notna(from_dt):
            df = df[
                (df['publication date'].isna()) |  # keep NaT rows
                (df['publication date'] >= from_dt)  # apply filter only to real dates
            ]

    if to_date:
        to_dt = pd.to_datetime(to_date, errors='coerce') # Fills all invalid dates with NaT
        if pd.notna(to_dt):
            df = df[
                (df['publication date'].isna()) |  # keep NaT rows
                (df['publication date'] <= to_dt)  # apply filter only to real dates
            ]

    df['publication date'] = df['publication date'].dt.strftime('%Y-%m-%d')
    
    return df

def sample_even_by_source(df, n, source_col="source", random_state=None):
    if df.empty or n <= 0:
        return df.head(0).copy()
    if len(df) <= n:
        return df.copy()

    tmp = df.copy()
    tmp[source_col] = tmp[source_col].fillna("UNKNOWN")

    # Shuffle rows once for randomness within each source
    tmp = tmp.sample(frac=1, random_state=random_state)

    # Build per-source queues (row indices) in this shuffled order
    source_to_idxs = tmp.groupby(source_col).apply(lambda g: list(g.index)).to_dict()

    # Randomize source order (so who gets picked first is random)
    sources = list(source_to_idxs.keys())
    sources = pd.Series(sources).sample(frac=1, random_state=random_state).tolist()

    chosen = []
    # Round-robin selection
    while len(chosen) < n:
        progressed = False
        for s in sources:
            if source_to_idxs[s]:
                chosen.append(source_to_idxs[s].pop(0))
                progressed = True
                if len(chosen) == n:
                    break
        if not progressed:
            break  # no more rows left anywhere

    return tmp.loc[chosen]

for country in all_countries:
    reduced_data_path = f'{reduced_data_folder}/{country}_reduced.jl'
    with open(reduced_data_path, 'r', encoding='utf-8') as reduced:
        reduced_data = [json.loads(line) for line in reduced]

    df_reduced = pd.DataFrame(reduced_data).reset_index(drop=True)

    for theme in all_themes:
        input_data_path = f'{input_data_folder}/{country}/{country}_{theme}_indexed.jl'
        input_peaks_path = f'{input_peaks_folder}/{country}/{theme}_peaks.json'

        with open(input_data_path, 'r', encoding='utf-8') as input_data:
            data = [json.loads(line) for line in input_data]

        with open(input_peaks_path, 'r', encoding='utf-8') as input_peaks:
            peaks = json.load(input_peaks)

        df = pd.DataFrame(data)
        df['theme'] = theme
        df['matched keywords'] = df[f'matched keywords - {theme}']
        df = df.drop([f'matched keywords - {theme}'], axis=1)

        for peak_id, (from_date, to_date) in peaks.items():
            df_filtered = filter_dates(df, from_date, to_date)
            df_filtered['peak_ID'] = peak_id

            df_chosen = sample_even_by_source(df_filtered, number_of_texts, source_col="source", random_state=42)

            # Join relevant columns from reduced data into chosen data
            df_chosen['text_ID'] = df_chosen['text_ID'].astype(int)

            df_chosen[cols_to_add_from_reduced] = df_reduced.loc[
                df_chosen['text_ID'],
                cols_to_add_from_reduced
            ].to_numpy()

            # Save df_chosen as html
            output_base = Path(output_folder) / country / theme / f"peak_{peak_id}" / "sampled_texts"
            output_base.mkdir(parents=True, exist_ok=True)

            for i, (_, row) in enumerate(df_chosen.iterrows(), start=1):
                title = html.escape(str(row.get("title", "")))
                link = html.escape(str(row.get("link", "")))
                source = html.escape(str(row.get("source", "")))
                date = html.escape(str(row.get("publication date", "")))
                text = html.escape(str(row.get("text", row.get("sentence", "")))).replace("\n", "<br>")

                html_content = f"""<!doctype html>
                <html>
                <head>
                <meta charset="utf-8">
                <title>{title}</title>
                </head>
                <body>

                <h1>{title}</h1>

                <p><strong>Link:</strong> <a href="{link}">{link}</a><br>
                    <strong>Source:</strong> {source}<br>
                    <strong>Publication date:</strong> {date}
                </p>

                <hr>

                <div>{text}</div>

                </body>
                </html>
                """

                output_data_path = output_base / f"text_{i}.html"
                output_data_path.write_text(html_content, encoding="utf-8")