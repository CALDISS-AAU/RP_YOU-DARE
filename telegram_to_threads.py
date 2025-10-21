import pandas as pd
import json
import os
from os.path import join

# TODO:
    # - Should be written as a module and able to use as a function/module
    # - Should be placed with other scraper functions when ready: YOU-DARE/scrapers/scrapers/functions 


# Path to data files
# TODO: 
    # - Directory to telegram data files as input
    # - Find data files based on filename: "archive.csv" for posts; "reply_archives.csv"
    # - Account/error handle for "reply_archives.csv" not being present (many forums do not have replies)
data_posts_p = '/work/YOU-DARE/scrapers/data/Romania/Telegram/comunitateaidentitara/comunitateaidentitara_2025_07_03-14_18_archive.csv'
data_replies_p = '/work/YOU-DARE/scrapers/data/Romania/Telegram/comunitateaidentitara/comunitateaidentitara_2025_07_03-14_18_reply_archive.csv'



# Read data
posts_df = pd.read_csv(data_posts_p, sep=';')
# TODO:
    # - Account/error handle for "reply_archives.csv" not being present (many forums do not have replies)
    # - If no replies, the posts must still be reformatted and exported as jsonlines (in that case, the 'thread' simply consists of the post)
replies_df = pd.read_csv(data_replies_p, sep=';')


# Rename columns to match posts_df
replies_df = replies_df.rename(columns={
    'ID': 'User ID'
})


# Concatenate posts and replies
# TODO:
    # - Remove missing/empty replies (nan) before concatenating
combined = pd.concat([posts_df, replies_df], ignore_index=True)

# Sort all by Message ID and Timestamp
combined['Timestamp'] = pd.to_datetime(combined['Timestamp'])
combined = combined.sort_values(by=['Message ID', 'Timestamp'])

# Group by Message ID and format
def format_thread(df):
    return '\n\n---\n\n'.join(
        f"{row['User ID']} - {row['Timestamp']}\n{row['Message_text']}"
        for _, row in df.iterrows()
    )

formatted_threads = combined.groupby('Message ID').apply(format_thread).reset_index()
formatted_threads.columns = ['Message ID', 'Thread']

# Join to original post data
posts_threads_df = pd.merge(posts_df, formatted_threads, how='left', on='Message ID')

# Preview data frame
print(posts_threads_df[['Message ID', 'Thread']].head())

# Preview single thread
print(posts_threads_df['Thread'].to_list()[5])

# Write to file
# TODO: 
    # - Filename based on input filename (see convention in pytube functions)
    # - File stored to same directory as input data (see convention in pytube functions)
posts_threads_df.to_json('posts_threads.jl', orient='records', index=False)