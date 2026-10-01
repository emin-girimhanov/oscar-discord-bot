""" Text a student typed is shown to other students, in a message OSCAR sends.

    A review and the language of a code golf entry are free text. Discord renders
    markdown in a bot message, so a review could carry a masked link, a heading or a
    ping, all of it in the voice of the bot. `util.safe_text.plain` takes that out.
"""
# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import MagicMock, patch

import pytest

from oscar.ui.challenge_view import ChallengeView
from oscar.ui.module_reviews_view import ModuleReviewsView
from util.enums import LanguageCode, ModuleLanguage
from util.module import Module
from util.safe_text import plain


MASKED_LINK = "[Altklausur](https://evil.example/login)"


def texts_of(view) -> str:
    """Every text a view shows, joined, the way a student reads it."""
    return "\n".join(
        item.content for item in view.walk_children() if hasattr(item, "content")
    )


class TestPlain:
    """What `plain` does to one string."""

    def test_ordinary_text_is_left_alone(self):
        text = "Sehr gute Vorlesung, die Folien reichen zum Lernen (5 CP)."
        assert plain(text) == text

    def test_a_masked_link_no_longer_hides_its_address(self):
        """`[text](url)` renders as a link named `text`. Escaped, it prints as typed."""
        assert plain(MASKED_LINK) == r"\[Altklausur\](https://evil.example/login)"

    @pytest.mark.parametrize("markup", ["**fett**", "`code`", "||spoiler||", "~~weg~~", "__u__"])
    def test_formatting_is_printed_not_rendered(self, markup: str):
        escaped = plain(markup)
        assert escaped != markup
        assert escaped.replace("\\", "") == markup

    def test_a_heading_cannot_start_a_new_line(self):
        """A review full of newlines used to put `# Ankündigung` on a line of its own."""
        escaped = plain("gut\n# Ankündigung\n- Punkt")
        assert "\n" not in escaped
        assert r"\#" in escaped

    @pytest.mark.parametrize("ping", ["@everyone", "@here", "<@123456789012345678>", "<@&123456789012345678>"])
    def test_nothing_pings(self, ping: str):
        escaped = plain(f"hallo {ping}")
        assert ping not in escaped

    def test_a_backslash_cannot_undo_the_escape(self):
        """`\\[` would turn the escape of the bracket into an escaped backslash."""
        assert plain("\\[x](https://evil.example)").startswith("\\\\\\[")

    def test_a_language_name_survives(self):
        assert plain("C++ (gcc 14)") == "C++ (gcc 14)"


class TestWhereItIsUsed:
    """The filter is only worth something where the text is printed."""

    def test_a_review_cannot_carry_a_masked_link(self):
        module = Module(id_=100, language=ModuleLanguage.DE, title="Datenbanken")
        review = {"rating": 5, "difficulty": 2, "timestamp": 1_700_000_000,
                  "comment": f"Lösung hier: {MASKED_LINK}"}
        with patch("oscar.ui.module_reviews_view.get_user_language",
                   return_value=LanguageCode.DE), \
             patch("oscar.ui.module_reviews_view.get_database") as database:
            database.return_value.get_module_ratings.return_value = {
                "count": 1, "avg_rating": 5.0, "avg_difficulty": 2.0,
            }
            database.return_value.get_module_comments.return_value = [review]
            text = texts_of(ModuleReviewsView(1, module))

        assert MASKED_LINK not in text
        assert "evil.example" in text, "the address stays visible, it is only not hidden"

    def test_the_leaderboard_escapes_the_typed_language(self):
        entry = {"rank": 1, "user_id": 7, "name": None, "code_length": 42,
                 "language": MASKED_LINK, "timestamp": 1}
        challenge = MagicMock()
        challenge.id = "c1"
        challenge.number = 1
        challenge.title.return_value = "FizzBuzz"
        with patch("oscar.ui.challenge_view.get_database") as database:
            database.return_value.get_challenge_leaderboard.return_value = [entry]
            parts = ChallengeView._render_leaderboard(challenge, LanguageCode.DE)

        text = "\n".join(part.content for part in parts)
        assert MASKED_LINK not in text
        assert "42" in text
