""" Unit tests for FIN OVGU contacts data and ContactsView."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import discord

from oscar.ui.contacts_view import ContactsView
from util.contacts import (
    CONTACT_CATEGORIES,
    ContactCategory,
    ContactPerson,
    CONTACT_CATEGORIES,
    get_category_by_key,
)
from util.enums import LanguageCode


class TestContactsData:
    """Tests covering the structured contact dataset."""

    def test_categories_not_empty(self):
        cats = CONTACT_CATEGORIES
        assert len(cats) >= 5

    def test_category_keys_unique(self):
        keys = [c.key for c in CONTACT_CATEGORIES]
        assert len(keys) == len(set(keys))

    def test_category_fields_populated(self):
        for cat in CONTACT_CATEGORIES:
            assert cat.key
            assert cat.emoji
            assert cat.title_de
            assert cat.title_en
            assert cat.description_de
            assert cat.description_en
            assert len(cat.contacts) > 0

    def test_contact_person_fields_populated(self):
        """ A room and a mail address may be empty, a link may not.

            The list used to require a mail address for everybody, and so everybody got
            one, whether it existed or not. The page a contact links to is the source,
            and an empty field sends the student there.
        """
        for cat in CONTACT_CATEGORIES:
            for person in cat.contacts:
                assert person.title_de
                assert person.title_en
                assert person.email == "" or "@" in person.email
                assert person.url.startswith("https://")
                assert person.details_de
                assert person.details_en

    def test_the_made_up_addresses_stay_out(self):
        """ None of these mailboxes exists. They were written down because they sounded
            right, and a student who wrote to one got a bounce.
        """
        made_up = {
            "pa-fin@ovgu.de", "studiendekanat@cs.ovgu.de", "farafin@ovgu.de",
            "eet@farafin.de", "studienberatung-inf@cs.ovgu.de",
            "studienberatung-inginf@cs.ovgu.de", "studienberatung-wif@cs.ovgu.de",
            "studienberatung-cv@cs.ovgu.de", "dke-advisor@ovgu.de", "de-advisor@ovgu.de",
            "praktikumsamt-fin@ovgu.de", "erasmus-fin@ovgu.de", "gleichstellung-fin@ovgu.de",
        }
        used = {person.email for cat in CONTACT_CATEGORIES for person in cat.contacts}
        assert not used & made_up

    def test_the_dead_links_stay_out(self):
        """These answered 404, or did not answer, on 2026-10-02."""
        dead = (
            "inf.ovgu.de/Studium/Fachstudienberatung",
            "inf.ovgu.de/Studium/Praktikumsamt",
            "inf.ovgu.de/Fakult%C3%A4t/Studiendekanat",
            "inf.ovgu.de/Fakult%C3%A4t/Gleichstellung",
            "studentenwerk-magdeburg.de/beratung/psychosoziale-beratung",
            "eet.farafin.de",
        )
        for cat in CONTACT_CATEGORIES:
            for person in cat.contacts:
                assert not any(part in person.url for part in dead), person.title_de

    def test_the_student_council_is_where_it_says_it_is(self):
        """Room, mail and phone as `farafin.de` states them."""
        council = get_category_by_key("farafin").contacts[0]
        assert council.office == "G29-103"
        assert council.email == "post@farafin.de"
        assert council.phone == "(+49) 391 67 51377"

    def test_the_examination_office_is_the_official_one(self):
        office = get_category_by_key("dekanat_pa").contacts[0]
        assert office.url == "https://www.fin.ovgu.de/pamt.html"
        assert office.email == "fin-pruefungsamt@ovgu.de"

    def test_get_category_by_key_found(self):
        cat = get_category_by_key("dekanat_pa")
        assert cat is not None
        assert "Prüfungsamt" in cat.title_de

    def test_get_category_by_key_farafin(self):
        cat = get_category_by_key("farafin")
        assert cat is not None
        assert "FaRaFIN" in cat.title_de

    def test_get_category_by_key_stipendien(self):
        cat = get_category_by_key("stipendien")
        assert cat is not None
        assert "Deutschlandstipendium" in cat.title_de

    def test_get_category_by_key_not_found(self):
        cat = get_category_by_key("nonexistent_key_xyz")
        assert cat is None


class TestContactsView:
    """Tests covering the interactive ContactsView."""

    @pytest.mark.asyncio
    async def test_view_initialization_default(self):
        view = ContactsView(default_language=LanguageCode.DE)
        assert view.language_code == LanguageCode.DE
        assert view.selected_category_key == "dekanat_pa"
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_view_initialization_english(self):
        view = ContactsView(default_language=LanguageCode.EN, initial_category_key="farafin")
        assert view.language_code == LanguageCode.EN
        assert view.selected_category_key == "farafin"
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_view_invalid_initial_category_falls_back(self):
        view = ContactsView(default_language=LanguageCode.DE, initial_category_key="invalid")
        assert view.selected_category_key == CONTACT_CATEGORIES[0].key

    @pytest.mark.asyncio
    async def test_view_language_toggle(self):
        view = ContactsView(default_language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()

        # Find the language button
        toggle_btn = view._create_language_toggle()
        await toggle_btn.callback(interaction)

        assert view.language_code == LanguageCode.EN
        assert interaction.response.edit_message.await_count >= 1
