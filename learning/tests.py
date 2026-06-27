from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import json

from .dialect import detect_rules, southern_tone
from .models import Card, Deck, Review
from .srs import apply_review
from .views import _target_text


class DialectTests(TestCase):
    def test_nga_merges_to_hoi_in_south(self):
        self.assertEqual(southern_tone("nga"), "hoi")
        self.assertEqual(southern_tone("sac"), "sac")

    def test_detects_southern_d_v_r_features(self):
        self.assertIn("d_gi_v_to_y", detect_rules("dạ"))
        self.assertIn("r_kept", detect_rules("rồi"))


class SrsTests(TestCase):
    def setUp(self):
        self.deck = Deck.objects.create(slug="t", name="T")
        self.card = Card.objects.create(deck=self.deck, key="x",
                                        vietnamese="Dạ", english="Yes")

    def test_review_advances_schedule_and_counts(self):
        before = timezone.now()
        apply_review(self.card, Review.Rating.GOOD)
        self.assertEqual(self.card.reps, 1)
        self.assertEqual(self.card.lapses, 0)
        self.assertIsNotNone(self.card.fsrs_state)
        self.assertGreater(self.card.due, before)

    def test_again_increments_lapses(self):
        apply_review(self.card, Review.Rating.GOOD)
        apply_review(self.card, Review.Rating.AGAIN)
        self.assertEqual(self.card.lapses, 1)


class StudyFlowTests(TestCase):
    def setUp(self):
        self.deck = Deck.objects.create(slug="greetings", name="G")
        self.card = Card.objects.create(deck=self.deck, key="hello",
                                        vietnamese="Xin chào", english="Hello")

    def test_study_page_renders_card(self):
        resp = self.client.get(reverse("learning:study", args=["greetings"]))
        self.assertContains(resp, "Xin chào")

    def test_review_grades_and_returns_next(self):
        url = reverse("learning:review", args=["greetings", self.card.id])
        resp = self.client.post(url, {"rating": "3"})
        self.assertEqual(resp.status_code, 200)
        self.card.refresh_from_db()
        self.assertEqual(self.card.reps, 1)
        self.assertEqual(Review.objects.count(), 1)


class MatchTests(TestCase):
    def setUp(self):
        self.nums = Deck.objects.create(slug="numbers", name="N",
                                        category=Deck.Category.NUMBERS)
        self.c7 = Card.objects.create(deck=self.nums, key="7", order=0,
                                      vietnamese="bảy", english="7 — seven")

    def test_target_text_number_vs_translation(self):
        self.assertEqual(_target_text(self.c7, "number"), "7")
        self.assertEqual(_target_text(self.c7, "translation"), "seven")

    def test_numbers_deck_defaults_to_number_mode(self):
        resp = self.client.get(reverse("learning:match", args=["numbers"]))
        # The right-column target for number mode is the digit (in the JSON
        # island the Vietnamese is unicode-escaped, so assert on the target).
        self.assertContains(resp, '"target": "7"')
        self.assertContains(resp, 'class="on">word ↔ number')

    def test_match_grade_applies_fsrs(self):
        url = reverse("learning:match_grade", args=["numbers"])
        body = json.dumps({"results": [{"card_id": self.c7.id, "rating": 3}]})
        resp = self.client.post(url, body, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["graded"], 1)
        self.c7.refresh_from_db()
        self.assertEqual(self.c7.reps, 1)
        self.assertEqual(Review.objects.count(), 1)
