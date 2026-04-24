source /work/YOU-DARE/environment/bin/activate

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/DK_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/DK_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "DK" \
--language "da" \
--author "CALDISS"

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/ES_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/ES_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "ES" \
--language "es" \
--author "CALDISS"

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/FR_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/FR_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "FR" \
--language "fr" \
--author "CALDISS"

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/HU_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/HU_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "HU" \
--language "hu" \
--author "CALDISS"

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/IT_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/IT_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "IT" \
--language "it" \
--author "CALDISS"

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/RO_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/RO_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "RO" \
--language "ro" \
--author "CALDISS"

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/SE_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/SE_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "SE" \
--language "sv" \
--author "CALDISS"

python /work/YOU-DARE/raw-data/metadata/create_sidecar.py \
--file "/work/YOU-DARE/raw-data/final_raw/UK_YOUDARE-WEBDATA_combined.jsonl" \
--output "/work/YOU-DARE/raw-data/final-raw/metadata/UK_YOUDARE-WEBDATA_combined.metadata.jsonld" \
--country "UK" \
--language "en" \
--author "CALDISS"