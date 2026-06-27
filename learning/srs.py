"""Thin wrapper around the FSRS spaced-repetition scheduler (fsrs 6.x).

The rest of the app deals only in ``Card`` model instances and an integer
rating; this module hides the fsrs ``Card``/``Scheduler`` objects and the
JSON (de)serialization of their state.
"""

from __future__ import annotations

from fsrs import Card as FsrsCard
from fsrs import Rating, Scheduler

# A single scheduler with default parameters is stateless and reusable.
_scheduler = Scheduler()


def _load(card) -> FsrsCard:
    """Rebuild the fsrs card from a model's stored state (or start fresh)."""
    if card.fsrs_state:
        return FsrsCard.from_dict(card.fsrs_state)
    return FsrsCard()


def apply_review(card, rating: int):
    """Grade ``card`` (a learning.models.Card) and mutate its SRS fields.

    Returns the updated model instance (not yet saved).
    """
    fsrs_card = _load(card)
    updated, _log = _scheduler.review_card(fsrs_card, Rating(rating))

    card.fsrs_state = updated.to_dict()
    card.due = updated.due
    card.reps += 1
    if rating == Rating.Again:
        card.lapses += 1
    return card
