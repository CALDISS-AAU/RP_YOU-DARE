#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CM_DIR="${REPO_ROOT}/controversy-mapping"
PYTHON_BIN="${PYTHON_BIN:-python}"

TARGET_COUNTRY="DK"
TARGET_THEMES=(lgb migration woke)
RAW_DATASET_NAME="DK_YOUDARE-WEBDATA_combined.jsonl"
RAW_DATASET_PATH="/home/kgk/temp/YOU-DARE data/${RAW_DATASET_NAME}"

REDUCED_DATA_PATH="${CM_DIR}/data/reduced_data/${TARGET_COUNTRY}_reduced.jl"
MATCHED_DATA_DIR="${CM_DIR}/data/matched_data/${TARGET_COUNTRY}"
INDEXED_DATA_DIR="${CM_DIR}/data/indexed_data/${TARGET_COUNTRY}"
PEAKS_OUTPUT_DIR="${CM_DIR}/trend-analysis/output/peaks/${TARGET_COUNTRY}"
RESEARCHER_OUTPUT_DIR="${CM_DIR}/trend-analysis/output/packages_for_researchers"
SEMANTIC_EMBEDDINGS_DIR="${CM_DIR}/semantic-mapping/output/embeddings"
SEMANTIC_UMAP_DIR="${CM_DIR}/semantic-mapping/output/umap_positions/${TARGET_COUNTRY}"
SEMANTIC_PLOTS_DIR="${CM_DIR}/semantic-mapping/plots/semantic-maps_analyze/${TARGET_COUNTRY}"
FINAL_PLOTS_DIR="${CM_DIR}/final_plots/plots"
FINAL_TIMELINE_INPUT="${CM_DIR}/final_plots/input_data/D2.1 Timelines/${TARGET_COUNTRY}/input_peaks-overview-annotation.xlsx"
FINAL_SEMANTIC_INPUT="${CM_DIR}/final_plots/input_data/D2.1 Socio-symbolic maps/${TARGET_COUNTRY}/input_semantic-map-annotation.xlsx"
FINAL_CHUNKS_KEEP_CSV="${CM_DIR}/final_plots/input_data/umap_chunks_keep/umap_chunks_keep.csv"
FINAL_UMAP_INPUT_DIR="${CM_DIR}/final_plots/input_data/used_positions_mar20/umap_positions/${TARGET_COUNTRY}"

AUTO_CONFIRM=0
if [[ "${1:-}" == "--yes" || "${1:-}" == "-y" ]]; then
  AUTO_CONFIRM=1
fi

log() {
  printf '[pipeline] %s\n' "$1"
}

fail() {
  printf '[pipeline] ERROR: %s\n' "$1" >&2
  exit 1
}

confirm_repo_root() {
  log "Current directory: $(pwd)"
  log "This pipeline script needs to cd to: ${REPO_ROOT}"

  if [[ "${AUTO_CONFIRM}" -eq 0 ]]; then
    read -r -p "Continue and cd there? [y/N] " reply
    case "${reply}" in
      [yY]|[yY][eE][sS]) ;;
      *) fail "Cancelled before changing directory." ;;
    esac
  fi

  cd "${REPO_ROOT}"
  log "Confirmed repository root: $(pwd)"
}

require_file() {
  local path="$1"
  [[ -f "${path}" ]] || fail "Required file is missing: ${path}"
}

require_dir() {
  local path="$1"
  [[ -d "${path}" ]] || fail "Required directory is missing: ${path}"
}

require_any_match() {
  local search_dir="$1"
  local name_pattern="$2"
  local label="$3"

  [[ -d "${search_dir}" ]] || fail "Required directory is missing: ${search_dir}"

  if ! find "${search_dir}" -type f -name "${name_pattern}" -print -quit | grep -q .; then
    fail "No ${label} found under ${search_dir} matching ${name_pattern}"
  fi
}

run_step() {
  local step_label="$1"
  shift

  log "${step_label}"
  "$@"
}

check_theme_outputs() {
  local prefix="$1"
  local suffix="$2"

  local theme
  for theme in "${TARGET_THEMES[@]}"; do
    require_file "${prefix}${theme}${suffix}"
  done
}

prepare_environment() {
  export YOUDARE_REPO_ROOT="${REPO_ROOT}"
  export PYTHONUNBUFFERED=1
}

sync_umap_outputs_for_final_plots() {
  mkdir -p "${FINAL_UMAP_INPUT_DIR}"
  cp -f "${SEMANTIC_UMAP_DIR}/"*.csv "${FINAL_UMAP_INPUT_DIR}/"
}

confirm_repo_root
prepare_environment

source /home/kgk/repos/RP_YOU-DARE/ydenv/bin/activate

require_file "${RAW_DATASET_PATH}"

run_step "1. Running extract_datasets.py for ${TARGET_COUNTRY}" \
  python "${CM_DIR}/pre-processing/sentence_filtering/extract_datasets.py" 
require_file "${REDUCED_DATA_PATH}"

run_step "2. Running keyword_matching.py for ${TARGET_COUNTRY}" \
  python "${CM_DIR}/pre-processing/sentence_filtering/keyword_matching.py"
check_theme_outputs "${MATCHED_DATA_DIR}/${TARGET_COUNTRY}_" "_matched.jl"

run_step "3. Running index_data.py for ${TARGET_COUNTRY}" \
  python "${CM_DIR}/pre-processing/sentence_filtering/index_data.py" 
check_theme_outputs "${INDEXED_DATA_DIR}/${TARGET_COUNTRY}_" "_indexed.jl"

run_step "4. Running peak_detection.py from trend-analysis" \
  bash -lc "cd '${CM_DIR}/trend-analysis' && '${PYTHON_BIN}' -m peak_detection --data-dir '${INDEXED_DATA_DIR}'"
check_theme_outputs "${PEAKS_OUTPUT_DIR}/" "_peaks.json"

run_step "5. Running date_filtering.py for ${TARGET_COUNTRY}" \
  python "${CM_DIR}/pre-processing/sentence_filtering/date_filtering.py" 
require_file "${RESEARCHER_OUTPUT_DIR}/sampling_log.json"
require_any_match "${RESEARCHER_OUTPUT_DIR}/${TARGET_COUNTRY}" "sampled_texts.xlsx" "sampled text workbooks"

run_step "6. Running extract_words_peaks_spacy.py for ${TARGET_COUNTRY}" \
  python "${CM_DIR}/trend-analysis/py-scr/wordclouds/extract_words_peaks_spacy.py" 
require_any_match "${PEAKS_OUTPUT_DIR}" "peak_*_term_frequencies.csv" "peak term frequency CSVs"

run_step "7. Running peaks_to_clouds.py for ${TARGET_COUNTRY}" \
  python "${CM_DIR}/trend-analysis/py-scr/wordclouds/peaks_to_clouds.py"
require_any_match "${RESEARCHER_OUTPUT_DIR}/${TARGET_COUNTRY}" "*_wordcloud.png" "wordcloud images"
require_any_match "${RESEARCHER_OUTPUT_DIR}/${TARGET_COUNTRY}" "*_term-counts.xlsx" "word frequency workbooks"

run_step "8. Running embed_data.py for ${TARGET_COUNTRY}" \
  cd "${CM_DIR}/semantic-mapping" && conda activate mapping-env && python -m py-scr.embed_data
check_theme_outputs "${SEMANTIC_EMBEDDINGS_DIR}/${TARGET_COUNTRY}_" "_chunked.parquet"
check_theme_outputs "${SEMANTIC_EMBEDDINGS_DIR}/${TARGET_COUNTRY}_" "_embeddings.npy"

run_step "9. Running make_da_map.py from semantic-mapping" \
  bash -lc "cd '${CM_DIR}/semantic-mapping' && for theme in lgb migration woke; do '${PYTHON_BIN}' -m cluster_fun.make_da_map --country '${TARGET_COUNTRY}' --theme \"\$theme\"; done"
check_theme_outputs "${SEMANTIC_UMAP_DIR}/" "_umap-coords.csv"
check_theme_outputs "${SEMANTIC_UMAP_DIR}/" "_umap-actors-coords.csv"
check_theme_outputs "${SEMANTIC_PLOTS_DIR}/" "_semantic-map.html"

require_file "${FINAL_TIMELINE_INPUT}"
run_step "10. Running gen_final_peaksgraphs.py from final_plots" \
  bash -lc "cd '${CM_DIR}/final_plots' && '${PYTHON_BIN}' - <<'PY'
import gen_final_peaksgraphs as module
for theme in ['lgb', 'migration', 'woke']:
    module.generate('DK', theme)
PY"
check_theme_outputs "${FINAL_PLOTS_DIR}/peaks_deliverable/${TARGET_COUNTRY}_" "_peaks.png"
require_any_match "${FINAL_PLOTS_DIR}/peaks_deliverable/peaks_tables" "*.docx" "peaks tables"

require_file "${FINAL_SEMANTIC_INPUT}"
require_file "${FINAL_CHUNKS_KEEP_CSV}"
sync_umap_outputs_for_final_plots
run_step "11. Running gen_final_semantic_maps.py from final_plots" \
  bash -lc "cd '${CM_DIR}/final_plots' && '${PYTHON_BIN}' - <<'PY'
import gen_final_semantic_maps as module
for theme in ['lgb', 'migration', 'woke']:
    module.generate('DK', theme)
PY"
check_theme_outputs "${FINAL_PLOTS_DIR}/socio-semantic-maps_deliverable/${TARGET_COUNTRY}_" "_socio-semantic_map.png"

log "Full DK pipeline completed successfully."
