import zipfile
import os

def zip_directory(folder_path, zip_file):
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for folder_name, subfolders, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

zip_directory('/work/YOU-DARE/various_tasks/Spain_datadump', '/work/YOU-DARE/various_tasks/Spain_datadump/archive.zip')