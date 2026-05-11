from pathlib import Path
import os
from dotenv import load_dotenv

import whisper
from pydub import AudioSegment
import csv
import warnings
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


# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def transcribe_all_files(input_folder, output_folder):
    # Make sure output directory exists,
    os.makedirs(output_folder, exist_ok=True)
    
    model = whisper.load_model('large')
    
    for file_path in Path(input_folder).iterdir():
        if file_path.suffix == '.m4a':
            transcription_result = model.transcribe(str(file_path))
    
            json_filename = file_path.stem + '.json'
            full_output_path = os.path.join(output_folder, json_filename)
    
    save_transcription_to_json(transcription_result, full_output_path)
    print('Saved transcription:', full_output_path)


def transcribe_with_whisper(file_path):
    """Transcribe an audio file using Whisper and return the full output."""
    model = whisper.load_model("large")  # Load the model once per process
    result = model.transcribe(file_path)
    return result  # Full output: text, segments, language, etc.

def save_transcription_to_json(result, output_path):
    """Save the full Whisper transcription result as JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


# Basic usage
if __name__ == "__main__":
    folder_path = str(REPO_ROOT / "scrapers" / "data" / "Spain" / "red_pill_podcast_YT" / "m4a_files")
    output_dir = str(REPO_ROOT / "scrapers" / "data" / "Spain" / "red_pill_podcast_YT" / "transcribed")

    transcribe_all_files(folder_path, output_dir)