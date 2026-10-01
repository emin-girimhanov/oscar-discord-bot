""" Tests for the study buddy matching feature and StudyBuddyView. """

from unittest.mock import AsyncMock, MagicMock, patch
import discord
import pytest

from oscar.ui.study_buddy_view import (
    CreateThreadButton,
    JoinStudyBuddyButton,
    LeaveStudyBuddyButton,
    StudyBuddyView,
)
from util.database import Database
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.module import Module


STUDENT_A = 1001
STUDENT_B = 1002
STUDENT_C = 1003
MODULE_MATH = 101
MODULE_INFO = 102


@pytest.fixture
def db(tmp_path):
    """A throwaway database for study buddy tests."""
    test_db = Database(db_path=str(tmp_path / "study_buddies.db"))
    test_db.add_module(MODULE_MATH, LanguageCode.DE, "Mathematik I", "Mathematics I")
    test_db.add_module(MODULE_INFO, LanguageCode.DE, "Informatik I", "Computer Science I")
    return test_db


class TestStudyBuddyDatabase:
    def test_join_and_leave_study_buddy(self, db):
        # Initially not opted in
        assert db.is_study_buddy(STUDENT_A, MODULE_MATH) is False
        assert db.get_study_buddy_count(MODULE_MATH) == 0

        # Join
        joined = db.join_study_buddy(STUDENT_A, MODULE_MATH)
        assert joined is True
        assert db.is_study_buddy(STUDENT_A, MODULE_MATH) is True
        assert db.get_study_buddy_count(MODULE_MATH) == 1

        # Joining again is ignored
        joined_again = db.join_study_buddy(STUDENT_A, MODULE_MATH)
        assert joined_again is False
        assert db.get_study_buddy_count(MODULE_MATH) == 1

        # Leave
        left = db.leave_study_buddy(STUDENT_A, MODULE_MATH)
        assert left is True
        assert db.is_study_buddy(STUDENT_A, MODULE_MATH) is False
        assert db.get_study_buddy_count(MODULE_MATH) == 0

        # Leaving again returns False
        assert db.leave_study_buddy(STUDENT_A, MODULE_MATH) is False

    def test_get_study_buddies_order(self, db):
        db.join_study_buddy(STUDENT_A, MODULE_MATH)
        db.join_study_buddy(STUDENT_B, MODULE_MATH)
        db.join_study_buddy(STUDENT_C, MODULE_INFO)

        math_buddies = db.get_study_buddies(MODULE_MATH)
        assert math_buddies == [STUDENT_A, STUDENT_B]

        info_buddies = db.get_study_buddies(MODULE_INFO)
        assert info_buddies == [STUDENT_C]

    def test_get_study_buddy_modules(self, db):
        db.join_study_buddy(STUDENT_A, MODULE_MATH)
        db.join_study_buddy(STUDENT_A, MODULE_INFO)

        mods = db.get_study_buddy_modules(STUDENT_A)
        assert sorted(mods) == [MODULE_MATH, MODULE_INFO]

    def test_module_planner_count(self, db):
        assert db.get_module_planner_count(MODULE_MATH) == 0

        db.add_to_semesterplan(STUDENT_A, MODULE_MATH)
        db.add_to_semesterplan(STUDENT_B, MODULE_MATH)
        assert db.get_module_planner_count(MODULE_MATH) == 2

    def test_study_buddies_exported_and_deleted(self, db):
        db.join_study_buddy(STUDENT_A, MODULE_MATH)

        data = db.export_user_data(STUDENT_A)
        assert "study_buddies" in data
        assert len(data["study_buddies"]) == 1
        assert data["study_buddies"][0]["module_id"] == MODULE_MATH

        removed = db.delete_user_data(STUDENT_A)
        assert removed.get("study_buddies") == 1
        assert db.is_study_buddy(STUDENT_A, MODULE_MATH) is False


class TestStudyBuddyView:
    @patch("oscar.ui.study_buddy_view.get_database")
    @patch("oscar.ui.study_buddy_view.get_user_language", return_value=LanguageCode.DE)
    def test_view_empty_plan_no_module(self, mock_lang, mock_get_db):
        mock_db = MagicMock()
        mock_db.get_semesterplan.return_value = []
        mock_get_db.return_value = mock_db

        view = StudyBuddyView(user_id=STUDENT_A, module_id=None)
        assert len(view.children) > 0

    @patch("oscar.ui.study_buddy_view.get_database")
    @patch("oscar.ui.study_buddy_view.get_user_language", return_value=LanguageCode.DE)
    @patch("util.module.Module.from_id")
    def test_view_not_opted_in(self, mock_from_id, mock_lang, mock_get_db):
        mock_db = MagicMock()
        mock_db.get_semesterplan.return_value = []
        mock_db.get_module_planner_count.return_value = 5
        mock_db.get_study_buddy_count.return_value = 2
        mock_db.is_study_buddy.return_value = False
        mock_get_db.return_value = mock_db

        dummy_mod = Module(
            id_=MODULE_MATH,
            language=ModuleLanguage.DE,
            title="Mathematik I",
            credit_points="6",
        )
        mock_from_id.return_value = dummy_mod

        view = StudyBuddyView(user_id=STUDENT_A, module_id=MODULE_MATH)
        # Should contain JoinStudyBuddyButton
        buttons = [
            child for container in view.children
            if hasattr(container, "children")
            for child in container.children
            if hasattr(child, "children")
            for btn in child.children
            if isinstance(btn, JoinStudyBuddyButton)
        ]
        assert len(buttons) >= 1

    @patch("oscar.ui.study_buddy_view.get_database")
    @patch("oscar.ui.study_buddy_view.get_user_language", return_value=LanguageCode.DE)
    @patch("util.module.Module.from_id")
    def test_view_opted_in_with_others(self, mock_from_id, mock_lang, mock_get_db):
        mock_db = MagicMock()
        mock_db.get_semesterplan.return_value = []
        mock_db.get_module_planner_count.return_value = 5
        mock_db.get_study_buddy_count.return_value = 2
        mock_db.is_study_buddy.return_value = True
        mock_db.get_study_buddies.return_value = [STUDENT_A, STUDENT_B]
        mock_get_db.return_value = mock_db

        dummy_mod = Module(
            id_=MODULE_MATH,
            language=ModuleLanguage.DE,
            title="Mathematik I",
            credit_points="6",
        )
        mock_from_id.return_value = dummy_mod

        view = StudyBuddyView(user_id=STUDENT_A, module_id=MODULE_MATH)
        # Should contain LeaveStudyBuddyButton and CreateThreadButton
        leave_buttons = []
        thread_buttons = []
        for container in view.children:
            if hasattr(container, "children"):
                for row in container.children:
                    if hasattr(row, "children"):
                        for item in row.children:
                            if isinstance(item, LeaveStudyBuddyButton):
                                leave_buttons.append(item)
                            elif isinstance(item, CreateThreadButton):
                                thread_buttons.append(item)

        assert len(leave_buttons) == 1
        assert len(thread_buttons) == 1


class TestButtonsCallback:
    @pytest.mark.asyncio
    async def test_join_button_callback(self):
        view = MagicMock(spec=StudyBuddyView)
        view.user_id = STUDENT_A
        view.build_view = MagicMock()

        btn = JoinStudyBuddyButton(view=view, module_id=MODULE_MATH, language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.edit_message = AsyncMock()

        with patch("oscar.ui.study_buddy_view.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            await btn.callback(interaction)

            mock_db.join_study_buddy.assert_called_once_with(
                user_id=STUDENT_A, module_id=MODULE_MATH
            )
            view.build_view.assert_called_once()
            interaction.response.edit_message.assert_awaited_once_with(view=view)

    @pytest.mark.asyncio
    async def test_leave_button_callback(self):
        view = MagicMock(spec=StudyBuddyView)
        view.user_id = STUDENT_A
        view.build_view = MagicMock()

        btn = LeaveStudyBuddyButton(view=view, module_id=MODULE_MATH, language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.edit_message = AsyncMock()

        with patch("oscar.ui.study_buddy_view.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            await btn.callback(interaction)

            mock_db.leave_study_buddy.assert_called_once_with(
                user_id=STUDENT_A, module_id=MODULE_MATH
            )
            view.build_view.assert_called_once()
            interaction.response.edit_message.assert_awaited_once_with(view=view)

    @pytest.mark.asyncio
    async def test_create_thread_button_in_dm_fails_gracefully(self):
        dummy_mod = Module(id_=MODULE_MATH, language=ModuleLanguage.DE, title="Mathematik I")
        btn = CreateThreadButton(module=dummy_mod, buddies=[STUDENT_A, STUDENT_B], language=LanguageCode.DE)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.channel = MagicMock(spec=discord.DMChannel)  # DMChannel lacks create_thread
        interaction.response.send_message = AsyncMock()

        await btn.callback(interaction)
        interaction.response.send_message.assert_awaited_once()
        args, kwargs = interaction.response.send_message.call_args
        assert "Discord-Servers" in args[0]
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_create_thread_button_success(self):
        dummy_mod = Module(id_=MODULE_MATH, language=ModuleLanguage.DE, title="Mathematik I")
        btn = CreateThreadButton(module=dummy_mod, buddies=[STUDENT_A, STUDENT_B], language=LanguageCode.DE)

        mock_thread = MagicMock()
        mock_thread.mention = "<#thread-123>"
        mock_thread.send = AsyncMock()

        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.create_thread = AsyncMock(return_value=mock_thread)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.channel = mock_channel
        interaction.response.send_message = AsyncMock()

        await btn.callback(interaction)

        mock_channel.create_thread.assert_awaited_once()
        mock_thread.send.assert_awaited_once()
        interaction.response.send_message.assert_awaited_once()
        args, kwargs = interaction.response.send_message.call_args
        assert "erfolgreich erstellt" in args[0]
        assert kwargs.get("ephemeral") is True
