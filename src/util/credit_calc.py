"""Utility functions for credit point calculations based on semester plans."""

from util.enums import StudyCourse
from util.semesterplans import Semesterplan, get_semesterplans_manager


def _spo_year(spo: str | int) -> int:
    """Converts a stored PO value like `'PO_2024'` (or `2024`) into the year."""
    if isinstance(spo, int):
        return spo
    return int(str(spo).rsplit("_", 1)[-1])


def _find_plan(spo: str | int, major: StudyCourse, winter: bool) -> Semesterplan:
    """Looks the plan up by its content, the json file names don't follow the StudyCourse ids."""
    plan = get_semesterplans_manager().get_best_matching_plan(
        study_course=major, spo=_spo_year(spo), winter_semester=winter
    )
    if plan is None:
        raise FileNotFoundError(f"No semesterplan for {major.name}, SPO {spo}, winter={winter}")
    return plan


# pylint: disable=W0613 # study_course reserved for future filtering
def get_modules_for_semester(
    spo: str | int, major: StudyCourse, winter: bool, semester: int, study_course: StudyCourse
) -> list[dict]:  # pyright: ignore[reportMissingTypeArgument]
    """Return list of module dicts for the given semester in the plan."""
    plan = _find_plan(spo, major, winter)
    if not 1 <= semester <= len(plan.semesters):
        return []

    return [
        {
            'title': module.title,
            'credit_points': module.credit_points,
            'usability': module.usability,
            'identification': module.identification,
        }
        for module in plan.semesters[semester - 1]
    ]
