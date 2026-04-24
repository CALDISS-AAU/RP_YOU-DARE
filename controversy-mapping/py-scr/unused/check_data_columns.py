import json
import glob
import os
from rich import pretty
pretty.install()
from rich.console import Console
from rich.theme import Theme

# Secret console recipe
console = Console(record=True)

# Loading dataset lists
FRANCE_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/France/*.j*',
    recursive = True
)

HUNGARY_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/Hungary/*.j*',
    recursive=True
    )

ITALY_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/Italy/*.jl',
    recursive=True
    )

DENMARK_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/Denmark/*.jl',
    recursive=True
)

UK_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/United_Kingdom/*.jl',
    recursive=True
)

SWEDEN_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/Sweden/*.jl',
    recursive=True
)

ROMANIA_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/Romania/*.jl',
    recursive=True
)

SPAIN_dir = glob.glob(
    '/work/YOU-DARE/scrapers/data/backup_data/Spain/*.jl',
    recursive=True
)

# Very sexy function
def printing_keys(jl_files, output_path):
    for file in jl_files:
        console.print(
            f'📁 Processing [data]{os.path.basename(file)}[/data] :vampire:',
            style="bold gold3"
        )
        try:
            with open(file) as f:
                first_obj = json.loads(next(f))

            console.print(first_obj.keys(), style='cyan2')

        except json.JSONDecodeError:
            console.print(
                f"[Warning]⚠ Skipping corrupted first line in {os.path.basename(file)}",
                style="bold red"
            )
            continue

        except StopIteration:
            console.print(
                f"[Warning]⚠ {os.path.basename(file)} is empty",
                style="bold red"
            )


    text = console.save_text(output_path)

printing_keys(FRANCE_dir, '/work/YOU-DARE/controversy-mapping/logs/France_keys.txt')
printing_keys(HUNGARY_dir, '/work/YOU-DARE/controversy-mapping/logs/Hungary_keys.txt')
printing_keys(ITALY_dir, '/work/YOU-DARE/controversy-mapping/logs/Italy_keys.txt')
printing_keys(DENMARK_dir, '/work/YOU-DARE/controversy-mapping/logs/Denmark_keys.txt')
printing_keys(UK_dir, '/work/YOU-DARE/controversy-mapping/logs/UK_keys.txt')
printing_keys(SWEDEN_dir, '/work/YOU-DARE/controversy-mapping/logs/Sweden_keys.txt')
printing_keys(ROMANIA_dir, '/work/YOU-DARE/controversy-mapping/logs/Romania_keys.txt')
printing_keys(SPAIN_dir, '/work/YOU-DARE/controversy-mapping/logs/Spain_keys.txt')

console.print("All keys successfully handled, saved and prayed using computer magic", style='#D670D6')