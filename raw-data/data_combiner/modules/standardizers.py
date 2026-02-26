"""Standardizer-functions for scraped data."""

import pandas as pd
from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime, timedelta

# Helperfunction for all 
def empty_to_none(value):
    ''' Makes all empty lists and dicts into None '''
    if isinstance(value, (list, dict)) and len(value) == 0:
        return None
    return value

### TELEGRAM ###

# Reply keys lowered
keys_lowered = {
    'Message ID': 'message_ID',
    'Reply ID': 'reply_ID', 
    'User_ID': 'user_ID', 
    'Message_text': 'message_text', 
    'Timestamp': 'timestamp',
    'Reply_to_ID': 'reply_to_ID'
}

# telegram standardizer
def telegram_to_threads(posts_df, replies_df=None, paths_dict=None, sep=';') -> list[dict[str, Any]]:
    """
    Converts telegram csv to threads-format: one thread per post.
    Based on a message ID from posts, it adds replies from replies_archive as well as reples via post (Reply_to_ID) (recursive).
    All replies are stored as separate key (replies) with key for whether reply is a reply or reply via post.
    Returns json records (list of dicrs)
    """

    # Derive source from path
    if paths_dict is not None:
        source_re = re.compile(r"(.+)(?=_\d{4}_\d{2}_\d{2})")

        posts_path = paths_dict.get('posts')

        source = source_re.match(posts_path.stem).group(1)
    else:
        # Derive source from posts
        source = posts_df['To'].value_counts().index[0]
    
    # list for threads
    threads = []

    ## Initial handling: Standardize user ID, add source, replace NaN
    posts_df = posts_df.rename(columns={
        'User ID': 'User_ID'
        })
    posts_df['source'] = source
    posts_df = posts_df.fillna("")

    ## convert to lower-case
    posts_df = posts_df.rename(columns = keys_lowered)

    if replies_df is not None:
        replies_df = replies_df.rename(columns={
        'ID': 'User_ID'
        })
        
        replies_df['source'] = source
        replies_df = replies_df.fillna("")

        ## convert to lower-case
        replies_df = replies_df.rename(columns=keys_lowered)

    # keeping track of messages seen
    seen_messages = []

    # sort by message ID
    posts_df = posts_df.sort_values('message_ID', ascending=True)

    ## Build one thread per post
    for row_index, post in posts_df.iterrows():
        
        post_id = post.get("message_ID")

        # check if seen
        if post_id in seen_messages:
            continue

        single_thread = {   ##This is the outside meta, and the thread_text will contain the post + its comments
            "message_ID": post.get("message_ID"),
            "thread_text": "",
            "message_text": post.get("message_text", ""),
            "URL": post.get("URL", ""),
            "timestamp": str(post.get("timestamp", "")),
            "user_ID": post.get("user_ID", ""),
            "source" : source
        }
        
        ## Get the replies for this post (trying to match the "Message ID")
        replies_ordered = []

        if replies_df is not None:
            post_replies = replies_df[replies_df["message_ID"] == post_id].sort_values('reply_ID', ascending=True)
            
            # store replies as separate records
            post_replies['is_reply'] = 1
            post_replies['is_reply_via_post'] = 0
            
            replies_records = post_replies[['message_ID', 'reply_ID', 'user_ID', 'message_text', 'timestamp', 'is_reply', 'is_reply_via_post']].to_dict(orient='records')
            
            # first add "normal" replies
            replies_ordered.extend(replies_records)
        
        # get replies via posts
        post_replies_internal_ = posts_df[posts_df["reply_to_ID"] == post_id]

        # recursive function for fetching replies and replies via posts
        def get_replies_recursive(post_replies_internal, posts_df=posts_df, replies_df=replies_df):

            # look for replies via post
            if post_replies_internal.shape[0] > 0:
                # sort by message id
                post_replies_internal = post_replies_internal.sort_values('message_ID', ascending=True)
                
                # select columns
                post_replies_internal = post_replies_internal[["message_ID", "message_text", "URL", "timestamp", "user_ID", "reply_to_ID"]]
                post_replies_internal['is_reply'] = 0
                post_replies_internal['is_reply_via_post'] = 1

                # iter over replies via post
                for _, reply_via_post in post_replies_internal.iterrows():
                    
                    # get id
                    reply_via_post_id = reply_via_post.get("message_ID")

                    # adding main reply via post
                    replies_ordered.append(reply_via_post.to_dict())
                    seen_messages.append(reply_via_post_id)
                    
                    # check whether replies to reply via post - if so, add
                    if replies_df is not None:
                        reply_via_post_replies = replies_df[replies_df["message_ID"] == reply_via_post_id].sort_values('reply_ID', ascending=True)
                        if reply_via_post_replies.shape[0] > 0:
                            reply_via_post_replies['is_reply'] = 1
                            reply_via_post_replies['is_reply_via_post'] = 0
                
                            reply_via_post_replies_records = (
                                reply_via_post_replies[['message_ID', 'reply_ID', 'user_ID', 'message_text', 'timestamp', 'is_reply', 'is_reply_via_post']]
                                .to_dict(orient='records')
                            )

                            replies_ordered.extend(reply_via_post_replies_records)

                    # check whether further nested in replies via posts
                    reply_via_post_replies_internal = posts_df[posts_df["reply_to_ID"] == reply_via_post_id]

                    if reply_via_post_replies_internal.shape[0] > 0:
                        # imma gonna do it again
                        get_replies_recursive(reply_via_post_replies_internal)
                        
            
        # fetch replies recursively
        get_replies_recursive(post_replies_internal_)
            
        # combine thread
        if len(replies_ordered) > 0:
            single_thread["thread_text"] += f"{post.get("message_text", "")}\n--- \n\n\n"             
            for reply in replies_ordered:
                single_thread["thread_text"] += f"{reply.get("message_text", "")} \n--- \n\n\n"
        else:
            single_thread["thread_text"] += f"{post.get("message_text", "")}"

        # add replies
        single_thread["replies"] = replies_ordered

        # Convert empty lists/dicts to None (top-level only)
        for k in list(single_thread.keys()):
            single_thread[k] = empty_to_none(single_thread[k])

        # append
        threads.append(single_thread)
        seen_messages.append(post_id)

    return threads

### YOUTUBE ###
# Helper function for YT
def normalize_yt_publication_date(v):
    """
    Normalizes YouTube publication_date to 'YYYY-MM-DD'.

    Handles:
      - int like 20250608
      - str like "20250608"
      - already-ISO "YYYY-MM-DD"
      - None -> None
    Falls back to string for unexpected formats.

    REASON: Sources collected by yt-dlp returns a string like "20250608", which is interpretaded as an int
    """
    if v is None:
        return None

    s = str(v).strip()

    # Handle YYYYMMDD (8 digits)
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"

    # Already in ISO format?
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s

    # Fallback
    return s

# YouTube standardizer
def standardize_yt(
    df,
    data_p,
    expected_columns = [
        "scrape_date",
        "video_title",
        "source",
        "publication_date",
        "video_link",
        "video_id",
        "video_text", 
    ]):
    """
    Standardizer for YouTube sources.
    Checks YT sources against expected columns for validity,
    and normalizes publication_date to 'YYYY-MM-DD'.
    """

    actual_columns = set(df.columns)
    missing_columns = set(expected_columns) - actual_columns

    if missing_columns:
        raise KeyError(f"The following columns are missing from {data_p}: {', '.join(missing_columns)}")

    # Normalize publication_date
    df = df.copy()
    df["publication_date"] = df["publication_date"].apply(normalize_yt_publication_date)

    return df[expected_columns].to_dict(orient="records")

### WEBSITES ###
# Helper functions for websites
def values_to_be_changed(value, none_words):
    ''' Checks for false None's (e.g. "none", "nothing else" etc.)'''
    if not isinstance(value, str):  # If the value of an entry is not a string, we return false
        return False
    else:
        value = value.strip().lower()  # if value is a string remove space, and make it lower
        return value in none_words  # check if the word is in the defined set, and if yes return True or False

def set_value_to_none(article, key, incorrect_words):
    ''' Transforms false None's (e.g. "none", "nothing else" etc.) to true None '''
    v = article.get(key)
    if values_to_be_changed(value=v, none_words=incorrect_words):
        article[key] = None

def ensure_value_is_list(article, key, none_words):
    '''
    Force selected fields to always be lists.
    - None/missing -> []
    - strings like "none"/"null"/"nothing else" -> []
    - single non-list value -> [value] (safe fallback)

    REASON: To make sure every entry in a column is always the same type (in this case a list).
            Transforming missing values to empty lists has been preserven even though it is reversed later on, 
            to make it easy to remove the later step and once again have only pure lists on a column
    '''
    v = article.get(key)

    # Missing/None -> []
    if v is None:
        article[key] = []
        return

    # If string and is a "none" word -> []
    if isinstance(v, str) and values_to_be_changed(value=v, none_words=none_words):
        article[key] = []
        return

    # If already list -> keep
    if isinstance(v, list):
        return

    # Otherwise wrap (defensive; you can choose to set [] instead if you prefer)
    article[key] = [v]

def apply_subtitle_into_article_text(article, stuff_to_be_replaced):
    ''' If subtitles add them to the beginning og the text '''
    sub = article.get("article_sub_title")
    if isinstance(sub, str):
        sub = sub.strip()
        if sub and not values_to_be_changed(sub, stuff_to_be_replaced):
            text = article.get("article_text")
            if isinstance(text, str) and text.strip():
                text_clean = text.lstrip()
                if not text_clean.startswith(sub):
                    article["article_text"] = f"{sub}\n{text_clean}"
            else:
                article["article_text"] = sub
    article.pop("article_sub_title", None)

def pack_references_into_other_items(article):
    ''' If references add them to other_items '''
    refs = article.get("references_text")
    if isinstance(refs, list):
        refs_clean = [r.strip() for r in refs if isinstance(r, str) and r.strip()]
    else:
        refs_clean = []
    if refs_clean:
        article["other_items"] = {"references_text": refs_clean}
    else:
        article["other_items"] = None
    article.pop("references_text", None)

# Web standardizer
def standardize_web(df: pd.DataFrame, data_p):
    """
    Standardizes Website/SPIDER/MANUAL jsonl chunks.

    Mimics old `standartize_dataset()` behavior for ARTICLE datasets ONLY
    (flashback excluded - handled by `standardize_flashback`).

    Args:
        df: pandas dataframe chunk (from read_jsonl_chunks)
        data_p: Path to underlying dataset (passed through from combiner; used for context/debug)
    Returns:
        list[dict]: standardized rows (ready to be streamed as jsonl)
    """

    #### Data standard ####
    # STEP 1) Desired key order for article datasets.
    # Keys have to have a specific order.
    # If entry not found, add it with 'null'/None value.
    # Author with value "None" or "no author" needs to have None value.
    # Also other_items cant be "none", "nothing else" or []. It must have None as value.
    # NOTE: article_categories, image_links, embedded_media_links, links_in_text should ALWAYS be lists.

    desired_key_order_article = [
        'scrape_date',
        'source',
        'article_link',
        'article_title',
        'publication_date',
        'author',
        'article_categories',
        'article_text',
        'image_links',
        'embedded_media_links',
        'links_in_text',
        'other_items',
    ]

    stuff_to_be_replaced = {"none", "null", "nothing else"}
    author_that_needs_replacement = {"no author", "none", "null"}

    # Convert chunk dataframe to list of dicts.
    # IMPORTANT: replace NaN/NaT with None so pandas doesn't write NaN strings later.
    records = df.where(pd.notnull(df), None).to_dict(orient="records")

    articles_standartized = []

    # Looping through the rows
    for row_number, article in enumerate(records, start=1):

        # STEP 1) Add missing keys in desired key order with None value
        for key in desired_key_order_article:
            article.setdefault(key, None)

        # Put references into other_items and subtitle into article_text (then remove the old keys)
        pack_references_into_other_items(article)
        apply_subtitle_into_article_text(article, stuff_to_be_replaced)
        
        title_val = article.get("article_title")
        author_val = article.get("author")
        publication_date = article.get("publication_date")

        # If title is a list -> join into line-separated string
        if isinstance(title_val, list):
            cleaned = [str(t).strip() for t in title_val if str(t).strip()]
            article["article_title"] = "\n".join(cleaned) if cleaned else None

        # If author is a list -> join into comma-separated string
        if isinstance(author_val, list):
            cleaned = [str(a).strip() for a in author_val if str(a).strip()]
            article["author"] = ", ".join(cleaned) if cleaned else None
            author_val = article["author"]

        if values_to_be_changed(author_val, author_that_needs_replacement):
            article["author"] = None

        # Change external_links to links_in_text
        external_links = article.pop('external_links', None)  # return None value if key does not exist
        if external_links:
            article["links_in_text"] = external_links

        # Move youtube_links to embedded_media_links
        youtube_links = article.pop('youtube_links', None)
        if youtube_links:
            article['embedded_media_links'] = youtube_links

        # Merge categories + themes_text -> article_categories
        categories = article.pop("categories", None)
        themes = article.pop("themes_text", None)

        merged = []
        if isinstance(categories, list):
            merged.extend(categories)
        if isinstance(themes, list):
            merged.extend(themes)

        article["article_categories"] = merged if merged else None

        # Apply to other_items, image_links, article_categories, embedded_media_links, links_in_text
        set_value_to_none(article, "other_items", stuff_to_be_replaced)

        # These should ALWAYS be lists (so null-values become [])
        ensure_value_is_list(article, "image_links", stuff_to_be_replaced)
        ensure_value_is_list(article, "article_categories", stuff_to_be_replaced)
        ensure_value_is_list(article, "embedded_media_links", stuff_to_be_replaced)
        ensure_value_is_list(article, "links_in_text", stuff_to_be_replaced)

        # Remove flashback keys if present (flashback handled elsewhere)
        for k in ("post_link", "post_title", "post_author", "categories", "thread_text", "post_HTML"):
            article.pop(k, None)

        # Reorder and return standardized rows (ignore extra keys not in desired order)
        for key in article:
            article[key] = empty_to_none(article[key])  
        reordered_article = {key: article[key] for key in desired_key_order_article}
        articles_standartized.append(reordered_article)

    return articles_standartized

### FLASHBACK ###
# Helper functions for Flashback
_YAML_BLOCK_RE = re.compile(
    r"""
    ^\s*---\s*\n
    (?P<label>POST|COMMENT)\s*:\s*\n
    Author:\s*(?P<author>.*?)\s*\n
    Date:\s*(?P<date>.*?)\s*\n
    Tag:\s*(?P<tag>.*?)\s*\n
    ---\s*\n
    (?P<text>.*?)
    (?=\n\s*\n\s*\n---\s*\n|\Z)
    """,
    re.DOTALL | re.VERBOSE | re.MULTILINE
)

_CITING_PREFIX_RE = re.compile(r"^\s*Citing comment\s+(?P<cited_tag>p\d+)\s*\n", re.MULTILINE)

def _normalize_swedish_date_against(scrape_date: str, raw_date: str) -> str:
    """
    Old data can contain 'Idag'/'Igår'. Convert those to YYYY-MM-DD based on scrape_date.
    scrape_date is expected like 'YYYY-MM-DD' (as produced by your spider).
    If parsing fails, returns raw_date unchanged.
    """
    if not raw_date:
        return raw_date

    s = str(raw_date).strip()
    low = s.lower()

    try:
        base = datetime.strptime(str(scrape_date).strip(), "%Y-%m-%d")
    except Exception:
        # fall back to runtime date if scrape_date is malformed
        base = datetime.now()

    if low.startswith("idag"):
        time_part = s[4:].strip()  # everything after "Idag"
        return f"{base.strftime('%Y-%m-%d')} {time_part}".strip()

    if low.startswith("igår"):
        time_part = s[4:].strip()  # everything after "Igår"
        d = base - timedelta(days=1)
        return f"{d.strftime('%Y-%m-%d')} {time_part}".strip()

    return s

def _parse_old_flashback_yaml(thread_text: str) -> list[dict[str, str]]:
    """
    Parse the OLD spider thread_text (YAML-ish blocks) into ordered blocks:
      label, author, date, tag, text
    """
    if not thread_text:
        return []
    tt = str(thread_text).strip()
    return [
        {
            "label": (m.group("label") or "").strip(),
            "author": (m.group("author") or "").strip(),
            "date": (m.group("date") or "").strip(),
            "tag": (m.group("tag") or "").strip(),
            "text": (m.group("text") or "").strip(),
        }
        for m in _YAML_BLOCK_RE.finditer(tt)
    ]

# Flashback standardizer
def standardize_flashback(df: pd.DataFrame, data_p) -> list[dict[str, Any]]:
    """
    Transform OLD Flashback spider output into the NEW structure:
      - thread_text: concatenated plain text with separators (already matches new spider)
      - replies: list of dicts per post/comment with fields:
          label, author, date (normalized vs scrape_date), tag, text
      - also normalizes publication_date if it contains 'Idag'/'Igår' (rare, but safe)

    Signature matches your pipeline:
      standardize_flashback(df, data_p)

    Notes:
      - Keeps existing keys from df rows (scrape_date/source/post_link/etc.)
      - If a row already has 'replies' (new spider), it is left as-is.
      - If YAML parsing fails, returns the row unchanged (plus empty replies if missing).
      - Renames:
            categories -> post_categories
            external_links -> links_in_text
      - post_categories is forced to list[str] (or None)
      - Removes keys that are always None/"None":
            embedded_media_links, image_links, other_items, post_HTML
      - Converts empty lists/dicts to None (top-level only)
    """
    if df is None or df.shape[0] == 0:
        return []

    out: list[dict[str, Any]] = []
    work = df.copy()

    # avoid NaNs becoming float and breaking string ops
    # work = work.fillna("")

    def _clean_str(x) -> str | None:
        if x is None:
            return None
        s = str(x).strip()
        if not s:
            return None
        if s.lower() in {"none", "null", "nothing else"}:
            return None
        return s

    def _coerce_categories_to_list(v) -> list[str] | None:
        """
        Ensures categories becomes list[str] or None.
        """
        if v is None:
            return None

        # If it's already a list: keep only meaningful strings
        if isinstance(v, list):
            cleaned = []
            for item in v:
                s = _clean_str(item)
                if s is not None:
                    cleaned.append(s)
            return cleaned if cleaned else None

        # If it's a string: treat as one category (unless it's "None"/empty)
        if isinstance(v, str):
            s = _clean_str(v)
            return [s] if s is not None else None

        # Fallback: coerce unknown types to string if meaningful
        s = _clean_str(v)
        return [s] if s is not None else None

    for _, row in work.iterrows():
        rec: dict[str, Any] = row.to_dict()

        # -------------------------------------------------
        # Remove keys that are always None/"None"
        # -------------------------------------------------
        for k in ("embedded_media_links", "image_links", "other_items", "post_HTML"):
            rec.pop(k, None)

        # -------------------------------------------------
        # Rename keys (categories -> post_categories,
        #             external_links -> links_in_text)
        # -------------------------------------------------
        if "categories" in rec and "post_categories" not in rec:
            rec["post_categories"] = rec.pop("categories")
        else:
            rec.pop("categories", None)

        if "external_links" in rec and "links_in_text" not in rec:
            rec["links_in_text"] = rec.pop("external_links")
        else:
            rec.pop("external_links", None)

        # -------------------------------------------------
        # Force post_categories to list[str] (or None)
        # -------------------------------------------------
        rec["post_categories"] = _coerce_categories_to_list(rec.get("post_categories"))

        # If already new format (has replies list), keep it; optionally normalize dates inside replies.
        existing_replies = rec.get("replies")
        if isinstance(existing_replies, list) and existing_replies:
            scrape_date = rec.get("scrape_date", "")
            for r in existing_replies:
                if isinstance(r, dict) and "date" in r:
                    r["date"] = _normalize_swedish_date_against(scrape_date, r.get("date", ""))

            # normalize publication_date too
            if "publication_date" in rec and rec["publication_date"]:
                rec["publication_date"] = _normalize_swedish_date_against(scrape_date, rec["publication_date"])

            # Convert empty lists/dicts to None
            for k in list(rec.keys()):
                rec[k] = empty_to_none(rec[k])

            out.append(rec)
            continue

        scrape_date = rec.get("scrape_date", "")
        thread_text_raw = rec.get("thread_text", "")

        blocks = _parse_old_flashback_yaml(thread_text_raw)

        # If we can't parse, still provide the new key so downstream doesn't crash
        if not blocks:
            if "replies" not in rec:
                rec["replies"] = []

            # Convert empty lists/dicts to None
            for k in list(rec.keys()):
                rec[k] = empty_to_none(rec[k])

            out.append(rec)
            continue

        replies: list[dict[str, Any]] = []

        # Build combined_text like the NEW spider:
        # - starts with the *first* block's text (post)
        # - each subsequent block adds "\n---\n\n" + text
        combined_text = ""

        for idx, b in enumerate(blocks):
            is_post = (b.get("label") == "POST") or (idx == 0)
            label = "POST" if is_post else f"COMMENT_{idx}"

            # normalize date against scrape_date (handles Idag/Igår)
            norm_date = _normalize_swedish_date_against(scrape_date, b.get("date", ""))

            text = b.get("text", "")

            replies.append(
                {
                    "label": label,
                    "author": b.get("author", ""),
                    "date": norm_date,
                    "tag": b.get("tag", ""),
                    "text": text,
                }
            )

            if combined_text:
                combined_text = f"{combined_text}\n---\n\n{text}"
            else:
                combined_text = text

        # Set outputs to match NEW spider
        rec["thread_text"] = combined_text
        rec["replies"] = replies

        # publication_date in your OLD spider came from the first block; normalize it too.
        if rec.get("publication_date"):
            rec["publication_date"] = _normalize_swedish_date_against(scrape_date, rec.get("publication_date"))
        else:
            # if missing, populate from first reply (the POST)
            rec["publication_date"] = replies[0].get("date", "") if replies else None

        # post_author in old spider should already be present; if missing populate from POST
        if not str(rec.get("post_author", "")).strip():
            rec["post_author"] = replies[0].get("author", "") if replies else None

        # Convert empty lists/dicts to None
        for k in list(rec.keys()):
            rec[k] = empty_to_none(rec[k])

        out.append(rec)

    return out


