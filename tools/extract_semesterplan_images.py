""" Cuts the official Regelstudienplan tables out of the SPO pdf as pictures.

    `/standard_plan` used to show a table OSCAR had drawn itself from json. Two
    programmes already shipped the real thing instead, a picture of the table as the
    Studien- und Prüfungsordnung prints it, and it reads far better than anything
    rendered: the exam rules, the weightings and the "mind. 10 CP benotet" bars are all
    in it, and none of that fits in a list of module names.

    So this does the same for every programme. It renders the page the table sits on,
    trims the white margin, and writes a png next to the two that were already there.

    A picture cannot be ticked off, so `SPlanView` still renders the json once a
    student has saved modules. The json has to stay right either way.

    Run it from the repository root:

        pip install pymupdf
        python tools/extract_semesterplan_images.py

    It downloads the pdfs itself. The page numbers below were read off the documents
    on 2026-09-17; check them after the faculty publishes a new edition.
"""

import sys
from pathlib import Path

# pymupdf is only needed to rebuild the pictures, not to run the bot, so it is not
# in the project dependencies. Install it when you need it: `pip install pymupdf`.
import pymupdf  # pylint: disable=import-error
import requests


BACHELOR_PDF = (
    "https://www.fin.ovgu.de/inf_media/Studiendokumente/Studien_+und+Pr%C3%BCfungsordnung/"
    "Bachelorstudieng%C3%A4nge/SPO_Bachelor_2024_04_02_Lesefassung.pdf"
)

# What to call the file, and which page of the pdf the table is on. The names follow
# the two that already shipped: `<image id>_SPO_<year>_<season>.png`, where the image
# id is the one `STUDYCOURSE_TO_IMAGE_ID` in `oscar/ui/splan_view.py` maps to.
PAGES: dict[str, int] = {
    "2_SPO_2024_WiSe": 29,   # Computervisualistik, Start Wintersemester
    "2_SPO_2024_SoSe": 30,   # Computervisualistik, Start Sommersemester
    "1_SPO_2024_WiSe": 32,   # Informatik, Start Wintersemester
    "1_SPO_2024_SoSe": 33,   # Informatik, Start Sommersemester
    "3_SPO_2024_WiSe": 34,   # Ingenieurinformatik, Start Wintersemester
    "3_SPO_2024_SoSe": 35,   # Ingenieurinformatik, Start Sommersemester
    "4_SPO_2024_WiSe": 36,   # Wirtschaftsinformatik, Start Wintersemester
    "4_SPO_2024_SoSe": 37,   # Wirtschaftsinformatik, Start Sommersemester
}

# Discord scales the picture down, so it has to be rendered well above screen size or
# the small print in the cells turns to mush.
ZOOM: float = 3.0

# How much white to leave around the table once it is trimmed.
MARGIN: int = 8


def download(url: str, target: Path) -> Path:
    """Fetches the pdf once and keeps it, so a rerun costs nothing."""
    if target.is_file():
        print(f"  using the copy in {target}")
        return target
    print(f"  downloading {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = target.write_bytes(response.content)
    return target


def render(pdf: Path, page_number: int, target: Path) -> tuple[int, int]:
    """ Renders one page and trims the empty margin off it.

        Returns:
            The width and height of the picture that was written.
    """
    with pymupdf.open(pdf) as document:
        page = document[page_number - 1]
        # the drawn area of the page, which is the table plus its caption
        content = page.get_bbox() if hasattr(page, "get_bbox") else page.rect
        box = pymupdf.Rect(content) & page.rect
        box = pymupdf.Rect(
            max(page.rect.x0, box.x0 - MARGIN),
            max(page.rect.y0, box.y0 - MARGIN),
            min(page.rect.x1, box.x1 + MARGIN),
            min(page.rect.y1, box.y1 + MARGIN),
        )
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=box)
        target.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(target)
        return pixmap.width, pixmap.height


def main() -> int:
    """Writes one picture per plan and reports its size."""
    root = Path(__file__).resolve().parents[1]
    images = root / "assets" / "images"
    cache = root / ".cache" / "spo"

    try:
        pdf = download(BACHELOR_PDF, cache / "SPO_Bachelor_2024_04_02_Lesefassung.pdf")
    except requests.RequestException as error:
        print(f"could not fetch the regulation: {error}", file=sys.stderr)
        return 1

    for name, page_number in PAGES.items():
        target = images / f"{name}.png"
        width, height = render(pdf, page_number, target)
        size = target.stat().st_size // 1024
        print(f"  {name:<20} page {page_number:>2}  {width}x{height}  {size} KB")

    print(f"\nwritten to {images}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
