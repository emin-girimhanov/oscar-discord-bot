""" Interactive view displaying semester deadlines and exam registration periods.

    Presents verified FIN OVGU deadlines, countdowns to critical dates (e.g. exam
    registration, re-registration), withdrawal rules, and quick links.
"""

from datetime import date
from typing import override
import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from oscar.ui.translated_view import TranslatedView
from util.deadlines import DeadlineItem, SemesterDeadlines, get_semester_deadlines
from util.enums import LanguageCode


class DeadlinesView(TranslatedView):
    """View displaying verified academic dates and examination deadlines."""

    def __init__(
        self,
        default_language: LanguageCode = LanguageCode.DE,
        reference_date: date | None = None,
    ):
        self.reference_date: date = reference_date or date.today()
        super().__init__(default_language=default_language)

    @classmethod
    def _render_item(
        cls, item: DeadlineItem, lang: LanguageCode, ref: date
    ) -> TextDisplay:
        """Renders one deadline card with status and date window."""
        title = item.title_de if lang == LanguageCode.DE else item.title_en
        desc = item.description_de if lang == LanguageCode.DE else item.description_en
        status = item.status_label(lang, ref)
        date_str = f"{item.start_date.strftime('%d.%m.%Y')} – {item.end_date.strftime('%d.%m.%Y')}"

        lines = [
            f"### {title}",
            f"📅 **Zeitraum / Dates:** `{date_str}` | {status}",
            f"> {desc}",
        ]
        return TextDisplay("\n".join(lines))

    @classmethod
    def _render_next_focus(
        cls, next_dl: DeadlineItem, lang: LanguageCode, ref: date
    ) -> TextDisplay:
        """Renders callout for the currently active or next upcoming deadline."""
        title = next_dl.title_de if lang == LanguageCode.DE else next_dl.title_en
        status = next_dl.status_label(lang, ref)
        start_fmt = next_dl.start_date.strftime('%d.%m.')
        end_fmt = next_dl.end_date.strftime('%d.%m.%Y')
        date_range = f"{start_fmt} – {end_fmt}"

        prefix = "### 🔔 Aktueller Fokus:" if lang == LanguageCode.DE else "### 🔔 Next Focus:"
        return TextDisplay(f"{prefix} **{title}**\nStatus: **{status}** ({date_range})")

    @override
    def _build_content(self) -> None:
        lang: LanguageCode = self.language_code
        deadlines: SemesterDeadlines = get_semester_deadlines(self.reference_date)
        term = deadlines.term
        term_name = term.name_de if lang == LanguageCode.DE else term.name_en

        container = Container[LayoutView]()
        header = (
            f"# ⏰ Termine & Prüfungsfristen ({term_name})"
            if lang == LanguageCode.DE else
            f"# ⏰ Academic & Exam Deadlines ({term_name})"
        )
        _ = container.add_item(TextDisplay(header))
        _ = container.add_item(Separator())

        next_dl = deadlines.next_deadline(self.reference_date)
        if next_dl:
            _ = container.add_item(self._render_next_focus(next_dl, lang, self.reference_date))
            _ = container.add_item(Separator())

        for item in deadlines.items:
            _ = container.add_item(self._render_item(item, lang, self.reference_date))
            _ = container.add_item(Separator())

        withdrawal_note = (
            "ℹ️ **Wichtig zur Prüfungsabmeldung:**\n"
            "Bis zu **3 Tage** vor einer Klausur kannst du dich im LSF "
            "ohne Angabe von Gründen wieder abmelden."
            if lang == LanguageCode.DE else
            "ℹ️ **Exam Deregistration Policy:**\n"
            "You can withdraw from any exam in LSF up to **3 days** prior "
            "to the exam date without giving reasons."
        )
        _ = container.add_item(TextDisplay(withdrawal_note))
        _ = container.add_item(Separator())

        link_buttons = [
            Button(label="🔗 LSF Portal", style=discord.ButtonStyle.link, url="https://lsf.ovgu.de"),
            Button(
                label="🔗 Prüfungsamt FIN",
                style=discord.ButtonStyle.link,
                url="https://www.inf.ovgu.de/Studium/Pr%C3%BCfungsamt.html",
            ),
        ]
        _ = container.add_item(ActionRow[LayoutView](*link_buttons))
        _ = container.add_item(ActionRow[LayoutView](self._create_language_toggle()))
        _ = self.add_item(container)
