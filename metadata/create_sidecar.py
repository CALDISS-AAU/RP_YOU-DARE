import json
import os
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from rich import pretty
pretty.install()
from rich.console import Console
console = Console()
from rich.theme import Theme


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


# Function
def  create_dc_sidecar(filepath, output_path,creator="", language="", origin_country= ""):
    '''
    function to create a Dublin Core based json sidecar for the project

        Parameters:
        data_path (str or Path): Path to the .jl file
        creator (str): Metadata creator name or system (e.g., Author of scraper)
        language (str): Language code (e.g., "fr" from original data)
        origin_country (str): Country of data origin
    '''
    filepath = Path(filepath)
    stem_parts = filepath.stem.split("_")
    assert len(stem_parts) >= 2, "Filename must have 2 or 3 parts: <source>_<type> or <data>_<source>_<type>"
    dataset_code = stem_parts[-1].upper()
    
    with open(filepath) as f:
        console.print(f"Processing [data]{filepath.name}[/data]", style="info")
        first_entry = json.loads(f.readline())
        scrape_date = first_entry.get("scrape_date")
        source = first_entry.get('source')

    if dataset_code == "SPIDER":
        dc_description = f"Web-scraped dataset containing news articles from {source}"
        dc_type = "Website"
    elif dataset_code == 'YT':
        dc_description = f"Web-scraped and transcribed YouTube videos from {source}"
        dc_type = "Transcribed audio"
    elif dataset_code == 'TELEGRAM':
        dc_description = f"Web-scraped dataset containing telegram posts from {source}"
        dc_type = "Telegram thread dataset"

    # Statistics gathering
    record_count = 0
    field_freq = Counter()
    field_types = defaultdict(set)

    with open(filepath) as f:
        for line in f:
            try:
                record = json.loads(line)
                record_count += 1
                field_freq.update(record.keys())
                for k, v in record.items():
                    field_types[k].add(type(v).__name__)
            except json.JSONDecodeError:
                continue

    dublincore_metadata = {
            "dc:source": source,
            "dc:creator": creator,
            "dc:coverage": origin_country,
            "dc:description": dc_description,
            "dc:publisher": "YOU-DARE/CALDISS",
            "dcterms:modified": scrape_date,
            "dc:type": dc_type,
            "dc:format": "jsonlines",
            "dc:language": language,
            "dcterms:license": "PLACEHOLDER",
        "record_stats": {
            "record_count": record_count,
            "field_types": {k: next(iter(v)) if v else "unknown" for k, v in field_types.items()},
            "field_frequencies": dict(field_freq)
            }
        }
    
    sidecar_path = Path(output_path)
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(dublincore_metadata, f, indent=4)

    console.print(f"✅ Sidecar written to [data]{sidecar_path}[/data]", style="success")


def main():
    parser = argparse.ArgumentParser(description="Create a Dublin Core based json sidecar for a dataset")
    parser.add_argument('--filepath', required=True, help="Path to the .jl JSON Lines file")
    parser.add_argument('--output', required=True, help="Output path for the generated metadata file")
    parser.add_argument('--country', required=True, type=str, help="Origin country for the dataset")
    parser.add_argument('--language', required=True, type=str, help="Language of dataset")
    parser.add_argument('--author', required=True, type=str ,help='Name of dataset creator')
    args = parser.parse_args()

    filepath = args.filepath
    filename = Path(filepath).name
    output_path = args.output
    country = args.country
    language = args.language
    author = args.author



    filename = Path(filepath).name
    valid_suffixes = ['SPIDER.jl', 'YT.jl', 'TELEGRAM.jl']

    if not filename.endswith('.jl'):
        print("Error: File must be a .jl JSON Lines file")
        sys.exit(1)

    if not any(filename.endswith(suffix) for suffix in valid_suffixes):
        console.print("Error: Filename must end with SPIDER.jl, YT.jl or TELEGRAM.jl", style='danger')
        sys.exit(1)

    create_dc_sidecar(filepath, output_path, creator=author, language=language, origin_country=country)

if __name__ == '__main__':
    main()