""" The answer of `/klausuren`: where the past exams of the OVGU actually live.

    OSCAR used to show a single button to `klausuren.farafin.de`. That host stopped
    resolving, so the button led nowhere, and it only ever covered the FIN anyway.
    A Wirtschaftsinformatik student writes exams at the FWW, everybody writes maths
    at the FMA, and each of those faculties keeps its own archive.

    The list itself is in `util.exams`, together with the note that every address
    there was opened by hand.
"""

import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from util.database import get_user_language
from util.enums import LanguageCode
from util.exams import ExamArchive, get_archives
from util.translations import EXAM_TEXTS, t


ACCENT_COLOR: int = 0x4378D5

# Discord refuses a button label longer than this.
MAX_LABEL_LENGTH: int = 80


class ExamArchiveView(LayoutView):
    """ Lists every past exam archive OSCAR knows, with a link button each."""

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id: int = user_id
        self.language: LanguageCode = get_user_language(user_id)
        self._build_view()

    def _text(self, key: str) -> str:
        """ Reads one string of the answer in the language of its reader.

            Parameters:
                key: The key in `translations.EXAM_TEXTS`.

            Returns:
                The translated text.
        """
        return t(self.language, key, EXAM_TEXTS)

    def _archive_lines(self) -> str:
        """ One paragraph per archive, saying whose it is and what is in it.

            Returns:
                The paragraphs, separated by a blank line.
        """
        paragraphs: list[str] = []
        for archive in get_archives():
            paragraphs.append(
                f"{archive.emoji} **{archive.council}** "
                f"({archive.faculty(self.language)})\n"
                f"{archive.covers(self.language)}"
            )
        return "\n\n".join(paragraphs)

    def _archive_button(self, archive: ExamArchive) -> Button[LayoutView]:
        """ Builds the link button of one archive.

            Parameters:
                archive: The archive to link.

            Returns:
                A link button, which needs no callback.
        """
        return Button(
            label=f"{archive.emoji} {archive.council}"[:MAX_LABEL_LENGTH],
            style=discord.ButtonStyle.link,
            url=archive.url(self.language),
        )

    def _build_view(self) -> None:
        """ Draws the explanation, the archive list and one button per archive."""
        _ = self.clear_items()
        buttons: list[Button[LayoutView]] = [
            self._archive_button(archive) for archive in get_archives()
        ]
        _ = self.add_item(
            Container(
                TextDisplay(f"# {self._text('exam_title')}"),
                Separator(),
                TextDisplay(self._text("exam_desc")),
                TextDisplay("\u200b"),
                TextDisplay(self._archive_lines()),
                TextDisplay("\u200b"),
                TextDisplay(self._text("exam_hint")),
                Separator(),
                ActionRow(*buttons),
                accent_color=discord.Color(ACCENT_COLOR),
            )
        )
