""" Some features are switched off, and switched off has to mean gone from every screen.

    OSCAR had grown to twenty nine commands. The weekly puzzle, the badges and the
    comparison with the cohort are a game around the semester plan, and a new student
    had to read past them to find the plan. `util.command_surface.HIDDEN` switches them
    off without deleting anything.

    A feature that is half switched off is worse than one that is on: a command that
    `/help` explains and discord does not know, or a button that opens a screen nobody
    can reach any other way. So these tests go through every place a feature shows up.
"""
# pylint: disable=redefined-outer-name, protected-access

import importlib
import os
import pkgutil
from unittest.mock import MagicMock, patch

import discord
import pytest

import oscar.cogs as cogs
from oscar.cogs.help import command_order
from oscar.oscar import Oscar
from oscar.ui.help_launcher import ALL_ENTRIES, HELP_ENTRIES
from oscar.ui.progress_view import ProgressView
from util.command_surface import ADMIN, CORE, HIDDEN
from util.enums import LanguageCode


def defined_commands() -> set[str]:
    """Every slash command a cog defines, switched off or not."""
    names: set[str] = set()
    for module in pkgutil.iter_modules(cogs.__path__):
        imported = importlib.import_module(f"oscar.cogs.{module.name}")
        for value in vars(imported).values():
            if isinstance(value, type) and hasattr(value, "__cog_app_commands__"):
                names.update(command.name for command in value.__cog_app_commands__)
    return names


def texts_of(view: discord.ui.LayoutView) -> str:
    return "\n".join(
        item.content for item in view.walk_children()
        if isinstance(item, discord.ui.TextDisplay)
    )


class TestTheSwitch:
    def test_it_names_what_was_asked_for(self):
        assert HIDDEN == {"codegolf", "challenge", "badges", "cohort", "statistik"}

    def test_every_name_is_a_real_command(self):
        """A typo in the set would switch nothing off and nobody would notice."""
        assert HIDDEN <= defined_commands()

    def test_nothing_a_student_needs_is_switched_off(self):
        assert not HIDDEN & CORE
        assert not HIDDEN & ADMIN

    def test_both_names_of_a_command_are_switched_off_together(self):
        """One name left behind is a command that still works under an alias."""
        for pair in ({"codegolf", "challenge"}, {"cohort", "statistik"}):
            assert pair <= HIDDEN or not pair & HIDDEN


class TestDiscordDoesNotGetThem:
    @pytest.fixture(name="bot")
    def bot_fixture(self):
        """Anything with a command tree will do, `hide_commands` touches nothing else."""
        return MagicMock(spec=Oscar)

    def test_each_one_is_taken_out_of_the_tree(self, bot):
        bot.tree.remove_command.return_value = MagicMock()
        assert Oscar.hide_commands(bot) == sorted(HIDDEN)
        assert {call.args[0] for call in bot.tree.remove_command.call_args_list} == HIDDEN

    def test_a_command_that_is_not_there_is_not_reported(self, bot):
        bot.tree.remove_command.return_value = None
        assert Oscar.hide_commands(bot) == []

    def test_a_real_bot_loses_exactly_these(self):
        """The same thing on a real tree, with the real cogs loaded into it."""
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=True):
            real = Oscar(command_prefix="!", intents=discord.Intents.default())
        for module in pkgutil.iter_modules(cogs.__path__):
            imported = importlib.import_module(f"oscar.cogs.{module.name}")
            for value in vars(imported).values():
                if isinstance(value, type) and hasattr(value, "__cog_app_commands__"):
                    for command in value.__cog_app_commands__:
                        if real.tree.get_command(command.name) is None:
                            real.tree.add_command(command)

        before = {command.name for command in real.tree.get_commands()}
        assert HIDDEN <= before
        _ = real.hide_commands()
        after = {command.name for command in real.tree.get_commands()}
        assert after == before - HIDDEN


class TestHelpDoesNotMentionThem:
    def test_the_command_menu_leaves_them_out(self):
        assert not HIDDEN & set(command_order())

    def test_the_open_menu_leaves_them_out(self):
        assert not HIDDEN & {entry.key for entry in HELP_ENTRIES}

    def test_the_entries_are_kept_for_later(self):
        """Switching a feature back on is one line, the menu entry is still there."""
        assert "codegolf" in {entry.key for entry in ALL_ENTRIES}

    def test_the_progress_entry_no_longer_promises_badges(self):
        entry = next(entry for entry in HELP_ENTRIES if entry.key == "progress")
        for language in (LanguageCode.DE, LanguageCode.EN):
            assert "badge" not in entry.label(language).lower()


class TestProgressShowsOnlyProgress:
    @pytest.fixture(name="view")
    def view_fixture(self):
        with patch("oscar.ui.progress_view.get_database"):
            return ProgressView(user_id=4711, default_language=LanguageCode.DE)

    def test_the_credit_points_are_still_there(self, view):
        assert "CP" in texts_of(view)

    def test_no_badges_are_listed(self, view):
        text = texts_of(view)
        for word in ("Badges", "Erfolge", "Freigeschaltet", "Meilensteine"):
            assert word not in text

    def test_there_is_no_button_to_the_cohort_screen(self, view):
        buttons = [item for item in view.walk_children() if isinstance(item, discord.ui.Button)]
        assert len(buttons) == 1, "only the language toggle is left"

    def test_the_cohort_screen_cannot_be_opened_directly(self):
        """`initial_mode` is how `/cohort` opened it. The command is gone, the door too."""
        with patch("oscar.ui.progress_view.get_database") as database:
            view = ProgressView(
                user_id=4711, default_language=LanguageCode.DE, initial_mode="cohort"
            )
        database.return_value.get_cohort_statistics.assert_not_called()
        assert "Studienfortschritt" in texts_of(view)

    def test_switching_them_back_on_brings_everything_back(self):
        with patch("oscar.ui.progress_view.get_database"), \
             patch("oscar.ui.progress_view.HIDDEN", frozenset()):
            view = ProgressView(user_id=4711, default_language=LanguageCode.DE)
        buttons = [item for item in view.walk_children() if isinstance(item, discord.ui.Button)]
        assert len(buttons) == 2
        assert "Erfolge" in texts_of(view)
