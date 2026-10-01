""" The picker `/here` shows when a channel name fits more than one module.

    `#datenbanken` is either "Datenbanken 1" or "Datenbanken 2", and no amount of
    fuzzy matching can tell which one the channel means. Guessing would open the
    wrong module half the time, so the student picks instead.

    The list is short by design. `channel_module.find_candidates` never returns more
    than five entries, and every one of them scored high enough to be plausible.
"""

import discord
from discord.ui import ActionRow, Container, LayoutView, Select, Separator, TextDisplay

from oscar.ui.module_view import ModuleView
from oscar.ui.owner_only import OwnerOnly
from util.database import get_user_language
from util.enums import LanguageCode
from util.module import Module
from util.tables import ModuleMatch
from util.translations import HERE_TEXTS, t


ACCENT_COLOR: int = 0x4378D5

# Discord refuses a select option whose label is longer than this.
MAX_LABEL_LENGTH: int = 100

# The same limit for the second line under an option.
MAX_DESCRIPTION_LENGTH: int = 100


class ChannelModuleView(OwnerOnly, LayoutView):
    """ Lets the student say which module a channel is about."""

    def __init__(
        self,
        user_id: int,
        channel_name: str,
        candidates: list[tuple[ModuleMatch, float]],
    ):
        super().__init__()
        self.user_id: int = user_id
        self.channel_name: str = channel_name
        self.candidates: list[tuple[ModuleMatch, float]] = candidates
        self.language: LanguageCode = get_user_language(user_id)
        self._build_view()

    def _text(self, key: str) -> str:
        """ Reads one string of the picker in the language of its owner.

            Parameters:
                key: The key in `translations.HERE_TEXTS`.

            Returns:
                The translated text.
        """
        return t(self.language, key, HERE_TEXTS)

    def _option_description(self, module_id: int) -> str | None:
        """ The second line under one option, so two equal titles can be told apart.

            The handbook lists the same module once per programme, which is why
            `#algorithmen-und-datenstrukturen` offers two entries with the same name.
            The lecturer and the credit points are what actually differ.

            Parameters:
                module_id: The module to describe.

            Returns:
                A short line, or `None` when the module cannot be read. A missing
                description is a cosmetic loss, an exception would break the picker.
        """
        # pylint: disable=broad-exception-caught
        # The lookup reads the module catalogue, so it can fail for any reason the
        # Tables API invents. None of them is worth losing the picker over.
        try:
            module = Module.from_id(module_id)
        except Exception:
            return None
        parts: list[str] = [part for part in (module.lecturer, module.credit_points) if part]
        if not parts:
            return None
        return " • ".join(str(part) for part in parts)[:MAX_DESCRIPTION_LENGTH]

    def _module_select(self) -> Select[LayoutView]:
        """ Builds the dropdown of the modules the channel could be about.

            Returns:
                A select whose values are module ids, so a pick opens exactly the
                module that was shown.
        """
        options: list[discord.SelectOption] = [
            discord.SelectOption(
                label=match.label[:MAX_LABEL_LENGTH],
                value=str(match.id_),
                description=self._option_description(match.id_),
            )
            for match, _score in self.candidates
        ]
        select: Select[LayoutView] = Select(
            placeholder=self._text("here_placeholder"),
            options=options,
        )

        async def callback(interaction: discord.Interaction):
            module = Module.from_id(int(select.values[0]))
            _ = await interaction.response.edit_message(
                view=ModuleView(self.user_id, module)
            )

        select.callback = callback
        return select

    def _build_view(self) -> None:
        """ Draws the question and the dropdown below it."""
        _ = self.clear_items()
        _ = self.add_item(
            Container(
                TextDisplay(self._text("here_pick_title")),
                Separator(),
                TextDisplay(
                    self._text("here_pick_desc").format(channel=self.channel_name)
                ),
                ActionRow(self._module_select()),
                accent_color=discord.Color(ACCENT_COLOR),
            )
        )
