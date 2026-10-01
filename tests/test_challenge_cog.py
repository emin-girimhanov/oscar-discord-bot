""" Unit tests for Code Golf challenges UI and Cog (Issue #53)."""
# pylint: disable=redefined-outer-name, protected-access, too-many-locals, duplicate-code

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import discord
from discord.ui import ActionRow, Button, Container, Select

from oscar.cogs.challenge import ChallengeCog, setup
from oscar.ui.challenge_view import ChallengeSubmitModal, ChallengeView
from util.challenges import get_challenge_by_id
from util.enums import LanguageCode


@pytest.fixture
def mock_challenge():
    """Returns challenge #1 (fizzbuzz)."""
    return get_challenge_by_id("fizzbuzz")


class TestChallengeSubmitModal:
    """Tests covering ChallengeSubmitModal dialog submission logic."""

    @pytest.mark.asyncio
    @patch("oscar.ui.challenge_view.get_database")
    async def test_on_submit_first_time(self, mock_get_db, mock_challenge):
        mock_db = MagicMock()
        mock_db.submit_challenge_solution.return_value = (True, 0, 42)
        mock_get_db.return_value = mock_db

        modal = ChallengeSubmitModal(challenge=mock_challenge, language=LanguageCode.DE)
        modal.lang_input = MagicMock(value="python")
        modal.code_input = MagicMock(value="print('FizzBuzz')")

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await modal.on_submit(interaction)

        mock_db.submit_challenge_solution.assert_called_once_with(
            user_id=12345,
            challenge_id="fizzbuzz",
            language="python",
            code_snippet="print('FizzBuzz')",
        )
        interaction.response.send_message.assert_awaited_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "42 Bytes" in msg
        assert "python" in msg

    @pytest.mark.asyncio
    @patch("oscar.ui.challenge_view.get_database")
    async def test_on_submit_improved_score(self, mock_get_db, mock_challenge):
        mock_db = MagicMock()
        mock_db.submit_challenge_solution.return_value = (True, 50, 30)
        mock_get_db.return_value = mock_db

        modal = ChallengeSubmitModal(challenge=mock_challenge, language=LanguageCode.DE)
        modal.lang_input = MagicMock(value="python")
        modal.code_input = MagicMock(value="print(1)")

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await modal.on_submit(interaction)

        msg = interaction.response.send_message.call_args[0][0]
        assert "30 Bytes" in msg
        assert "50 Bytes" in msg

    @pytest.mark.asyncio
    @patch("oscar.ui.challenge_view.get_database")
    async def test_on_submit_worse_score(self, mock_get_db, mock_challenge):
        mock_db = MagicMock()
        mock_db.submit_challenge_solution.return_value = (False, 30, 60)
        mock_get_db.return_value = mock_db

        modal = ChallengeSubmitModal(challenge=mock_challenge, language=LanguageCode.EN)
        modal.lang_input = MagicMock(value="python")
        modal.code_input = MagicMock(value="print(123456789)")

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await modal.on_submit(interaction)

        msg = interaction.response.send_message.call_args[0][0]
        assert "60 Bytes" in msg
        assert "30 Bytes" in msg


class TestChallengeView:
    """Tests covering ChallengeView rendering, switching, and callbacks."""

    def test_initialization_defaults(self):
        view = ChallengeView(default_language=LanguageCode.DE)
        assert view.language_code == LanguageCode.DE
        assert view.selected_challenge_id is not None
        assert view.show_leaderboard is False
        assert len(view.children) > 0

    def test_initialization_with_leaderboard(self):
        view = ChallengeView(
            default_language=LanguageCode.EN,
            initial_challenge_id="primes",
            initial_show_leaderboard=True,
        )
        assert view.language_code == LanguageCode.EN
        assert view.selected_challenge_id == "primes"
        assert view.show_leaderboard is True

    @pytest.mark.asyncio
    async def test_language_toggle(self):
        view = ChallengeView(default_language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()

        toggle = view._create_language_toggle()
        await toggle.callback(interaction)

        assert view.language_code == LanguageCode.EN
        assert interaction.response.edit_message.await_count >= 1

    @pytest.mark.asyncio
    async def test_challenge_select_callback(self):
        view = ChallengeView(default_language=LanguageCode.DE, initial_challenge_id="fizzbuzz")
        row = view._create_challenge_select(LanguageCode.DE)
        select = row.children[0]
        assert isinstance(select, Select)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()

        select._values = ["palindrome"]
        await select.callback(interaction)

        assert view.selected_challenge_id == "palindrome"
        assert view.show_leaderboard is False
        assert interaction.response.edit_message.await_count >= 1

    @patch("oscar.ui.challenge_view.get_database")
    def test_render_leaderboard_empty(self, mock_get_db, mock_challenge):
        mock_db = MagicMock()
        mock_db.get_challenge_leaderboard.return_value = []
        mock_get_db.return_value = mock_db

        items = ChallengeView._render_leaderboard(mock_challenge, LanguageCode.DE)
        assert len(items) == 1
        assert "Noch keine Einreichungen" in items[0].content

    @patch("oscar.ui.challenge_view.get_database")
    def test_render_leaderboard_with_entries(self, mock_get_db, mock_challenge):
        mock_db = MagicMock()
        mock_db.get_challenge_leaderboard.return_value = [
            {"user_id": 1, "name": "Alice", "language": "python", "code_length": 25, "rank": 1},
            {"user_id": 2, "name": "Bob", "language": "c", "code_length": 30, "rank": 2},
            {"user_id": 515896235081859091, "name": None, "language": "rust", "code_length": 40, "rank": 3},
            {"user_id": 4, "name": "Dave", "language": "js", "code_length": 50, "rank": 4},
        ]
        mock_get_db.return_value = mock_db

        items = ChallengeView._render_leaderboard(mock_challenge, LanguageCode.DE)
        assert len(items) == 1
        text = items[0].content
        assert "🥇" in text
        assert "Alice" in text
        assert "25 Bytes" in text
        assert "🥈" in text
        assert "🥉" in text
        assert "Student" in text
        # no name is stored, and the fallback used to print the raw discord id
        assert "515896235081859091" not in text

    @pytest.mark.asyncio
    async def test_button_callbacks(self, mock_challenge):
        view = ChallengeView(
            default_language=LanguageCode.DE,
            initial_challenge_id=mock_challenge.id,
        )

        container = view.children[0]
        assert isinstance(container, Container)
        action_row = [c for c in container.children if isinstance(c, ActionRow)][-1]
        buttons = [c for c in action_row.children if isinstance(c, Button)]

        btn_submit = buttons[0]
        btn_toggle = buttons[1]
        btn_my = buttons[2]

        # 1. Test submit button opens modal
        interaction_submit = MagicMock(spec=discord.Interaction)
        interaction_submit.response = MagicMock()
        interaction_submit.response.send_modal = AsyncMock()

        await btn_submit.callback(interaction_submit)
        interaction_submit.response.send_modal.assert_awaited_once()
        modal_arg = interaction_submit.response.send_modal.call_args[0][0]
        assert isinstance(modal_arg, ChallengeSubmitModal)

        # 2. Test toggle button toggles show_leaderboard
        interaction_toggle = MagicMock(spec=discord.Interaction)
        interaction_toggle.response = MagicMock()
        interaction_toggle.response.is_done.return_value = False
        interaction_toggle.response.edit_message = AsyncMock()

        await btn_toggle.callback(interaction_toggle)
        assert view.show_leaderboard is True
        assert interaction_toggle.response.edit_message.await_count >= 1

        # 3. Test my submission button with no submission
        interaction_my = MagicMock(spec=discord.Interaction)
        interaction_my.user.id = 999
        interaction_my.response = MagicMock()
        interaction_my.response.send_message = AsyncMock()

        with patch("oscar.ui.challenge_view.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_user_challenge_submission.return_value = None
            mock_get_db.return_value = mock_db

            await btn_my.callback(interaction_my)
            interaction_my.response.send_message.assert_awaited_once()
            msg = interaction_my.response.send_message.call_args[0][0]
            assert "noch keine Lösung eingereicht" in msg

        # 4. Test my submission button with existing submission
        interaction_my2 = MagicMock(spec=discord.Interaction)
        interaction_my2.user.id = 111
        interaction_my2.response = MagicMock()
        interaction_my2.response.send_message = AsyncMock()

        with patch("oscar.ui.challenge_view.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_user_challenge_submission.return_value = {
                "user_id": 111,
                "challenge_id": "fizzbuzz",
                "language": "python",
                "code_length": 15,
                "code_snippet": "for i in...:...",
            }
            mock_get_db.return_value = mock_db

            await btn_my.callback(interaction_my2)
            interaction_my2.response.send_message.assert_awaited_once()
            msg = interaction_my2.response.send_message.call_args[0][0]
            assert "15 Bytes" in msg
            assert "for i in...:..." in msg


class TestChallengeCog:
    """Tests for /codegolf and /challenge slash commands."""

    @pytest.mark.asyncio
    async def test_codegolf_command(self):
        bot = MagicMock()
        cog = ChallengeCog(bot)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 777
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        with patch("oscar.cogs.challenge.get_user_language", return_value=LanguageCode.DE):
            await cog.codegolf.callback(cog, interaction, nummer=None, rangliste=False)

        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once()
        _, kwargs = interaction.followup.send.call_args
        view = kwargs.get("view")
        assert isinstance(view, ChallengeView)
        assert view.show_leaderboard is False

    @pytest.mark.asyncio
    async def test_challenge_alias_with_number_and_leaderboard(self):
        bot = MagicMock()
        cog = ChallengeCog(bot)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 888
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        with patch("oscar.cogs.challenge.get_user_language", return_value=LanguageCode.EN):
            await cog.challenge.callback(cog, interaction, nummer=2, rangliste=True)

        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once()
        _, kwargs = interaction.followup.send.call_args
        view = kwargs.get("view")
        assert isinstance(view, ChallengeView)
        assert view.selected_challenge_id == "palindrome"
        assert view.show_leaderboard is True
        assert view.language_code == LanguageCode.EN

    @pytest.mark.asyncio
    async def test_cog_setup(self):
        bot = MagicMock()
        bot.add_cog = AsyncMock()
        await setup(bot)
        bot.add_cog.assert_awaited_once()
        added_cog = bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, ChallengeCog)
