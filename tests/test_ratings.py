""" Tests for module ratings, difficulty evaluations, and the past exams archive."""
# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import AsyncMock, patch
import pytest

from oscar.ui.rating_modal import ModuleRatingModal
from util.database import Database
from util.enums import LanguageCode
from util.module import Module
from util.translations import EXAM_TEXTS, RATING_TEXTS


@pytest.fixture
def db(tmp_path):
    """ Isolated temporary database for ratings testing."""
    return Database(db_path=str(tmp_path / "test_ratings.db"))


@pytest.fixture
def dummy_module():
    """ Sample module for rating testing."""
    return Module(
        id_=101,
        language=LanguageCode.DE,
        title="Algorithmen und Datenstrukturen",
        title_en="Algorithms and Data Structures",
        abbreviation="AuD",
        lecturer="Prof. Dr. Mustermann",
        credit_points="5 CP",
    )


class TestRatingModal:
    """ Tests for the ModuleRatingModal UI component."""

    def test_modal_initialization_de(self, dummy_module):
        modal = ModuleRatingModal(module=dummy_module, language=LanguageCode.DE)
        assert "Modul bewerten" in modal.title
        assert len(modal.children) == 3

    def test_modal_initialization_en(self, dummy_module):
        modal = ModuleRatingModal(module=dummy_module, language=LanguageCode.EN)
        assert "Rate Module" in modal.title
        assert len(modal.children) == 3

    @pytest.mark.asyncio
    async def test_modal_submit_valid(self, db, dummy_module):
        modal = ModuleRatingModal(module=dummy_module, language=LanguageCode.DE)
        modal.rating_input._value = "4"
        modal.difficulty_input._value = "3"
        modal.comment_input._value = "Tolle Vorlesung!"

        interaction = AsyncMock()
        interaction.user.id = 42

        with patch("oscar.ui.rating_modal.get_database", return_value=db):
            await modal.on_submit(interaction)

        ratings = db.get_module_ratings(dummy_module.id_)
        assert ratings["count"] == 1
        assert ratings["avg_rating"] == 4.0
        assert ratings["avg_difficulty"] == 3.0

        user_rating = db.get_user_module_rating(user_id=42, module_id=dummy_module.id_)
        assert user_rating is not None
        assert user_rating["rating"] == 4
        assert user_rating["difficulty"] == 3
        assert user_rating["comment"] == "Tolle Vorlesung!"

        interaction.response.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_modal_submit_invalid_digits(self, db, dummy_module):
        modal = ModuleRatingModal(module=dummy_module, language=LanguageCode.DE)
        modal.rating_input._value = "abc"
        modal.difficulty_input._value = "3"

        interaction = AsyncMock()
        interaction.user.id = 42

        with patch("oscar.ui.rating_modal.get_database", return_value=db):
            await modal.on_submit(interaction)

        assert db.get_module_ratings(dummy_module.id_)["count"] == 0
        interaction.response.send_message.assert_awaited_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_modal_submit_out_of_range(self, db, dummy_module):
        modal = ModuleRatingModal(module=dummy_module, language=LanguageCode.DE)
        modal.rating_input._value = "6"
        modal.difficulty_input._value = "3"

        interaction = AsyncMock()
        interaction.user.id = 42

        with patch("oscar.ui.rating_modal.get_database", return_value=db):
            await modal.on_submit(interaction)

        assert db.get_module_ratings(dummy_module.id_)["count"] == 0
        interaction.response.send_message.assert_awaited_once()


class TestRatingExportAndDelete:
    """ Tests verifying ratings are included in data export and wiped on delete."""

    def test_ratings_exported_in_user_data(self, db):
        db.rate_module(user_id=123, module_id=101, rating=5, difficulty=2, comment="Great")
        exported = db.export_user_data(123)

        assert len(exported["module_ratings"]) == 1
        assert exported["module_ratings"][0]["module_id"] == 101
        assert exported["module_ratings"][0]["rating"] == 5

    def test_ratings_deleted_on_delete_user_data(self, db):
        db.rate_module(user_id=123, module_id=101, rating=5, difficulty=2)
        removed = db.delete_user_data(123)

        assert removed.get("module_ratings") == 1
        assert db.get_user_module_rating(123, 101) is None
        assert db.get_module_ratings(101)["count"] == 0


class TestRatingTranslations:
    """ Verify completeness of translations for ratings and exams."""

    @pytest.mark.parametrize("key", list(RATING_TEXTS.keys()))
    def test_rating_texts_has_both_languages(self, key):
        assert LanguageCode.DE in RATING_TEXTS[key]
        assert LanguageCode.EN in RATING_TEXTS[key]
        assert len(RATING_TEXTS[key][LanguageCode.DE]) > 0
        assert len(RATING_TEXTS[key][LanguageCode.EN]) > 0

    @pytest.mark.parametrize("key", list(EXAM_TEXTS.keys()))
    def test_exam_texts_has_both_languages(self, key):
        assert LanguageCode.DE in EXAM_TEXTS[key]
        assert LanguageCode.EN in EXAM_TEXTS[key]
        assert len(EXAM_TEXTS[key][LanguageCode.DE]) > 0
        assert len(EXAM_TEXTS[key][LanguageCode.EN]) > 0

    def test_exam_desc_names_no_dead_host(self):
        """The text used to advertise `klausuren.farafin.de`, which stopped resolving.

        The addresses live in `util.exams` now, where they can be checked one by one,
        and no url is written into a translated sentence any more.
        """
        for language in (LanguageCode.DE, LanguageCode.EN):
            assert "klausuren.farafin.de" not in EXAM_TEXTS["exam_desc"][language]
            assert "http" not in EXAM_TEXTS["exam_desc"][language]
