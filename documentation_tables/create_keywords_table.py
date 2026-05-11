from pathlib import Path
import os
from dotenv import load_dotenv

import json

from docx import Document


ENV_PATH = next(
    (
        parent / ".env"
        for parent in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
        if (parent / ".env").exists()
    ),
    None,
)
if ENV_PATH is None:
    raise FileNotFoundError("Could not locate .env")

load_dotenv(ENV_PATH)
REPO_ROOT = Path(os.environ.get("YOUDARE_REPO_ROOT", ".")).resolve()


HEADERS = ["Topic", "Dictionary Terms", "False Positives"]
PREFIXES = ["DK", "HU", "SE", "FR", "IT", "RO", "UK", "ES"]
BASE_DIR = REPO_ROOT / "controversy-mapping" / "sentence_filtering" / "keyword_related_data"
OUT_DIR = REPO_ROOT / "documentation_tables" / "keywords_tables"

TOPICS = {
    "lgb": "LGBTQI+",
    "migration": "Remigration and Replacement",
    "woke": "Woke"
}


def create_keywords_table(prefix, output_dir=None):
    keywords_path = BASE_DIR / "keyword_lists" / f"{prefix}_keywords_lists.txt"
    false_positives_path = BASE_DIR / "false_positives_lists" / f"{prefix}_false_positives_lists.txt"
    output_path = Path(output_dir or OUT_DIR) / f"{prefix}_keywords_table.docx"

    output_path.mkdir(parents=True, exist_ok=True)

    with keywords_path.open() as f:
        keywords = json.load(f)

    with false_positives_path.open() as f:
        false_positives = json.load(f)

    document = Document()
    table = document.add_table(rows=1, cols=len(HEADERS))
    table.style = "Table Grid"

    for index, header in enumerate(HEADERS):
        table.rows[0].cells[index].text = header

    for topic, terms in keywords.items():
        topic_print = TOPICS.get(topic)
        row = table.add_row().cells
        row[0].text = topic_print
        row[1].text = ", ".join(terms)
        row[2].text = ", ".join(false_positives[topic])

    document.save(output_path)
    return output_path


if __name__ == "__main__":
    for prefix in PREFIXES:
        create_keywords_table(prefix)
        