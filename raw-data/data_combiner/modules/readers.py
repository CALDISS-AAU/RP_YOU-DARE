"""Reader functions for data combiner"""

import pandas as pd

def read_telegram(paths_dict, sep=';'):
    """
    Reader for telegram data. Returns iterable to comply with main combiner.
    """

    # retrieve paths from dict
    post_csv_path = paths_dict.get('posts')
    replies_csv_path = paths_dict.get('replies')
    
    # Read posts
    posts_df = pd.read_csv(post_csv_path, sep=sep, engine='python', on_bad_lines='skip')
    
    # Read replies if any, else None
    try:
        replies_df = pd.read_csv(replies_csv_path, sep=sep, engine='python', on_bad_lines='skip') if replies_csv_path else None
    except FileNotFoundError:
        replies_df = None
    
    return [(posts_df, replies_df)] # main combiner function expects iterable


def read_jsonl_chunks(data_p, chunksize = 10000, encoding = "utf-8"):
    """Yield a JSONL file as dataframe chunks using pandas' chunk iterator."""
    
    reader = pd.read_json(data_p, lines=True, chunksize=chunksize, encoding=encoding)
    yield from reader