""" What `/help` and the slash menu say has to be true, and readable.

    A review on 2026-10-02 found seven things they said that were not:

    * `/help` opened in English for everybody, whatever language `/start` had saved.
    * The FAQ called `/standard_plan` public. It answers privately.
    * A note said the slash menu lists only a few commands. It lists all of them.
    * "What does OSCAR store" and `/my_data` left out ratings, study groups and code golf.
    * The code golf help promised that a human looks at the submissions. Nobody can.
    * The FAQ on removing a module knew nothing of the list a long plan is shown as.
    * The slash menu itself said `geradiger semesterplan` and `fpr your first interaction`.

    Each test below pins one of them, so the text and the bot cannot drift apart again.
"""
# pylint: disable=redefined-outer-name, protected-access

import importlib
import inspect
import pkgutil
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord import app_commands
from discord.ext import commands

import oscar.cogs
from oscar.cogs.help import Help
from oscar.ui import help_launcher
from util.enums import LanguageCode
from util.translations import FAQ_ANSWERS, HELP_ANSWERS, HELP_LANGUAGES


LANGUAGES = [LanguageCode.DE, LanguageCode.EN]

# Discord refuses a longer description, and the picker cuts it off long before.
MAX_DESCRIPTION = 100


def slash_commands() -> list[app_commands.Command]:
    """Every slash command a cog of the bot defines, without starting the bot."""
    found: list[app_commands.Command] = []
    for _, name, _ in pkgutil.walk_packages(oscar.cogs.__path__, oscar.cogs.__name__ + "."):
        if name.endswith(".examples"):
            continue  # the playground cog registers nothing
        module = importlib.import_module(name)
        for _, cog in inspect.getmembers(module, inspect.isclass):
            if issubclass(cog, commands.Cog) and cog.__module__ == name:
                found.extend(
                    member for _, member in inspect.getmembers(cog)
                    if isinstance(member, app_commands.Command)
                )
    return found


class TestHelpSpeaksTheLanguageOfTheStudent:
    @pytest.mark.parametrize("language", LANGUAGES)
    async def test_it_opens_in_the_saved_language(self, language):
        cog = Help(MagicMock(spec=commands.Bot))
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 4711
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        with patch("oscar.cogs.help.get_user_language", return_value=language) as saved:
            await cog.help.callback(cog, interaction)

        saved.assert_called_once_with(4711)
        view = interaction.followup.send.call_args.kwargs["view"]
        assert view.language_code == language


class TestTheSlashMenuIsReadable:
    """The description is the first thing a student reads about a command."""

    def test_the_commands_are_found(self):
        assert len(slash_commands()) >= 25, "the test looks at nothing"

    def test_no_description_is_too_long_for_discord(self):
        too_long = {c.name: len(c.description) for c in slash_commands()
                    if len(c.description) > MAX_DESCRIPTION}
        assert not too_long

    def test_a_description_is_a_sentence_not_a_note(self):
        """`geradiger semesterplan` and `suchmaske für module` started in lower case."""
        sloppy = [c.name for c in slash_commands() if not c.description[:1].isupper()]
        assert not sloppy

    @pytest.mark.parametrize("typo", ["geradiger", " fpr ", "for a modul", "bescheid"])
    def test_the_old_typos_are_gone(self, typo: str):
        hits = [c.name for c in slash_commands() if typo in c.description]
        assert not hits


class TestWhatTheHelpClaims:
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_the_standard_plan_is_not_called_public(self, language):
        """`open_standard_plan` answers ephemerally, and the FAQ said the opposite."""
        source = inspect.getsource(help_launcher.open_standard_plan)
        assert "ephemeral=True" in source and "ephemeral=False" not in source
        answer = FAQ_ANSWERS["who_sees_plan"][language].lower()
        assert "öffentlich" not in answer and "is public" not in answer

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_the_slash_menu_is_not_said_to_hide_commands(self, language):
        """Every command is registered, `test_command_surface` pins that."""
        note = HELP_LANGUAGES["core_note"][language].lower()
        assert "nur die befehle" not in note and "only lists" not in note

    @pytest.mark.parametrize("language", LANGUAGES)
    @pytest.mark.parametrize("text", ["stored_data", "my_data"])
    def test_everything_that_is_stored_is_named(self, language, text: str):
        """`delete_user_data` empties six tables, the text named three of them."""
        answer = (
            FAQ_ANSWERS[text][language] if text in FAQ_ANSWERS else HELP_ANSWERS[text][language]
        ).lower()
        words = (
            ["bewertung", "lerngruppe", "code-golf"] if language == LanguageCode.DE
            else ["rating", "study group", "code golf"]
        )
        missing = [word for word in words if word not in answer]
        assert not missing

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_code_golf_does_not_promise_a_reviewer(self, language):
        """Nothing in the bot shows a submission to anybody but its author."""
        answer = HELP_ANSWERS["codegolf"][language].lower()
        assert "mensch" not in answer and "human" not in answer

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_removing_a_module_knows_the_long_plan(self, language):
        answer = FAQ_ANSWERS["remove_module"][language]
        assert "**X**" in answer
        assert ("Modul entfernen" if language == LanguageCode.DE else "Remove a module") in answer

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_students_are_not_sent_to_operator_commands(self, language):
        """`!ping` and `!resync` answer to operators only."""
        for answers in (FAQ_ANSWERS, HELP_ANSWERS):
            for key, texts in answers.items():
                assert "!resync" not in texts[language], key
                assert "!ping" not in texts[language], key
