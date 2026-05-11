from pathlib import Path
import os
from dotenv import load_dotenv

import json
import math
from collections import Counter, defaultdict

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


all_countries = [
    'DK', 
    'FR', 
    'ES', 
    'HU', 
    'IT', 
    'RO', 
    'SE', 
    'UK'
    ]

input_folder = REPO_ROOT / "raw-data" / "final_raw"

log_dir = REPO_ROOT / "raw-data" / "data_combiner" / "logs" / "validation"
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / "column_type_validation.log"

# =========================
# EXPECTED TYPES (schema)
# =========================
EXPECTED_TYPES = {
	'entry_ID': 'str',
	'message_ID': 'int',
	'message_text': 'str',
	'replies': 'list',
	'timestamp': 'str',
	'URL': 'str',
	'user_ID': 'int',
	'actor': 'str',
	'article_categories': 'list',
	'article_link': 'str',
	'article_text': 'str',
	'article_title': 'str',
	'author': 'str',
	'embedded_media_links': 'list',
	'image_links': 'list',
	'links_in_text': 'list',
	'other_items': 'dict',
	'platform': 'str',
	'publication_date': 'str',
	'scrape_date': 'str',
	'source': 'str',
	'video_id': 'str',
	'video_link': 'str',
	'video_text': 'str',
	'video_title': 'str',
	'categories': 'list',
	'external_links': 'list',
	'post_author': 'str',
	'post_categories': 'list',
	'post_link': 'str',
	'post_title': 'str',
	'replies': 'list',
	'thread_text': 'str'
}

MAX_CONTEXT_PLATFORMS = 50
MAX_CONTEXT_ACTORS = 200
MAX_CONTEXT_PAIRS = 300  # (platform, actor) pairs

def allowed_type_labels_for_expected(expected: str) -> set[str]:
    """
    Allowed observed labels given expected base type.
    We allow NA for null-ish values.
    We do NOT allow EmptyList anymore.
    """
    return {expected, "NA"}

def deviation_from_expected(key: str, observed: set[str]) -> str | None:
    """
    Returns a deviation reason, or None if OK.
    """
    expected = EXPECTED_TYPES.get(key)

    if expected is None:
        return "UNEXPECTED KEY (not in EXPECTED_TYPES)"

    allowed = allowed_type_labels_for_expected(expected)
    extras = observed - allowed

    if extras:
        return f"Unexpected type labels: {', '.join(sorted(extras))} (expected {expected} + NA)"

    # # Optional: flag keys that are ONLY NA (often means always missing/null)
    # if expected not in observed and observed == {"NA"}:
    #     return f"Only NA observed (expected {expected})"

    return None

def log_line(f, text, also_print=True):
    f.write(text + "\n")
    if also_print:
        print(text)


def is_missing_value(v) -> bool:
    # Key is present but value is null-ish
    if v is None:
        return True
    # JSON won't produce NaN normally, but keep it safe if it appears
    if isinstance(v, float) and math.isnan(v):
        return True
    return False


def value_type_label(v) -> str:
    # Only called when key is present in the row
    if is_missing_value(v):
        return "NA"

    if isinstance(v, list):
        if len(v) == 0:
            return "EmptyList"
        return "list"

    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, dict):
        return "dict"

    return type(v).__name__

def stream_profile_jsonl(
    file_path: Path,
    expected_types: dict[str, str],
    examples_per_type=2,
    only_examples_for_types=("float",),
):
    """
    Returns:
      counts_per_key: dict[key] -> Counter(type_label -> count)
      examples: dict[key] -> dict[type_label] -> list[full_row_dict]
      keyset_counts: Counter(frozenset(keys_in_row) -> count)
      mismatch_context: dict[key] -> dict[type_label] -> dict with platform/actor/pairs sets
    Only considers keys present in each JSON row.
    """
    counts_per_key = defaultdict(Counter)
    examples = defaultdict(lambda: defaultdict(list))
    keyset_counts = Counter()

    # key -> observed_type -> {"platforms": set, "actors": set, "pairs": set[(platform, actor)]}
    mismatch_context = defaultdict(lambda: defaultdict(lambda: {"platforms": set(), "actors": set(), "pairs": set()}))

    # Small helper: check if a type label is allowed given expected base type
    def _is_allowed_type_for_key(key: str, type_label: str) -> bool:
        exp = expected_types.get(key)
        if exp is None:
            # unexpected key; treat as mismatch so we capture context
            return False
        return type_label in {exp, "NA"}  # your current rule (no EmptyList allowed)

    with file_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue

            keyset_counts[frozenset(row.keys())] += 1

            row_platform = row.get("platform", None)
            row_actor = row.get("actor", None)
            pair = (row_platform, row_actor)

            for key, val in row.items():
                t = value_type_label(val)
                counts_per_key[key][t] += 1

                # Store row examples (unchanged behavior)
                if only_examples_for_types is None or t in only_examples_for_types:
                    if len(examples[key][t]) < examples_per_type:
                        examples[key][t].append(row)

                # If this key/type is NOT allowed, record platform/actor context
                if not _is_allowed_type_for_key(key, t):
                    ctx = mismatch_context[key][t]

                    if row_platform is not None and len(ctx["platforms"]) < MAX_CONTEXT_PLATFORMS:
                        ctx["platforms"].add(row_platform)
                    if row_actor is not None and len(ctx["actors"]) < MAX_CONTEXT_ACTORS:
                        ctx["actors"].add(row_actor)
                    if len(ctx["pairs"]) < MAX_CONTEXT_PAIRS:
                        ctx["pairs"].add(pair)

    return counts_per_key, examples, keyset_counts, mismatch_context


# --- Allowed "mixed type" combos that should NOT be flagged ---
ALLOWED_TYPE_SETS = {
    frozenset(["str", "NA"]),
    frozenset(["list", "NA"]),
}

def is_problematic_type_mix(type_set: set[str]) -> bool:
    """
    Flag keys that have more than one type, except the allowed 2-type combos:
      - str + NA
      - list + EmptyList
    """
    if len(type_set) <= 1:
        return False
    if frozenset(type_set) in ALLOWED_TYPE_SETS:
        return False
    return True


with open(log_path, "w", encoding="utf-8") as logf:
    log_line(logf, f"Log file: {log_path}")
    log_line(logf, f"Input folder: {input_folder}")
    log_line(logf, "Note: Types are computed ONLY for keys present in each row (missing keys are ignored).")

    # --- Collect per-country summaries for the final section ---
    country_keyset_counts = {}          # country -> Counter(frozenset(keys) -> count)
    country_types_per_key = {}          # country -> dict(key -> set(types))

    for country in all_countries:
        file_path = input_folder / f"{country}_YOUDARE-WEBDATA_combined.jsonl"

        if not file_path.exists():
            log_line(logf, f"\n[{country}] Missing file: {file_path}")
            continue

        log_line(logf, f"\n===== {country} | streaming {file_path.name} =====")

        counts_per_key, examples, keyset_counts, mismatch_context = stream_profile_jsonl(
            file_path,
            expected_types=EXPECTED_TYPES,
            examples_per_type=2,
            only_examples_for_types=("float",),
        )

        # Save for end-of-log summary
        country_keyset_counts[country] = keyset_counts
        country_types_per_key[country] = {k: set(v.keys()) for k, v in counts_per_key.items()}

        observed_keys = set(counts_per_key.keys())
        expected_keys = set(EXPECTED_TYPES.keys())

        unexpected_keys = sorted(observed_keys - expected_keys)
        missing_expected_keys = sorted(expected_keys - observed_keys)

        if unexpected_keys:
            log_line(logf, f"UNEXPECTED KEYS: {', '.join(unexpected_keys)}")

        # Summary: ONLY keys deviating from expected types
        deviations = []
        for key in sorted(counts_per_key.keys()):
            observed_types = set(counts_per_key[key].keys())
            reason = deviation_from_expected(key, observed_types)
            if reason:
                deviations.append((key, reason))

        if not deviations:
            log_line(logf, "OK: No keys deviate from expected types.")
        else:
            log_line(logf, f"DEVIATIONS: {len(deviations):,} keys")
            for key, reason in deviations:
                c = counts_per_key[key]
                types_sorted = ", ".join(sorted(c.keys()))
                counts_str = ", ".join(f"{k}={v:,}" for k, v in c.most_common())

                log_line(logf, f"{key}: {types_sorted}")
                log_line(logf, f"  counts: {counts_str}")
                log_line(logf, f"  reason: {reason}")

                # Add platform/actor context for mismatching types
                # For this key, only print context for the "bad" types (types not allowed)
                expected = EXPECTED_TYPES.get(key)
                allowed = {expected, "NA"} if expected is not None else set()

                bad_types = sorted(set(c.keys()) - allowed)

                for bad_t in bad_types:
                    ctx = mismatch_context.get(key, {}).get(bad_t)
                    if not ctx:
                        continue

                    # Pretty print small sets (sorted, capped already)
                    platforms = ", ".join(sorted(str(x) for x in ctx["platforms"])) if ctx["platforms"] else "-"
                    actors = ", ".join(sorted(str(x) for x in ctx["actors"])) if ctx["actors"] else "-"

                    log_line(logf, f"  context for type={bad_t}:")
                    log_line(logf, f"    platforms: {platforms}")
                    log_line(logf, f"    actors: {actors}")

                    # Optional: also print pairs (useful when actors repeat across platforms)
                    pairs = sorted(ctx["pairs"])
                    if pairs:
                        pairs_str = "; ".join(f"{p}|{a}" for p, a in pairs[:50])
                        log_line(logf, f"    platform|actor pairs (first {min(50, len(pairs))}): {pairs_str}")
                        if len(pairs) > 50:
                            log_line(logf, f"    NOTE: pairs list truncated (showing 50 of {len(pairs)})")

                # If floats appear, dump full-row examples
                if "float" in c:
                    log_line(logf, f"  float row examples (full rows):")
                    for i, row in enumerate(examples[key].get("float", []), start=1):
                        log_line(logf, f"    [{i}] {json.dumps(row, ensure_ascii=False)}")

    # =========================
    # Final cross-country summary
    # =========================
    log_line(logf, "\n=========================")
    log_line(logf, "CROSS-COUNTRY SUMMARY")
    log_line(logf, "=========================")

    # 1) All unique sets of keys for each row (per country)
    log_line(logf, "\n--- Unique keysets per row (per country) ---")
    for country in all_countries:
        if country not in country_keyset_counts:
            continue
        ks_counts = country_keyset_counts[country]
        log_line(logf, f"\n[{country}] unique keysets: {len(ks_counts):,}")

        # Print ALL unique keysets (sorted by frequency desc, then size desc)
        for keyset, cnt in sorted(ks_counts.items(), key=lambda kv: (-kv[1], -len(kv[0]), sorted(kv[0]))):
            keys_sorted = ", ".join(sorted(keyset))
            log_line(logf, f"  count={cnt:,} | keys({len(keyset)}): {keys_sorted}")

    # 2) Keys where there's more than one type (except allowed combos)
    log_line(logf, "\n--- Keys with problematic mixed types (per country) ---")
    for country in all_countries:
        if country not in country_types_per_key:
            continue
        types_map = country_types_per_key[country]

        problematic = []
        for key, tset in types_map.items():
            if is_problematic_type_mix(tset):
                problematic.append((key, tset))

        log_line(logf, f"\n[{country}] problematic keys: {len(problematic):,}")
        for key, tset in sorted(problematic, key=lambda x: (x[0])):
            log_line(logf, f"  {key}: {', '.join(sorted(tset))}")

    # Also provide an aggregated view: which keys are problematic in which countries
    log_line(logf, "\n--- Keys with problematic mixed types (across countries) ---")
    key_to_countries = defaultdict(list)  # key -> list of (country, typeset)

    for country, types_map in country_types_per_key.items():
        for key, tset in types_map.items():
            if is_problematic_type_mix(tset):
                key_to_countries[key].append((country, tset))

    log_line(logf, f"Unique problematic keys across all countries: {len(key_to_countries):,}")
    for key in sorted(key_to_countries.keys()):
        parts = []
        for country, tset in sorted(key_to_countries[key], key=lambda x: x[0]):
            parts.append(f"{country}=[{', '.join(sorted(tset))}]")
        log_line(logf, f"  {key}: " + "; ".join(parts))

log_line(open(log_path, "a", encoding="utf-8"), f"\nDone. Log written to: {log_path}", also_print=True)

# =========================
# ADDITIONAL VALIDATION
# - Duplicate full rows (excluding entry_ID)
# - Unique entry_ID check
# =========================

import hashlib
from collections import defaultdict, Counter

# Ensure you're using SE (not SWE)
# (Assumes you already corrected this earlier in the script)
# all_countries = ['DK', 'FR', 'ES', 'HU', 'IT', 'RO', 'SE', 'UK']

def stable_row_fingerprint(row: dict, exclude_keys=("entry_ID",)) -> str:
    """
    Create a stable hash fingerprint for a row dict, excluding certain keys.
    Sorting keys ensures stable representation across runs.
    """
    filtered = {k: row.get(k) for k in row.keys() if k not in exclude_keys}
    payload = json.dumps(filtered, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Track duplicates of full rows excluding entry_ID (across ALL countries)
first_seen_rowhash = {}  # rowhash -> (country, line_no, entry_ID)
dup_rowhash_occurrences = defaultdict(list)  # rowhash -> list[(country, line_no, entry_ID)] (only duplicates, not first)

# Track entry_ID uniqueness (across ALL countries)
first_seen_entryid = {}  # entry_ID -> (country, line_no)
dup_entryid_occurrences = defaultdict(list)  # entry_ID -> list[(country, line_no)] (includes duplicates; first stored separately)

missing_entryid = []  # list of (country, line_no)

# Safety caps to avoid insane memory/log explosion in worst-case scenarios
MAX_DUP_OCC_PER_HASH = 2000
MAX_DUP_OCC_PER_ENTRYID = 2000

with open(log_path, "a", encoding="utf-8") as logf:
    log_line(logf, "\n=========================")
    log_line(logf, "DUPLICATE + ENTRY_ID VALIDATION")
    log_line(logf, "=========================")
    log_line(logf, "Definition: duplicate row = identical full JSON object EXCLUDING entry_ID.")
    log_line(logf, "Note: line_no refers to the JSONL line number in the country file (1-based).")

    for country in all_countries:
        file_path = input_folder / f"{country}_YOUDARE-WEBDATA_combined.jsonl"

        if not file_path.exists():
            log_line(logf, f"\n[{country}] Missing file: {file_path}")
            continue

        log_line(logf, f"\n[{country}] scanning for duplicates and entry_ID issues: {file_path.name}")

        with file_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if not isinstance(row, dict):
                    continue

                # ---- entry_ID uniqueness check ----
                entry_id = row.get("entry_ID", None)
                if entry_id is None:
                    missing_entryid.append((country, line_no))
                else:
                    if entry_id in first_seen_entryid:
                        # record duplicates (keep occurrences bounded)
                        if len(dup_entryid_occurrences[entry_id]) < MAX_DUP_OCC_PER_ENTRYID:
                            dup_entryid_occurrences[entry_id].append((country, line_no))
                    else:
                        first_seen_entryid[entry_id] = (country, line_no)

                # ---- duplicate row check (excluding entry_ID) ----
                rowhash = stable_row_fingerprint(row, exclude_keys=("entry_ID",))

                if rowhash in first_seen_rowhash:
                    if len(dup_rowhash_occurrences[rowhash]) < MAX_DUP_OCC_PER_HASH:
                        dup_rowhash_occurrences[rowhash].append((country, line_no, entry_id))
                else:
                    first_seen_rowhash[rowhash] = (country, line_no, entry_id)

    # =========================
    # Report duplicate rows
    # =========================
    if not dup_rowhash_occurrences:
        log_line(logf, "\nDuplicate rows (excluding entry_ID): No duplicates")
    else:
        # Number of duplicate groups and total duplicate occurrences
        total_dup_occ = sum(len(v) for v in dup_rowhash_occurrences.values())
        log_line(logf, f"\nDuplicate rows (excluding entry_ID): FOUND")
        log_line(logf, f"Duplicate groups: {len(dup_rowhash_occurrences):,}")
        log_line(logf, f"Duplicate occurrences (excluding first instance in each group): {total_dup_occ:,}")

        # Print per group: first occurrence + all duplicate occurrences
        # (sorted by number of duplicates desc)
        for rowhash, occs in sorted(dup_rowhash_occurrences.items(), key=lambda kv: -len(kv[1])):
            first_country, first_line, first_entryid = first_seen_rowhash[rowhash]
            log_line(logf, f"\nRow duplicate group | duplicates={len(occs):,}")
            log_line(logf, f"  FIRST: country={first_country} line_no={first_line} entry_ID={repr(first_entryid)}")
            for (c, ln, eid) in occs:
                log_line(logf, f"  DUP:   country={c} line_no={ln} entry_ID={repr(eid)}")

            if len(occs) >= MAX_DUP_OCC_PER_HASH:
                log_line(logf, f"  NOTE: duplicate list truncated at {MAX_DUP_OCC_PER_HASH} occurrences for this group.")

    # =========================
    # Report entry_ID uniqueness
    # =========================
    if not dup_entryid_occurrences and not missing_entryid:
        log_line(logf, "\nentry_ID uniqueness: All entry_ID values are unique and present in every row.")
    else:
        if missing_entryid:
            log_line(logf, f"\nentry_ID missing: FOUND {len(missing_entryid):,} rows where entry_ID is missing or null.")
            # Print a few examples so you can locate them
            for c, ln in missing_entryid[:50]:
                log_line(logf, f"  MISSING entry_ID: country={c} line_no={ln}")
            if len(missing_entryid) > 50:
                log_line(logf, "  NOTE: missing entry_ID list truncated to first 50 rows.")

        if dup_entryid_occurrences:
            log_line(logf, f"\nentry_ID uniqueness: DUPLICATES FOUND")
            log_line(logf, f"Unique entry_IDs with duplicates: {len(dup_entryid_occurrences):,}")

            # For each duplicated entry_ID, count total occurrences (first + duplicates stored)
            # and print where to find them.
            for entry_id in sorted(dup_entryid_occurrences.keys()):
                first_c, first_ln = first_seen_entryid[entry_id]
                dup_list = dup_entryid_occurrences[entry_id]
                total = 1 + len(dup_list)

                log_line(logf, f"\nentry_ID={repr(entry_id)} occurs {total:,} times")
                log_line(logf, f"  FIRST: country={first_c} line_no={first_ln}")
                for (c, ln) in dup_list:
                    log_line(logf, f"  DUP:   country={c} line_no={ln}")

                if len(dup_list) >= MAX_DUP_OCC_PER_ENTRYID:
                    log_line(logf, f"  NOTE: duplicate list truncated at {MAX_DUP_OCC_PER_ENTRYID} occurrences for this entry_ID.")

log_line(open(log_path, "a", encoding="utf-8"), "\nDuplicate + entry_ID validation done.", also_print=True)