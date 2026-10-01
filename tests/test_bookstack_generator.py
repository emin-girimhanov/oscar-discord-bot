"""Picking the right book out of thirty, without writing a slug down anywhere.

The slugs used to be a table in `tools/generate_bookstack_map.py`. They rotted twice
in one day: the combined catalogue moved in the morning, and by the afternoon all
eleven programme books of summer 2026 answered 404, replaced by a winter 2026/27
edition with a fresh random suffix each.

A slug carries the term and a random suffix, and both change without warning. So the
generator reads `/books` and matches on the part that does not change. These tests use
the real listing of 2026-09-17, so they pin down the picking rules against real names.
"""

import pytest

from generate_bookstack_map import (
    BOOK_PREFIXES,
    edition_of,
    listed_slugs,
    pick_book,
)


# Every book BookStack listed on 2026-09-17, copied as it came.
LISTING: list[str] = [
    "archived-module-handbooks",
    "archivierte-modulhandbucher",
    "archivierte-modulhandbucher-6aT",
    "archivierte-modulhandbucher-n05",
    "bsc-bilinguale-informatik-ab-winter-202627-Ux9",
    "bsc-computervisualistik-ab-winter-202627-HD7",
    "bsc-ingenieurinformatik-ab-winter-202627-8KT",
    "bsc-wirtschaftsinformatik-ab-winter-202627-fDx",
    "entwurf-bsc-informatik-ab-winter-202627",
    "module-catalog-courtesy-translation-for-winter-202627",
    "modulkatalog-ab-winter-202627",
    "msc-data-and-knowledge-engineering-ab-winter-202627-b4s",
    "msc-digital-engineering-ab-sommer-2026-eJ2",
    "msc-digital-engineering-ab-winter-202627-8bg",
    "msc-informatik-ab-winter-202627-aZI",
    "msc-ingenieurinformatik-ab-winter-202627-Muk",
    "msc-ingenieurinformatik-winter-202526-ZRf",
    "msc-visual-computing-from-winter-202627-d7Q",
    "msc-wirtschaftsinformatik-ab-winter-202627-yj1",
    "templates-new",
    "unregelmassige-module",
]


class TestPickingABook:
    """One book per programme, out of a listing that holds several editions."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("BSC_CV", "bsc-computervisualistik-ab-winter-202627-HD7"),
            ("BSC_WIF", "bsc-wirtschaftsinformatik-ab-winter-202627-fDx"),
            ("MSC_DKE", "msc-data-and-knowledge-engineering-ab-winter-202627-b4s"),
            ("MSC_VC", "msc-visual-computing-from-winter-202627-d7Q"),
            ("CATALOGUE", "modulkatalog-ab-winter-202627"),
            ("IRREGULAR", "unregelmassige-module"),
        ],
    )
    def test_it_finds_the_current_edition(self, key: str, expected: str):
        assert pick_book(LISTING, BOOK_PREFIXES[key]) == expected

    def test_the_newest_edition_wins(self):
        """Digital Engineering is listed for summer 2026 and winter 2026/27."""
        assert pick_book(LISTING, BOOK_PREFIXES["MSC_DE"]).endswith("winter-202627-8bg")

    def test_an_older_winter_loses_to_a_newer_one(self):
        """Ingenieurinformatik is listed for winter 2025/26 and winter 2026/27."""
        assert pick_book(LISTING, BOOK_PREFIXES["MSC_INGINF"]).endswith("winter-202627-Muk")

    def test_a_draft_is_used_when_nothing_else_exists(self):
        """BSc Informatik had only `entwurf-...` on 2026-09-17. A draft beats nothing."""
        assert pick_book(LISTING, BOOK_PREFIXES["BSC_INF"]) == (
            "entwurf-bsc-informatik-ab-winter-202627"
        )

    def test_a_published_book_beats_a_draft(self):
        listing = LISTING + ["bsc-informatik-ab-winter-202627-XyZ"]
        assert pick_book(listing, BOOK_PREFIXES["BSC_INF"]) == (
            "bsc-informatik-ab-winter-202627-XyZ"
        )

    def test_every_programme_finds_something(self):
        for key, prefix in BOOK_PREFIXES.items():
            assert pick_book(LISTING, prefix) is not None, f"{key} found no book"

    def test_nothing_is_picked_twice(self):
        """Two programmes sharing a book would mean a prefix is too loose."""
        picked = [pick_book(LISTING, prefix) for prefix in BOOK_PREFIXES.values()]
        assert len(picked) == len(set(picked))

    def test_an_unknown_programme_finds_nothing(self):
        assert pick_book(LISTING, "bsc-maschinenbau") is None

    def test_an_empty_listing_finds_nothing(self):
        assert pick_book([], BOOK_PREFIXES["BSC_CV"]) is None


class TestWhatIsNeverPicked:
    """A wrong book is worse than no book, because the student believes it."""

    @pytest.mark.parametrize(
        "unwanted",
        ["archiv", "templates", "courtesy-translation"],
    )
    def test_it_is_not_picked_for_any_programme(self, unwanted: str):
        for prefix in BOOK_PREFIXES.values():
            picked = pick_book(LISTING, prefix)
            assert picked is None or unwanted not in picked

    def test_informatik_does_not_take_ingenieurinformatik(self):
        """The two names overlap, and picking the wrong one is silent."""
        assert pick_book(LISTING, BOOK_PREFIXES["BSC_INF"]).startswith(
            "entwurf-bsc-informatik"
        )
        assert pick_book(LISTING, BOOK_PREFIXES["MSC_INF"]).startswith("msc-informatik")

    def test_a_longer_name_is_not_an_edition(self):
        """`msc-informatikrecht` would be a different programme, not a new term."""
        listing = LISTING + ["msc-informatikrecht-ab-winter-203031"]
        assert pick_book(listing, BOOK_PREFIXES["MSC_INF"]) == "msc-informatik-ab-winter-202627-aZI"


class TestSortingTheEditions:
    """Which of two terms is the later one."""

    def test_a_winter_beats_the_summer_of_the_same_year(self):
        assert edition_of("x-ab-winter-202627") > edition_of("x-ab-sommer-2026")

    def test_a_later_year_wins(self):
        assert edition_of("x-ab-sommer-2027") > edition_of("x-ab-winter-202526")

    def test_the_english_spelling_counts_too(self):
        assert edition_of("x-from-summer-2026") == edition_of("x-ab-sommer-2026")

    def test_a_slug_without_a_term_sorts_last(self):
        assert edition_of("unregelmassige-module") == 0


class TestReadingTheListing:
    """One request per page, and a slug is only counted once."""

    @staticmethod
    def _session(pages: list[str]):
        from unittest.mock import MagicMock

        session = MagicMock()
        responses = [MagicMock(text=page) for page in pages]
        session.get.side_effect = responses + [MagicMock(text="")] * 10
        return session

    def test_it_reads_the_slugs(self):
        base = "https://bookstack.cs.ovgu.de/books"
        page = f'<a href="{base}/first-book">a</a><a href="{base}/second-book">b</a>'
        assert listed_slugs(self._session([page]))[:2] == ["first-book", "second-book"]

    def test_a_slug_on_two_pages_is_counted_once(self):
        base = "https://bookstack.cs.ovgu.de/books"
        page = f'<a href="{base}/same-book">a</a>'
        assert listed_slugs(self._session([page, page])).count("same-book") == 1

    def test_a_page_link_is_not_a_book(self):
        base = "https://bookstack.cs.ovgu.de/books"
        page = f'<a href="{base}/a-book/page/a-page">p</a>'
        assert listed_slugs(self._session([page])) == []
