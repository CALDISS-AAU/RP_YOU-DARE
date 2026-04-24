import pandas as pd
import os
from pathlib import Path
from datetime import datetime

data_dir = Path("/work/YOU-DARE/raw-data/final_raw")

data_files = os.listdir(data_dir)

scraped_time_df = pd.DataFrame()

df = pd.read_json(data_dir / data_files[0], lines=True)

def format_date(datestring):

    if type != str:
        return(datestring)

    try:
        date = datetime.strptime(datestring, "%Y-%m-%d").date()
    except ValueError:
        date = datetime.strptime(datestring, "%d-%m-%Y").date()

    return(date)

for file in data_files:
    data_in_p = data_dir / file

    df = pd.read_json(data_in_p, lines=True)

    #df['scrape_date'] = df['scrape_date'].apply(format_date)

    try: 
        df['scrape_date'] = pd.to_datetime(df['scrape_date'], format="%Y-%m-%d")
    except ValueError:
        print(file)
        continue

    grouped = df.groupby(['actor', 'platform'])

    max_scraped = grouped['scrape_date'].max().reset_index()

    scraped_time_df = pd.concat([scraped_time_df, max_scraped], axis=0)