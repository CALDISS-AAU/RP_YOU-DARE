from pathlib import Path
import os
from dotenv import load_dotenv

import zipfile

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


def zip_directory(folder_path, zip_file):
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for folder_name, subfolders, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

zip_directory(str(REPO_ROOT / "various_tasks" / "Spain_datadump"), str(REPO_ROOT / "various_tasks" / "Spain_datadump" / "archive.zip"))