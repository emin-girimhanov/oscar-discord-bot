""" Unit tests for deadlines utility and DeadlinesView."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
import pytest
import discord

from oscar.ui.deadlines_view import DeadlinesView
from util.deadlines import (
    DeadlineItem,
    SemesterDeadlines,
    get_semester_deadlines,
)
from util.enums import LanguageCode


class TestDeadlineItem:
    """Tests covering DeadlineItem methods."""

    def test_status_label_active(self):
        item = DeadlineItem(
            id="test",
            title_de="Klausuranmeldung",
            title_en="Exam Registration",
            start_date=date(2026, 11, 15),
            end_date=date(2026, 11, 30),
            description_de="Desc",
            description_en="Desc",
            is_critical=True,
            url="https://lsf.ovgu.de",
        )
        assert item.is_active(date(2026, 11, 20))
        assert not item.is_past(date(2026, 11, 20))
        assert "Läuft" in item.status_label(LanguageCode.DE, date(2026, 11, 20))
        assert "Active" in item.status_label(LanguageCode.EN, date(2026, 11, 20))

    def test_status_label_today_last_day(self):
        item = DeadlineItem(
            id="test",
            title_de="Klausuranmeldung",
            title_en="Exam Registration",
            start_date=date(2026, 11, 15),
            end_date=date(2026, 11, 30),
            description_de="Desc",
            description_en="Desc",
            is_critical=True,
            url="https://lsf.ovgu.de",
        )
        assert "Heute letzter Tag" in item.status_label(LanguageCode.DE, date(2026, 11, 30))
        assert "Last day today" in item.status_label(LanguageCode.EN, date(2026, 11, 30))

    def test_status_label_future(self):
        item = DeadlineItem(
            id="test",
            title_de="Klausuranmeldung",
            title_en="Exam Registration",
            start_date=date(2026, 11, 15),
            end_date=date(2026, 11, 30),
            description_de="Desc",
            description_en="Desc",
            is_critical=True,
            url="https://lsf.ovgu.de",
        )
        assert not item.is_active(date(2026, 11, 5))
        assert item.days_until_start(date(2026, 11, 5)) == 10
        assert "In 10 Tagen" in item.status_label(LanguageCode.DE, date(2026, 11, 5))
        assert "In 10 days" in item.status_label(LanguageCode.EN, date(2026, 11, 5))

    def test_status_label_tomorrow(self):
        item = DeadlineItem(
            id="test",
            title_de="Klausuranmeldung",
            title_en="Exam Registration",
            start_date=date(2026, 11, 15),
            end_date=date(2026, 11, 30),
            description_de="Desc",
            description_en="Desc",
            is_critical=True,
            url="https://lsf.ovgu.de",
        )
        assert "Morgen" in item.status_label(LanguageCode.DE, date(2026, 11, 14))
        assert "Tomorrow" in item.status_label(LanguageCode.EN, date(2026, 11, 14))

    def test_status_label_past(self):
        item = DeadlineItem(
            id="test",
            title_de="Klausuranmeldung",
            title_en="Exam Registration",
            start_date=date(2026, 11, 15),
            end_date=date(2026, 11, 30),
            description_de="Desc",
            description_en="Desc",
            is_critical=True,
            url="https://lsf.ovgu.de",
        )
        assert item.is_past(date(2026, 12, 1))
        assert "Vorbei" in item.status_label(LanguageCode.DE, date(2026, 12, 1))
        assert "Ended" in item.status_label(LanguageCode.EN, date(2026, 12, 1))


class TestSemesterDeadlines:
    """Tests covering SemesterDeadlines aggregation and next_deadline lookup."""

    def test_get_semester_deadlines_structure(self):
        deadlines = get_semester_deadlines(date(2026, 10, 15))
        assert len(deadlines.items) >= 4
        item_ids = [it.id for it in deadlines.items]
        assert "exam_registration" in item_ids
        assert "reregistration" in item_ids

    def test_next_deadline_active_critical(self):
        deadlines = get_semester_deadlines(date(2026, 11, 20))
        next_dl = deadlines.next_deadline(date(2026, 11, 20))
        assert next_dl is not None
        assert next_dl.id == "exam_registration"

    def test_next_deadline_upcoming(self):
        deadlines = get_semester_deadlines(date(2026, 10, 15))
        next_dl = deadlines.next_deadline(date(2026, 10, 15))
        assert next_dl is not None
        assert next_dl.id == "exam_registration"


class TestDeadlinesView:
    """Tests covering the interactive DeadlinesView."""

    @pytest.mark.asyncio
    async def test_view_initialization_default(self):
        view = DeadlinesView(
            default_language=LanguageCode.DE,
            reference_date=date(2026, 11, 18),
        )
        assert view.language_code == LanguageCode.DE
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_view_initialization_english(self):
        view = DeadlinesView(
            default_language=LanguageCode.EN,
            reference_date=date(2026, 11, 18),
        )
        assert view.language_code == LanguageCode.EN
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_view_language_toggle(self):
        view = DeadlinesView(
            default_language=LanguageCode.DE,
            reference_date=date(2026, 11, 18),
        )
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()

        toggle = view._create_language_toggle()
        await toggle.callback(interaction)

        assert view.language_code == LanguageCode.EN
        assert interaction.response.edit_message.await_count >= 1
