"""Load deck/card content from the version-controlled YAML files into the DB.

Idempotent: re-running updates existing decks/cards (matched by slug/key)
without touching their spaced-repetition progress. Content is the source of
truth in ``content/``; the SQLite DB is just a local, rebuildable cache.

    python manage.py load_decks
"""

from __future__ import annotations

from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from learning.models import Card, Deck

CONTENT_DIR = settings.BASE_DIR / "content"

# Fields copied verbatim from each YAML card entry (defaults applied below).
CARD_FIELDS = (
    "vietnamese",
    "english",
    "southern_ipa",
    "tone_pattern",
    "tags",
    "southern_notes",
)


class Command(BaseCommand):
    help = "Load decks and cards from content/*.yaml into the database."

    def handle(self, *args, **options):
        files = sorted(CONTENT_DIR.rglob("*.yaml"))
        if not files:
            self.stderr.write(self.style.WARNING(f"No YAML in {CONTENT_DIR}"))
            return

        decks = cards = 0
        for path in files:
            d, c = self._load_file(path)
            decks += d
            cards += c
            self.stdout.write(f"  {path.relative_to(CONTENT_DIR)} → {c} cards")

        self.stdout.write(
            self.style.SUCCESS(f"Loaded {cards} cards across {decks} decks.")
        )

    @transaction.atomic
    def _load_file(self, path: Path) -> tuple[int, int]:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        meta = data["deck"]

        deck, _ = Deck.objects.update_or_create(
            slug=meta["slug"],
            defaults={
                "name": meta["name"],
                "category": meta.get("category", Deck.Category.LETTERS),
                "description": meta.get("description", ""),
                "order": meta.get("order", 0),
            },
        )

        for i, entry in enumerate(data.get("cards", [])):
            defaults = {f: entry.get(f, "") for f in CARD_FIELDS}
            # JSON list fields must default to [] not "".
            defaults["tone_pattern"] = entry.get("tone_pattern", [])
            defaults["tags"] = entry.get("tags", [])
            defaults["order"] = i
            Card.objects.update_or_create(
                deck=deck, key=str(entry["key"]), defaults=defaults
            )

        return 1, len(data.get("cards", []))
