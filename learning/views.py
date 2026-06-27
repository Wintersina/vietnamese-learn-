"""Views for the study loop.

The page at ``/study/<deck>/`` renders a shell; HTMX then swaps in one card
partial at a time. Grading POSTs back, updates the schedule, and returns the
next due card — so the whole review session is a sequence of partial swaps
with no full page reloads.
"""

from __future__ import annotations

import json
import random

from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import audio, dialect
from .models import Card, Deck, Review
from .srs import apply_review

# How many pairs to show in one matching round.
MATCH_BATCH = 6


def home(request):
    decks = Deck.objects.all()
    return render(request, "learning/home.html", {"decks": decks})


def _next_card(deck: Deck) -> Card | None:
    """The most-overdue card in ``deck`` (new cards have due=created time)."""
    return (
        deck.cards.filter(Q(due__lte=timezone.now()))
        .order_by("due", "order")
        .first()
    )


def _card_context(card: Card | None) -> dict:
    if card is None:
        return {"card": None}
    notes = card.southern_notes or " ".join(dialect.explain(card.vietnamese))
    return {
        "card": card,
        "southern_notes": notes,
        "audio_enabled": audio.is_enabled(),
        "ratings": Review.Rating.choices,
    }


def study(request, slug: str):
    deck = get_object_or_404(Deck, slug=slug)
    card = _next_card(deck)
    return render(
        request,
        "learning/study.html",
        {"deck": deck, **_card_context(card)},
    )


def next_card(request, slug: str):
    """HTMX partial: render the next due card (or a 'done' state)."""
    deck = get_object_or_404(Deck, slug=slug)
    card = _next_card(deck)
    return render(request, "learning/_card.html",
                  {"deck": deck, **_card_context(card)})


@require_POST
def review(request, slug: str, card_id: int):
    """Grade a card, advance its schedule, return the next card partial."""
    deck = get_object_or_404(Deck, slug=slug)
    card = get_object_or_404(Card, pk=card_id, deck=deck)

    try:
        rating = int(request.POST["rating"])
    except (KeyError, ValueError):
        return HttpResponse("bad rating", status=400)
    if rating not in dict(Review.Rating.choices):
        return HttpResponse("bad rating", status=400)

    apply_review(card, rating)
    card.save(update_fields=["fsrs_state", "due", "reps", "lapses", "updated_at"])
    Review.objects.create(card=card, rating=rating)

    nxt = _next_card(deck)
    return render(request, "learning/_card.html",
                  {"deck": deck, **_card_context(nxt)})


# --- Matching game --------------------------------------------------------

def _target_text(card: Card, by: str) -> str:
    """The right-column value a card is matched against."""
    if by == "number":
        return card.key  # numbers decks key on the digit, e.g. "7"
    eng = card.english
    # Trim the long form ("1 — one", "a — as in 'father'") to the gloss.
    return eng.split(" — ", 1)[1] if " — " in eng else eng


def _match_mode(deck: Deck, requested: str | None) -> str:
    if requested in ("number", "translation"):
        return requested
    return "number" if deck.category == Deck.Category.NUMBERS else "translation"


def match(request, slug: str):
    """Render a round of the matching game for ``deck``."""
    deck = get_object_or_404(Deck, slug=slug)
    by = _match_mode(deck, request.GET.get("by"))

    # Favor due cards, then take a random batch for variety.
    pool = list(deck.cards.order_by("due", "order")[: MATCH_BATCH * 2])
    random.shuffle(pool)
    batch = pool[:MATCH_BATCH]
    pairs = [
        {
            "id": c.id,
            "vietnamese": c.vietnamese,
            "target": _target_text(c, by),
            "audio": audio.is_enabled() and bool(c.vietnamese),
        }
        for c in batch
    ]
    return render(
        request,
        "learning/match.html",
        {"deck": deck, "by": by, "pairs": pairs, "audio_enabled": audio.is_enabled()},
    )


@require_POST
def match_grade(request, slug: str):
    """Apply FSRS grades from a completed matching round (JSON body)."""
    deck = get_object_or_404(Deck, slug=slug)
    try:
        results = json.loads(request.body)["results"]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "bad payload"}, status=400)

    valid = dict(Review.Rating.choices)
    graded = 0
    for item in results:
        try:
            card_id = int(item["card_id"])
            rating = int(item["rating"])
        except (KeyError, ValueError, TypeError):
            continue
        if rating not in valid:
            continue
        card = deck.cards.filter(pk=card_id).first()
        if card is None:
            continue
        apply_review(card, rating)
        card.save(update_fields=["fsrs_state", "due", "reps", "lapses", "updated_at"])
        Review.objects.create(card=card, rating=rating)
        graded += 1
    return JsonResponse({"graded": graded})


def card_audio(request, card_id: int):
    """Serve (synthesizing + caching on first hit) the card's Southern audio."""
    card = get_object_or_404(Card, pk=card_id)
    path = audio.audio_path(card.vietnamese)
    if path is None:
        raise Http404("audio unavailable")
    return FileResponse(open(path, "rb"), content_type="audio/mpeg")
