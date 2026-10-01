""" This module builds links into the BookStack module handbooks of the faculty.

    The wiki at `https://bookstack.cs.ovgu.de` is public and holds one book per study
    programme. A module page is addressed by its module number, not by its title, so
    `assets/json/bookstack_pages.json` maps the number to a page. Regenerate that file
    with `tools/generate_bookstack_map.py`.

    BookStack ignores search filters such as `{book_id:N}`, so a search cannot be
    narrowed to one book. The plain search is the fallback when no page is known.

    **The map goes stale, and faster than anybody expects.** On 2026-09-17 the
    combined catalogue had moved to a new slug by the morning and all eleven programme
    books of summer 2026 answered 404 by the afternoon, replaced by a winter 2026/27
    edition. A student clicking the handbook button landed on a BookStack error page.

    So `drop_missing_books` runs once at startup. It asks BookStack for each book and
    forgets the ones it answers 404 for. A module in a forgotten book falls through to
    the catalogue and then to the search, which always works. The bot ends up one click
    worse instead of broken, and the log says which book to regenerate.
"""

import json
from pathlib import Path
from typing import TypedDict
from urllib.parse import quote

import requests
from loguru import logger

from util.enums import StudyCourse
from util.paths import assets_dir


BOOKSTACK_BASE: str = "https://bookstack.cs.ovgu.de"

# Holds every module, used when the programme book has no page for it.
CATALOGUE_KEY: str = "CATALOGUE"

# Modules that are not read every term. They are in no programme book and in no
# catalogue, so they are the last book to look in before falling back to the search.
IRREGULAR_KEY: str = "IRREGULAR"

# How long to wait for one book during the startup check. It is a `HEAD` against a
# public page, and the check runs off the hot path, so this can be short.
VERIFY_TIMEOUT: int = 10

# Words that carry no meaning in a module title. BookStack scores every term of a
# search separately, and a four word query with two articles in it takes the server
# over two minutes to answer. `Einführung in die Informatik` measured 122 seconds,
# `Einführung Informatik` 1.7 seconds, with the same pages on top. So the articles go.
SEARCH_STOPWORDS: frozenset[str] = frozenset({
    "in", "die", "der", "das", "den", "dem", "des",
    "und", "oder", "von", "vom", "zu", "zum", "zur", "für", "fuer",
    "auf", "an", "am", "im", "mit", "bei", "als",
    "ein", "eine", "einer", "eines", "einem", "einen",
    "the", "of", "for", "a",
})


class _Book(TypedDict):
    """ One programme book as stored in the generated map."""
    slug: str
    pages: dict[str, str]


_books: dict[str, _Book] | None = None


def _load() -> dict[str, _Book]:
    """ Reads the generated map once and keeps it in memory.

        A missing or broken file is not fatal. Every lookup then falls back to the
        search, which needs no map at all.
    """
    # pylint: disable=W0603 # (global-statement)
    global _books
    if _books is not None:
        return _books

    path: Path = assets_dir() / "json" / "bookstack_pages.json"
    try:
        with path.open(encoding="utf8") as file:
            data = json.load(file)
        _books = data.get("books", {})
        logger.info(f"Loaded BookStack pages for {len(_books)} books")
    except (OSError, ValueError) as error:
        logger.warning(f"No BookStack page map ({error}), falling back to the search")
        _books = {}

    return _books


def search_term(term: str) -> str:
    """ Shortens a module title to the words worth searching for.

        Parameters:
            term: The module title, as it is written in the catalogue.

        Returns:
            The same words without the German and English articles. The title is
            returned unchanged when it is made of nothing else, so a search for
            `Die Firma` still asks for something.
    """
    words = term.split()
    kept = [word for word in words if word.casefold() not in SEARCH_STOPWORDS]
    return " ".join(kept or words)


def search_url(term: str) -> str:
    """ Builds a link to the public BookStack search.

        Parameters:
            term: What to search for, usually a module title.

        Returns:
            An absolute `https` url. Falls back to the empty search when term is blank.
    """
    return f"{BOOKSTACK_BASE}/search?term={quote(search_term(term.strip()), safe='')}"


def book_url(study_course: StudyCourse | None) -> str:
    """ Builds a link to the module handbook of one programme.

        Parameters:
            study_course: The programme, or `None` for the combined catalogue.

        Returns:
            An absolute `https` url. Falls back to the book overview when the
            programme has no book.
    """
    books = _load()
    key: str = CATALOGUE_KEY if study_course is None else study_course.name

    book = books.get(key) or books.get(CATALOGUE_KEY)
    if book is None:
        return f"{BOOKSTACK_BASE}/books"
    return f"{BOOKSTACK_BASE}/books/{book['slug']}"


def module_url(
    module_id: int,
    title: str = "",
    study_course: StudyCourse | None = None,
) -> str:
    """ Builds the most precise link we have for a module.

        The programme book is preferred, so a student lands in their own handbook.
        The combined catalogue is next. When neither knows the module number, the
        search by title is used, which always resolves to something readable.

        Parameters:
            module_id: The module number, the same id as `Identifizierung`.
            title: The module title, used for the search fallback.
            study_course: The programme of the user, if known.

        Returns:
            An absolute `https` url.
    """
    books = _load()
    number: str = str(module_id)

    keys: list[str] = []
    if study_course is not None:
        keys.append(study_course.name)
    keys.extend((CATALOGUE_KEY, IRREGULAR_KEY))

    for key in keys:
        book = books.get(key)
        if book is not None and number in book["pages"]:
            return f"{BOOKSTACK_BASE}/books/{book['slug']}/page/{book['pages'][number]}"

    return search_url(title or number)


def has_page(module_id: int, study_course: StudyCourse | None = None) -> bool:
    """ Tells whether a real page is known, rather than only a search fallback.

        Parameters:
            module_id: The module number.
            study_course: The programme of the user, if known.

        Returns:
            `True` when the programme book or the catalogue holds the module.
    """
    books = _load()
    number: str = str(module_id)

    keys: list[str] = []
    if study_course is not None:
        keys.append(study_course.name)
    keys.extend((CATALOGUE_KEY, IRREGULAR_KEY))

    return any(
        books.get(key) is not None and number in books[key]["pages"]
        for key in keys
    )


def drop_missing_books(session: requests.Session | None = None) -> list[str]:
    """ Forgets every book BookStack no longer has.

        The faculty renames a book whenever an edition rolls over, and the slug in
        `bookstack_pages.json` then points at nothing. This asks once per book and
        removes the ones that are gone, so `module_url` falls through to the search
        instead of handing a student a 404.

        A book is only dropped on a definite 404 or 410. A timeout, a DNS failure or a
        server error keeps it, because "I could not ask" is not "it is gone", and the
        bot runs outside the university network often enough.

        Parameters:
            session: The session to ask with, for tests. A new one is made otherwise.

        Returns:
            The keys of the books that were dropped, empty when the map is current.
    """
    books = _load()
    if not books:
        return []

    owned = session is None
    session = session or requests.Session()
    dropped: list[str] = []
    try:
        for key, book in list(books.items()):
            url = f"{BOOKSTACK_BASE}/books/{book['slug']}"
            try:
                status = session.head(url, timeout=VERIFY_TIMEOUT, allow_redirects=True).status_code
            except requests.RequestException as error:
                logger.warning(f"Could not check the BookStack book '{key}': {error}")
                continue
            if status in (404, 410):
                del books[key]
                dropped.append(key)
                logger.warning(
                    f"BookStack no longer has '{book['slug']}' ({key}, {status}). "
                    "Its modules fall back to the search. "
                    "Run tools/generate_bookstack_map.py to fix it."
                )
    finally:
        if owned:
            session.close()

    if dropped:
        logger.warning(
            f"{len(dropped)} of {len(dropped) + len(books)} BookStack books are gone: "
            f"{dropped}"
        )
    else:
        logger.info(f"All {len(books)} BookStack books answer")
    return dropped
