""" This module exports semester plans into standard RFC 5545 iCalendar (.ics) files.

    Students can import the generated .ics file into Google Calendar, Apple Calendar,
    Outlook, or any other calendar application. Since the module database does not
    contain lecture time slots or rooms, modules are represented as all-day entries
    for the semester with handbook links, module responsibility, workload, and
    official FIN examination and registration deadlines.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
import re

from util.bookstack import module_url
from util.enums import LanguageCode, StudyCourse
from util.module import Module
from util.typed_dicts import PrefsDict


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class AcademicTerm:
    """Represents an academic term and its key dates at FIN OVGU."""
    name_de: str
    name_en: str
    term_code: str
    start_date: date
    end_date: date
    lecture_start: date
    lecture_end: date
    exam_reg_start: date
    exam_reg_end: date
    exam_period_start: date
    exam_period_end: date
    reregistration_start: date
    reregistration_end: date


def get_academic_term(
    reference_date: date | None = None,
    winter_semester: bool | None = None
) -> AcademicTerm:
    """ Computes the academic term and its key dates for FIN OVGU.

        If `winter_semester` is not explicitly given, the term is inferred from
        `reference_date` (defaults to `date.today()`).
        Winter semester: October 1 to March 31.
        Summer semester: April 1 to September 30.

        Parameters:
            reference_date: Optional reference date to determine the year and term.
            winter_semester: Explicit flag (True for WiSe, False for SoSe).

        Returns:
            An AcademicTerm object with official FIN calendar dates.
    """
    ref: date = reference_date or date.today()
    year: int = ref.year

    if winter_semester is None:
        # Month 10, 11, 12: WiSe of current year / next year
        # Month 1, 2, 3: WiSe of previous year / current year
        # Month 4 to 9: SoSe of current year
        is_winter = ref.month >= 10 or ref.month <= 3
    else:
        is_winter = winter_semester

    if is_winter:
        start_year = year if ref.month >= 10 else year - 1
        end_year = start_year + 1
        return AcademicTerm(
            name_de=f"Wintersemester {start_year}/{end_year}",
            name_en=f"Winter Term {start_year}/{end_year}",
            term_code=f"wise_{start_year}_{end_year}",
            start_date=date(start_year, 10, 1),
            end_date=date(end_year, 3, 31),
            lecture_start=date(start_year, 10, 7),
            lecture_end=date(end_year, 1, 31),
            exam_reg_start=date(start_year, 11, 15),
            exam_reg_end=date(start_year, 11, 30),
            exam_period_start=date(end_year, 2, 1),
            exam_period_end=date(end_year, 2, 28),
            reregistration_start=date(end_year, 1, 15),
            reregistration_end=date(end_year, 2, 15),
        )

    return AcademicTerm(
        name_de=f"Sommersemester {year}",
        name_en=f"Summer Term {year}",
        term_code=f"sose_{year}",
        start_date=date(year, 4, 1),
        end_date=date(year, 9, 30),
        lecture_start=date(year, 4, 7),
        lecture_end=date(year, 7, 11),
        exam_reg_start=date(year, 5, 15),
        exam_reg_end=date(year, 5, 31),
        exam_period_start=date(year, 7, 14),
        exam_period_end=date(year, 8, 8),
        reregistration_start=date(year, 6, 15),
        reregistration_end=date(year, 7, 15),
    )


def escape_ics_text(text: str) -> str:
    """ Escapes special characters for RFC 5545 text fields.

        Semicolons, commas, backslashes, and newlines must be escaped.
    """
    if not text:
        return ""
    escaped = text.replace("\\", "\\\\")
    escaped = escaped.replace(";", "\\;")
    escaped = escaped.replace(",", "\\,")
    escaped = escaped.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
    return escaped


def fold_line(line: str) -> str:
    """ Folds a line of text according to RFC 5545 (max 75 octets per line).

        Long lines are split by inserting CRLF followed by a single space.
    """
    bytes_line = line.encode("utf-8")
    if len(bytes_line) <= 75:
        return line

    chunks: list[bytes] = []
    current: bytes = bytes_line

    first_chunk_size = 75
    # Ensure we don't cut in the middle of a multi-byte UTF-8 character
    while first_chunk_size > 0:
        try:
            current[:first_chunk_size].decode("utf-8")
            break
        except UnicodeDecodeError:
            first_chunk_size -= 1

    chunks.append(current[:first_chunk_size])
    remaining = current[first_chunk_size:]

    while len(remaining) > 74:
        chunk_size = 74
        while chunk_size > 0:
            try:
                remaining[:chunk_size].decode("utf-8")
                break
            except UnicodeDecodeError:
                chunk_size -= 1
        chunks.append(b" " + remaining[:chunk_size])
        remaining = remaining[chunk_size:]

    if remaining:
        chunks.append(b" " + remaining)

    return "\r\n".join(c.decode("utf-8") for c in chunks)


def format_date(d: date) -> str:
    """ Formats a date as YYYYMMDD for VALUE=DATE. """
    return d.strftime("%Y%m%d")


def strip_markdown(text: str) -> str:
    """ Removes common Markdown markup from text. """
    if not text:
        return ""
    text = re.sub(r"[*_`#]", "", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", text)
    return text.strip()


def build_module_description(
    module: Module,
    language: LanguageCode,
    major: StudyCourse | None = None
) -> str:
    """ Formats a clear, rich description for a calendar event from a Module. """
    title = module.get_title(language)
    cp = module.credit_points.strip() if module.credit_points else "?"
    url = module_url(module.id_, title=title, study_course=major)

    lines: list[str] = [
        f"{title} ({cp} CP)",
        "----------------------------------------",
    ]

    if module.abbreviation:
        lines.append(f"Kürzel: {module.abbreviation}")

    if module.lecturer:
        lines.append(f"Dozent:in: {module.lecturer}")
    elif module.responsibility:
        lines.append(f"Modulverantwortung: {module.responsibility}")

    teaching_form = getattr(module, "_teaching_form_sws", "").strip()
    if teaching_form:
        lines.append(f"Lehrform: {strip_markdown(teaching_form)}")

    exam_type = getattr(module, "_study_exam_type", "").strip()
    if exam_type:
        lines.append(f"Prüfungsleistung: {strip_markdown(exam_type)}")

    lines.append(f"BookStack Modulhandbuch: {url}")
    lines.append("----------------------------------------")
    if language == LanguageCode.DE:
        lines.append(
            "Genaue Vorlesungstermine und Hörsäle findest du im LSF (https://lsf.ovgu.de)."
        )
    else:
        lines.append(
            "Exact lecture times and rooms can be found on LSF (https://lsf.ovgu.de)."
        )

    return "\n".join(lines)


# pylint: disable=too-many-locals
def generate_semester_calendar(
    modules: list[Module],
    preferences: PrefsDict | None = None,
    language: LanguageCode = LanguageCode.DE,
    reference_date: date | None = None,
    include_deadlines: bool = True,
) -> str:
    """ Generates a standard RFC 5545 iCalendar (.ics) string for a student's semester plan.

        Parameters:
            modules: List of enrolled modules in the user's semester plan.
            preferences: User preferences dict (contains major, spo, winter, semester).
            language: Language for titles and descriptions.
            reference_date: Optional reference date to calculate term dates.
            include_deadlines: Whether to include official FIN academic deadlines.

        Returns:
            The complete .ics file content as a string with CRLF line breaks.
    """
    major: StudyCourse | None = preferences.get("major") if preferences else None
    winter_pref = preferences.get("winter_semester") if preferences else None

    # Determine term parity if student started in WiSe/SoSe and has current semester number
    winter_flag: bool | None = None
    if preferences and preferences.get("semester") and winter_pref is not None:
        sem_num = preferences["semester"]
        # If started in WiSe: sem 1 (WiSe), sem 2 (SoSe), sem 3 (WiSe)...
        # If started in SoSe: sem 1 (SoSe), sem 2 (WiSe), sem 3 (SoSe)...
        winter_flag = (sem_num % 2 == 1) if winter_pref else (sem_num % 2 == 0)

    term: AcademicTerm = get_academic_term(
        reference_date=reference_date,
        winter_semester=winter_flag,
    )
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    cal_name = (
        f"OSCAR – {term.name_de}" if language == LanguageCode.DE
        else f"OSCAR – {term.name_en}"
    )

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OSCAR//FIN OVGU//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ics_text(cal_name)}",
        "X-WR-TIMEZONE:Europe/Berlin",
    ]

    # Add enrolled modules
    for module in modules:
        mod_title = module.get_title(language)
        cp_str = f" ({module.credit_points.strip()} CP)" if module.credit_points else ""
        summary = f"[OSCAR] {mod_title}{cp_str}"
        description = build_module_description(module, language=language, major=major)
        url = module_url(module.id_, title=mod_title, study_course=major)
        uid = f"oscar-module-{module.id_}-{term.term_code}@fin.ovgu.de"

        # The module is marked as an all-day event on the lecture start date
        start_str = format_date(term.lecture_start)

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;VALUE=DATE:{start_str}",
            f"SUMMARY:{escape_ics_text(summary)}",
            f"DESCRIPTION:{escape_ics_text(description)}",
            f"URL:{escape_ics_text(url)}",
            "LOCATION:FIN OVGU Magdeburg",
            "CATEGORIES:STUDY,OSCAR,MODULE",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ])

    # Add official FIN academic deadlines & milestones
    if include_deadlines:
        deadlines: list[tuple[str, str, date, str, str]] = []

        if language == LanguageCode.DE:
            deadlines.append((
                f"oscar-term-start-{term.term_code}@fin.ovgu.de",
                f"Vorlesungsbeginn ({term.name_de})",
                term.lecture_start,
                "Erster Vorlesungstag der Fakultät für Informatik an der OVGU.",
                "ACADEMIC,MILESTONE",
            ))
            deadlines.append((
                f"oscar-exam-reg-start-{term.term_code}@fin.ovgu.de",
                "Start Prüfungsanmeldung FIN",
                term.exam_reg_start,
                "Beginn des Prüfungsanmeldezeitraums für FIN-Studiengänge im HISQIS / LSF.",
                "ACADEMIC,DEADLINE",
            ))
            deadlines.append((
                f"oscar-exam-reg-end-{term.term_code}@fin.ovgu.de",
                "⚠️ Ende Prüfungsanmeldung FIN (Fristende!)",
                term.exam_reg_end,
                "Letzter Tag zur verbindlichen Anmeldung von Prüfungsleistungen "
                "im Prüfungsamt / LSF.",
                "ACADEMIC,DEADLINE,IMPORTANT",
            ))
            deadlines.append((
                f"oscar-lecture-end-{term.term_code}@fin.ovgu.de",
                f"Vorlesungsende ({term.name_de})",
                term.lecture_end,
                "Letzter Vorlesungstag vor dem Prüfungszeitraum.",
                "ACADEMIC,MILESTONE",
            ))
            deadlines.append((
                f"oscar-exam-period-{term.term_code}@fin.ovgu.de",
                "Beginn Prüfungszeitraum FIN",
                term.exam_period_start,
                "Start des offiziellen Prüfungszeitraums der Fakultät für Informatik. "
                "Hinweis: Eine Prüfungsabmeldung ist bis 3 Tage vor der Prüfung "
                "ohne Angabe von Gründen möglich.",
                "ACADEMIC,EXAM",
            ))
            deadlines.append((
                f"oscar-reregistration-{term.term_code}@fin.ovgu.de",
                "Rückmeldefrist Folgesemester",
                term.reregistration_end,
                "Fristende für die Rückmeldung (Semesterbeitrag überweisen) "
                "für das Folgesemester.",
                "ACADEMIC,DEADLINE",
            ))
        else:
            deadlines.append((
                f"oscar-term-start-{term.term_code}@fin.ovgu.de",
                f"Start of Lectures ({term.name_en})",
                term.lecture_start,
                "First day of lectures at the Faculty of Computer Science (FIN OVGU).",
                "ACADEMIC,MILESTONE",
            ))
            deadlines.append((
                f"oscar-exam-reg-start-{term.term_code}@fin.ovgu.de",
                "Start of Exam Registration FIN",
                term.exam_reg_start,
                "Beginning of the examination registration period in HISQIS / LSF.",
                "ACADEMIC,DEADLINE",
            ))
            deadlines.append((
                f"oscar-exam-reg-end-{term.term_code}@fin.ovgu.de",
                "⚠️ Examination Registration Deadline FIN",
                term.exam_reg_end,
                "Final deadline to register for examinations in HISQIS / LSF.",
                "ACADEMIC,DEADLINE,IMPORTANT",
            ))
            deadlines.append((
                f"oscar-lecture-end-{term.term_code}@fin.ovgu.de",
                f"End of Lectures ({term.name_en})",
                term.lecture_end,
                "Last lecture day prior to the examination period.",
                "ACADEMIC,MILESTONE",
            ))
            deadlines.append((
                f"oscar-exam-period-{term.term_code}@fin.ovgu.de",
                "Start of Examination Period FIN",
                term.exam_period_start,
                "Start of the examination period at FIN OVGU. "
                "Note: Examination withdrawal is permitted up to 3 days before "
                "the exam date.",
                "ACADEMIC,EXAM",
            ))
            deadlines.append((
                f"oscar-reregistration-{term.term_code}@fin.ovgu.de",
                "Re-registration Deadline",
                term.reregistration_end,
                "Deadline to pay semester re-registration fees for the upcoming semester.",
                "ACADEMIC,DEADLINE",
            ))

        for uid, title, event_date, desc, categories in deadlines:
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;VALUE=DATE:{format_date(event_date)}",
                f"SUMMARY:{escape_ics_text(title)}",
                f"DESCRIPTION:{escape_ics_text(desc)}",
                "LOCATION:OVGU Magdeburg",
                f"CATEGORIES:{categories}",
                "STATUS:CONFIRMED",
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ])

    lines.append("END:VCALENDAR")

    # Fold long lines as required by RFC 5545 and join with CRLF
    folded_lines = [fold_line(line) for line in lines]
    return "\r\n".join(folded_lines) + "\r\n"
