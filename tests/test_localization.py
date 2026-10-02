""" One command, two names, and discord picks the one that fits the client.

    `/fristen` and `/deadlines` were two commands that did the same thing, and so were
    three other pairs. Every student saw both in the picker. Each pair is one command
    now, with a German name discord shows to a client set to German.

    That only works when three things agree: the name on the command, the translation
    discord is handed, and the name `/help` prints. These tests hold them together.
"""
# pylint: disable=redefined-outer-name, protected-access

import importlib
import pkgutil
import re

import discord
import pytest
from discord import app_commands
from discord.app_commands import locale_str

import oscar.cogs as cogs
from oscar.cogs.help import HelpView
from oscar.localization import GermanNames
from util.command_surface import HIDDEN, TWO_NAMES, shown_name
from util.enums import LanguageCode
from util.translations import COMMAND_TEXTS, HELP_ANSWERS


# what discord accepts as a command name in any language
VALID_NAME = re.compile(r"^[-_a-z0-9äöüß]{1,32}$")


def commands_of_the_bot() -> list[app_commands.Command]:
    found: list[app_commands.Command] = []
    for module in pkgutil.iter_modules(cogs.__path__):
        if module.name == "examples":
            continue  # the playground cog registers nothing
        imported = importlib.import_module(f"oscar.cogs.{module.name}")
        for value in vars(imported).values():
            if isinstance(value, type) and hasattr(value, "__cog_app_commands__"):
                found.extend(value.__cog_app_commands__)
    return found


def german_name(command: app_commands.Command) -> str | None:
    return command._locale_name.extras.get("de") if command._locale_name else None


class TestTheTranslator:
    async def test_a_german_client_gets_the_german_text(self):
        text = await GermanNames().translate(
            locale_str("deadlines", de="fristen"), discord.Locale.german, None
        )
        assert text == "fristen"

    @pytest.mark.parametrize(
        "locale", [discord.Locale.american_english, discord.Locale.british_english,
                   discord.Locale.french, discord.Locale.turkish]
    )
    async def test_everybody_else_gets_the_text_itself(self, locale):
        """`None` tells discord.py to send no translation for that language."""
        text = await GermanNames().translate(locale_str("deadlines", de="fristen"), locale, None)
        assert text is None

    async def test_a_string_without_a_german_text_is_left_alone(self):
        assert await GermanNames().translate(
            locale_str("module"), discord.Locale.german, None
        ) is None


class TestEveryPairIsOneCommand:
    def test_there_are_four(self):
        assert set(TWO_NAMES) == {"fristen", "ansprechpartner", "lms", "suggest"}

    @pytest.mark.parametrize("key", sorted(TWO_NAMES))
    def test_the_command_carries_both_names(self, key: str):
        german, english = TWO_NAMES[key]
        matches = [c for c in commands_of_the_bot() if c.name == english]
        assert len(matches) == 1, f"/{english} is defined {len(matches)} times"
        assert german_name(matches[0]) == german

    @pytest.mark.parametrize("key", sorted(TWO_NAMES))
    def test_the_second_name_is_not_a_command_of_its_own(self, key: str):
        """That is what the pair used to be, and what put both into the picker."""
        german, english = TWO_NAMES[key]
        names = [c.name for c in commands_of_the_bot()]
        if german != english:
            assert german not in names

    def test_the_old_second_english_name_is_gone(self):
        assert "recommend" not in [c.name for c in commands_of_the_bot()]

    def test_no_german_name_collides_with_another_command(self):
        """Discord refuses a sync in which two commands answer to one name."""
        commands = commands_of_the_bot()
        names = [c.name for c in commands]
        german = [german_name(c) for c in commands if german_name(c)]
        assert len(set(german)) == len(german)
        assert not set(german) & set(names)

    def test_every_name_is_one_discord_accepts(self):
        for command in commands_of_the_bot():
            assert VALID_NAME.match(command.name), command.name
            if german_name(command):
                assert VALID_NAME.match(german_name(command)), german_name(command)

    def test_a_translated_command_has_a_translated_description(self):
        """A German name above an English sentence reads like a mistake."""
        for command in commands_of_the_bot():
            if german_name(command):
                description = command._locale_description
                assert description is not None and description.extras.get("de"), command.name


class TestHelpPrintsTheNameThatFits:
    @pytest.mark.parametrize("key", sorted(TWO_NAMES))
    def test_the_two_names(self, key: str):
        german, english = TWO_NAMES[key]
        assert shown_name(key, german=True) == german
        assert shown_name(key, german=False) == english

    def test_a_command_with_one_name_keeps_it(self):
        assert shown_name("module", german=True) == "module"
        assert shown_name("module", german=False) == "module"

    @pytest.mark.parametrize("language", [LanguageCode.DE, LanguageCode.EN])
    async def test_the_menu_shows_them(self, language):
        view = HelpView(language)
        menus = [item for item in view.walk_children() if isinstance(item, discord.ui.Select)]
        labels = {option.label for menu in menus for option in menu.options}
        for key, (german, english) in TWO_NAMES.items():
            if key in HIDDEN:
                continue
            wanted = german if language == LanguageCode.DE else english
            other = english if language == LanguageCode.DE else german
            assert f"/{wanted}" in labels
            if other != wanted:
                assert f"/{other}" not in labels

    @pytest.mark.parametrize("key", sorted(TWO_NAMES))
    def test_the_answer_names_both_so_nobody_is_lost(self, key: str):
        """A student with an English discord reads the German help, and the other way."""
        german, english = TWO_NAMES[key]
        for language in (LanguageCode.DE, LanguageCode.EN):
            answer = HELP_ANSWERS[key][language]
            assert f"/{german}" in answer and f"/{english}" in answer, (key, language)

    def test_every_pair_is_explained(self):
        assert set(TWO_NAMES) <= set(COMMAND_TEXTS)
