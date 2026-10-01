""" This module holds various utiliity classes and functions for interacting with the standard
    curiculua singleton.
"""

import json
from pathlib import Path
from loguru import logger

from util.enums import StudyCourse
from util.paths import assets_dir


# pylint: disable=R0903 (too-few-public-methods)
class SemestereplanModule():
    """ Class for storing a single Entry in a semesterplan"""

    title: str
    identification: int|None
    credit_points: int
    usability: list[int]
    groupId: int|None

    # pylint: disable=R0913 (too-many-arguments)
    # pylint: disable=R0917 (too-many-positional-arguments)
    def __init__(
        self,
        title: str,
        creditp_points: int,
        identification: int|None = None,
        usability: list[int]|None = None,
        groupId: int|None = None
    ) -> None:
        self.title = title
        self.identification = identification
        self.credit_points = creditp_points
        if usability:
            self.usability = usability
        else:
            self.usability = []
        self.groupId = groupId



class SemesterplanGroup():
    """ Class for organizing grouped [SemestereplanModule]s"""

    id: int
    graded_credits: int
    weight: float

    def __init__(self, _id: int, graded_credits:int, weight: float = 1.0) -> None:
        self.id = _id
        self.graded_credits = graded_credits
        self.weight = min(max(0, weight), 1)



class Semesterplan():
    """ Class for representing a single Semesterplan"""

    spo: int
    study_course: StudyCourse
    winter_semester: bool
    title: str
    semesters: list[list[SemestereplanModule]]
    groups: list[SemesterplanGroup]

    # pylint: disable=R0913 (too-many-arguments)
    # pylint: disable=R0917 (too-many-positional-arguments)
    def __init__(
        self,
        spo: int,
        study_course: StudyCourse,
        winter_semester: bool,
        title: str,
        semesters: list[list[SemestereplanModule]]|None = None,
        groups: list[SemesterplanGroup]|None = None
    ) -> None:
        self.spo = spo
        self.study_course = study_course
        self.winter_semester = winter_semester
        self.title = title
        if semesters:
            self.semesters = semesters
        else:
            self.semesters = []
        if groups:
            self.groups = groups
        else:
            self.groups = []

    # TODO: add a to json method
    # def to_data(self) -> dict[]: # create Semesterplan typed dict
    #     pass



class SemesterplansManager():
    """ Class for parsing standard curiculua json files and retrieving corresponding information"""

    json_path: Path
    semesterplans: list[Semesterplan]

    def __init__(self, json_path: Path|None = None):
        """ INitialy parse `.json` files.

            Parameters:
                json_path: Path to the folder containing the `.json` files.
                Defaults to ./database/oscar.db
        """
        if json_path is None:
            logger.debug("Missing explicit json path (reverting to default)")
            json_path = assets_dir() / "json" / "semesterplans"

        self.json_path = json_path
        self.semesterplans = []
        self._load_jsons()


    # pylint: disable=C0301 # (line-too-long)
    def _json_to_semesterplan(self, data: dict) -> Semesterplan:   # pyright: ignore[reportMissingTypeArgument]
        """ Parse a Semesterplan json dictionary.

            Parameters:
                data: Dictionary containing the JSON data

            Returns:
                A Semesterplan object populated with the data
        """
        groups: list[SemesterplanGroup] = []
        for group in data.get("groups", []):
            groups.append(
                SemesterplanGroup(
                    _id=group["id"],
                    graded_credits=group["graded_credits"],
                    weight=group.get("weight", 1.0)
                )
            )

        semesters: list[list[SemestereplanModule]] = []
        for semester in range(len(data.get("semesters", []))):
            modules: list[SemestereplanModule] = []
            for module in data["semesters"][semester]:
                modules.append(
                    SemestereplanModule(
                        title = module.get("title", ""),
                        creditp_points = module.get("credit_points", 5),
                        identification = module.get("identification"),
                        usability = module.get("usability", []),
                        groupId = module.get("groupId"),
                    )
                )
            semesters.append(modules)

        semesterplan: Semesterplan = Semesterplan(
            spo = data["spo"],
            study_course = StudyCourse(data["study_course"]),
            winter_semester = data["winter_semester"],
            title = data.get(
                "title",
                f"{StudyCourse(data["study_course"]).name} - Start Wintersemester"
                    if data["winter_semester"] else
                f"{StudyCourse(data["study_course"]).name} - Start Sommersemester"),
            semesters = semesters,
            groups = groups
        )

        return semesterplan

    def _load_jsons(self):
        if not self.json_path.exists():
            logger.error(
                f"Unable to load semesterplans. Dirctory: '{self.json_path}' doesn't exist."
            )
            return

        for json_file in self.json_path.glob("*.json"):
            try:
                with json_file.open(encoding="utf8") as file:
                    logger.debug(f"Parsing `.json` file: '{json_file.name}'")
                    data = json.load(file)
                    semesterplan = self._json_to_semesterplan(data)
                    self.semesterplans.append(semesterplan)
            # every way a broken plan file can fail: unreadable, invalid json,
            # missing key, wrong type
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
                logger.error(f"An error occured while loading '{json_file.name}':\n{e}")
        logger.info(f"Finished loading {len(self.semesterplans)} semesterplans")


    def get_best_matching_plan(
        self,
        study_course: StudyCourse,
        spo: int | None = None,
        winter_semester: bool = True,
    ) -> Semesterplan | None:
        '''Find the best matching semesterplan based on given criteria.

        Parameters:
            studyCourse: The study course to filter for (e.g., StudyCourse.BSC_INF)
            spo: The SPO year. If None, uses the newest available SPO.
            If provided SPO doesn't exist, tries to find the closest older SPO,
            or if none exists, the next newer SPO.
            winterSemester: Whether the semesterplan starts in winter semester

        Returns:
            The best matching Semesterplan, or None if no matching plan is found.
        '''

        # preselect only fitting coicecs
        candidate_plans: list[Semesterplan] = [
            plan for plan in self.semesterplans
            if plan.study_course == study_course
        ]
        for plan in candidate_plans:
            if plan.winter_semester!=winter_semester and any(
            plan.spo==p.spo and
            p.winter_semester==winter_semester for p in candidate_plans):
                candidate_plans.remove(plan)


        if not candidate_plans:
            return None

        # Find the appropriate SPO
        matching_plan: Semesterplan | None = None

        if spo is None:
            matching_plan = max(candidate_plans, key=lambda p: p.spo)
        else:
            exact_matches = [p for p in candidate_plans if p.spo == spo]

            if exact_matches:
                matching_plan = exact_matches[0]
            else:
                older_spos = [p for p in candidate_plans if p.spo < spo]
                if older_spos:
                    matching_plan = max(older_spos, key=lambda p: p.spo)
                else:
                    newer_spos = [p for p in candidate_plans if p.spo > spo]
                    if newer_spos:
                        matching_plan = min(newer_spos, key=lambda p: p.spo)

        return matching_plan



# For assertion of a singleton instance
_manager_singleton: SemesterplansManager|None = None

def get_semesterplans_manager() -> SemesterplansManager:
    """Get or create the database singleton."""
    # pylint: disable=W0603 # (global-statement)
    global _manager_singleton
    if _manager_singleton is None:
        _manager_singleton = SemesterplansManager()
    return _manager_singleton
