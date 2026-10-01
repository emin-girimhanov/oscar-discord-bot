"""The written reviews were stored from day one and shown nowhere.

`/rate` asks for "Erfahrungsbericht / Tipps (optional)", writes it into the
`module_ratings` table, and `Database.get_module_comments` reads it back. Nothing ever
called that method. The module card showed the two averages and no text, so every tip a
student wrote went into the database and was never read by anybody.

Two things show them now: the card quotes the newest one, and a button opens the rest.
These tests fail if either goes quiet again.
"""

from unittest.mock import MagicMock, patch

import discord
import pytest

from oscar.ui.module_reviews_view import (
    MAX_COMMENT_LENGTH,
    ModuleReviewsView,
    format_date,
    format_stars,
    shorten,
)
from oscar.ui.module_view import MAX_PEEK_LENGTH, ModuleView
from util.enums import LanguageCode


USER = 4711

REVIEWS = [
    {
        "rating": 5,
        "difficulty": 2,
        "comment": "Sehr gute Vorlesung, die Folien reichen zum Lernen.",
        "timestamp": 1758000000,
    },
    {
        "rating": 3,
        "difficulty": 4,
        "comment": "Viel Stoff, fang früh mit den Übungen an.",
        "timestamp": 1757000000,
    },
]

SUMMARY = {"count": 2, "avg_rating": 4.0, "avg_difficulty": 3.0}
NO_RATINGS = {"count": 0, "avg_rating": None, "avg_difficulty": None}


def a_module() -> MagicMock:
    module = MagicMock()
    module.id_ = 500100
    module.get_title.return_value = "Datenbanken 1"
    module.get_content.return_value = "Inhalt"
    module.get_teaching_form_sws.return_value = "2V"
    module.abbreviation = "DB1"
    module.lecturer = "Gunter Saake"
    module.credit_points = "5"
    return module


def texts_of(view: discord.ui.LayoutView) -> str:
    """Everything the student reads in this view, as one string."""
    return "\n".join(
        item.content
        for item in view.walk_children()
        if isinstance(item, discord.ui.TextDisplay)
    )


def build_card(ratings: dict, comments: list[dict]) -> ModuleView:
    with patch("oscar.ui.module_view.get_user_language", return_value=LanguageCode.DE), \
         patch("oscar.ui.module_view.get_database") as database, \
         patch("oscar.ui.module_view.module_url", return_value="https://example.invalid"), \
         patch("oscar.ui.module_view.lsf_search_url", return_value="https://example.invalid"):
        database.return_value.get_preferences.return_value = None
        database.return_value.get_module_ratings.return_value = ratings
        database.return_value.get_module_comments.return_value = comments
        return ModuleView(USER, a_module())


def build_reviews(ratings: dict, comments: list[dict]) -> ModuleReviewsView:
    with patch("oscar.ui.module_reviews_view.get_user_language", return_value=LanguageCode.DE), \
         patch("oscar.ui.module_reviews_view.get_database") as database:
        database.return_value.get_module_ratings.return_value = ratings
        database.return_value.get_module_comments.return_value = comments
        return ModuleReviewsView(USER, a_module())


class TestTheCardShowsAReview:
    """Without a click, because the averages alone never say why."""

    def test_the_newest_review_is_quoted(self):
        card = build_card(SUMMARY, REVIEWS)
        assert "Sehr gute Vorlesung" in texts_of(card)

    def test_the_rest_are_counted(self):
        card = build_card(SUMMARY, REVIEWS)
        assert "1 weitere" in texts_of(card)

    def test_one_review_is_not_counted(self):
        card = build_card(SUMMARY, REVIEWS[:1])
        assert "weitere" not in texts_of(card)

    def test_a_module_without_reviews_says_nothing_extra(self):
        card = build_card(NO_RATINGS, [])
        assert "💬" not in texts_of(card)

    def test_a_long_review_is_cut(self):
        long_one = [{**REVIEWS[0], "comment": "sehr " * 200}]
        card = build_card(SUMMARY, long_one)
        quoted = [
            line for line in texts_of(card).splitlines() if line.startswith("💬")
        ][0]
        assert len(quoted) <= MAX_PEEK_LENGTH + 10

    def test_a_review_with_line_breaks_stays_on_one_line(self):
        """A card is a summary. A comment full of newlines would take it over."""
        multiline = [{**REVIEWS[0], "comment": "erste Zeile\nzweite Zeile\ndritte"}]
        card = build_card(SUMMARY, multiline)
        quoted = [
            line for line in texts_of(card).splitlines() if line.startswith("💬")
        ][0]
        assert "zweite Zeile" in quoted

    def test_an_empty_comment_is_not_quoted(self):
        blank = [{**REVIEWS[0], "comment": "   "}]
        card = build_card(SUMMARY, blank)
        assert "💬" not in texts_of(card)

    def test_the_card_carries_the_button_to_the_rest(self):
        card = build_card(SUMMARY, REVIEWS)
        labels = [
            item.label
            for item in card.walk_children()
            if isinstance(item, discord.ui.Button)
        ]
        assert any("Erfahrungen" in (label or "") for label in labels)


class TestTheReviewsView:
    """What the button opens."""

    def test_every_review_is_listed(self):
        view = build_reviews(SUMMARY, REVIEWS)
        text = texts_of(view)
        for review in REVIEWS:
            assert review["comment"] in text

    def test_the_averages_are_on_top(self):
        text = texts_of(build_reviews(SUMMARY, REVIEWS))
        assert "4.0/5" in text
        assert "3.0/5" in text

    def test_an_empty_module_asks_for_the_first_review(self):
        text = texts_of(build_reviews(NO_RATINGS, []))
        assert "Noch hat niemand" in text

    def test_it_can_be_rated_from_here(self):
        view = build_reviews(SUMMARY, REVIEWS)
        labels = [
            item.label
            for item in view.walk_children()
            if isinstance(item, discord.ui.Button)
        ]
        assert any("Bewerten" in (label or "") for label in labels)

    def test_no_name_and_no_id_is_shown(self):
        """The table stores a discord id to keep one vote per student, not to name them."""
        text = texts_of(build_reviews(SUMMARY, REVIEWS))
        assert str(USER) not in text
        assert "user_id" not in text

    def test_it_says_how_to_delete_your_own(self):
        assert "/my_data" in texts_of(build_reviews(SUMMARY, REVIEWS))


class TestFormatting:
    """The small pieces, where an off by one is easy and invisible."""

    @pytest.mark.parametrize(
        ("rating", "expected_full"),
        [(0, 0), (1, 1), (3, 3), (5, 5)],
    )
    def test_stars_match_the_rating(self, rating: int, expected_full: int):
        assert format_stars(rating, 3).count("⭐") == expected_full

    def test_five_symbols_whatever_the_rating(self):
        for rating in range(0, 6):
            line = format_stars(rating, 3)
            assert line.count("⭐") + line.count("☆") == 5

    def test_a_rating_out_of_range_does_not_crash(self):
        assert format_stars(9, 3)
        assert format_stars(-1, 3)

    def test_a_short_comment_is_untouched(self):
        assert shorten("kurz") == "kurz"

    def test_a_long_comment_is_cut_to_the_limit(self):
        assert len(shorten("a" * 1000)) <= MAX_COMMENT_LENGTH

    def test_the_date_is_german_or_iso(self):
        assert "." in format_date(1758000000, LanguageCode.DE)
        assert "-" in format_date(1758000000, LanguageCode.EN)

    def test_a_broken_timestamp_is_left_out(self):
        """A bad row must not take the whole list down with it."""
        assert format_date(10 ** 20, LanguageCode.DE) == ""
