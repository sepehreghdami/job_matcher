# services/keyword_matcher.py
"""Pure keyword-matching helpers for pre-filtering messages before scoring."""

import re
from typing import List


def _make_pattern(keyword: str) -> re.Pattern:
    # Custom boundary (not \b): \b requires a transition between a word char
    # and a non-word char, which fails for keywords ending in a symbol
    # (e.g. "c++", "c#" — the trailing symbol is already non-word, so \b never
    # matches there). These lookarounds instead just require the characters
    # immediately outside the keyword to not be alphanumeric, regardless of
    # the keyword's own edge characters — still blocks "go" from matching
    # inside "going"/"google".
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(keyword)}(?![A-Za-z0-9_])", re.IGNORECASE)


def _compile_patterns(keywords: List[str]) -> List[List[re.Pattern]]:
    # Two pattern variants per keyword — the keyword as-is, and with hyphens
    # stripped (so "domain-driven design" also matches "domaindriven design").
    # Matched against both the original and hyphen-stripped text (see
    # _count_matches) — checking all 4 combinations, not just one direction,
    # matters: stripping hyphens from the TEXT alone would wrongly merge
    # "frontend" into "frontend-developer" (destroying a boundary that
    # already matched correctly), while stripping only the keyword misses
    # "front-end" appearing literally in the text. Trying both text forms
    # against both keyword forms covers all real spelling variants without
    # that regression.
    variants = []
    for k in keywords:
        forms = {k}
        stripped = k.replace("-", "")
        if stripped:
            forms.add(stripped)
        variants.append([_make_pattern(f) for f in forms])
    return variants


def _count_matches(text: str, patterns_per_keyword: List[List[re.Pattern]]) -> int:
    stripped_text = text.replace("-", "")
    count = 0
    for variants in patterns_per_keyword:
        if any(p.search(text) or p.search(stripped_text) for p in variants):
            count += 1
    return count


def matches_keywords(text: str, keywords: List[str], min_count: int) -> bool:
    """True if at least `min_count` of `keywords` appear in `text` as whole words."""
    if not keywords or not text:
        return False
    return _count_matches(text, _compile_patterns(keywords)) >= min_count


def filter_messages_by_keywords(messages: list, keywords: List[str], min_count: int) -> list:
    """Keep only messages whose .text matches at least `min_count` keywords."""
    if not keywords:
        return []
    patterns = _compile_patterns(keywords)
    return [m for m in messages if _count_matches(m.text or "", patterns) >= min_count]
