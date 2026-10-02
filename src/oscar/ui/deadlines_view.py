""" Interactive view displaying semester deadlines and exam registration periods.

    **The dates are not official.** `util.calendar_export.get_academic_term` computes
    them from the calendar: lectures from 7 October, exam registration from 15 to 30
    November, and so on, the same days every year. The real periods are set by the
    examination board each semester (SPO Bachelor 2024, § 17 (2)) and published by the
    examination office. The view used to call its dates "official" and counted down to
    "last day today". A student who trusted that could miss the real period.

    So the view says what the dates are, a guide, and sends the student to the
    examination office for the real ones. The withdrawal rule below the list is real,
    it is § 17 (4) of the same regulations.
"""

from datetime import date
from typing import override
import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from oscar.ui.translated_view import TranslatedView
from util.deadlines import DeadlineItem, SemesterDeadlines, get_semester_deadlines
from util.enums import LanguageCode


class DeadlinesView(TranslatedView):
    """View displaying approximate academic dates, and where the real ones are."""

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
            f"**{'Etwa' if lang == LanguageCode.DE else 'About'}:** `{date_str}` | {status}",
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

        prefix = "### Als Nächstes:" if lang == LanguageCode.DE else "### Next:"
        return TextDisplay(f"{prefix} **{title}**\nStatus: **{status}** ({date_range})")

    @override
    def _build_content(self) -> None:
        lang: LanguageCode = self.language_code
        deadlines: SemesterDeadlines = get_semester_deadlines(self.reference_date)
        term = deadlines.term
        term_name = term.name_de if lang == LanguageCode.DE else term.name_en

        container = Container[LayoutView]()
        header = (
            f"# Termine & Prüfungsfristen ({term_name})"
            if lang == LanguageCode.DE else
            f"# Academic & Exam Deadlines ({term_name})"
        )
        _ = container.add_item(TextDisplay(header))
        approximate_note = (
            "**Das sind Richtwerte, keine amtlichen Termine.** "
            "Die genauen Zeiträume legt der Prüfungsausschuss jedes Semester neu fest. "
            "Verlass dich bei Fristen auf das Prüfungsamt und das LSF, nicht auf diese Liste."
            if lang == LanguageCode.DE else
            "**These dates are a guide, not official.** "
            "The examination board sets the real periods anew every semester. "
            "For a deadline, rely on the examination office and the LSF, not on this list."
        )
        _ = container.add_item(TextDisplay(approximate_note))
        _ = container.add_item(Separator())

        next_dl = deadlines.next_deadline(self.reference_date)
        if next_dl:
            _ = container.add_item(self._render_next_focus(next_dl, lang, self.reference_date))
            _ = container.add_item(Separator())

        for item in deadlines.items:
            _ = container.add_item(self._render_item(item, lang, self.reference_date))
            _ = container.add_item(Separator())

        withdrawal_note = (
            "**Prüfungsabmeldung:**\n"
            "Du kannst eine Anmeldung zurücknehmen, solange bis zur Prüfung noch "
            "mindestens **3 Tage** liegen. Das geht im LSF "
            "(SPO Bachelor 2024, § 17 Abs. 4). Für andere Ordnungen frag das Prüfungsamt."
            if lang == LanguageCode.DE else
            "**Exam withdrawal:**\n"
            "You can take a registration back as long as at least **3 days** remain "
            "until the exam. You do it in the LSF "
            "(SPO Bachelor 2024, § 17 (4)). For other regulations ask the examination office."
        )
        _ = container.add_item(TextDisplay(withdrawal_note))
        _ = container.add_item(Separator())

        link_buttons = [
            Button(label="LSF", style=discord.ButtonStyle.link, url="https://lsf.ovgu.de"),
            Button(
                label="Prüfungsamt FIN",
                style=discord.ButtonStyle.link,
                url="https://www.fin.ovgu.de/pamt.html",
            ),
        ]
        _ = container.add_item(ActionRow[LayoutView](*link_buttons))
        _ = container.add_item(ActionRow[LayoutView](self._create_language_toggle()))
        _ = self.add_item(container)
