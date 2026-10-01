""" Puts two or three modules next to each other so the differences are visible.

    Picking one elective out of three meant opening three cards and remembering what
    the first one said. Everything needed is already on `Module`, so this is only a
    matter of presentation.

    A discord embed renders up to three inline fields in one row on a wide screen and
    stacks them on a phone. Three is therefore the honest limit, not a round number.
"""


import discord
from discord.ui import Button, View

from oscar.ui.owner_only import OwnerOnly
from util.bookstack import module_url
from util.database import get_database, get_user_language
from util.enums import LanguageCode, StudyCourse
from util.module import Module
from util.translations import COMPARE_TEXTS, module_language_name, t


# A discord embed renders at most three fields next to each other.
MAX_MODULES: int = 3

# Hard limits from the discord API. Going over them makes the whole message fail.
MAX_FIELD_NAME: int = 256
MAX_FIELD_VALUE: int = 1024

# Shown where a module carries nothing for a row.
UNKNOWN: str = "–"

# The rows of the comparison, in the order a student weighs them up.
ROW_KEYS: tuple[str, ...] = ("credit_points", "sws", "language", "exam", "lecturer")


def _clean(text: str) -> str:
    """ Squeezes a value from the module table onto a single line.

        The table stores several teaching forms separated by newlines. In a narrow
        column those turn into a column of their own, so they are joined instead.
    """
    squeezed: str = " ".join(text.split())
    return squeezed if squeezed else UNKNOWN


def module_rows(module: Module, language: LanguageCode) -> dict[str, str]:
    """ The values this module contributes to the comparison, keyed by `ROW_KEYS`.

        Parameters:
            module: The module to read.
            language: The language the student picked.

        Returns:
            One cleaned, single line value per row key.
    """
    return {
        "credit_points": _clean(module.credit_points),
        "sws": _clean(module.get_teaching_form_sws(language)),
        "language": _clean(module_language_name(module.language, language)),
        "exam": _clean(module.get_study_exam_type(language)),
        "lecturer": _clean(module.lecturer),
    }


def differing_rows(rows: list[dict[str, str]]) -> list[str]:
    """ The row keys on which the modules do not agree.

        That is the whole reason for putting them side by side, so it is worth saying
        out loud rather than leaving the reader to spot it.

        Parameters:
            rows: One `module_rows` result per module.

        Returns:
            The differing keys, in `ROW_KEYS` order. Empty when everything matches.
    """
    return [
        key for key in ROW_KEYS
        if len({row[key] for row in rows}) > 1
    ]


def _shorten(text: str, limit: int) -> str:
    """Cuts `text` to `limit` characters, marking that something was cut."""
    stripped: str = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 1] + "…"


class CompareView(OwnerOnly, View):
    """ Two or three modules side by side, with a handbook link under each."""

    def __init__(self, user_id: int, modules: list[Module]):
        super().__init__(timeout=300)

        self.user_id: int = user_id
        self.language: LanguageCode = get_user_language(user_id)
        self.modules: list[Module] = modules[:MAX_MODULES]

        preferences = get_database().get_preferences(user_id)
        self.study_course: StudyCourse | None = (
            preferences.get("major") if preferences else None
        )

        for module in self.modules:
            _ = self.add_item(
                Button(
                    label=_shorten(module.get_title(self.language), 40),
                    style=discord.ButtonStyle.link,
                    url=module_url(
                        module.id_,
                        module.get_title(self.language),
                        self.study_course,
                    ),
                )
            )

    def create_embed(self) -> discord.Embed:
        """ Builds the comparison itself.

            Returns:
                An embed with one inline field per module and a closing line naming
                what differs.
        """
        rows: list[dict[str, str]] = [
            module_rows(module, self.language) for module in self.modules
        ]

        embed = discord.Embed(
            title=t(self.language, "title", COMPARE_TEXTS),
            color=discord.Color.dark_blue(),
        )

        for module, row in zip(self.modules, rows):
            lines: list[str] = [
                f"**{t(self.language, key, COMPARE_TEXTS)}**\n{row[key]}"
                for key in ROW_KEYS
            ]
            _ = embed.add_field(
                name=_shorten(module.get_title(self.language), MAX_FIELD_NAME),
                value=_shorten("\n".join(lines), MAX_FIELD_VALUE),
                inline=True,
            )

        differing: list[str] = differing_rows(rows)
        if differing:
            named: str = ", ".join(
                t(self.language, key, COMPARE_TEXTS) for key in differing
            )
            embed.set_footer(
                text=f"{t(self.language, 'differs', COMPARE_TEXTS)} {named}"
            )
        else:
            embed.set_footer(text=t(self.language, "identical", COMPARE_TEXTS))

        return embed
