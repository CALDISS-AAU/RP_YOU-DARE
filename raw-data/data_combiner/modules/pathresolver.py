"""functions for determining how to process filepaths to datasets."""

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable


def determine_datafile_platform(
    path: str | Path,
    seen_paths: set[Path] | None = None,
    seen_dirs: dict[Path, str] | None = None,
) -> tuple[Path | dict[str, Path], str | None]:
    """
    Determine datafile platform from path and naming conventions.
    Returns (payload, platform), where platform is one of:
    "Website", "YouTube", "Flashback", "Telegram", or None.
    For Telegram, payload is resolve_telegram_processing_paths(path).
    If Telegram payload was already seen, returns (path, None).
    """
    resolved_path = Path(path)
    parent_name = resolved_path.parent.name
    grandparent_name = resolved_path.parent.parent.name
    stem_upper = resolved_path.stem.upper()
    parent_upper = parent_name.upper()
    file_name_lower = resolved_path.name.lower()

    # Keep track of processed directories by platform.
    def _track_dir(candidate_path: Path, platform_name: str):
        if seen_dirs is None:
            return
        normalized_dir = candidate_path.resolve().parent
        existing_platform = seen_dirs.get(normalized_dir)
        if existing_platform == platform_name:
            print(f"Potential duplicate source dir ({platform_name}): {normalized_dir}")
        elif existing_platform is None:
            seen_dirs[normalized_dir] = platform_name
        else:
            print(
                "WARNING: source dir seen with differing platforms: "
                f"{normalized_dir} ({existing_platform} vs {platform_name})"
            )

    # path is website flashback
    if (
        resolved_path.suffix.lower() == ".jl"
        and stem_upper.endswith("_SPIDER")
        and parent_upper.startswith("FLASHBACK_")
    ):
        _track_dir(resolved_path, "Flashback")
        return resolved_path, "Flashback"

    # path is website spider
    if (
        resolved_path.suffix.lower() == ".jl"
        and stem_upper.endswith("_SPIDER")
        and parent_upper.endswith("_SPIDER")
    ):
        _track_dir(resolved_path, "Website")
        return resolved_path, "Website"

    # path is youtube
    if (
        resolved_path.suffix.lower() == ".jl"
        and stem_upper.endswith("_YT")
        and (parent_upper.endswith("_YT") or parent_name.lower() == "youtube")
    ):
        _track_dir(resolved_path, "YouTube")
        return resolved_path, "YouTube"

    # path is manual
    if (
        resolved_path.suffix.lower() == ".jl"
        and stem_upper.endswith("_MANUAL")
        and parent_upper.endswith("_MANUAL")
    ):
        _track_dir(resolved_path, "Website")
        return resolved_path, "Website"

    # path is telegram
    if (
        resolved_path.suffix.lower() == ".csv"
        and file_name_lower.endswith("_archive.csv")
        and (
            parent_upper.endswith("_TELEGRAM")
            or grandparent_name.upper().endswith("_TELEGRAM")
            or grandparent_name.lower() == "telegram"
        )
    ):
        telegram_payload = resolve_telegram_processing_paths(resolved_path)

        if seen_paths is not None:
            resolved_files = {
                p.resolve(strict=False)
                for p in telegram_payload.values()
            }
            if resolved_files and resolved_files.issubset(seen_paths):
                return resolved_path, None
            seen_paths.update(resolved_files)

        # track seen dir for telegram after seen_path check
        if seen_dirs is not None:
            for telegram_path in telegram_payload.values():
                _track_dir(telegram_path, "Telegram")
                break # only check first value (posts)

        return telegram_payload, "Telegram"

    # return None if neither
    return resolved_path, None


def _extract_telegram_timestamp(path: Path):
    """Parse YYYY_MM_DD date from filename."""
    
    _TELEGRAM_TIMESTAMP_RE = re.compile(
        r"(\d{4})_(\d{2})_(\d{2})")

    match = _TELEGRAM_TIMESTAMP_RE.search(path.stem)
    if not match:
        return None
    year, month, day = (int(group) for group in match.groups())

    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def _latest_telegram_file(candidates: Iterable[Path]) -> Path | None:
    candidate_list = list(candidates)
    if not candidate_list:
        return None

    def sort_key(item: Path) -> tuple[int, datetime, str]:
        """
        Sorting function based on: whether timestamp in file, date of timestamp, item.name.
        max() can sort using a tuple evaluating tuple values left to right, with left-most getting more priority.
        The sorting is then based on first whether date is in file, second which file has the highest datevalue.
        """
        
        stamp = _extract_telegram_timestamp(item) # extract date from filename
        if stamp is not None:
            return 1, stamp, item.name # 1 for priority 1, then date
        if item.exists():
            return 0, datetime.fromtimestamp(item.stat().st_mtime), item.name # if not date, use modified time
        return 0, datetime.min, item.name # if neither, place last

    return max(candidate_list, key=sort_key)


def resolve_telegram_processing_paths(
    path: str | Path,
    ):
    """
    For a Telegram source, return newest files to process as:
      {"posts": path, "replies": path}
    or:
      {"posts": path}
    """
    source_path = Path(path)
    source_dir = source_path if source_path.is_dir() else source_path.parent

    if not source_dir.exists():
        return {}

    post_candidates = []
    reply_candidates = []

    # iter over files in dir of telegram file and find other relevant files
    for candidate in source_dir.iterdir():
        if not candidate.is_file():
            continue
        candidate_name = candidate.name.lower()
        if candidate_name.endswith("_reply_archive.csv"):
            reply_candidates.append(candidate)
        elif candidate_name.endswith("_archive.csv"):
            post_candidates.append(candidate)

    # find latest
    latest_posts = _latest_telegram_file(post_candidates)
    latest_replies = _latest_telegram_file(reply_candidates)

    # return latest files
    output = {}
    if latest_posts is not None:
        output["posts"] = latest_posts
    if latest_replies is not None:
        output["replies"] = latest_replies

    return output