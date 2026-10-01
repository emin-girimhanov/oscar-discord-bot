"""Tests for usability ids per study programme and for the help dialog."""

import pytest

from oscar.cogs.help import MAX_OPTION_DESCRIPTION, shorten
from oscar.ui.semesterplan_view import get_usability_for_major
from util.enums import LanguageCode, StudyCourse
from util.module import Module
from util.translations import COMMAND_TEXTS, HELP_ANSWERS


# --- usability ids ---

class TestUsabilityIds:
    """Every programme must resolve, not only the four bachelors we started with."""

    def test_every_programme_resolves(self):
        module = Module(id_=1, language=LanguageCode.DE)
        for course in StudyCourse:
            assert module.get_usability_ids(course) == []

    def test_returns_the_stored_ids(self):
        module = Module(id_=1, language=LanguageCode.DE, usability_bsc_wif=[3, 4])
        assert module.get_usability_ids(StudyCourse.BSC_WIF) == [3, 4]

    def test_programmes_do_not_leak_into_each_other(self):
        module = Module(id_=1, language=LanguageCode.DE, usability_bsc_cv=[7])
        assert module.get_usability_ids(StudyCourse.BSC_CV) == [7]
        assert module.get_usability_ids(StudyCourse.BSC_INF) == []

    def test_master_programme_is_covered(self):
        module = Module(id_=1, language=LanguageCode.DE, usability_msc_vc=[9])
        assert module.get_usability_ids(StudyCourse.MSC_VC) == [9]

    def test_bilingual_programme_is_covered(self):
        module = Module(id_=1, language=LanguageCode.DE, usability_bsc_inf_bilingual=[5])
        assert module.get_usability_ids(StudyCourse.BSC_INF_BILINGUAL) == [5]

    def test_view_helper_uses_the_same_ids(self):
        module = Module(id_=1, language=LanguageCode.DE, usability_msc_dke=[2])
        assert get_usability_for_major(module, StudyCourse.MSC_DKE) == [2]

    def test_view_helper_covers_a_master_that_used_to_be_empty(self):
        module = Module(id_=1, language=LanguageCode.DE, usability_msc_inginf=[1, 2])
        assert get_usability_for_major(module, StudyCourse.MSC_INGINF) == [1, 2]


# --- help answers ---

class TestHelpAnswers:
    """The help must answer, and it must answer for every command it lists."""

    def test_every_listed_command_has_an_answer(self):
        assert set(HELP_ANSWERS) == set(COMMAND_TEXTS)

    @pytest.mark.parametrize("command", list(COMMAND_TEXTS))
    def test_both_languages_are_present(self, command):
        assert LanguageCode.DE in HELP_ANSWERS[command]
        assert LanguageCode.EN in HELP_ANSWERS[command]

    @pytest.mark.parametrize("command", list(COMMAND_TEXTS))
    def test_answers_are_not_empty(self, command):
        for language in (LanguageCode.DE, LanguageCode.EN):
            assert HELP_ANSWERS[command][language].strip()

    def test_an_answer_names_its_own_command(self):
        for command, texts in HELP_ANSWERS.items():
            if command == "help":
                continue  # the help does not point at itself
            assert f"/{command}" in texts[LanguageCode.DE]
            assert f"/{command}" in texts[LanguageCode.EN]


# --- select option descriptions ---

class TestShorten:
    """Discord rejects a select option with a description that is too long."""

    @pytest.mark.parametrize("command", list(COMMAND_TEXTS))
    def test_every_description_fits(self, command):
        for language in (LanguageCode.DE, LanguageCode.EN):
            assert len(shorten(COMMAND_TEXTS[command][language])) <= MAX_OPTION_DESCRIPTION

    def test_keeps_a_short_text(self):
        assert shorten("kurz") == "kurz"

    def test_takes_only_the_first_line(self):
        assert shorten("erste Zeile\nzweite Zeile") == "erste Zeile"

    def test_marks_a_cut_text(self):
        assert shorten("x" * 200).endswith("…")

    def test_empty_text_stays_empty(self):
        assert shorten("   ") == ""
