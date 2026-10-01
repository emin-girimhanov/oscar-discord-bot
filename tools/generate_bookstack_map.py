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

    The reading itself lives in `util.bookstack_map`, because the bot runs it as well.
    This script is what writes the result to the file the image ships as a fallback.

    Run it from the repository root. BookStack is public, any network will do:

        python tools/generate_bookstack_map.py

    The generated file is read by `util.bookstack` at startup. The bot then refreshes
    it in memory, so a stale file costs a few seconds of search links, not weeks.
"""

import json
import sys
from pathlib import Path

import requests

# the script is run from the repository root, without the package being installed
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# pylint: disable=wrong-import-position
from util.bookstack_map import (  # noqa: E402
    BASE,
    BOOK_PREFIXES,
    DRAFT_PREFIX,
    _modules_of,
    edition_of,
    listed_slugs,
    pick_book,
)

__all__ = [
    "BASE", "BOOK_PREFIXES", "DRAFT_PREFIX", "edition_of", "listed_slugs", "pick_book", "main",
]


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
