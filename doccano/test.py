import pandas as pd
import shutil

jl_path = '/work/YOU-DARE/scrapers/data/Hungary/fidesz_videos_YT/combined_metadata.jl'

df = pd.read_json(jl_path, lines=True)
df["source"] = "Fidesz videos"          # creates the column if it didn't exist
df.to_json(jl_path, orient="records", lines=True, force_ascii=False)

# print("Updated 'source' for all rows.")

# import pandas as pd
# import numpy as np

# # Load
# df = pd.read_json(jl_path, lines=True)

# # 1) Parse to UTC-aware, then drop tz to make all timestamps tz-naive (uniform)
# df["publication_date"] = (
#     pd.to_datetime(df["publication_date"], errors="coerce", utc=True)
#       .dt.tz_convert(None)
# )

# # 2) Build naive Timestamp bounds (same timezone-agnostic basis as the series)
# VOX_ranges = [
#     ('2017-03-01','2017-03-31'),
#     ('2017-06-15','2017-07-14'),
#     ('2018-03-01','2018-03-31'),
#     ('2018-06-15','2018-07-14'),
#     ('2019-03-01','2019-07-14'),
#     ('2019-10-10','2019-12-10'),
#     ('2020-03-01','2020-03-31'),
#     ('2020-06-15','2020-07-14'),
#     ('2021-03-01','2021-03-31'),
#     ('2021-06-15','2021-07-14'),
#     ('2022-03-01','2022-03-31'),
#     ('2022-06-15','2022-07-14'),
#     ('2023-03-01','2023-03-31'),
#     ('2023-06-15','2023-08-23'),
#     ('2024-03-01','2024-03-31'),
#     ('2024-05-09','2024-07-14'),
#     ('2025-03-01','2025-03-31'),
#     ('2025-06-15','2025-07-14'),
# ]
# ranges_ts = [(pd.to_datetime(s), pd.to_datetime(e)) for s, e in VOX_ranges]

# # 3) Mask for 'in ANY range' (inclusive)
# masks = [df["publication_date"].between(s, e, inclusive="both") for s, e in ranges_ts]
# any_mask = np.logical_or.reduce(masks) if masks else pd.Series(False, index=df.index)

# # 4) Counts
# total_count = int(any_mask.sum())
# counts_per_range = [int(m.sum()) for m in masks]

# print("Counts per interval:", counts_per_range)
# print("Total count:", total_count)

# # Optional: tidy table
# out = pd.DataFrame(VOX_ranges, columns=["start","end"])
# out["count"] = counts_per_range
# print(out)
