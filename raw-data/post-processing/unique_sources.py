import os
import json
import csv

def collect_unique_sources(folder_path, output_file):
    unique_sources = set()

    for filename in os.listdir(folder_path):
        if filename.endswith("_data_combined.jl"):
            country = filename.split("_")[0]

            file_path = os.path.join(folder_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    row = json.loads(line)

                    source = row.get("source") or row.get("Source")
                    platform = row.get("platform")

                    if source:
                        platform = platform.strip() if platform else "UNKNOWN"
                        unique_sources.add((country, platform, source.strip()))

    sorted_sources = sorted(unique_sources)

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["country", "platform", "source"])
        writer.writerows(sorted_sources)

    print(f"Saved {len(sorted_sources)} unique entries to {output_file}")


if __name__ == "__main__":
    folder = "/work/YOU-DARE/raw-data/"
    output = "unique_sources.csv"
    collect_unique_sources(folder, output)
