"""The past exam archives have to be real addresses, and `klausuren.farafin.de` is not.

OSCAR advertised that host from `/klausuren` and from every module card. It does not
resolve, so the button led students into a connection error. The addresses now live in
`util.exams`, where each one was opened by hand before it was added.

These tests cannot open a page, the suite runs without network. They keep the shape
right and they keep the dead host from coming back.
"""

import re
from pathlib import Path
from unittest.mock import patch

import discord
import pytest

from oscar.ui.exam_archive_view import ExamArchiveView
from util.enums import LanguageCode
from util.exams import EXAM_ARCHIVES, get_archives, primary_archive


REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "src"

# The host that stopped resolving.
DEAD_HOST = "klausuren.farafin.de"

# Nothing may link to it again. The bare host is still allowed to appear in a
# comment, because that is where the story of the broken button is written down.
DEAD_LINK = f"//{DEAD_HOST}"


def _source_files() -> list[Path]:
    """Every python file OSCAR ships."""
    return sorted(SOURCE.rglob("*.py"))


class TestArchiveShape:
    """Each entry has to carry everything a button and a line of text need."""

    @pytest.mark.parametrize("archive", EXAM_ARCHIVES, ids=lambda a: a.key)
    def test_both_languages_are_filled(self, archive):
        for language in (LanguageCode.DE, LanguageCode.EN):
            assert archive.url(language).startswith("https://")
            assert archive.faculty(language)
            assert archive.covers(language)

    @pytest.mark.parametrize("archive", EXAM_ARCHIVES, ids=lambda a: a.key)
    def test_the_council_is_named(self, archive):
        """A student has to see whose archive they are about to open."""
        assert archive.council
        assert archive.emoji

    def test_keys_are_unique(self):
        keys = [archive.key for archive in EXAM_ARCHIVES]
        assert len(keys) == len(set(keys))

    def test_urls_are_unique_per_language(self):
        for language in (LanguageCode.DE, LanguageCode.EN):
            urls = [archive.url(language) for archive in EXAM_ARCHIVES]
            assert len(urls) == len(set(urls))

    def test_no_url_carries_a_space(self):
        """A space in a url is the usual sign of a hand edited address."""
        for archive in EXAM_ARCHIVES:
            for language in (LanguageCode.DE, LanguageCode.EN):
                assert " " not in archive.url(language)


class TestFacultiesCovered:
    """OSCAR serves programmes that write exams at three faculties."""

    def test_the_fin_archive_comes_first(self):
        """Every student OSCAR serves studies at the FIN, so it is the default."""
        assert primary_archive().key == "farafin"
        assert EXAM_ARCHIVES[0].key == "farafin"

    @pytest.mark.parametrize("key", ["farafin", "farawiwi", "faramath"])
    def test_the_faculties_students_actually_need(self, key: str):
        """Wirtschaftsinformatik writes at the FWW, everybody writes maths at the FMA."""
        assert any(archive.key == key for archive in get_archives())

    def test_get_archives_cannot_be_reordered_by_a_caller(self):
        first = get_archives()
        assert first == EXAM_ARCHIVES


class TestDeadHostStaysGone:
    """The regression this module exists for."""

    def test_no_source_file_links_to_the_dead_host(self):
        offenders = [
            path.relative_to(REPO).as_posix()
            for path in _source_files()
            if DEAD_LINK in path.read_text(encoding="utf-8")
        ]
        assert not offenders, f"{DEAD_HOST} does not resolve, linked in {offenders}"

    def test_no_archive_points_at_the_dead_host(self):
        for archive in EXAM_ARCHIVES:
            for language in (LanguageCode.DE, LanguageCode.EN):
                assert DEAD_HOST not in archive.url(language)

    def test_every_archive_url_has_a_host_with_a_dot(self):
        """A bare hostname is how the dead link looked after the domain moved."""
        host = re.compile(r"^https://([^/]+)/")
        for archive in EXAM_ARCHIVES:
            for language in (LanguageCode.DE, LanguageCode.EN):
                match = host.match(archive.url(language))
                assert match is not None, archive.url(language)
                assert "." in match.group(1)


class TestExamArchiveView:
    """What `/klausuren` puts on the screen."""

    @pytest.fixture(name="view")
    def view_fixture(self):
        with patch("oscar.ui.exam_archive_view.get_user_language") as language:
            language.return_value = LanguageCode.DE
            yield ExamArchiveView(4711)

    def test_one_button_per_archive(self, view):
        buttons = [
            item for item in view.walk_children() if isinstance(item, discord.ui.Button)
        ]
        assert len(buttons) == len(EXAM_ARCHIVES)

    def test_every_button_links_to_a_known_archive(self, view):
        known = {archive.url(LanguageCode.DE) for archive in EXAM_ARCHIVES}
        for item in view.walk_children():
            if isinstance(item, discord.ui.Button):
                assert item.url in known

    def test_every_council_is_named_in_the_text(self, view):
        texts = " ".join(
            item.content
            for item in view.walk_children()
            if isinstance(item, discord.ui.TextDisplay)
        )
        for archive in EXAM_ARCHIVES:
            assert archive.council in texts

    def test_the_text_says_oscar_hosts_nothing(self, view):
        """Issue #43 settled it: link, never host. The screen has to say so."""
        texts = " ".join(
            item.content
            for item in view.walk_children()
            if isinstance(item, discord.ui.TextDisplay)
        )
        assert "Urheberrecht" in texts
