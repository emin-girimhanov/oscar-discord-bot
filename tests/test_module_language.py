"""Tests for the module language, including modules taught in both languages."""

import pytest
from unittest.mock import patch

from oscar.ui.all_info_view import AllInfoView
from oscar.ui.module_view import ModuleView
from util.database import Database
from util.enums import LanguageCode, ModuleLanguage
from util.module import Module
from util.translations import MODULE_LANGUAGES, module_language_name


# The row of a module that is taught in english and german, as module 110103 is.
BILINGUAL_ROW = {
    "Identifizierung": 110103,
    "Modulsprache": 2,
    "Modultitel": "Logik",
    "Modultitel (englisch)": "Logic",
}


def make_module(language: int) -> Module:
    """Builds a module from a tables row, the way the bot reads the catalogue."""
    row = dict(BILINGUAL_ROW)
    row["Modulsprache"] = language
    return Module.from_tables_dict(row)


def rendered(view) -> str:
    """Collects every text and button label of a view into one string."""
    parts: list[str] = []

    def walk(item):
        content = getattr(item, "content", None)
        if isinstance(content, str):
            parts.append(content)
        label = getattr(item, "label", None)
        if isinstance(label, str):
            parts.append(label)
        for child in getattr(item, "children", []):
            walk(child)

    walk(view)
    return "\n".join(parts)


# --- ModuleLanguage enum ---

class TestModuleLanguageEnum:
    """Tests for the ModuleLanguage enum."""

    def test_values(self):
        assert ModuleLanguage.values() == [0, 1, 2]

    @pytest.mark.parametrize("member, value, name", [
        (ModuleLanguage.EN, 0, "en"),
        (ModuleLanguage.DE, 1, "de"),
        (ModuleLanguage.EN_DE, 2, "en_de"),
    ])
    def test_members(self, member, value, name):
        assert int(member) == value
        assert member.name == name

    def test_valid_languages(self):
        assert ModuleLanguage.valid_languages() == ["en", "de", "en_de"]

    @pytest.mark.parametrize("code, expected", [
        ("en", ModuleLanguage.EN),
        ("DE", ModuleLanguage.DE),
        ("en_de", ModuleLanguage.EN_DE),
        ("EN_DE", ModuleLanguage.EN_DE),
    ])
    def test_from_language_code(self, code, expected):
        assert ModuleLanguage.from_language_code(code) == expected

    def test_unknown_value_raises(self):
        with pytest.raises(ValueError):
            ModuleLanguage(3)

    @pytest.mark.parametrize("module_language, language_code", [
        (ModuleLanguage.EN, LanguageCode.EN),
        (ModuleLanguage.DE, LanguageCode.DE),
    ])
    def test_single_languages_match_the_bot_languages(self, module_language, language_code):
        """A module in one language keeps the value the bot itself uses."""
        assert module_language == language_code

    def test_bot_languages_are_unchanged(self):
        """The bot still speaks two languages only."""
        assert LanguageCode.values() == [0, 1]


# --- module_language_name() ---

class TestModuleLanguageName:
    """Tests for the rendered name of a module language."""

    @pytest.mark.parametrize("module_language, display_language, expected", [
        (ModuleLanguage.EN, LanguageCode.EN, "English"),
        (ModuleLanguage.EN, LanguageCode.DE, "Englisch"),
        (ModuleLanguage.DE, LanguageCode.EN, "German"),
        (ModuleLanguage.DE, LanguageCode.DE, "Deutsch"),
        (ModuleLanguage.EN_DE, LanguageCode.EN, "english/deutsch"),
        (ModuleLanguage.EN_DE, LanguageCode.DE, "Englisch/Deutsch"),
    ])
    def test_names(self, module_language, display_language, expected):
        assert module_language_name(module_language, display_language) == expected

    @pytest.mark.parametrize("raw, expected", [
        (0, "English"),
        (1, "German"),
        (2, "english/deutsch"),
        ("en", "English"),
        ("de", "German"),
        ("en_de", "english/deutsch"),
    ])
    def test_raw_values_are_accepted(self, raw, expected):
        """Modules read from the database carry the id or the name of their language."""
        assert module_language_name(raw, LanguageCode.EN) == expected

    @pytest.mark.parametrize("unknown", [3, 999, -1, "fr", ""])
    def test_unknown_values_fall_back_to_english(self, unknown):
        """An id we do not know yet must not take a view down."""
        assert module_language_name(unknown, LanguageCode.DE) == "Englisch"

    def test_dictionary_covers_every_module_language(self):
        for module_language in ModuleLanguage:
            assert module_language in MODULE_LANGUAGES
            for language_code in LanguageCode:
                assert language_code in MODULE_LANGUAGES[module_language]


# --- Module parsing ---

class TestModuleReadsBothLanguages:
    """Tests for the language a Module keeps."""

    @pytest.mark.parametrize("value, expected", [
        (0, ModuleLanguage.EN),
        (1, ModuleLanguage.DE),
        (2, ModuleLanguage.EN_DE),
    ])
    def test_from_tables_dict(self, value, expected):
        assert make_module(value).language == expected

    def test_from_tables_dict_keeps_the_unknown_fallback(self):
        """An id outside the enum is still read as english."""
        assert make_module(999).language == ModuleLanguage.EN

    @pytest.mark.parametrize("value, expected", [
        (0, ModuleLanguage.EN),
        (1, ModuleLanguage.DE),
        (2, ModuleLanguage.EN_DE),
        ("2", ModuleLanguage.EN_DE),
    ])
    def test_from_dict(self, value, expected):
        module = Module.from_dict({"id": 110103, "language": value})
        assert module.language == expected

    def test_from_dict_still_rejects_an_unknown_language(self):
        with pytest.raises(ValueError):
            Module.from_dict({"id": 110103, "language": 3})

    def test_str_names_the_language(self):
        assert "en_de" in str(make_module(2))

    @pytest.mark.parametrize("language_code", [LanguageCode.DE, LanguageCode.EN])
    def test_getters_do_not_crash(self, language_code):
        """A bilingual module answers in both languages without a translation row."""
        module = Module.from_tables_dict({**BILINGUAL_ROW, "Inhalt": "Beides"})
        assert module.get_content(language_code) == "Beides"
        assert module.get_title(language_code) != ""


# --- Views ---

class TestViewsShowBothLanguages:
    """End to end tests for the language a user gets to see."""

    @pytest.fixture(autouse=True)
    def offline_lookups(self):
        """The detail view resolves selection ids, which needs no tables api here."""
        with patch("util.module.get_value_by_id", return_value="1"):
            yield

    @pytest.mark.parametrize("user_language, expected", [
        (LanguageCode.EN, "english/deutsch"),
        (LanguageCode.DE, "Englisch/Deutsch"),
    ])
    def test_module_view_bilingual(self, user_language, expected):
        with patch("oscar.ui.module_view.get_user_language", return_value=user_language), \
             patch("oscar.ui.module_view.get_database") as mock_database:
            mock_database.return_value.get_preferences.return_value = None
            view = ModuleView(user_id=1, module=make_module(2))

        assert expected in rendered(view)

    @pytest.mark.parametrize("user_language, expected", [
        (LanguageCode.EN, "english/deutsch"),
        (LanguageCode.DE, "Englisch/Deutsch"),
    ])
    def test_all_info_view_bilingual(self, user_language, expected):
        with patch("oscar.ui.all_info_view.get_user_language", return_value=user_language):
            view = AllInfoView(user_id=1, module=make_module(2))

        assert expected in rendered(view)

    @pytest.mark.parametrize("value, user_language, expected", [
        (0, LanguageCode.EN, "English"),
        (0, LanguageCode.DE, "Englisch"),
        (1, LanguageCode.EN, "German"),
        (1, LanguageCode.DE, "Deutsch"),
    ])
    def test_views_keep_the_single_languages(self, value, user_language, expected):
        with patch("oscar.ui.module_view.get_user_language", return_value=user_language), \
             patch("oscar.ui.module_view.get_database") as mock_database:
            mock_database.return_value.get_preferences.return_value = None
            module_view = ModuleView(user_id=1, module=make_module(value))
        with patch("oscar.ui.all_info_view.get_user_language", return_value=user_language):
            all_info_view = AllInfoView(user_id=1, module=make_module(value))

        assert expected in rendered(module_view)
        assert expected in rendered(all_info_view)


# --- Database ---

class TestDatabaseKeepsBothLanguages:
    """Tests for the catalogue cache and the semester plan."""

    @pytest.fixture
    def db(self, tmp_path):
        return Database(db_path=str(tmp_path / "test.db"))

    def test_add_module_from_a_bilingual_row(self, db):  # pylint: disable=redefined-outer-name
        """The cache knows the two bot languages only, so the row is kept as german."""
        with patch("util.database.get_rows_from_view") as mock_view:
            mock_view.return_value = [BILINGUAL_ROW]
            db.add_module(110103)

        module = db.get_module(110103, LanguageCode.DE)
        assert module is not None
        assert module.language == LanguageCode.DE.name
        assert module.get_title(LanguageCode.DE) == "Logik"
        assert module.get_title(LanguageCode.EN) == "Logic"

    def test_add_to_semesterplan_with_a_bilingual_module(self, db):  # pylint: disable=redefined-outer-name
        """The 'add to semester overview' button must work for these modules too."""
        with patch("util.database.get_rows_from_view") as mock_view:
            mock_view.return_value = [BILINGUAL_ROW]
            db.add_to_semesterplan(user_id=12345, module_id=110103)

        plan = db.get_semesterplan(12345)
        assert [module.id_ for module in plan] == [110103]
