""" Deadlines and academic milestone calculations for FIN OVGU students.

    Provides deadline tracking, remaining day countdowns, and exam registration
    windows for the current and upcoming semester (Issue #50).
"""

from dataclasses import dataclass
from datetime import date

from util.calendar_export import AcademicTerm, get_academic_term
from util.enums import LanguageCode


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class DeadlineItem:
    """Represents an academic or exam milestone."""
    id: str
    title_de: str
    title_en: str
    start_date: date
    end_date: date
    description_de: str
    description_en: str
    is_critical: bool
    url: str

    def is_active(self, ref_date: date) -> bool:
        """Returns True if ref_date falls between start_date and end_date."""
        return self.start_date <= ref_date <= self.end_date

    def is_past(self, ref_date: date) -> bool:
        """Returns True if end_date is before ref_date."""
        return ref_date > self.end_date

    def days_until_start(self, ref_date: date) -> int:
        """Number of days until milestone starts."""
        return (self.start_date - ref_date).days

    def days_until_end(self, ref_date: date) -> int:
        """Number of days until milestone ends."""
        return (self.end_date - ref_date).days

    def status_label(self, lang: LanguageCode, ref_date: date) -> str:
        """Human-readable status label with emoji."""
        if self.is_active(ref_date):
            left = self.days_until_end(ref_date)
            if left == 0:
                return "🚨 Heute letzter Tag!" if lang == LanguageCode.DE else "🚨 Last day today!"
            return (
                f"🟢 Läuft (noch {left} Tage)"
                if lang == LanguageCode.DE else
                f"🟢 Active ({left} days left)"
            )

        if self.is_past(ref_date):
            return "⚪ Vorbei" if lang == LanguageCode.DE else "⚪ Ended"

        days = self.days_until_start(ref_date)
        if days == 1:
            return "🟡 Morgen" if lang == LanguageCode.DE else "🟡 Tomorrow"
        return f"🟡 In {days} Tagen" if lang == LanguageCode.DE else f"🟡 In {days} days"


@dataclass(frozen=True)
class SemesterDeadlines:
    """Collection of milestones and deadlines for an academic term."""
    term: AcademicTerm
    items: tuple[DeadlineItem, ...]

    def next_deadline(self, ref_date: date) -> DeadlineItem | None:
        """Returns the next upcoming or currently active critical deadline."""
        # Check active critical deadlines first
        for item in self.items:
            if item.is_critical and item.is_active(ref_date):
                return item

        # Upcoming critical deadlines (e.g. exam registration or re-registration)
        upcoming_critical = [
            item for item in self.items
            if item.is_critical and not item.is_past(ref_date)
        ]
        if upcoming_critical:
            return min(upcoming_critical, key=lambda x: x.start_date)

        # General upcoming milestones
        upcoming = [item for item in self.items if not item.is_past(ref_date)]
        if not upcoming:
            return None
        return min(upcoming, key=lambda x: x.start_date)


def get_semester_deadlines(reference_date: date | None = None) -> SemesterDeadlines:
    """Constructs structured deadlines for the current academic term."""
    ref = reference_date or date.today()
    term = get_academic_term(reference_date=ref)

    items = (
        DeadlineItem(
            id="exam_registration",
            title_de="Prüfungsanmeldung (LSF)",
            title_en="Exam Registration (LSF)",
            start_date=term.exam_reg_start,
            end_date=term.exam_reg_end,
            description_de=(
                "Ausschlussfrist! Alle schriftlichen und mündlichen Prüfungen "
                "müssen fristgerecht im LSF angemeldet werden."
            ),
            description_en=(
                "Strict deadline! All written and oral exams must be registered "
                "in the LSF portal within this window."
            ),
            is_critical=True,
            url="https://lsf.ovgu.de",
        ),
        DeadlineItem(
            id="reregistration",
            title_de="Rückmeldung fürs Folgesemester",
            title_en="Re-registration for Next Term",
            start_date=term.reregistration_start,
            end_date=term.reregistration_end,
            description_de=(
                "Überweisung des Semesterbeitrags an das Studentensekretariat "
                "zur Fortsetzung des Studiums."
            ),
            description_en=(
                "Transfer of the semester fee to the Student Secretariat "
                "to re-enroll for the upcoming term."
            ),
            is_critical=True,
            url="https://www.ovgu.de/rueckmeldung.html",
        ),
        DeadlineItem(
            id="lecture_period",
            title_de="Vorlesungszeit",
            title_en="Lecture Period",
            start_date=term.lecture_start,
            end_date=term.lecture_end,
            description_de="Regulärer Zeitraum für Vorlesungen, Übungen und Seminare.",
            description_en="Regular period for lectures, tutorials, and seminars.",
            is_critical=False,
            url="https://www.ovgu.de/semestertermine.html",
        ),
        DeadlineItem(
            id="exam_period",
            title_de="Prüfungszeitraum",
            title_en="Examination Period",
            start_date=term.exam_period_start,
            end_date=term.exam_period_end,
            description_de="Hauptprüfungszeitraum der FIN für Klausuren und Prüfungen.",
            description_en="Main FIN exam period for written and oral examinations.",
            is_critical=False,
            url="https://www.inf.ovgu.de/Studium/Pr%C3%BCfungsamt.html",
        ),
    )

    return SemesterDeadlines(term=term, items=items)
