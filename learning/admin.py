from django.contrib import admin

from .models import Card, Deck, Review


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("vietnamese", "english", "deck", "due", "reps")
    list_filter = ("deck",)
    search_fields = ("vietnamese", "english")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("card", "rating", "reviewed_at")
    list_filter = ("rating",)
