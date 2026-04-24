# import pandas as pd

# df = pd.read_csv('/work/YOU-DARE/scrapers/data/Denmark/DDUngdom_MANUAL/DDUngdom_fixed_dates_MANUAL.csv')
# pd.to_json(df, lines=True)

import pandas as pd
from pathlib import Path

# file_path = Path("/work/YOU-DARE/scrapers/data/Denmark/DDUngdom_MANUAL/DDUngdom_fixed_dates_MANUAL.csv")
file_path = Path("/work/YOU-DARE/scrapers/data/Denmark/DFUngdom_MANUAL/DF_Ungdom_fixed_dates_MANUAL.csv")

df = pd.read_csv(file_path, sep=";")

output_path = file_path.with_suffix(".jl")

df.to_json(output_path, orient="records", lines=True)