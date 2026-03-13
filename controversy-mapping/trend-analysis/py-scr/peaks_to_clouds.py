"""Convert word frequency csvs to wordclouds"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import warnings
from tqdm import tqdm

import json
import re
import pandas as pd
import openpyxl

from wordcloud import WordCloud
import matplotlib.pyplot as plt

#INPUT_DIR = "/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks"
INPUT_DIR = "/work/YOU-DARE/controversy-mapping/trend-analysis/output/peaks/SWE/"
OUTPUT_DIR = "/work/YOU-DARE/controversy-mapping/trend-analysis/output/packages_for_researchers"

# Function for wordcloud gen
def generate_wc(text_df, theme, peak, outpath, n_include=100):

    # conform with format
    word_freqs = dict(zip(text_df['term'], text_df['count']))

    # gen wordcloud
    wordcloud = WordCloud(
        width=1920,
        height=1080,
        background_color='white',
        max_words=n_include,
        colormap='coolwarm'
        ).generate_from_frequencies(
            word_freqs
            )
    
    # store
    plt.figure(figsize=(19, 11), dpi=100)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  
    plt.title(f"Word cloud for top {n_include} terms - {theme} - {peak}")
    plt.savefig(outpath)
    plt.close()    

# Main function
def main(INPUT_DIR=INPUT_DIR):
    
    # as Paths
    input_dir_path = Path(INPUT_DIR)
    output_dir_path = Path(OUTPUT_DIR)

    # find csvs
    csv_paths = [str(p.resolve()) for p in input_dir_path.rglob('*.csv')]
    
    # update to console
    print(f"Generating wordclouds for {len(csv_paths)} files...")

    # iter over csvs - gen wordcloud
    if len(csv_paths) > 0:
        for csv_path in tqdm(csv_paths):

            p = Path(csv_path)

            # path components
            theme = str(p.parent.name)
            country = str(p.parent.parent.name)
            
            # peak component
            p_stem = p.stem
            peak = p_stem.replace("_term_frequencies", "")

            # read words csv as data frame
            words_df = pd.read_csv(csv_path)
            words_df['term'] = words_df['term'].astype(str)
            words_df = words_df.dropna()

            # full paths for output
            output_dir_peak = output_dir_path / country / theme / peak 
            outpath_plot = output_dir_peak / f"{peak}_wordcloud.png"
            outpath_xlsx = output_dir_peak / f"{peak}_term-counts.xlsx"
            outpath_plot.parent.mkdir(parents=True, exist_ok=True) # ensure directories
            
            # Skips if file exist - NOTE: Comment out if clouds are to be re-generated
            #if outpath_plot.is_file():
            #    continue

            # output excel
            words_df_filtered = words_df.sort_values('count')
            words_df_filtered = words_df_filtered[words_df_filtered['count'] > 1]
            words_df_filtered.to_excel(outpath_xlsx, index=False)

            # Gen wordcloud from words_df and save to outpath
            try:
                generate_wc(words_df, theme=theme, peak=peak, outpath=outpath_plot)
            except TypeError:
                raise TypeError(f"this {csv_path} is all messed up")
    else:
        print(f"No csvs found in {INPUT_DIR}. Skipping generating wordclouds and excel tables.")

# run main
if __name__ == "__main__":
    main()