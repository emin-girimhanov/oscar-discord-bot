""" Help cog for a discord bot."""


from typing import override
import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from discord.ui import ActionRow, Container, LayoutView, Section, Separator, TextDisplay
from loguru import logger

from oscar.ui.help_launcher import (
    HELP_ENTRIES,
    get_entry,
    open_contacts,
    open_platforms,
)
from oscar.ui.translated_view import TranslatedView
from util.command_surface import CORE, CORE_ORDER, HIDDEN, shown_name
from util.database import get_user_language
from util.enums import LanguageCode
from util.translations import (
    COMMAND_TEXTS,
    FAQ_ANSWERS,
    FAQ_QUESTIONS,
    HELP_ANSWERS,
    HELP_LANGUAGES,
)


# Discord rejects a select option whose description is longer than this.
MAX_OPTION_DESCRIPTION: int = 100

# It rejects a label longer than this, too.
MAX_OPTION_LABEL: int = 100


class Help(commands.Cog):
    """ Class for the help cog."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded Help cog")

    @app_commands.command(description="Hilfe zu allen Befehlen (help for every command)")
    async def help(self, interaction: discord.Interaction):
        """ Command to open the help dialog."""
        # \/ important (makes the bot say its thinking)
        _ = await interaction.response.defer(
            ephemeral=True
        )

        # the help opened in english for everybody, whatever they had picked in /start
        language: LanguageCode = get_user_language(interaction.user.id)
        await interaction.followup.send(view=HelpView(language), ephemeral=True)

    # one command each, a German client sees the German name, see `oscar.localization`
    @app_commands.command(
        name=locale_str("contacts", de="ansprechpartner"),
        description=locale_str(
            "Key contacts at the FIN and the OVGU, with a link to their page",
            de="Wichtige Ansprechpartner der FIN und OVGU, mit Link zur Seite",
        ),
    )
    async def contacts(self, interaction: discord.Interaction):
        """ Command to display key contact persons at FIN and OVGU."""
        await open_contacts(interaction)

    @app_commands.command(
        name=locale_str("elearning", de="lms"),
        description=locale_str(
            "The university portals: eLearning, LSF, module handbook, GitLab",
            de="Lernplattformen der OVGU: eLearning, LSF, Modulhandbuch, GitLab",
        ),
    )
    async def elearning(self, interaction: discord.Interaction):
        """Command to display guide on faculty learning management systems."""
        await open_platforms(interaction)


async def setup(bot: commands.Bot):
    """ Setup the Help cog."""
    await bot.add_cog(Help(bot))


def command_order() -> list[str]:
    """ Every documented command, the eight from `/start` first.

        A discord select shows twenty five options, `COMMAND_TEXTS` has fewer, so
        nothing is cut. The order is what decides which names a student reads before
        they stop scrolling.

        Returns:
            The keys of `COMMAND_TEXTS`, core ones first, the rest in the order they
            were written down.
    """
    core = [name for name in CORE_ORDER if name in COMMAND_TEXTS]
    # a command that is switched off cannot be typed, so explaining it would mislead
    rest = [name for name in COMMAND_TEXTS if name not in CORE and name not in HIDDEN]
    return core + rest


def shorten(text: str, limit: int = MAX_OPTION_DESCRIPTION) -> str:
    """ Cuts a piece of text down to what a select option accepts.

        Parameters:
            text: The full text, which may span several lines.
            limit: The number of characters discord allows in this field.

        Returns:
            The first line, at most `limit` characters long.
    """
    stripped: str = text.strip()
    if not stripped:
        return ""

    first_line: str = stripped.splitlines()[0]
    if len(first_line) <= limit:
        return first_line
    return first_line[: limit - 1] + "…"


class HelpView(TranslatedView):
    """Help view that extends TranslatedView for language switching.

        It answers two different kinds of question. "What does this command do" comes
        from `COMMAND_TEXTS`, "why does this not work" comes from `FAQ_QUESTIONS`. Both
        selects are shown at once, and picking in one clears the other, so exactly one
        answer is on screen.
    """

    def __init__(self, default_language: LanguageCode = LanguageCode.EN):
        # set before the base class builds the content, they are read while building
        self.selected_command: str | None = None
        self.selected_question: str | None = None
        self.opened: str | None = None
        super().__init__(default_language)

    def _open_select(self) -> discord.ui.Select[LayoutView]:
        """The features that are no longer slash commands, ready to be started.

        Picking a line sends a **new** private message and leaves this one standing,
        so a student can open the next thing without typing `/help` again.
        """
        select: discord.ui.Select[LayoutView] = discord.ui.Select(
            placeholder=HELP_LANGUAGES["open_placeholder"][self.language_code],
            options=[
                discord.SelectOption(
                    label=entry.label(self.language_code)[:MAX_OPTION_LABEL],
                    value=entry.key,
                    default=(self.opened == entry.key),
                )
                for entry in HELP_ENTRIES
            ],
        )

        async def callback(interaction: discord.Interaction):
            self.opened = select.values[0]
            entry = get_entry(self.opened)
            if entry is not None:
                await entry.open(interaction)

        select.callback = callback
        return select

    def _command_select(self) -> discord.ui.Select[LayoutView]:
        """Every command `COMMAND_TEXTS` describes, the eight from `/start` first.

        All of them are typeable. The order only decides which ones a student reads
        before they stop scrolling.
        """
        select: discord.ui.Select[LayoutView] = discord.ui.Select(
            placeholder=HELP_LANGUAGES["command_placeholder"][self.language_code],
            options=[
                discord.SelectOption(
                    # `/fristen` in the German help, `/deadlines` in the English one
                    label=f"/{shown_name(command, self.language_code == LanguageCode.DE)}",
                    value=command,
                    description=shorten(COMMAND_TEXTS[command][self.language_code]),
                    default=(self.selected_command == command),
                )
                for command in command_order()
            ],
        )

        async def callback(interaction: discord.Interaction):
            self.selected_command = select.values[0]
            self.selected_question = None
            await self._update(interaction)

        select.callback = callback
        return select

    def _faq_select(self) -> discord.ui.Select[LayoutView]:
        """The questions students actually ask, from `FAQ_QUESTIONS`."""
        select: discord.ui.Select[LayoutView] = discord.ui.Select(
            placeholder=HELP_LANGUAGES["faq_placeholder"][self.language_code],
            options=[
                discord.SelectOption(
                    label=shorten(texts[self.language_code], MAX_OPTION_LABEL),
                    value=key,
                    default=(self.selected_question == key),
                )
                for key, texts in FAQ_QUESTIONS.items()
            ],
        )

        async def callback(interaction: discord.Interaction):
            self.selected_question = select.values[0]
            self.selected_command = None
            await self._update(interaction)

        select.callback = callback
        return select

    def _answer(self) -> str:
        """Whatever was picked last, or the greeting when nothing was picked yet."""
        if self.selected_question in FAQ_ANSWERS:
            question: str = FAQ_QUESTIONS[self.selected_question][self.language_code]
            return (
                f"**{question}**\n\n"
                + FAQ_ANSWERS[self.selected_question][self.language_code]
            )

        if self.selected_command in HELP_ANSWERS:
            return (
                HELP_ANSWERS[self.selected_command][self.language_code]
                + "\n\n"
                + HELP_LANGUAGES["core_note"][self.language_code]
            )

        return HELP_LANGUAGES["description"][self.language_code]

    @override
    def _build_content(self):
        """Build the help view content with current language."""
        _ = self.add_item(
            item=Container(
                Section[LayoutView](
                    TextDisplay(f"# {HELP_LANGUAGES['help'][self.language_code]}"),
                    accessory=self._create_language_toggle(),
                ),
                Separator(),
                ActionRow(self._open_select()),
                ActionRow(self._command_select()),
                ActionRow(self._faq_select()),
                Separator(),
                TextDisplay(self._answer()),
                accent_color=0x4378D5,
            ),
        )
