""" Tests for the calendar export utility (RFC 5545 iCalendar format). """

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from oscar.ui.select_button import ExportCalendarButton
from util.calendar_export import (
    AcademicTerm,
    build_module_description,
    escape_ics_text,
    fold_line,
    format_date,
    generate_semester_calendar,
    get_academic_term,
    strip_markdown,
)
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.module import Module
from util.typed_dicts import PrefsDict


def _make_dummy_module(
    module_id: int = 101,
    title: str = "Algorithmen und Datenstrukturen",
    title_en: str = "Algorithms and Data Structures",
    cp: str = "6",
    lecturer: str = "Prof. Dr. Muster",
    teaching_form: str = "V2 / Ü2",
    exam_type: str = "Klausur (120 Min.)",
    abbrev: str = "AuD",
) -> Module:
    return Module(
        id_=module_id,
        language=ModuleLanguage.DE,
        title=title,
        title_en=title_en,
        credit_points=cp,
        lecturer=lecturer,
        teaching_form_sws=teaching_form,
        study_exam_type=exam_type,
        abbreviation=abbrev,
    )


class TestAcademicTerm:
    def test_winter_term_inferred_from_autumn(self):
        term = get_academic_term(reference_date=date(2025, 11, 1))
        assert "Wintersemester 2025/2026" in term.name_de
        assert "Winter Term 2025/2026" in term.name_en
        assert term.start_date == date(2025, 10, 1)
        assert term.end_date == date(2026, 3, 31)
        assert term.exam_reg_start == date(2025, 11, 15)
        assert term.exam_reg_end == date(2025, 11, 30)

    def test_winter_term_inferred_from_january(self):
        term = get_academic_term(reference_date=date(2026, 1, 15))
        assert "Wintersemester 2025/2026" in term.name_de
        assert term.start_date == date(2025, 10, 1)
        assert term.end_date == date(2026, 3, 31)

    def test_summer_term_inferred_from_may(self):
        term = get_academic_term(reference_date=date(2025, 5, 20))
        assert "Sommersemester 2025" in term.name_de
        assert "Summer Term 2025" in term.name_en
        assert term.start_date == date(2025, 4, 1)
        assert term.end_date == date(2025, 9, 30)
        assert term.exam_reg_start == date(2025, 5, 15)
        assert term.exam_reg_end == date(2025, 5, 31)

    def test_explicit_winter_flag(self):
        term_wi = get_academic_term(reference_date=date(2025, 6, 1), winter_semester=True)
        assert "Wintersemester" in term_wi.name_de
        term_so = get_academic_term(reference_date=date(2025, 12, 1), winter_semester=False)
        assert "Sommersemester" in term_so.name_de


class TestIcsFormatting:
    def test_escape_ics_text(self):
        raw = "Hello, World; path\\test\nNew line\r\nAnother"
        escaped = escape_ics_text(raw)
        assert "\\," in escaped
        assert "\\;" in escaped
        assert "\\\\" in escaped
        assert "\\n" in escaped
        assert "\r" not in escaped

    def test_escape_empty_text(self):
        assert escape_ics_text("") == ""

    def test_fold_line_short(self):
        short = "SUMMARY:Short line"
        assert fold_line(short) == short

    def test_fold_line_long(self):
        long_line = "DESCRIPTION:" + ("A" * 120)
        folded = fold_line(long_line)
        assert "\r\n " in folded
        # Each line section (before CRLF) must be <= 75 octets
        parts = folded.split("\r\n")
        assert len(parts[0].encode("utf-8")) <= 75
        for part in parts[1:]:
            assert len(part.encode("utf-8")) <= 75

    def test_fold_line_with_unicode(self):
        # Ü and emojis are multi-byte
        line = "SUMMARY:" + ("Prüfung 💡 " * 15)
        folded = fold_line(line)
        # Verify decoding is intact when unfolded
        unfolded = folded.replace("\r\n ", "")
        assert unfolded == line

    def test_format_date(self):
        d = date(2025, 11, 15)
        assert format_date(d) == "20251115"

    def test_strip_markdown(self):
        text = "Hier ist **wichtig**, *kursiv* und ein [Link](https://ovgu.de)."
        stripped = strip_markdown(text)
        assert "**" not in stripped
        assert "*" not in stripped
        assert "Link (https://ovgu.de)" in stripped


class TestModuleDescription:
    def test_module_description_content(self):
        mod = _make_dummy_module()
        desc = build_module_description(mod, language=LanguageCode.DE, major=StudyCourse.BSC_INF)
        assert "Algorithmen und Datenstrukturen (6 CP)" in desc
        assert "Kürzel: AuD" in desc
        assert "Dozent:in: Prof. Dr. Muster" in desc
        assert "Lehrform: V2 / Ü2" in desc
        assert "Prüfungsleistung: Klausur (120 Min.)" in desc
        assert "BookStack Modulhandbuch:" in desc
        assert "https://lsf.ovgu.de" in desc

    def test_module_description_english(self):
        mod = _make_dummy_module()
        desc = build_module_description(mod, language=LanguageCode.EN)
        assert "Algorithms and Data Structures (6 CP)" in desc
        assert "Exact lecture times" in desc


class TestGenerateSemesterCalendar:
    def test_calendar_structure(self):
        mod = _make_dummy_module()
        ics = generate_semester_calendar(
            modules=[mod],
            language=LanguageCode.DE,
            reference_date=date(2025, 10, 15),
        )

        assert ics.startswith("BEGIN:VCALENDAR\r\n")
        assert ics.endswith("END:VCALENDAR\r\n")
        assert "VERSION:2.0\r\n" in ics
        assert "PRODID:-//OSCAR//FIN OVGU//DE\r\n" in ics
        assert "X-WR-CALNAME:OSCAR – Wintersemester 2025/2026\r\n" in ics
        assert "BEGIN:VEVENT\r\n" in ics
        assert "SUMMARY:[OSCAR] Algorithmen und Datenstrukturen (6 CP)\r\n" in ics
        assert "DTSTART;VALUE=DATE:20251007\r\n" in ics
        assert "UID:oscar-module-101-wise_2025_2026@fin.ovgu.de\r\n" in ics
        assert "CATEGORIES:STUDY,OSCAR,MODULE\r\n" in ics

    def test_calendar_english_and_sose(self):
        mod = _make_dummy_module()
        ics = generate_semester_calendar(
            modules=[mod],
            language=LanguageCode.EN,
            reference_date=date(2025, 4, 15),
        )
        assert "X-WR-CALNAME:OSCAR – Summer Term 2025\r\n" in ics
        assert "SUMMARY:[OSCAR] Algorithms and Data Structures (6 CP)\r\n" in ics
        assert "Start of Lectures (Summer Term 2025)" in ics
        assert "⚠️ Examination Registration Deadline FIN" in ics

    def test_calendar_deadlines_included(self):
        ics = generate_semester_calendar(
            modules=[],
            language=LanguageCode.DE,
            reference_date=date(2025, 10, 15),
            include_deadlines=True,
        )
        assert "Start Prüfungsanmeldung FIN" in ics
        assert "⚠️ Ende Prüfungsanmeldung FIN (Fristende!)" in ics
        assert "Rückmeldefrist Folgesemester" in ics

    def test_calendar_without_deadlines(self):
        mod = _make_dummy_module()
        ics = generate_semester_calendar(
            modules=[mod],
            include_deadlines=False,
            reference_date=date(2025, 10, 15),
        )
        assert "Start Prüfungsanmeldung FIN" not in ics
        assert "[OSCAR] Algorithmen und Datenstrukturen" in ics

    def test_semester_parity_from_preferences(self):
        mod = _make_dummy_module()
        # Student started in WiSe (winter_semester=True) and is currently in semester 2 (SoSe)
        prefs: PrefsDict = {
            "user_id": 12345,
            "language": LanguageCode.DE,
            "winter_semester": True,
            "semester": 2,
        }
        ics = generate_semester_calendar(
            modules=[mod],
            preferences=prefs,
            reference_date=date(2025, 10, 15),  # Even if ref date is in Oct, sem 2 means SoSe
        )
        assert "Sommersemester" in ics


class TestExportCalendarButton:
    def test_button_labels(self):
        btn_de = ExportCalendarButton(user_id=123, language=LanguageCode.DE)
        assert btn_de.label == "📅 Kalender (.ics, ohne Zeiten)"
        btn_en = ExportCalendarButton(user_id=123, language=LanguageCode.EN)
        assert btn_en.label == "📅 Calendar (.ics, no times)"

    @pytest.mark.asyncio
    async def test_callback_empty_plan(self):
        btn = ExportCalendarButton(user_id=123, language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        with patch("oscar.ui.select_button.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_semesterplan.return_value = []
            mock_get_db.return_value = mock_db

            await btn.callback(interaction)

            interaction.response.send_message.assert_awaited_once()
            args, kwargs = interaction.response.send_message.call_args
            assert "Dein Semesterplan enthält noch keine Module" in args[0]
            assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_callback_with_modules(self):
        btn = ExportCalendarButton(user_id=123, language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        dummy = _make_dummy_module()

        with (
            patch("oscar.ui.select_button.get_database") as mock_get_db,
            patch("util.module.Module.from_id", return_value=dummy)
        ):
            mock_db = MagicMock()
            mock_db.get_semesterplan.return_value = [dummy]
            mock_db.get_preferences.return_value = {"language": LanguageCode.DE}
            mock_get_db.return_value = mock_db

            await btn.callback(interaction)

            interaction.response.send_message.assert_awaited_once()
            args, kwargs = interaction.response.send_message.call_args
            assert "Hier ist dein Semesterplan" in args[0]
            assert kwargs.get("ephemeral") is True
            file_arg = kwargs.get("file")
            assert isinstance(file_arg, discord.File)
            assert file_arg.filename == "semesterplan.ics"
