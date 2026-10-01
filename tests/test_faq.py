"""The FAQ has one source, and the bot and the documentation site both read it.

The answers used to live only in `docs/features/faq.md`. A student in Discord never saw
them, and nothing stopped the page from drifting away from the bot. It had: the page
promised that only you could see your semester plan, while `/semesterplan` answered in
the channel for everyone to read.

Now `src/util/translations.py` holds the questions, `/help` reads them at runtime and
the page renders them at build time through the `show_faq` macro. These tests hold that
arrangement together and check that every entry still fits inside a discord select.
"""

import importlib
import sys
from pathlib import Path

import pytest

from oscar.cogs.help import MAX_OPTION_LABEL, HelpView, shorten
from util.enums import LanguageCode
from util.translations import FAQ_ANSWERS, FAQ_QUESTIONS


REPO = Path(__file__).resolve().parent.parent

# discord refuses a select with more than this many options
MAX_SELECT_OPTIONS = 25

LANGUAGES = [LanguageCode.DE, LanguageCode.EN]


class TestEveryEntryIsComplete:
    def test_questions_and_answers_use_the_same_keys(self):
        assert FAQ_QUESTIONS.keys() == FAQ_ANSWERS.keys(), (
            "A question without an answer shows an empty card, an answer without a "
            "question is unreachable."
        )

    def test_there_is_at_least_one(self):
        """Guards against an empty dictionary passing every other test here."""
        assert len(FAQ_QUESTIONS) >= 5

    @pytest.mark.parametrize("key", sorted(FAQ_QUESTIONS))
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_both_languages_are_written(self, key, language):
        assert FAQ_QUESTIONS[key].get(language, "").strip()
        assert FAQ_ANSWERS[key].get(language, "").strip()


class TestItFitsInsideDiscord:
    def test_the_list_is_not_too_long_for_a_select(self):
        assert len(FAQ_QUESTIONS) <= MAX_SELECT_OPTIONS, (
            f"A discord select holds at most {MAX_SELECT_OPTIONS} options. Drop a "
            "question or split the list before adding more."
        )

    @pytest.mark.parametrize("key", sorted(FAQ_QUESTIONS))
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_a_question_fits_on_one_option_label(self, key, language):
        """A label over the limit makes discord reject the whole message."""
        label = shorten(FAQ_QUESTIONS[key][language], MAX_OPTION_LABEL)
        assert 0 < len(label) <= MAX_OPTION_LABEL

    @pytest.mark.parametrize("key", sorted(FAQ_QUESTIONS))
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_a_question_is_not_cut_off(self, key, language):
        """Shortening is a safety net, not the plan. Write questions that fit."""
        question = FAQ_QUESTIONS[key][language]
        assert len(question) <= MAX_OPTION_LABEL, (
            f"The {language.name} question for {key!r} is {len(question)} characters "
            f"and would be truncated at {MAX_OPTION_LABEL}. Shorten it."
        )


class TestHelpShowsTheAnswers:
    def test_nothing_picked_names_the_three_menus(self):
        """The greeting has one job: say what the three dropdowns are for."""
        answer = HelpView(LanguageCode.EN)._answer()
        assert "welcome to OSCAR" in answer
        for menu in ("**Open**", "**Command**", "**Question**"):
            assert menu in answer

    @pytest.mark.parametrize("key", sorted(FAQ_QUESTIONS))
    def test_a_picked_question_shows_its_answer(self, key):
        view = HelpView(LanguageCode.EN)
        view.selected_question = key

        answer = view._answer()
        assert FAQ_QUESTIONS[key][LanguageCode.EN] in answer
        assert FAQ_ANSWERS[key][LanguageCode.EN] in answer

    def test_picking_a_question_drops_the_command_answer(self):
        """Two answers on screen at once would be confusing, so one clears the other."""
        view = HelpView(LanguageCode.EN)
        view.selected_command = "module"
        view.selected_question = "mobile"

        assert FAQ_ANSWERS["mobile"][LanguageCode.EN] in view._answer()

    def test_the_language_toggle_reaches_the_faq(self):
        view = HelpView(LanguageCode.DE)
        view.selected_question = "mobile"

        assert FAQ_ANSWERS["mobile"][LanguageCode.DE] in view._answer()


class TestTheDocumentationPageRendersTheSameText:
    @staticmethod
    def _main_module():
        """Imports `docs/main.py`, the module mkdocs-macros loads."""
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        return importlib.import_module("docs.main")

    @pytest.mark.parametrize("language", ["en", "de"])
    def test_every_question_reaches_the_page(self, language):
        rendered = self._main_module().render_faq(language)
        code = LanguageCode.DE if language == "de" else LanguageCode.EN

        for key, question in FAQ_QUESTIONS.items():
            assert question[code] in rendered, f"{key} is missing from the page"

    def test_the_page_does_not_hold_its_own_copy(self):
        """The markdown must call the macro, not repeat the answers."""
        page = (REPO / "docs" / "features" / "faq.md").read_text(encoding="utf8")
        assert "show_faq()" in page

        for answer in FAQ_ANSWERS.values():
            first_line = answer[LanguageCode.EN].split("\n")[0]
            assert first_line not in page, (
                "An answer was pasted into faq.md. That is the second copy this "
                "arrangement exists to prevent."
            )
