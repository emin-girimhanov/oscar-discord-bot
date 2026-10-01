""" Rebuilds `assets/json/bookstack_pages.json` from the faculty BookStack.

    The wiki at `https://bookstack.cs.ovgu.de` holds one public book per study
    programme. Every module page names its module number, written as
    `Modulnummer: FIN-INF-100391` or `Module-ID: FIN-INF-100391`. That number is the
    same id as `Identifizierung` in table 720, so it is the only reliable key for a
    deep link. Matching by title does not work: of 53 titles taken from our study
    plans only 5 matched a page title.

    The book listing already carries a text preview per page, so one request per book
    is enough. Pages whose preview is cut off before the module number are skipped.

    **The book slugs are not written down here.** They used to be, and they rotted
    twice in one day. On the morning of 2026-09-17 the combined catalogue had moved
    from `modulkatalog-ab-sommer-2026` to `modulkatalog-ab-winter-202627`, and by the
    afternoon all eleven programme books of summer 2026 answered 404 as well, replaced
    by a winter 2026/27 edition with a fresh random suffix each:

        bsc-computervisualistik-ab-sommer-2026-VQS    ->  404
        bsc-computervisualistik-ab-winter-202627-HD7  ->  200

    A slug carries the term and a random suffix, and both change without warning. So
    this script reads `/books`, matches each programme by the stable part of its slug,
    and picks the newest published edition.

    Run it from the repository root, inside the university network:

        python tools/generate_bookstack_map.py

    Nothing in the bot calls this. The generated file is read by `util.bookstack`.
"""

import html
import json
import re
import sys
from pathlib import Path

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


def main() -> int:
    """ Writes the map and reports the coverage per book."""
    target = Path(__file__).resolve().parents[1] / "assets" / "json" / "bookstack_pages.json"
    session = requests.Session()

    try:
        slugs = listed_slugs(session)
    except requests.RequestException as error:
        print(f"could not read the book listing: {error}", file=sys.stderr)
        return 1
    print(f"{len(slugs)} books listed\n")

    books: dict[str, dict[str, object]] = {}
    for key, prefix in BOOK_PREFIXES.items():
        slug = pick_book(slugs, prefix)
        if slug is None:
            print(f"{key:<18} no book found for '{prefix}*'", file=sys.stderr)
            continue
        try:
            modules = _modules_of(session, slug)
        except requests.RequestException as error:
            print(f"{key:<18} failed, {error}", file=sys.stderr)
            return 1
        draft = "  (draft, no published edition)" if slug.startswith(DRAFT_PREFIX) else ""
        books[key] = {"slug": slug, "pages": modules}
        print(f"{key:<18} {len(modules):>4} modules  {slug}{draft}")

    missing = sorted(set(BOOK_PREFIXES) - set(books))
    if missing:
        print(f"\nno book for {missing}", file=sys.stderr)
        return 1

    every_id: set[str] = set()
    for book in books.values():
        every_id |= set(book["pages"])  # pyright: ignore[reportArgumentType]
    print(f"\n{'total':<18} {len(every_id):>4} distinct module numbers")

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf8") as file:
        json.dump({"base": BASE, "books": books}, file, ensure_ascii=False, indent="\t")
        _ = file.write("\n")
    print(f"written to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
