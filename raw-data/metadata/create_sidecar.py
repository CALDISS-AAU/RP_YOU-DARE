import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from rich import pretty
from rich.console import Console
from rich.theme import Theme

pretty.install()

custom_theme = Theme({
    "info": "cyan2",
    "success": "medium_spring_green",
    "warning": "bold yellow",
    "danger": "bold red",
    "title": "bold magenta",
    "dim": "dim white",
    "data": "bold white"
})

console = Console(theme=custom_theme)
# ----------------------------
# FIELD DESCRIPTIONS
# ----------------------------
field_descriptions = {
    'author': 'Author of the article',
    'title': 'Title of the article',
    'publication_date': 'The date of content publication',
    'scrape_date': 'The date of data collection',
    'source': 'The name of the actor',
    'article_text': 'The text body of the article, cleared of any formatting',
    'embedded_media_links': 'Video links inside article body',
    'links_in_text': 'Links or hyperlinks found inside the article body',
    'categories': 'Tags or article categories from the webpage',
    'article_html': 'The full html code from the article, including all elements',
    'video_id': 'YouTube ID from each video',
    'video_title': 'Title of the video',
    'video_link': 'URL to the video',
    '\nPost_text': 'Telegram Post text content',
    '\nComment_1': 'Comment(s) to the Post',
    'Timestamp': 'Date time for message',
    'User ID': 'ID of the Telegram user',
    'platform': 'Dataset source platform (SPIDER, YT, TELEGRAM)'
}

ignored_keys = [
    'Has_media',
    'Reply_to_ID',
    'Replies',
    'Forwards',
    'Total_reactions',
    'Views',
    'Reply_ER_reach',
    'Reply_ER_impressions',
    'Forwards_ER_reach',
    'Reaction_ER_reach',
    'Forwards_ER_impressions',
    'Thumbs_up',
    'Thumbs_down',
    'Heart',
    'Fire',
    'Clap',
    'Poop',
    'Smile',
    'Thinking',
    'Smile_with_hearts',
    'Angry',
    'Starstruck',
    'Vomit',
    "Media save directory",
    'Pray',
    'Edit_date',
    'Single_tear',
    'Original_language',
    'Translation_confidence',
    'Translate_text',
    'Reactions_ER_impressions',
    'Exploding_head',
    'Scream',
    "",
    'To'
    ]

# ----------------------------
# MAIN FUNCTION
# ----------------------------
def  generate_sidecar(jsonl_file, output_path,creator="", language="", origin_country= ""):
    '''
    function to create a Dublin Core based json sidecar for the project

        Parameters:
        data_path (str or Path): Path to the .jsonl file
        creator (str): Metadata creator name or system (e.g., Author of scraper)
        language (str): Language code (e.g., "fr" from original data)
        origin_country (str): Country of data origin
    '''
    # Statistics gathering
    record_count = 0
    field_freq = Counter()
    field_types = defaultdict(set)
    dataset_types = set()
    sources = set()
    scrape_dates = []
    publication_dates = []
    dataset_codes = set()
    example_values = {}
    dataset_composition = Counter()
    
    console.print(f'Processing [data]{jsonl_file.name}[/data]', style='info')

    try:
        with open(jsonl_file, encoding='utf-8') as f:
            for line_number, line in enumerate(f, start=1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                        console.print(f"[warning]⚠ Skipping corrupted line {line_number}[/warning]")
                        continue

                record_count +=1
                # --------------------
                # PLATFORM LOGIC
                # --------------------
                platform = record.get('platform', 'UNKNOWN')
                platform = str(platform).strip().upper()
                dataset_composition[platform] += 1

                # -------------------
                # SOURCES + DATES
                # -------------------
                # sources.add(record.get('sources', 'unknown')) # If source is not available, unknown is set
                scrape_dates.append(record.get('scrape_date'))
                publication_dates.append(record.get('publication_date'))
                publication_dates_clean = [d for d in publication_dates if d]
                if publication_dates_clean:

                    start_date = min(publication_dates_clean)
                    end_date = max(publication_dates_clean)

                    start_year = start_date[:4]
                    end_year = end_date[:4]

                    temporal = f"{start_year} - {end_year}"
                else:
                    temporal = "unknown"    

                

                # -------------------
                # FIELD STATS
                # -------------------
                field_freq.update(k for k in record.keys() if k not in ignored_keys)

                for k, v in record.items():
                    if k in ignored_keys:
                        continue

                    if k not in example_values and v is not None:
                        example_values[k] = v
                    
                    field_types[k].add(type(v).__name__)
    except Exception as e:
        console.print(f'[danger]Error reading file: {e}[/danger]')
        sys.exit(1)

    # ------------------
    # DATASET LOGIC
    # ------------------
    dataset_types = {k for k, v in dataset_composition.items() if v > 0}

    if len(dataset_types) > 1:
        dc_type = list(sorted(dataset_types))
        # dc_description = (
        #     f'Combined dataset containing multiple: '
        #     f"{','.join(sorted(dataset_types))}"
        # )
    else:
        dataset_type = next(iter(dataset_types), 'UNKNOWN')
        if dataset_type == 'SPIDER':
            dc_type = 'Website'
            # dc_description = f'Web-scraped dataset containing articles from {', '.join(sources)}'

        elif dataset_type == 'YT':
            dc_type = 'Transcribed audio'
            # dc_description = f'Web--scraped and transcribed YouTube videos from {', '.join(sources)}'
        
        elif dataset_type == "TELEGRAM":
            dc_type = "Telegram thread dataset"
            # dc_description = f"Web-scraped dataset containing Telegram posts from {', '.join(sources)}"
        
        else:
            dc_type = 'Other Dataset'
            # dc_description = f'Dataset from {', '.join(sources)}'
        # Clean composition
        dataset_composition = {k: v for k,v in dataset_composition.items() if v > 0}

        # ----------------
        # BUILD METADATA
        # ----------------
    dublincore_metadata = {
        "@context": {
            "dcterms": "http://purl.org/dc/terms/",
            },
        "@type": "dcterms:Dataset",
        "dcterms:creator": creator,
        "dcterms:spatial": origin_country,
        "dcterms:description": "This resource contains web scraped content collected for Far-Right gender controversy mapping as part of the EU Horizon project YOU-DARE. Data are collected from three main sources: websites, YouTube and Telegram. With the exception of manually scraped sources, all data have been collected via Python programs. All software and code used for collecting the data along with documentation is made freely available on GitHub at the following link: https://github.com/CALDISS-AAU/YOU-DARE_scrapers",
        "dcterms:title": f"Web Scraped Content Dataset for Far-Right Gender Controversy Mapping - {origin_country}",
        "dcterms:publisher": "YOU-DARE/CALDISS",
        "dcterms:modified": max([d for d in scrape_dates if d], default="unknown"),
        "dcterms:format": "jsonlines",
        "dcterms:language": language,
        "dcterms:date": 2026,
        "dcterms:identifier": "10.5281/zenodo.19188182",
        "dcterms:rights": 'Access granted upon request; non-commercial use only; attribution required.',

    "record_stats": {
        "record_count": record_count,
    
        "dataset_composition": dataset_composition,

        "dataset_percentages": {
            k: round(v / record_count * 100, 2)
            for k, v in dataset_composition.items()
        } if record_count > 0 else {},

        "field_types": {
            k: next(iter(v - {'NoneType'})) if (v - {'NoneType'}) else next(iter(v))
            for k, v in field_types.items()
        },
        "field_frequencies": dict(field_freq),

        "data_examples": [
            {
                "variable": k,
                "example_values": v,
                "variable_description": field_descriptions.get(
                    k, f"A field type of {type(v).__name__}."
                ),
            }
            for k, v in example_values.items()
            if k not in ignored_keys
        ]
    }
}

    # ----------------
    # WRITE FILE
    # ----------------
    output_path = Path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dublincore_metadata, f, indent=4)

    console.print(f"✅ Sidecar written to [data]{output_path}[/data]", style="success")

# ----------------
# CLI
# ----------------
def main():
    parser = argparse.ArgumentParser(
        description="Create a Dublin Core based json sidecar for a dataset"
        )
    parser.add_argument('--file', required=True, help="Path to .jsonl file")
    parser.add_argument('--output', required=True, help="Output path for the generated metadata file")
    parser.add_argument('--country', required=True, type=str, help="Origin country for the dataset")
    parser.add_argument('--language', required=True, type=str, help="Language of dataset")
    parser.add_argument('--author', required=True, type=str ,help='Name of dataset creator')

    args = parser.parse_args()

    jsonl_file = Path(args.file)
    if not jsonl_file.exists():
        console.print(f"[danger]File not found {jsonl_file}[/danger]")
        sys.exit(1)
    
    generate_sidecar(
        jsonl_file,
        args.output,
        creator=args.author,
        language=args.language,
        origin_country=args.country
    )
    
    console.print(f"[bold cyan] Found {(jsonl_file)} file. Generating sidecar")
    console.print(f"[title]Jobs done - more work![/title]")

if __name__ == '__main__':
    main()