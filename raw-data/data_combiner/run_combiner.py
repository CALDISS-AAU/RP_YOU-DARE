"""Dream scenario:
- Replaces standardising_data, save_datasets_countries and telegram_prep
- Reads data from scrapers/data
- Fixes telegram using function in modules
- Standardizes data (like already done in standardising_data.py) - preferably without intermediary data storage
- Adds platform variable/key (currently done in save_datasets_countries.py)
- Adds actor variable/key
- Writes to final_raw/{ctr}_webdata_combine.jl as a combined jsonl - streams one dataset at the time (also avoid including irrelevant keys from other platforms)
"""

from modules.combinerfuns import telegram_to_threads # revised function

# Read data files from scrapers/data (all paths from a country)
    # NOTE: How to account for duplicates without having to manually delete? (risk of data loss)

# Iterate over paths

# Determine platform

# Perform standardization according to platform
    # Telegram -> use telegram_to_threads from this subproject (returns list of dicts; i.e. json records)
    # YouTube -> ? NOTE: Anything to clean here?
    # Websites -> re-use existing standardization features from standardising_data.py
    # Manual -> re-use existing standardization features from standardising_data.py
    # Flashback -> re-use existing standardization features from standardising_data.py
    # Add actor variable/key (from source<->actor mapping #TODO)
    # Add platform variable key
    # When source is processed, append to final_raw/{ctr}_webdata_combine.jl