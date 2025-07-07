import json
import re 
import pathlib

# input of file
class JLFileRenamer:
    @staticmethod
    def clean_audio_names(input_path):
        for file_path in list(pathlib.Path(input_path).glob('*.jl')):
            print(f'This is our file: {file_path}\n\n\n')
            try:
                with open(file_path, "r", encoding="utf-8") as infile, open(file_path, "w", encoding="utf-8") as outfile:
                    print(f'Input file: {infile}, output file: {outfile}')
                    for line in infile:
                        data = json.loads(line)

                        if "m4a_file_name" in data:
                            # Remove dots before .m4a, preserving the extension
                            data["m4a_file_name"] = re.sub(r"\.(?=.*\.m4a)", "", data["m4a_file_name"])

                        outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f'Failed to load data from {file_path}. Error: {e}')
                return []