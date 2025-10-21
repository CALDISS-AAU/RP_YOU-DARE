# import pandas as pd
# import json

# filepath_CPI = '/work/YOU-DARE/scrapers/data/Italy/casa_pound_italia_SPIDER/data_casa_pound_italia_SPIDER.jl'
# filepath_BS = '/work/YOU-DARE/scrapers/data/Italy/blocco_studentesco_SPIDER/data_blocco_studentesco_SPIDER.jl'
# filepath_BS_OLD = '/work/YOU-DARE/scrapers/data/Italy/blocco_studentesco_SPIDER/OLD_data_blocco_studentesco_SPIDER.jl'
# filepath_CV = '/work/YOU-DARE/scrapers/data/Romania/cultura_vietii_SPIDER/data_cultura_vietii_SPIDER.jl'

# # show the first ~100 characters with escapes visible
# with open(filepath_CPI,'rb') as f:
#     raw = f.read(120)
# print(raw[:60])  # raw bytes (helps spot BOM)
# print(repr(raw.decode('utf-8', errors='replace')[:100]))  # human view with escapes

# try:
#     with open(filepath_CPI, 'r', encoding='utf-8') as input_file:
#         data = [json.loads(line) for line in input_file]
#     print(f'Data loaded from {input_file}.')
# except Exception as e:
#     print(f'Failed to load data from {input_file}. Error: {e}')

# # show the first ~100 characters with escapes visible
# with open(filepath_BS,'rb') as f:
#     raw = f.read(120)
# print(raw[:60])  # raw bytes (helps spot BOM)
# print(repr(raw.decode('utf-8', errors='replace')[:100]))  # human view with escapes

# try:
#     with open(filepath_BS, 'r', encoding='utf-8') as input_file:
#         data = [json.loads(line) for line in input_file]
#     print(f'Data loaded from {input_file}.')
# except Exception as e:
#     print(f'Failed to load data from {input_file}. Error: {e}')

# # show the first ~100 characters with escapes visible
# with open(filepath_BS_OLD,'rb') as f:
#     raw = f.read(120)
# print(raw[:60])  # raw bytes (helps spot BOM)
# print(repr(raw.decode('utf-8', errors='replace')[:100]))  # human view with escapes

# try:
#     with open(filepath_BS_OLD, 'r', encoding='utf-8') as input_file:
#         data = [json.loads(line) for line in input_file]
#     print(f'Data loaded from {input_file}.')
# except Exception as e:
#     print(f'Failed to load data from {input_file}. Error: {e}')

# # show the first ~100 characters with escapes visible
# with open(filepath_CV,'rb') as f:
#     raw = f.read(120)
# print(raw[:60])  # raw bytes (helps spot BOM)
# print(repr(raw.decode('utf-8', errors='replace')[:100]))  # human view with escapes

# try:
#     with open(filepath_CV, 'r', encoding='utf-8') as input_file:
#         data = [json.loads(line) for line in input_file]
#     print(f'Data loaded from {input_file}.')
# except Exception as e:
#     print(f'Failed to load data from {input_file}. Error: {e}')

# ''' Fra Kristians review:
# def load_jsonlines(filepath):
#     with open(filepath, 'r', encoding='utf-8') as f:
#         return [json.loads(line) for line in f]
# '''

# #Kristians
# # def load_jsonlines(filepath):
# #     with open(filepath, 'r', encoding='utf-8') as f:
# #         return [json.loads(line) for line in f]

# # data = load_jsonlines(filepath)

import json

def find_first_bad_line(path):
    print('First function: \n')
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            s = line.rstrip('\r\n')
            try:
                json.loads(s)
            except json.JSONDecodeError as e:
                print(f'❌ Bad JSON at line {i}: {e}')
                print('repr:', repr(s[:120]))
                print('codepoints:', [ord(c) for c in s[:12]])
                break
        else:
            print('✅ All lines parsed as JSON.')

find_first_bad_line('/work/YOU-DARE/scrapers/data/Italy/blocco_studentesco_SPIDER/data_blocco_studentesco_SPIDER.jl')


def find_first_bad_line_2(path):
    print('Second function')
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            s = line.rstrip('\r\n')
            try:
                json.loads(s)
            except json.JSONDecodeError as e:
                print(f'❌ Bad JSON at line {i}: {e}')
                print('repr:', repr(s[:120]))
                print('codepoints:', [ord(c) for c in s[:12]])
                break
        else:
            print('✅ All lines parsed as JSON.')
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()    
        print("L58 tail:", repr(lines[57][-40:]))
        print("L59 head:", repr(lines[58][:40]))

find_first_bad_line_2('/work/YOU-DARE/scrapers/data/Italy/blocco_studentesco_SPIDER/data_blocco_studentesco_SPIDER.jl')

path = '/work/YOU-DARE/scrapers/data/Italy/blocco_studentesco_SPIDER/data_blocco_studentesco_SPIDER.jl'
import re
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if line.startswith('"}{'):
            print("Suspicious prefix at line", i)