"""`/help` starts a feature without anybody having to know its command name.

Every feature also has its own slash command, so a dead entry here loses nothing
permanently. It still wastes the click of somebody who did not know the command, which
is exactly the person the menu is for. So each entry is actually called, with a mocked
interaction, and has to answer.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from oscar.cogs.help import HelpView
from oscar.ui.help_launcher import (
    HELP_ENTRIES,
    UNKNOWN_SEMESTER,
    get_entry,
    semester_of,
)
from util.enums import LanguageCode


def make_interaction():
    """An interaction that records what was sent, without touching discord."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = 4711
    interaction.user.roles = []
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


def answered(interaction) -> bool:
    """Whether the handler put anything on the student's screen."""
    return (
        interaction.followup.send.await_count > 0
        or interaction.response.send_message.await_count > 0
    )


class TestTheMenuItself:
    """Shape of the list, before anything is opened."""

    def test_keys_are_unique(self):
        keys = [entry.key for entry in HELP_ENTRIES]
        assert len(keys) == len(set(keys))

    @pytest.mark.parametrize("entry", HELP_ENTRIES, ids=lambda e: e.key)
    def test_both_languages_are_filled(self, entry):
        assert entry.label(LanguageCode.DE)
        assert entry.label(LanguageCode.EN)
        assert entry.emoji in entry.label(LanguageCode.DE)

    def test_the_list_fits_a_discord_select(self):
        assert len(HELP_ENTRIES) <= 25

    def test_an_unknown_key_is_none(self):
        assert get_entry("nothing_like_this") is None


class TestEveryEntryOpens:
    """The point of the file: no line of the menu may do nothing."""

    @pytest.mark.parametrize("entry", HELP_ENTRIES, ids=lambda e: e.key)
    async def test_it_answers(self, entry):
        interaction = make_interaction()
        with patch("util.database.get_user_language", return_value=LanguageCode.DE):
            try:
                await entry.open(interaction)
            except Exception as error:  # pylint: disable=broad-exception-caught
                pytest.fail(f"the {entry.key!r} entry raised {error!r}")
        assert answered(interaction), f"the {entry.key!r} entry sent nothing"


class TestSemesterOf:
    """The feedback form wants to know what term somebody is in."""

    def test_a_semester_role_is_read(self):
        role = MagicMock()
        role.name = "Semester 3"
        interaction = make_interaction()
        interaction.user.roles = [role]
        assert semester_of(interaction) == 3

    def test_other_roles_are_ignored(self):
        role = MagicMock()
        role.name = "Moderator"
        interaction = make_interaction()
        interaction.user.roles = [role]
        assert semester_of(interaction) == UNKNOWN_SEMESTER

    def test_a_direct_message_has_no_roles(self):
        """`interaction.user` is a User there, and a User has no roles at all."""
        interaction = make_interaction()
        del interaction.user.roles
        assert semester_of(interaction) == UNKNOWN_SEMESTER


class TestHelpViewUsesTheMenu:
    """The view has to actually offer the entries."""

    def test_the_open_menu_lists_every_entry(self):
        view = HelpView(LanguageCode.DE)
        labels = [
            option.label
            for item in view.walk_children()
            if isinstance(item, discord.ui.Select)
            for option in item.options
        ]
        for entry in HELP_ENTRIES:
            assert entry.label(LanguageCode.DE) in labels

    def test_there_are_three_menus(self):
        """Open, explain a command, answer a question."""
        view = HelpView(LanguageCode.DE)
        selects = [
            item for item in view.walk_children() if isinstance(item, discord.ui.Select)
        ]
        assert len(selects) == 3

    def test_the_command_menu_starts_with_the_core_ones(self):
        """Every command is listed. The eight from `/start` come first."""
        # pylint: disable=import-outside-toplevel
        from util.command_surface import CORE_ORDER

        view = HelpView(LanguageCode.DE)
        selects = [
            item for item in view.walk_children() if isinstance(item, discord.ui.Select)
        ]
        listed = [option.value for option in selects[1].options]
        assert listed[: len(CORE_ORDER)] == list(CORE_ORDER)
        assert len(listed) > len(CORE_ORDER), "the other commands are listed too"
