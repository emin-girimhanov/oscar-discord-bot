"""Tests for the translations module (t function, format_duration, and dictionaries)."""

import pytest
from util.translations import (
    t,
    format_duration,
    LANGUAGES,
    STUDY_COURSES,
    HELP_LANGUAGES,
    START_TEXTS,
    INFO_TEXTS,
    FEEDBACK_REVIEW,
    FEEDBACK_TEXTS,
    MODULE_TEXTS,
)
from util.enums import LanguageCode, StudyCourse


# --- t() function tests ---

class TestTFunction:
    def test_valid_key_de(self):
        translations = {"greeting": {LanguageCode.DE: "Hallo", LanguageCode.EN: "Hello"}}
        assert t(LanguageCode.DE, "greeting", translations) == "Hallo"

    def test_valid_key_en(self):
        translations = {"greeting": {LanguageCode.DE: "Hallo", LanguageCode.EN: "Hello"}}
        assert t(LanguageCode.EN, "greeting", translations) == "Hello"

    def test_invalid_key(self):
        translations = {"greeting": {LanguageCode.DE: "Hallo"}}
        result = t(LanguageCode.DE, "nonexistent", translations)
        assert result == "[nonexistent]"

    def test_key_missing_language(self):
        translations = {"greeting": {LanguageCode.DE: "Hallo"}}
        result = t(LanguageCode.EN, "greeting", translations)
        assert result == "[greeting]"

    def test_empty_translations(self):
        result = t(LanguageCode.DE, "key", {})
        assert result == "[key]"


# --- format_duration() tests ---

class TestFormatDuration:
    def test_none_returns_all_time(self):
        assert format_duration(None) == FEEDBACK_REVIEW["all_time"][LanguageCode.EN]

    def test_none_returns_all_time_de(self):
        assert format_duration(None, LanguageCode.DE) == FEEDBACK_REVIEW["all_time"][LanguageCode.DE]

    @pytest.mark.parametrize("seconds, expected_suffix", [
        (3600, "h"),       # 1 hour
        (7200, "h"),       # 2 hours
        (43200, "h"),      # 12 hours
    ])
    def test_hours_en(self, seconds, expected_suffix):
        result = format_duration(seconds)
        assert result.endswith(expected_suffix)

    @pytest.mark.parametrize("seconds, expected_suffix", [
        (86400, "d"),      # 1 day
        (172800, "d"),     # 2 days
        (518400, "d"),     # 6 days
    ])
    def test_days_en(self, seconds, expected_suffix):
        result = format_duration(seconds)
        assert result.endswith(expected_suffix)

    @pytest.mark.parametrize("seconds, expected_suffix", [
        (604800, "w"),     # 1 week
        (2419200, "w"),    # 4 weeks
    ])
    def test_weeks_en(self, seconds, expected_suffix):
        result = format_duration(seconds)
        assert result.endswith(expected_suffix)

    @pytest.mark.parametrize("seconds, expected_suffix", [
        (2629743, "mo"),   # 1 month
        (15778458, "mo"),  # 6 months
    ])
    def test_months_en(self, seconds, expected_suffix):
        result = format_duration(seconds)
        assert result.endswith(expected_suffix)

    def test_years_en(self):
        result = format_duration(31556926)  # 1 year
        assert result.endswith("y")

    def test_format_duration_de(self):
        result = format_duration(3600, LanguageCode.DE)
        assert result.endswith("h")

    def test_format_duration_days_de(self):
        result = format_duration(86400, LanguageCode.DE)
        assert result.endswith("T")

    def test_format_duration_weeks_de(self):
        result = format_duration(604800, LanguageCode.DE)
        assert result.endswith("W")

    def test_format_duration_months_de(self):
        result = format_duration(2629743, LanguageCode.DE)
        assert result.endswith("M")

    def test_format_duration_years_de(self):
        result = format_duration(31556926, LanguageCode.DE)
        assert result.endswith("J")


# --- Translation dictionary completeness tests ---

class TestTranslationDictionaries:
    def test_languages_dict_has_both_codes(self):
        for lang_code in LanguageCode:
            assert lang_code in LANGUAGES
            assert LanguageCode.DE in LANGUAGES[lang_code]
            assert LanguageCode.EN in LANGUAGES[lang_code]

    def test_study_courses_dict_has_all_courses(self):
        for course in StudyCourse:
            assert course in STUDY_COURSES
            assert LanguageCode.DE in STUDY_COURSES[course]
            assert LanguageCode.EN in STUDY_COURSES[course]

    def test_help_languages_has_required_keys(self):
        required = ["help", "description", "select_option_1"]
        for key in required:
            assert key in HELP_LANGUAGES
            assert LanguageCode.DE in HELP_LANGUAGES[key]
            assert LanguageCode.EN in HELP_LANGUAGES[key]

    def test_start_texts_has_required_keys(self):
        required = ["welcome_title", "welcome_text", "language_question"]
        for key in required:
            assert key in START_TEXTS

    def test_info_texts_has_required_keys(self):
        required = ["responsibility", "lecturer", "content", "ilo"]
        for key in required:
            assert key in INFO_TEXTS

    def test_feedback_review_keys(self):
        required = ["intuitiveness", "discoverability", "usefulness", "rating"]
        for key in required:
            assert key in FEEDBACK_REVIEW

    def test_feedback_texts_keys(self):
        required = ["welcome_text", "choose_1", "improve", "wish", "bug"]
        for key in required:
            assert key in FEEDBACK_TEXTS

    def test_module_texts_keys(self):
        required = ["kuerzel", "sprache", "dozent"]
        for key in required:
            assert key in MODULE_TEXTS
