""" Unit tests for privacy-preserving cohort study progress statistics (Issue #48)."""
# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import discord

from oscar.ui.progress_view import ProgressView
from oscar.cogs.progress import Progress
from util.database import Database
from util.enums import LanguageCode
from util.translations import COHORT_TEXTS


@pytest.fixture
def db(tmp_path):
    """Isolated temporary database for cohort statistics testing."""
    return Database(db_path=str(tmp_path / "test_cohort.db"))


class TestCohortDatabaseMetrics:
    """Tests covering Database.get_cohort_statistics."""

    def test_empty_database_returns_insufficient_data(self, db):
        stats = db.get_cohort_statistics()
        assert stats["has_sufficient_data"] is False
        assert stats["cohort_size"] == 0
        assert stats["total_registered_students"] == 0
        assert stats["top_modules"] == []
        assert stats["major_distribution"] == []

    def test_k_anonymity_privacy_threshold_less_than_three(self, db):
        # 2 students in B-INF semester 2
        db.set_preferences(user_id=1, language=LanguageCode.DE, major="BSC_INF", semester=2)
        db.set_preferences(user_id=2, language=LanguageCode.DE, major="BSC_INF", semester=2)

        stats = db.get_cohort_statistics(major="BSC_INF", semester=2, min_cohort_size=3)
        assert stats["has_sufficient_data"] is False
        assert stats["cohort_size"] == 2
        assert stats["min_cohort_size"] == 3
        # Ensure detailed module breakdown is suppressed to prevent fingerprinting
        assert stats["top_modules"] == []
        assert stats["avg_modules_planned"] is None
        assert stats["avg_cp_planned"] is None

    def test_sufficient_cohort_calculates_averages_and_top_modules(self, db):
        # Add 3 modules
        db.add_module(101, LanguageCode.DE, "AuD", "AuD EN")
        db.add_module(102, LanguageCode.DE, "LinA", "LinA EN")
        db.add_module(103, LanguageCode.DE, "Theo", "Theo EN")

        # 3 students in B-INF semester 2
        db.set_preferences(user_id=1, language=LanguageCode.DE, major="BSC_INF", semester=2)
        db.set_preferences(user_id=2, language=LanguageCode.DE, major="BSC_INF", semester=2)
        db.set_preferences(user_id=3, language=LanguageCode.DE, major="BSC_INF", semester=2)

        # User 1 plans 101, 102
        db.add_to_semesterplan(1, 101, LanguageCode.DE)
        db.add_to_semesterplan(1, 102, LanguageCode.DE)

        # User 2 plans 101, 103
        db.add_to_semesterplan(2, 101, LanguageCode.DE)
        db.add_to_semesterplan(2, 103, LanguageCode.DE)

        # User 3 plans 101
        db.add_to_semesterplan(3, 101, LanguageCode.DE)

        stats = db.get_cohort_statistics(major="BSC_INF", semester=2, min_cohort_size=3)
        assert stats["has_sufficient_data"] is True
        assert stats["cohort_size"] == 3
        # Total modules: 2 + 2 + 1 = 5 / 3 = 1.7
        assert stats["avg_modules_planned"] == 1.7
        # 1.7 * 5 = 8.5 CP
        assert stats["avg_cp_planned"] == 8.5

        # Top modules check: 101 should be planned by all 3 (100%)
        top = stats["top_modules"]
        assert len(top) == 3
        assert top[0]["id"] == 101
        assert top[0]["count"] == 3
        assert top[0]["percentage"] == 100

    def test_major_distribution_across_faculty(self, db):
        db.set_preferences(user_id=1, language=LanguageCode.DE, major="BSC_INF")
        db.set_preferences(user_id=2, language=LanguageCode.DE, major="BSC_INF")
        db.set_preferences(user_id=3, language=LanguageCode.DE, major="BSC_CV")

        stats = db.get_cohort_statistics()
        assert stats["total_registered_students"] == 3
        dist = {d["major"]: d["count"] for d in stats["major_distribution"]}
        assert dist.get("BSC_INF") == 2
        assert dist.get("BSC_CV") == 1


class TestProgressViewCohortIntegration:
    """Tests covering ProgressView rendering with cohort statistics."""

    @pytest.mark.asyncio
    async def test_progress_view_initializes_cohort_mode(self, db):
        with patch("oscar.ui.progress_view.get_database", return_value=db):
            view = ProgressView(
                user_id=123,
                default_language=LanguageCode.DE,
                initial_mode="cohort",
                target_major="BSC_INF",
                target_semester=1,
            )
            assert view.view_mode == "cohort"
            assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_toggle_between_progress_and_cohort(self, db):
        with patch("oscar.ui.progress_view.get_database", return_value=db):
            view = ProgressView(user_id=123, default_language=LanguageCode.DE)
            assert view.view_mode == "progress"

            interaction = MagicMock(spec=discord.Interaction)
            interaction.response = MagicMock()
            interaction.response.is_done.return_value = False
            interaction.response.edit_message = AsyncMock()

            # Find cohort toggle button (second item in ActionRow)
            container = view.children[0]
            action_row = container.children[-1]
            cohort_btn = action_row.children[1]

            await cohort_btn.callback(interaction)
            assert view.view_mode == "cohort"

            await cohort_btn.callback(interaction)
            assert view.view_mode == "progress"


class TestCohortTranslations:
    """Verify completeness of translations for cohort statistics."""

    @pytest.mark.parametrize("key", list(COHORT_TEXTS.keys()))
    def test_cohort_texts_coverage(self, key):
        assert LanguageCode.DE in COHORT_TEXTS[key]
        assert LanguageCode.EN in COHORT_TEXTS[key]
        assert len(COHORT_TEXTS[key][LanguageCode.DE]) > 0
        assert len(COHORT_TEXTS[key][LanguageCode.EN]) > 0


class TestCohortCommands:
    """Tests for the /cohort and /statistik slash commands."""

    @pytest.mark.asyncio
    async def test_cohort_command_invokes_view(self):
        bot = MagicMock()
        cog = Progress(bot)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 999
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        await cog.cohort.callback(cog, interaction, studiengang="BSC_INF", semester=2)
        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once()
        _, kwargs = interaction.followup.send.call_args
        assert isinstance(kwargs.get("view"), ProgressView)
        assert kwargs.get("view").view_mode == "cohort"

    @pytest.mark.asyncio
    async def test_statistik_alias_command(self):
        bot = MagicMock()
        cog = Progress(bot)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 999
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        await cog.statistik.callback(cog, interaction)
        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once()
