"""replace keywords in text with mask"""

import re

def convert_to_regex(keyword):
    pattern = keyword.strip()

    starts = pattern.startswith('*')
    ends = pattern.endswith('*')

    if starts:
        pattern = pattern[1:]
    if ends:
        pattern = pattern[:-1]

    # escape everything except *
    pattern = re.escape(pattern)

    # turn internal * into \w*
    pattern = pattern.replace(r'\*', r'\w*')

    if starts and ends:
        return pattern
    elif starts:
        return r'\w*' + pattern + r'\b'
    elif ends:
        return r'\b' + pattern + r'\w*'
    else:
        return r'\b' + pattern + r'\b'

def mask_keywords(text, keywords, theme):
    
    # Build regex patterns
    compiled_regexes = []
    for kw in keywords:
        pattern = convert_to_regex(kw)
        try:
            rgx = re.compile(pattern, flags=re.IGNORECASE) 
            compiled_regexes.append((kw, rgx))
        except re.error as e:
            print(f"Bad regex for keyword '{kw}': {e}")

    matches = []

    # Use compiled regex objects 
    for original_kw, rgx in compiled_regexes:
        matches.extend(rgx.findall(text))
    
    # replace with mask
    new_text = text
    for match in matches:
        new_text = new_text.replace(match, f"[{theme.upper()}]")

    return new_text 