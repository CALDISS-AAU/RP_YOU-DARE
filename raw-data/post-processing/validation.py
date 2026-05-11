#!/usr/bin/env python3
from pathlib import Path
import os
from dotenv import load_dotenv

import json


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


# === CONFIG (hardcoded paths) ===
BASE_DIR = REPO_ROOT / "raw-data" / "post-processing"
OUTPUT_FILE = BASE_DIR / "actor_platform_pairs_log.txt"

COUNTRY_CODES = ["DK", "ES", "FR", "HU", "IT", "RO", "SE", "UK"]


def process_country_file(file_path: Path):
    """
    Returns:
    - ordered list of unique (actor, platform) pairs
    - total_rows
    """
    seen = set()
    ordered_pairs = []
    total_rows = 0

    with file_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            total_rows += 1

            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(f"[WARNING] Skipping invalid JSON in {file_path.name}, line {line_number}")
                continue

            if not isinstance(row, dict):
                continue

            pair = (row.get("actor"), row.get("platform"))

            if pair not in seen:
                seen.add(pair)
                ordered_pairs.append(pair)

    return ordered_pairs, total_rows


def main():
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        out.write("ACTOR / PLATFORM PAIRS LOG (ORDER PRESERVED)\n")
        out.write("=" * 80 + "\n\n")

        for country_code in COUNTRY_CODES:
            file_path = BASE_DIR / f"{country_code}_YOUDARE-WEBDATA_combined.jsonl"

            out.write(f"COUNTRY: {country_code}\n")
            out.write("-" * 80 + "\n")

            if not file_path.exists():
                out.write(f"[MISSING FILE] {file_path}\n\n")
                continue

            pairs, total_rows = process_country_file(file_path)

            out.write(f"File: {file_path.name}\n")
            out.write(f"Rows processed: {total_rows}\n")
            out.write(f"Unique actor/platform pairs: {len(pairs)}\n\n")

            for i, (actor, platform) in enumerate(pairs, start=1):
                out.write(f"{i}. actor={repr(actor)} | platform={repr(platform)}\n")

            out.write(f"\nSUMMARY FOR {country_code}: {len(pairs)} unique pairs\n")
            out.write("\n" + "=" * 80 + "\n\n")

    print(f"Log written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()