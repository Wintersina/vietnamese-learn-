"""Data models for the Vietnamese (Southern dialect) learning app.

A ``Deck`` groups ``Card`` objects (letters, numbers, or phrases). Each card
carries the spaced-repetition state inline (``fsrs_state``) so the study queue
is a simple ordering by ``due``. Every grading event is also appended to
``Review`` for history/analytics.
"""

from django.db import models
from django.utils import timezone


class Deck(models.Model):
    """A themed group of cards, e.g. the alphabet, numbers, or greetings."""

    class Category(models.TextChoices):
        LETTERS = "letters", "Letters"
        NUMBERS = "numbers", "Numbers"
        CONVERSATION = "conversation", "Conversation"
        VOCABULARY = "vocabulary", "Vocabulary"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.LETTERS
    )
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Card(models.Model):
    """A single thing to learn, with Southern-dialect pronunciation data."""

    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cards")
    # Stable identifier from the YAML source, unique within a deck.
    key = models.SlugField()

    vietnamese = models.CharField(max_length=200)
    english = models.CharField(max_length=200)
    # Southern-dialect IPA, e.g. "/sin tɕaːw/".
    southern_ipa = models.CharField(max_length=200, blank=True)
    # Per-syllable tone names, e.g. ["ngang", "huyen"].
    tone_pattern = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    # Why this sounds Southern (d/gi/v -> y, r kept, hoi/nga merge, ...).
    southern_notes = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)

    # --- Spaced-repetition state (serialized fsrs.Card.to_dict()) ---------
    fsrs_state = models.JSONField(null=True, blank=True)
    due = models.DateTimeField(default=timezone.now, db_index=True)
    reps = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["deck", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["deck", "key"], name="unique_card_key_per_deck"
            )
        ]

    def __str__(self) -> str:
        return f"{self.vietnamese} ({self.english})"

    @property
    def is_new(self) -> bool:
        return self.reps == 0


class Review(models.Model):
    """One grading event, kept for history and future analytics."""

    class Rating(models.IntegerChoices):
        AGAIN = 1, "Again"
        HARD = 2, "Hard"
        GOOD = 3, "Good"
        EASY = 4, "Easy"

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField(choices=Rating.choices)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reviewed_at"]

    def __str__(self) -> str:
        return f"{self.card} -> {self.get_rating_display()}"
