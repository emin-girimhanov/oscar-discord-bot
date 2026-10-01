"""Tests that guard the shipped semesterplan assets.

A student plans a year of their life from this picture, so every number in it has to
come out of the Studien- und Prüfungsordnung, not out of what would look plausible.

The tests used to assert that a master runs **four semesters and 120 credit points**.
That is true of the three English programmes and false of the three German ones:

    SPO_Master_2016_05_23_3Semester_2, § 5 (2)
    "Die Regelstudienzeit beträgt einschließlich der Masterarbeit drei Semester."
    § 6 (1) "Er beträgt insgesamt 90 CP"

The shipped plans for M.Sc. Informatik, Ingenieurinformatik and Wirtschaftsinformatik
showed four semesters and 120 CP, and the tests held that in place. So the expected
length is written down here per programme, with the document it comes from.
"""

import json
import re
from pathlib import Path

import pytest

from oscar.ui.splan_view import STUDYCOURSE_TO_IMAGE_ID
from util.enums import StudyCourse
from util.paths import assets_dir


SEMESTERS_PER_PLAN: int = 7
CREDITS_PER_SEMESTER: int = 30
CREDITS_PER_PLAN: int = SEMESTERS_PER_PLAN * CREDITS_PER_SEMESTER

# How long a programme runs, from its own regulation. A bachelor is seven semesters.
# The consecutive masters of the faculty are **three**, the English ones are four.
SEMESTERS: dict[StudyCourse, int] = {
    StudyCourse.MSC_INF: 3,        # SPO Master 2016, § 5 (2)
    StudyCourse.MSC_INGINF: 3,
    StudyCourse.MSC_WIF: 3,
    StudyCourse.MSC_DKE: 4,        # SPO Master (englischsprachig) 2021, Anlage A
    StudyCourse.MSC_DE: 4,         # Anlage B
    StudyCourse.MSC_VC: 4,         # Anlage C
}


def _plan_files() -> list[Path]:
    """All semesterplan json files that ship with the bot."""
    return sorted((assets_dir() / "json" / "semesterplans").glob("*.json"))


def _load(path: Path) -> dict:  # pyright: ignore[reportMissingTypeArgument]
    with path.open(encoding="utf8") as file:
        return json.load(file)


def test_plan_files_are_present():
    """Guards against an empty glob silently passing every other test."""
    assert len(_plan_files()) >= 8


def _semesters_of(data: dict) -> int:
    """How many semesters this programme runs, from `SEMESTERS`."""
    return SEMESTERS.get(StudyCourse(data["study_course"]), SEMESTERS_PER_PLAN)


@pytest.mark.parametrize("path", _plan_files(), ids=lambda p: p.name)
def test_every_semester_adds_up(path: Path):
    """Every semester of every plan is worth exactly 30 credit points."""
    data = _load(path)
    semesters = data["semesters"]
    expected_semesters = _semesters_of(data)

    assert len(semesters) == expected_semesters

    sums = [sum(module["credit_points"] for module in semester) for semester in semesters]
    assert sums == [CREDITS_PER_SEMESTER] * expected_semesters


@pytest.mark.parametrize("path", _plan_files(), ids=lambda p: p.name)
def test_plan_adds_up(path: Path):
    """Every plan is worth 30 credit points a semester, for as long as it runs."""
    data = _load(path)
    expected_total = _semesters_of(data) * CREDITS_PER_SEMESTER
    total = sum(
        module["credit_points"] for semester in data["semesters"] for module in semester
    )
    assert total == expected_total


@pytest.mark.parametrize("path", _plan_files(), ids=lambda p: p.name)
def test_study_course_is_a_known_enum(path: Path):
    """The plan is looked up by this field, not by its file name."""
    data = _load(path)
    assert data["study_course"] in StudyCourse.values()


def test_hand_drawn_images_belong_to_the_mapped_programme():
    """Pins the mapping of a programme to its hand drawn picture.

        The file names are easy to get wrong, because the json files carry the
        opposite numbers: `1_SPO_2024_WiSe.json` holds Computervisualistik and
        `2_SPO_2024_WiSe.json` holds Informatik, while the pictures are the
        other way round. The pictures decide, their heading names the
        programme:

        - `1_SPO_2024_WiSe.png` is headed "Informatik - Start Wintersemester"
        - `2_SPO_2024_WiSe.png` is headed "Computervisualistik - Start Wintersemester"
    """
    assert STUDYCOURSE_TO_IMAGE_ID[StudyCourse.BSC_INF] == "1"
    assert STUDYCOURSE_TO_IMAGE_ID[StudyCourse.BSC_CV] == "2"

    for image_id in STUDYCOURSE_TO_IMAGE_ID.values():
        assert (assets_dir() / "images" / f"{image_id}_SPO_2024_WiSe.png").is_file()



class TestEveryPlanNamesItsSource:
    """A plan a student trusts has to say where it came from.

        Nothing here may be worked out from module titles, from credit point sums or
        from what looks plausible. It comes out of the Studien- und Prüfungsordnung as
        a pdf, and the file says which document, which page, and when it was fetched.
        Without that nobody can check the plan a year from now, and a wrong plan reads
        exactly like a right one.
    """

    @pytest.mark.parametrize("path", _plan_files(), ids=lambda p: p.name)
    def test_it_has_a_source(self, path: Path):
        assert "source" in _load(path), (
            f"{path.name} names no source. Take the plan from the SPO pdf and record "
            "the document, the url and the page it came from."
        )

    @pytest.mark.parametrize("path", _plan_files(), ids=lambda p: p.name)
    def test_the_source_is_a_document_somebody_can_open(self, path: Path):
        source = _load(path)["source"]
        assert source.get("document"), f"{path.name} has no document name"
        assert str(source.get("url", "")).startswith("https://"), (
            f"{path.name} has no link to the document"
        )
        assert isinstance(source.get("page"), int), f"{path.name} names no page"

    @pytest.mark.parametrize("path", _plan_files(), ids=lambda p: p.name)
    def test_the_source_says_when_it_was_read(self, path: Path):
        """A regulation is replaced. The date says how old this reading is."""
        retrieved = _load(path)["source"].get("retrieved", "")
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(retrieved)), (
            f"{path.name} has no retrieval date in the form 2026-09-17"
        )

    @pytest.mark.parametrize("path", _plan_files(), ids=lambda p: p.name)
    def test_the_source_is_an_official_one(self, path: Path):
        """BookStack or the faculty document server, nothing else."""
        url = _load(path)["source"]["url"]
        assert "fin.ovgu.de" in url or "bookstack.cs.ovgu.de" in url, (
            f"{path.name} cites {url}, which is not a faculty document"
        )


class TestThePictureOfTheOfficialTable:
    """`/standard_plan` shows the table as the regulation prints it, not a redrawing.

        The picture carries what a list of module titles cannot: the exam rules, the
        weightings, the "mind. 10 CP benotet" bars and the legend. It is cut out of the
        pdf by `tools/extract_semesterplan_images.py`, so it is the official table and
        nothing else.

        A picture cannot be ticked off, so `SPlanView` renders the json instead once a
        student has saved modules. Both have to exist and both have to be right.
    """

    @pytest.mark.parametrize(
        "course",
        [StudyCourse.BSC_INF, StudyCourse.BSC_CV, StudyCourse.BSC_INGINF, StudyCourse.BSC_WIF],
    )
    def test_every_bachelor_has_one(self, course: StudyCourse):
        assert course in STUDYCOURSE_TO_IMAGE_ID, (
            f"{course.name} falls back to the drawn table. Add its page to "
            "tools/extract_semesterplan_images.py and run it."
        )

    @pytest.mark.parametrize(
        "course",
        [StudyCourse.BSC_INF, StudyCourse.BSC_CV, StudyCourse.BSC_INGINF, StudyCourse.BSC_WIF],
    )
    @pytest.mark.parametrize("season", ["WiSe", "SoSe"])
    def test_both_starts_ship_a_picture(self, course: StudyCourse, season: str):
        """A student who starts in summer reads a different table."""
        image_id = STUDYCOURSE_TO_IMAGE_ID[course]
        path = assets_dir() / "images" / f"{image_id}_SPO_2024_{season}.png"
        assert path.is_file(), f"{path.name} is missing"

    def test_no_picture_is_empty(self):
        for path in (assets_dir() / "images").glob("*_SPO_*.png"):
            assert path.stat().st_size > 20_000, f"{path.name} is too small to be a table"

    def test_a_picture_fits_in_a_discord_message(self):
        """Discord refuses an attachment over 8 MB on a free server."""
        for path in (assets_dir() / "images").glob("*_SPO_*.png"):
            assert path.stat().st_size < 8_000_000, f"{path.name} is too big to send"

    def test_every_picture_belongs_to_a_programme(self):
        """A file nobody maps to a course is one nobody sees."""
        known = {
            f"{image_id}_SPO_2024_{season}.png"
            for image_id in STUDYCOURSE_TO_IMAGE_ID.values()
            for season in ("WiSe", "SoSe")
        }
        shipped = {path.name for path in (assets_dir() / "images").glob("*_SPO_*.png")}
        assert shipped <= known, f"no programme shows {sorted(shipped - known)}"

    def test_the_master_programmes_have_no_picture(self):
        """Their regulation prints credit point ranges, not a table of modules."""
        for course in (StudyCourse.MSC_INF, StudyCourse.MSC_DKE, StudyCourse.MSC_VC):
            assert course not in STUDYCOURSE_TO_IMAGE_ID
