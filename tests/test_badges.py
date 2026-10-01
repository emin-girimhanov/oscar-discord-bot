""" Unit tests for gamification badges and personal study progress tracker."""
# pylint: disable=protected-access

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import discord

from oscar.ui.progress_view import ProgressView
from util.badges import (
    Badge,
    UserProgress,
    check_language_diversity,
    compute_user_progress,
    extract_module_cp,
)
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.module import Module


class TestBadgeModel:
    """Tests covering the Badge dataclass logic."""

    def test_progress_percentage(self):
        badge = Badge(
            id="test",
            emoji="⭐",
            name_de="Test",
            name_en="Test",
            desc_de="Desc",
            desc_en="Desc",
            unlocked=False,
            current=15,
            target=30,
        )
        assert badge.progress_pct == 50

    def test_progress_percentage_capped_at_100(self):
        badge = Badge(
            id="test",
            emoji="⭐",
            name_de="Test",
            name_en="Test",
            desc_de="Desc",
            desc_en="Desc",
            unlocked=True,
            current=45,
            target=30,
        )
        assert badge.progress_pct == 100

    def test_status_text_unlocked(self):
        badge = Badge(
            id="test",
            emoji="⭐",
            name_de="Test",
            name_en="Test",
            desc_de="Desc",
            desc_en="Desc",
            unlocked=True,
            current=30,
            target=30,
        )
        assert "Freigeschaltet" in badge.status_text(LanguageCode.DE)
        assert "Unlocked" in badge.status_text(LanguageCode.EN)

    def test_status_text_locked(self):
        badge = Badge(
            id="test",
            emoji="⭐",
            name_de="Test",
            name_en="Test",
            desc_de="Desc",
            desc_en="Desc",
            unlocked=False,
            current=10,
            target=30,
        )
        assert "10 / 30" in badge.status_text(LanguageCode.DE)
        assert "(33%)" in badge.status_text(LanguageCode.DE)


class TestProgressHelpers:
    """Tests covering CP extraction and language diversity helpers."""

    def test_extract_module_cp(self):
        m1 = Module(id_=1, language=LanguageCode.DE, credit_points="5")
        m2 = Module(id_=2, language=LanguageCode.DE, credit_points="6 CP")
        m3 = Module(id_=3, language=LanguageCode.DE, credit_points="")
        m4 = Module(id_=4, language=LanguageCode.DE, credit_points="None")

        assert extract_module_cp(m1) == 5
        assert extract_module_cp(m2) == 6
        assert extract_module_cp(m3) == 0
        assert extract_module_cp(m4) == 0

    def test_check_language_diversity_empty(self):
        assert check_language_diversity([]) == 0

    def test_check_language_diversity_single_language(self):
        m_de = Module(id_=1, language=ModuleLanguage.DE)
        assert check_language_diversity([m_de]) == 1

        m_en = Module(id_=2, language=ModuleLanguage.EN)
        assert check_language_diversity([m_en]) == 1

    def test_check_language_diversity_multilingual(self):
        m_de = Module(id_=1, language=ModuleLanguage.DE)
        m_en = Module(id_=2, language=ModuleLanguage.EN)
        assert check_language_diversity([m_de, m_en]) == 2

    def test_check_language_diversity_bilingual_module(self):
        m_bilingual = Module(id_=3, language=ModuleLanguage.EN_DE)
        assert check_language_diversity([m_bilingual]) == 2


class TestUserProgressModel:
    """Tests covering UserProgress dataclass and progress bar rendering."""

    def test_progress_bar_rendering(self):
        progress = UserProgress(
            user_id=123,
            has_profile=True,
            major=StudyCourse.BSC_INF,
            po=2024,
            semester=3,
            planned_modules_count=4,
            planned_cp=18,
            target_cp=30,
            study_groups_count=1,
            feedback_count=0,
            badges=(),
        )
        assert progress.completion_pct == 60
        bar_str = progress.progress_bar(10)
        assert "██████░░░░" in bar_str
        assert "60%" in bar_str


class TestComputeUserProgress:
    """Tests covering compute_user_progress integration with database state."""

    @patch("util.badges.get_database")
    def test_fresh_user_has_no_badges(self, mock_get_db):
        mock_db = MagicMock()
        mock_db.get_preferences.return_value = None
        mock_db.get_semesterplan.return_value = []
        mock_db.get_study_buddy_modules.return_value = []
        mock_db.export_user_data.return_value = {"feedback": []}
        mock_get_db.return_value = mock_db

        progress = compute_user_progress(user_id=999)
        assert progress.unlocked_badges_count == 0
        assert progress.total_badges_count == 9
        assert progress.planned_cp == 0
        assert not progress.has_profile

    @patch("util.badges.get_database")
    def test_fully_loaded_user_unlocks_all_badges(self, mock_get_db):
        mock_db = MagicMock()
        mock_db.get_preferences.return_value = {
            "major": 1,
            "po": 2024,
            "semester": 3,
        }
        # 8 modules: 6 DE (5 CP each = 30 CP), 2 EN (10 CP each = 20 CP) -> 50 CP total
        modules = [
            Module(id_=i, language=ModuleLanguage.DE, credit_points="5")
            for i in range(1, 7)
        ] + [
            Module(id_=i, language=ModuleLanguage.EN, credit_points="10")
            for i in range(7, 9)
        ]
        mock_db.get_semesterplan.return_value = modules
        mock_db.get_study_buddy_modules.return_value = [1, 2]
        mock_db.export_user_data.return_value = {
            "feedback": [{"id": 1}],
            "challenge_submissions": [{"challenge_id": "c1"}],
        }
        mock_get_db.return_value = mock_db

        progress = compute_user_progress(user_id=123)
        assert progress.has_profile is True
        assert progress.planned_cp == 50
        assert progress.unlocked_badges_count == 9
        for b in progress.badges:
            assert b.unlocked is True


class TestProgressView:
    """Tests covering the interactive ProgressView."""

    @pytest.mark.asyncio
    async def test_view_initialization(self):
        view = ProgressView(user_id=123, default_language=LanguageCode.DE)
        assert view.language_code == LanguageCode.DE
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_view_language_toggle(self):
        view = ProgressView(user_id=123, default_language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()

        toggle = view._create_language_toggle()
        await toggle.callback(interaction)

        assert view.language_code == LanguageCode.EN
        assert interaction.response.edit_message.await_count >= 1
