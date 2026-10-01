""" This module reads the faculty BookStack and finds the page of every module.

    The wiki at `https://bookstack.cs.ovgu.de` holds one public book per study
    programme. Every module page names its module number, written as
    `Modulnummer: FIN-INF-100391` or `Module-ID: FIN-INF-100391`. That number is the
    same id as `Identifizierung` in table 720, so it is the only reliable key for a
    deep link.

    **The book slugs rot.** A slug carries the term and a random suffix, and both
    change without warning:

        bsc-computervisualistik-ab-winter-202627-HD7  ->  404   (2026-10-01)
        bsc-computervisualistik-ab-winter-202627-GMD  ->  200

    The map used to be built by hand with `tools/generate_bookstack_map.py` and
    shipped as a file. On 2026-10-01 eleven of its thirteen books answered 404 again,
    two weeks after it was written, and the handbook button of every module fell back
    to the search. So the logic lives here now, where the bot can run it by itself,
    see `util.bookstack.refresh_books`. The tool still exists and calls this module.

    Reading the whole map takes one request per book plus the listing, about five
    seconds. BookStack is public, none of this needs the university network.
"""

import html
import re

import requests


BASE: str = "https://bookstack.cs.ovgu.de"
TIMEOUT: int = 30

# How many pages of the book listing to read. It has held three, four is slack.
LISTING_PAGES: int = 4

# The stable part of the slug per book, keyed by the `StudyCourse` member name plus
# the two fallback books. A slug matches when it starts with this after the `entwurf-`
# prefix is stripped. The prefixes are written so that no two of them overlap:
# `bsc-informatik` never matches `bsc-ingenieurinformatik`, which starts differently.
BOOK_PREFIXES: dict[str, str] = {
    "BSC_INF": "bsc-informatik",
    "BSC_CV": "bsc-computervisualistik",
    "BSC_INGINF": "bsc-ingenieurinformatik",
    "BSC_WIF": "bsc-wirtschaftsinformatik",
    "BSC_INF_BILINGUAL": "bsc-bilinguale-informatik",
    "MSC_INF": "msc-informatik",
    "MSC_INGINF": "msc-ingenieurinformatik",
    "MSC_WIF": "msc-wirtschaftsinformatik",
    "MSC_DKE": "msc-data-and-knowledge-engineering",
    "MSC_DE": "msc-digital-engineering",
    "MSC_VC": "msc-visual-computing",
    # The combined catalogue, the fallback for a module its programme book omits.
    "CATALOGUE": "modulkatalog",
    # Modules that are not read every term. They are in no programme book.
    "IRREGULAR": "unregelmassige-module",
}

# Books that are not the handbook of a current programme.
IGNORED_PREFIXES: tuple[str, ...] = (
    "archivierte-modulhandbucher",
    "archived-module-handbooks",
    "templates",
    "module-catalog-courtesy-translation",
)

# A draft is linked only when the programme has nothing else.
DRAFT_PREFIX: str = "entwurf-"

MODULE_NUMBER = re.compile(r"(?:Modulnummer|Module-ID|Modulnr\.?)\s*:?\s*FIN-[A-Za-z]+-(\d+)")
BOOK_LINK = re.compile(r'href="' + re.escape(f"{BASE}/books/") + r'([a-zA-Z0-9-]+)"')
TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")

# `winter-202627`, `sommer-2026`, `from-winter-202627`. The digits sort the editions.
TERM = re.compile(r"(?:winter|sommer|summer)-(\d{4,6})")


def listed_slugs(session: requests.Session) -> list[str]:
    """ Reads every book slug the listing shows.

        Parameters:
            session: The session to fetch with.

        Returns:
            The slugs, without duplicates, in the order they were seen.
    """
    seen: set[str] = set()
    slugs: list[str] = []
    for page in range(1, LISTING_PAGES + 1):
        response = session.get(f"{BASE}/books?page={page}", timeout=TIMEOUT)
        response.raise_for_status()
        for slug in BOOK_LINK.findall(response.text):
            if slug not in seen:
                seen.add(slug)
                slugs.append(slug)
    return slugs


def edition_of(slug: str) -> int:
    """ Turns the term in a slug into a number that sorts the editions.

        Parameters:
            slug: The book slug.

        Returns:
            A bigger number for a newer edition, `0` when the slug names no term.
            `winter-202627` beats `sommer-2026`, because the winter term that starts
            in 2026 comes after the summer term of the same year.
    """
    match = TERM.search(slug)
    if match is None:
        return 0
    digits = match.group(1)
    year = int(digits[:4])
    return year * 10 + (1 if len(digits) > 4 else 0)


def pick_book(slugs: list[str], prefix: str) -> str | None:
    """ Picks the book a programme should be linked to.

        Parameters:
            slugs: Every slug the listing showed.
            prefix: The stable part of the slug, from `BOOK_PREFIXES`.

        Returns:
            The newest published edition, or the newest draft when there is no
            published one, or `None` when the programme has no book at all.
    """
    candidates: list[tuple[bool, int, str]] = []
    for slug in slugs:
        if slug.startswith(IGNORED_PREFIXES):
            continue
        bare = slug[len(DRAFT_PREFIX):] if slug.startswith(DRAFT_PREFIX) else slug
        if not bare.startswith(prefix):
            continue
        # a hyphen or the end has to follow, so `msc-informatik` does not take
        # `msc-informatikrecht` for an edition of itself
        rest = bare[len(prefix):]
        if rest and not rest.startswith("-"):
            continue
        candidates.append((slug.startswith(DRAFT_PREFIX), edition_of(slug), slug))

    if not candidates:
        return None
    # published before draft, then the newest edition, then the name for a stable pick
    candidates.sort(key=lambda entry: (entry[0], -entry[1], entry[2]))
    return candidates[0][2]


def _page_links(page_html: str, book_slug: str) -> list[tuple[str, str]]:
    """ Returns `(page_slug, preview_text)` for every page link in a book listing."""
    pattern = re.compile(
        r'href="' + re.escape(f"{BASE}/books/{book_slug}/page/") + r'([^"#?]+)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    found: list[tuple[str, str]] = []
    for match in pattern.finditer(page_html):
        text = html.unescape(SPACE.sub(" ", TAG.sub(" ", match.group(2))).strip())
        found.append((match.group(1), text))
    return found


def _modules_of(session: requests.Session, book_slug: str) -> dict[str, str]:
    """ Maps module number to page slug for one book."""
    response = session.get(f"{BASE}/books/{book_slug}", timeout=TIMEOUT)
    response.raise_for_status()

    modules: dict[str, str] = {}
    for page_slug, preview in _page_links(response.text, book_slug):
        number = MODULE_NUMBER.search(preview)
        if number is not None:
            modules.setdefault(number.group(1), page_slug)
    return modules


def build_map(session: requests.Session) -> dict[str, dict[str, object]]:
    """ Reads every book that is listed and maps its module numbers to pages.

        Parameters:
            session: The session to fetch with.

        Returns:
            One entry per key of `BOOK_PREFIXES` that has a book, shaped like the
            `books` object of `bookstack_pages.json`. A programme without a book is
            left out, the caller decides whether that is an error.

        Raises:
            requests.RequestException: When the listing or a book cannot be read. A
                half read map would silently drop programmes, so nothing is returned.
    """
    slugs = listed_slugs(session)

    books: dict[str, dict[str, object]] = {}
    for key, prefix in BOOK_PREFIXES.items():
        slug = pick_book(slugs, prefix)
        if slug is None:
            continue
        books[key] = {"slug": slug, "pages": _modules_of(session, slug)}
    return books
