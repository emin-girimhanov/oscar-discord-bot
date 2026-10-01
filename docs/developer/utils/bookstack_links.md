# Module handbook links

Every module card carries a **📖 Modulhandbuch** button. It opens the page of that
module in the faculty BookStack at `bookstack.cs.ovgu.de`.

A module page is addressed by its **module number**, not by its title. So
`assets/json/bookstack_pages.json` maps the number to a page slug, and
`src/util/bookstack.py` reads that map.

---

## The books

| Key | Book | What it holds |
| :--- | :--- | :--- |
| `BSC_INF` … `MSC_VC` | one per study programme | the modules of that programme, summer 2026 edition |
| `CATALOGUE` | `modulkatalog-ab-winter-202627` | every module, the fallback |
| `IRREGULAR` | `unregelmassige-module` | modules that are not read every term |

`module_url()` tries the programme book first, so a student lands in their own
handbook. Then the catalogue, then the irregular book. When no book knows the number,
it falls back to the BookStack search by title.

`has_page()` says which of the two it will be, and the module card uses it to label
the button. About two thirds of the catalogue has a real page, so a third of the
students would otherwise press *"zum Modulhandbuch"* and get a result list:

| | Button |
| :--- | :--- |
| A page is known | **zum Modulhandbuch** |
| Only the search | **im Handbuch suchen** |

A programme whose only book is a draft (`entwurf-…`) is linked to that draft, because
a draft handbook beats no handbook. Otherwise drafts are skipped.

---

## Rebuilding the map

The bot rebuilds the map by itself, see below. To refresh the file the image ships,
run this from the repository root. BookStack is public, any network will do:

```bash
python tools/generate_bookstack_map.py
```

It reads `/books`, matches each programme on the stable part of its slug and picks the
newest published edition. **No slug is written down anywhere**, which is the whole
point: see below. It prints one line per book and writes the json.

The winter 2026/27 map covers **178 module numbers**, and **175 of the 269 modules**
in the Nextcloud catalogue get a real page.

---

## Why it goes stale, and how fast

The faculty renames a book every time an edition rolls over, and the rename is silent.
On **one day**, 2026-09-17:

| Time | What happened |
| :--- | :--- |
| morning | the catalogue had moved to `modulkatalog-ab-winter-202627`, every fallback link was a 404 |
| afternoon | all **eleven** programme books of summer 2026 answered 404 too |

A slug carries the term and a random suffix. `bsc-computervisualistik-ab-sommer-2026-VQS`
became `bsc-computervisualistik-ab-winter-202627-HD7`. Nothing in the slug survives a
rollover, so nothing about it can be written down.

It happened again. On **2026-10-01**, two weeks after the map was rebuilt, eleven of
thirteen books answered 404: every programme book had a new random suffix. Every
handbook button opened a search.

Four things guard against a repeat:

* **The bot rebuilds the map.** `refresh_books()` reads `/books` and every book again,
  at startup and every six hours, and uses the result in memory. It takes about five
  seconds and seventeen requests on a background thread. A renamed book is found
  under its new slug without anybody running a tool. The reading logic lives in
  `src/util/bookstack_map.py`, the tool in `tools/` only writes the file.

* **The generator discovers the books.** `BOOK_PREFIXES` holds only the part of a slug
  that never changes, such as `bsc-computervisualistik`. `pick_book()` takes the newest
  published edition. `tests/test_bookstack_generator.py` pins the rules to the real
  listing of 30 books, including the traps: `bsc-informatik` must not take
  `bsc-ingenieurinformatik`, and an archived handbook must never be picked.
* **The bot checks after every refresh.** `drop_missing_books()` asks BookStack for each book
  once and forgets the ones that answer 404, so a module in a gone book falls through
  to the search instead of handing a student a dead link. It only drops on 404 and
  410; a timeout or a DNS failure keeps everything, because the bot runs outside the
  university network and "I could not ask" is not "it is gone".
* **A test refuses the slugs that are already dead**, by name, so they cannot come back
  in a bad merge.

The file in the image is only the fallback for a start without BookStack. Rebuilding
it at the start of a semester keeps that fallback useful.

---

## The search fallback

For the 69 modules with no page, the button opens a BookStack search instead.

The search term is **not** the full module title. `search_term()` drops the articles
first, because BookStack scores every word separately and a title full of filler words
can take the server minutes to answer:

| Search term | Answer time |
| :--- | ---: |
| `Einführung in die Informatik` | 122 s |
| `Einführung Informatik` | 1.7 s |

Measured three times each, same results on top. Across all 69 fallbacks the median is
now **0.8 seconds**.

---

## Umlauts

They are not a problem here and it is worth writing down why.

BookStack builds its page slugs without the umlaut mark: "Einführung in die Informatik"
becomes `einfuhrung-in-die-informatik`, not `einfuehrung-…`. The map stores the slug
BookStack reports, so nothing has to guess. The search accepts the percent encoded
umlaut (`%C3%BC`) and treats `ü` and `u` as the same letter.

Inside OSCAR the folding is a different matter. See `src/util/matching.py`: a discord
channel is called `#schluesselkompetenzen` while the handbook writes
"Schlüsselkompetenzen", so both sides of every fuzzy search go through `match_key()`.

---

## Short channel names

`/here` reads the channel name and opens the module it finds. `fuzz.WRatio` scores a
short word sitting inside a long title at exactly 90, and that was often the only
candidate, so `#dev` opened "Clean Code Development" without asking. So did `#code`,
`#test` and `#lernen`. All four are ordinary chat channels.

`covers_the_title()` in `src/util/channel_module.py` now requires the channel name to
be at least half as long as the title before a single hit is opened. Below that the
student sees the picker and can tell what OSCAR guessed. The rule costs nothing: all
157 channels named after a module still open straight away.
