"""Southern Vietnamese dialect helpers.

The point of this project is the *Southern* accent, which differs from the
"standard"/Northern dialect in a few systematic ways. This module documents
those rules and can annotate a word with the ones that apply, so cards can
explain *why* something sounds the way it does.
"""

from __future__ import annotations

# Human-readable descriptions of the salient Southern features.
SOUTHERN_RULES = {
    "d_gi_v_to_y": "‘d’, ‘gi’ and ‘v’ are pronounced like ‘y’ (Northern: ‘z’).",
    "r_kept": "‘r’ keeps a real ‘r’/retroflex sound (Northern flattens to ‘z’).",
    "hoi_nga_merge": "The hỏi (̉) and ngã (˜) tones merge into one falling tone.",
    "final_n_t_shift": "Final ‘-n’/‘-t’ can shift toward ‘-ng’/‘-c’ after some vowels.",
    "s_x_distinct": "‘s’ stays retroflex/‘sh’-like, kept distinct from ‘x’.",
}

# The six written tones; in the South, hỏi and ngã are not distinguished.
TONES = ["ngang", "huyen", "sac", "hoi", "nga", "nang"]
SOUTHERN_TONE_MERGES = {"nga": "hoi"}  # ngã realized like hỏi


def southern_tone(tone: str) -> str:
    """Map a written tone to its spoken Southern realization."""
    return SOUTHERN_TONE_MERGES.get(tone, tone)


def detect_rules(vietnamese: str) -> list[str]:
    """Return keys of SOUTHERN_RULES that plausibly apply to ``vietnamese``.

    A lightweight heuristic over spelling — useful for auto-annotating cards
    that don't already carry hand-written ``southern_notes``.
    """
    word = vietnamese.lower()
    hits: list[str] = []
    if any(c in word for c in ("d", "v")) or "gi" in word:
        # 'đ' is a different letter and is excluded by checking bare 'd'.
        if "đ" in word:
            bare = word.replace("đ", "")
        else:
            bare = word
        if "d" in bare or "v" in bare or "gi" in bare:
            hits.append("d_gi_v_to_y")
    if "r" in word:
        hits.append("r_kept")
    if "s" in word:
        hits.append("s_x_distinct")
    return hits


def explain(vietnamese: str) -> list[str]:
    """Full descriptions for the rules that apply to ``vietnamese``."""
    return [SOUTHERN_RULES[k] for k in detect_rules(vietnamese)]
