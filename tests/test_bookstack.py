"""Tests for the BookStack links and for drawing a study plan as a picture."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from util import bookstack
from util.bookstack import (
    BOOKSTACK_BASE,
    book_url,
    drop_missing_books,
    has_page,
    module_url,
    search_term,
    search_url,
)
from util.enums import LanguageCode, StudyCourse
from util.plan_image import MAX_LINES, WRAP_WIDTH, _wrap, render_semesterplan
from util.semesterplans import Semesterplan, SemestereplanModule


# --- Fixtures ---

@pytest.fixture
def page_map(monkeypatch):
    """Installs a small page map and clears the cached one afterwards."""
    books = {
        "BSC_INF": {"slug": "bsc-informatik", "pages": {"100391": "datenbanken-1"}},
        "CATALOGUE": {
            "slug": "modulkatalog",
            "pages": {"100391": "datenbanken-1", "110127": "modellierung"},
        },
        "IRREGULAR": {
            "slug": "unregelmassige-module",
            "pages": {"120491": "algorithm-engineering"},
        },
    }
    monkeypatch.setattr(bookstack, "_books", books)
    return books


@pytest.fixture
def empty_map(monkeypatch):
    """Stands in for a missing or broken page map."""
    monkeypatch.setattr(bookstack, "_books", {})


def _plan(semesters=None) -> Semesterplan:
    """Builds a small plan without touching the json files."""
    if semesters is None:
        semesters = [
            [
                SemestereplanModule("Mathematik 1", 5, identification=501325),
                SemestereplanModule("WPF Informatik", 5),
            ],
            [SemestereplanModule("Datenbanken", 5, identification=100391)],
        ]
    return Semesterplan(
        spo=2024,
        study_course=StudyCourse.BSC_INF,
        winter_semester=True,
        title="Informatik - Start Wintersemester",
        semesters=semesters,
    )


# --- search_url ---

class TestSearchUrl:
    """The plain search is the fallback that always works."""

    def test_builds_an_absolute_url(self):
        assert search_url("Datenbanken") == f"{BOOKSTACK_BASE}/search?term=Datenbanken"

    def test_it_drops_the_articles(self):
        """BookStack took 122 seconds for the full title and 1.7 for the short one."""
        assert search_url("Einführung in die Informatik") == search_url("Einführung Informatik")

    def test_quotes_spaces_and_umlauts(self):
        url = search_url("Sichere Systeme für alle")
        assert " " not in url
        assert url.startswith(f"{BOOKSTACK_BASE}/search?term=")

    def test_strips_surrounding_whitespace(self):
        assert search_url("  Logik  ") == search_url("Logik")


class TestSearchTerm:
    """What is left of a module title once the filler words are gone."""

    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Einführung in die Informatik", "Einführung Informatik"),
            ("Algorithmen und Datenstrukturen", "Algorithmen Datenstrukturen"),
            ("Netzwerke für Bildungsstudiengänge", "Netzwerke Bildungsstudiengänge"),
            ("Selected Chapters of IT Security 1", "Selected Chapters IT Security 1"),
            ("Datenbanken", "Datenbanken"),
        ],
    )
    def test_it_keeps_the_words_that_name_the_module(self, title: str, expected: str):
        assert search_term(title) == expected

    def test_the_case_of_an_article_does_not_matter(self):
        assert search_term("Die Informatik") == "Informatik"

    def test_a_title_made_only_of_articles_survives(self):
        """Dropping everything would search for nothing at all."""
        assert search_term("Die und der") == "Die und der"

    def test_an_empty_title_stays_empty(self):
        assert search_term("") == ''


# --- book_url ---

class TestBookUrl:
    """One book per programme, the catalogue covers the rest."""

    def test_known_programme(self, page_map):
        assert book_url(StudyCourse.BSC_INF) == f"{BOOKSTACK_BASE}/books/bsc-informatik"

    def test_unknown_programme_falls_back_to_the_catalogue(self, page_map):
        assert book_url(StudyCourse.MSC_VC) == f"{BOOKSTACK_BASE}/books/modulkatalog"

    def test_none_means_the_catalogue(self, page_map):
        assert book_url(None) == f"{BOOKSTACK_BASE}/books/modulkatalog"

    def test_empty_map_falls_back_to_the_overview(self, empty_map):
        assert book_url(StudyCourse.BSC_INF) == f"{BOOKSTACK_BASE}/books"


# --- module_url ---

class TestModuleUrl:
    """A deep link when we know the page, a search otherwise."""

    def test_prefers_the_programme_book(self, page_map):
        url = module_url(100391, "Datenbanken", StudyCourse.BSC_INF)
        assert url == f"{BOOKSTACK_BASE}/books/bsc-informatik/page/datenbanken-1"

    def test_falls_back_to_the_catalogue(self, page_map):
        url = module_url(110127, "Modellierung", StudyCourse.BSC_INF)
        assert url == f"{BOOKSTACK_BASE}/books/modulkatalog/page/modellierung"

    def test_uses_the_catalogue_without_a_programme(self, page_map):
        url = module_url(100391, "Datenbanken")
        assert url == f"{BOOKSTACK_BASE}/books/modulkatalog/page/datenbanken-1"

    def test_falls_back_to_the_irregular_book(self, page_map):
        """Modules that are not read every term are in no catalogue."""
        url = module_url(120491, "Algorithm Engineering", StudyCourse.BSC_INF)
        assert url == f"{BOOKSTACK_BASE}/books/unregelmassige-module/page/algorithm-engineering"

    def test_unknown_module_falls_back_to_the_search(self, page_map):
        url = module_url(999999, "Gibt es nicht", StudyCourse.BSC_INF)
        assert url.startswith(f"{BOOKSTACK_BASE}/search?term=")

    def test_search_fallback_uses_the_id_when_no_title_is_given(self, page_map):
        assert module_url(999999) == search_url("999999")

    def test_empty_map_always_searches(self, empty_map):
        url = module_url(100391, "Datenbanken", StudyCourse.BSC_INF)
        assert url == search_url("Datenbanken")


# --- has_page ---

class TestHasPage:
    """Tells a real page apart from a search fallback."""

    def test_true_for_the_programme_book(self, page_map):
        assert has_page(100391, StudyCourse.BSC_INF) is True

    def test_true_through_the_catalogue(self, page_map):
        assert has_page(110127, StudyCourse.BSC_INF) is True

    def test_true_through_the_irregular_book(self, page_map):
        assert has_page(120491, StudyCourse.BSC_INF) is True

    def test_false_for_an_unknown_module(self, page_map):
        assert has_page(999999, StudyCourse.BSC_INF) is False

    def test_false_when_the_map_is_empty(self, empty_map):
        assert has_page(100391) is False


# --- the shipped map ---

class TestTheShippedMap:
    """The file the bot actually ships, not a fixture.

        The catalogue book was renamed from `modulkatalog-ab-sommer-2026` to
        `modulkatalog-ab-winter-202627` and nothing noticed. Every module that had no
        page in its own programme book linked into a 404 for weeks. These tests catch
        the shape of that failure without asking the network.
    """

    @staticmethod
    def _map() -> dict:
        path = Path(__file__).resolve().parents[1] / "assets" / "json" / "bookstack_pages.json"
        with path.open(encoding="utf8") as file:
            return json.load(file)

    # Slugs that used to be in the map and answer 404 today. Checked by hand on
    # 2026-09-17 against `https://bookstack.cs.ovgu.de/books`. The whole summer 2026
    # edition went in a single afternoon, which is why the generator discovers the
    # slugs now instead of carrying them.
    DEAD_SLUGS = frozenset({
        "modulkatalog-ab-sommer-2026",
        "bsc-informatik-ab-sommer-2026-0Mx",
        "bsc-computervisualistik-ab-sommer-2026-VQS",
        "bsc-ingenieurinformatik-ab-sommer-2026-BDb",
        "bsc-wirtschaftsinformatik-ab-sommer-2026-mTi",
        "bsc-bilinguale-informatik-ab-sommer-2026-Sj9",
        "msc-informatik-ab-sommer-2026-Kpz",
        "msc-ingenieurinformatik-ab-sommer-2026-Zeh",
        "msc-wirtschaftsinformatik-ab-sommer-2026-ECF",
        "msc-data-and-knowledge-engineering-ab-sommer-2026-pVO",
        "msc-digital-engineering-ab-sommer-2026",
        "msc-visual-computing-from-summer-2026-q5w",
    })

    # The winter 2026/27 edition maps 178 module numbers, 175 of which are modules the
    # Nextcloud catalogue still lists. The floor is under that, so a term that carries
    # a few modules fewer does not fail the build, but losing a whole book does.
    MINIMUM_MODULES = 150

    def test_the_dead_catalogue_slug_is_gone(self):
        slugs = {book["slug"] for book in self._map()["books"].values()}
        assert not slugs & self.DEAD_SLUGS, (
            "this book was renamed and answers 404. Run tools/generate_bookstack_map.py "
            "from inside the university network."
        )

    def test_the_fallback_books_are_in_it(self):
        books = self._map()["books"]
        assert bookstack.CATALOGUE_KEY in books
        assert bookstack.IRREGULAR_KEY in books

    def test_every_book_has_a_slug_and_pages(self):
        for key, book in self._map()["books"].items():
            assert book["slug"], f"{key} has no slug"
            assert book["pages"], f"{key} has no pages"

    def test_it_covers_the_modules_a_student_actually_opens(self):
        """A drop here means a whole book was lost, not that a term got smaller."""
        every = {number for book in self._map()["books"].values() for number in book["pages"]}
        assert len(every) >= self.MINIMUM_MODULES

    def test_every_programme_has_a_book(self):
        """A missing programme sends its students to the catalogue for everything."""
        books = self._map()["books"]
        for course in StudyCourse:
            assert course.name in books, f"{course.name} has no handbook book"

    def test_no_book_is_an_archive(self):
        """The archived handbooks describe a regulation nobody studies under."""
        for key, book in self._map()["books"].items():
            assert "archiv" not in book["slug"], f"{key} points at an archive"


# --- title wrapping ---

class TestWrap:
    """Titles must stay readable inside a box."""

    def test_keeps_long_words_whole(self):
        assert "\n" not in _wrap("Managementinformationssysteme")

    def test_breaks_between_words(self):
        assert _wrap("Informationstechnologie in Organisationen").split("\n") == [
            "Informationstechnologie",
            "in Organisationen",
        ]

    def test_never_exceeds_the_line_budget(self):
        long_title = "WPF Gestalten und Anwenden oder WPF Statistik und noch viel mehr Text"
        assert len(_wrap(long_title).split("\n")) <= MAX_LINES

    def test_marks_a_cut_title(self):
        long_title = " ".join(["wort"] * 40)
        assert _wrap(long_title).endswith("…")

    def test_empty_title_stays_empty(self):
        assert _wrap("   ") == ""

    def test_short_title_is_untouched(self):
        assert _wrap("Logik") == "Logik"

    def test_wrap_width_is_below_the_box_capacity(self):
        # the box holds roughly 44 characters at this font size
        assert WRAP_WIDTH < 44


# --- render_semesterplan ---

class TestRenderSemesterplan:
    """The picture is built from the same json as the text."""

    def test_returns_a_png(self):
        data = render_semesterplan(_plan()).getvalue()
        assert data[:4] == b"\x89PNG"

    def test_buffer_is_rewound(self):
        buffer = render_semesterplan(_plan())
        assert buffer.tell() == 0

    def test_english_renders_too(self):
        data = render_semesterplan(_plan(), LanguageCode.EN).getvalue()
        assert data[:4] == b"\x89PNG"

    def test_plan_without_semesters_still_renders(self):
        data = render_semesterplan(_plan(semesters=[])).getvalue()
        assert data[:4] == b"\x89PNG"

    def test_semester_with_no_modules_still_renders(self):
        data = render_semesterplan(_plan(semesters=[[]])).getvalue()
        assert data[:4] == b"\x89PNG"



class TestDroppingMissingBooks:
    """What happens when the map has gone stale between two releases.

        The faculty renames a book whenever an edition rolls over. The map then points
        at nothing and the handbook button opens a BookStack 404. `drop_missing_books`
        asks once at startup and forgets what is gone, so the module falls through to
        the search instead.

        The other half matters as much: the bot runs outside the university network,
        where BookStack does not even resolve. "I could not ask" must never be read as
        "it is gone", or a student on a train would lose every handbook link.
    """

    @staticmethod
    def _session(status_by_slug: dict[str, int]) -> MagicMock:
        """A session that answers each slug with the status it is given."""
        session = MagicMock()

        def head(url: str, **_kwargs):
            slug = url.rsplit("/", 1)[-1]
            response = MagicMock()
            response.status_code = status_by_slug.get(slug, 200)
            return response

        session.head.side_effect = head
        return session

    def test_a_current_map_keeps_every_book(self, page_map):
        session = self._session({})
        assert drop_missing_books(session) == []
        assert len(page_map) == 3

    def test_a_renamed_book_is_forgotten(self, page_map):
        session = self._session({"modulkatalog": 404})
        assert drop_missing_books(session) == ["CATALOGUE"]
        assert "CATALOGUE" not in page_map

    def test_a_gone_book_is_forgotten_too(self, page_map):
        """BookStack answers 410 for a book that was deleted rather than renamed."""
        session = self._session({"bsc-informatik": 410})
        assert drop_missing_books(session) == ["BSC_INF"]

    def test_the_module_falls_back_to_the_search(self, page_map):
        """The whole point. A dropped book must not leave a dead link behind."""
        session = self._session({"bsc-informatik": 404, "modulkatalog": 404})
        _ = drop_missing_books(session)
        assert module_url(100391, "Datenbanken", StudyCourse.BSC_INF).startswith(
            f"{BOOKSTACK_BASE}/search?term="
        )

    def test_a_network_error_keeps_everything(self, page_map):
        """Outside the university network BookStack does not resolve at all."""
        session = MagicMock()
        session.head.side_effect = requests.ConnectionError("no route to host")
        assert drop_missing_books(session) == []
        assert len(page_map) == 3

    def test_a_server_error_keeps_the_book(self, page_map):
        """A 500 is BookStack having a bad minute, not the book being gone."""
        session = self._session({"modulkatalog": 500})
        assert drop_missing_books(session) == []

    def test_a_redirect_counts_as_alive(self, page_map):
        session = self._session({"modulkatalog": 200})
        assert drop_missing_books(session) == []

    def test_an_empty_map_asks_nothing(self, empty_map):
        session = MagicMock()
        assert drop_missing_books(session) == []
        session.head.assert_not_called()

    def test_it_asks_once_per_book(self, page_map):
        session = self._session({})
        _ = drop_missing_books(session)
        assert session.head.call_count == 3


class TestTheHandbookButtonSaysWhereItGoes:
    """Only 175 of the 269 modules have a real page in the handbook.

        The other 94 open a BookStack search instead. The button used to promise the
        module either way, so a third of the students pressed "zum Modulhandbuch" and
        got a result list to read through.
    """

    @staticmethod
    def _labels(module_id: int) -> list[str]:
        # pylint: disable=import-outside-toplevel
        import discord
        from oscar.ui.module_view import ModuleView
        from util.enums import ModuleLanguage
        from util.module import Module

        module = Module(
            id_=module_id,
            language=ModuleLanguage.DE,
            title="Datenbanken",
            credit_points="5",
        )
        with patch("oscar.ui.module_view.get_user_language", return_value=LanguageCode.DE), \
             patch("oscar.ui.module_view.get_database") as database, \
             patch("oscar.ui.module_view.lsf_search_url", return_value="https://example.invalid"):
            database.return_value.get_preferences.return_value = None
            database.return_value.get_module_ratings.return_value = {"count": 0}
            database.return_value.get_module_comments.return_value = []
            view = ModuleView(4711, module)
        return [
            item.label
            for item in view.walk_children()
            if isinstance(item, discord.ui.Button) and item.label
        ]

    def test_a_known_module_offers_the_handbook(self, page_map):
        assert any("zum Modulhandbuch" in label for label in self._labels(110127))

    def test_an_unknown_module_offers_a_search(self, page_map):
        assert any("im Handbuch suchen" in label for label in self._labels(999999))

    def test_the_two_labels_are_never_both_there(self, page_map):
        labels = " ".join(self._labels(110127))
        assert not ("zum Modulhandbuch" in labels and "im Handbuch suchen" in labels)

    def test_there_is_always_exactly_one_handbook_button(self, page_map):
        for module_id in (110127, 999999):
            handbook = [
                label for label in self._labels(module_id)
                if "Modulhandbuch" in label or "Handbuch suchen" in label
            ]
            assert len(handbook) == 1, f"module {module_id} has {handbook}"


class TestRefreshingTheMap:
    """ The map in the image is a snapshot, and the slugs in it stop working.

        On 2026-10-01 eleven of thirteen books answered 404, two weeks after the file
        was written. Dropping them turned every handbook button into a search.
        `refresh_books` reads the map again, so a renamed book is found.
    """

    def test_a_renamed_book_is_found_under_its_new_slug(self, page_map):
        fresh = {"BSC_INF": {"slug": "bsc-informatik-new-Xy1", "pages": {"100391": "seite"}}}
        with patch("util.bookstack.build_map", return_value=fresh):
            assert bookstack.refresh_books(MagicMock()) == ["BSC_INF"]

        assert page_map["BSC_INF"]["slug"] == "bsc-informatik-new-Xy1"
        assert bookstack.module_url(100391, "x", StudyCourse.BSC_INF).endswith(
            "/books/bsc-informatik-new-Xy1/page/seite"
        )

    def test_an_unreachable_bookstack_keeps_the_old_map(self, page_map):
        before = {key: dict(book) for key, book in page_map.items()}
        with patch("util.bookstack.build_map", side_effect=requests.ConnectionError("down")):
            assert bookstack.refresh_books(MagicMock()) == []
        assert page_map == before

    def test_a_book_that_comes_back_empty_is_not_taken(self, page_map):
        """No pages means the markup changed, not that the handbook is empty."""
        old_slug = page_map["BSC_INF"]["slug"]
        fresh = {"BSC_INF": {"slug": "bsc-informatik-new-Xy1", "pages": {}}}
        with patch("util.bookstack.build_map", return_value=fresh):
            assert bookstack.refresh_books(MagicMock()) == []
        assert page_map["BSC_INF"]["slug"] == old_slug

    def test_nothing_is_written_to_disk(self, page_map, tmp_path):
        """The container has a read only filesystem, the fresh map lives in memory."""
        fresh = {"BSC_INF": {"slug": "bsc-informatik-new-Xy1", "pages": {"1": "a"}}}
        with patch("util.bookstack.build_map", return_value=fresh),              patch("util.bookstack.assets_dir", return_value=tmp_path):
            _ = bookstack.refresh_books(MagicMock())
        assert not list(tmp_path.iterdir())
        assert page_map["BSC_INF"]["pages"] == {"1": "a"}


class TestTheBotKeepsTheLinksFresh:
    """The loop around `refresh_books`, and what happens when a round fails."""

    @pytest.fixture(name="bot")
    def bot_fixture(self):
        # pylint: disable=import-outside-toplevel
        from oscar.oscar import Oscar
        bot = MagicMock(spec=Oscar)
        bot.keep_handbook_links_fresh = Oscar.keep_handbook_links_fresh.__get__(bot)
        return bot

    async def test_a_round_refreshes_first_and_drops_what_is_still_dead(self, bot):
        bot.is_closed.side_effect = [False, True]
        order: list[str] = []
        with patch("oscar.oscar.refresh_books", side_effect=lambda: order.append("refresh")),              patch("oscar.oscar.drop_missing_books", side_effect=lambda: order.append("drop")),              patch("asyncio.sleep") as sleep:
            await bot.keep_handbook_links_fresh()
        assert order == ["refresh", "drop"]
        sleep.assert_awaited_once()

    async def test_a_failed_round_does_not_end_the_loop(self, bot):
        bot.is_closed.side_effect = [False, False, True]
        with patch("oscar.oscar.refresh_books", side_effect=[OSError("down"), []]) as refresh,              patch("oscar.oscar.drop_missing_books", return_value=[]),              patch("asyncio.sleep"):
            await bot.keep_handbook_links_fresh()
        assert refresh.call_count == 2
