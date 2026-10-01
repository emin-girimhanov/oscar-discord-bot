""" This module contains a class for the filtering of modules"""

from enum import IntEnum
import re
from typing import NamedTuple
from loguru import logger

from util.enums import LanguageCode, StudyCourse
from util.module import Module, get_module_list
# pylint: disable=C0301 # (line-too-long)
from util.semesterplans import SemestereplanModule, Semesterplan, SemesterplansManager, get_semesterplans_manager
from util.filter_categorys import MODULE_FILTER_CATEGORIES



class CpFilter(IntEnum):
    """ Defines all valid crdit point filter options"""
    LESS_THAN_5 = 0
    EQUALS_5 = 1
    GREATER_THAN_5 = 2


class SwsFilter(IntEnum):
    """ Defines all valid sws filter options"""
    LESS_THAN_3 = 0
    EQUALS_3 = 1
    GREATER_THAN_3 = 2


class SortKey(IntEnum):
    """ Defines the orders a result list can be put into."""
    CREDIT_POINTS = 0
    TITLE = 1


def _credit_points_value(module: Module) -> float | None:
    """ Reads one comparable credit point number out of the free text field.

        The table stores the credit points as text, for example `5`, `5 CP` or
        `3 + 2 CP`. The largest number found is used, which matches `filter_cp`,
        where a module counts as soon as one of its numbers fits.

        Parameters:
            module: The module to read.

        Returns:
            The number, or `None` when the field holds no number at all.
    """
    numbers: list[str] = re.findall(r"\d+", module.credit_points)
    if not numbers:
        return None
    return float(max(int(number) for number in numbers))


def _title_value(module: Module, language: LanguageCode) -> str | None:
    """ Reads the comparable title of a module.

        Parameters:
            module: The module to read.
            language: The language the list is shown in.

        Returns:
            The lowercased title, or `None` when the module has no title.
    """
    title: str = module.get_title(language).strip()
    return title.casefold() or None


def sort_modules(
    modules: list[Module],
    key: SortKey,
    descending: bool = False,
    language: LanguageCode = LanguageCode.DE,
) -> list[Module]:
    """ Puts a result list into a wanted order.

        Modules whose value is missing keep to the end in both directions. An empty
        credit point field is not a small module, and a student looking for the
        cheapest module should not have to page past every module without data.

        Parameters:
            modules: The list to order. It is not changed.
            key: Whether to order by credit points or by title.
            descending: Whether the largest or last value comes first.
            language: The language the titles are compared in.

        Returns:
            A new list, ordered. Modules with the same value keep their old order.
    """
    known: list[tuple[float | str, Module]] = []
    unknown: list[Module] = []

    for module in modules:
        value: float | str | None = (
            _credit_points_value(module) if key == SortKey.CREDIT_POINTS
            else _title_value(module, language)
        )
        if value is None:
            unknown.append(module)
        else:
            known.append((value, module))

    known.sort(key=lambda pair: pair[0], reverse=descending)

    return [module for _, module in known] + unknown


class ModulesFilter:
    """Class for filtering module list based on different criterias"""

    module_list: list[Module] = []
    remove_invalid: bool = False

    def __init__(self, remove_invalid: bool = False) -> None:
        """ Parameters:
                remove_invalid: whether invalid results should be removed from the result list
        """
        self.remove_invalid = remove_invalid
        self.module_list = get_module_list()


    def filter_cp(self, criterion: CpFilter, modules: list[Module] | None = None) -> list[Module]:
        """ Retrieves the a list of modules that fulfill the criterion.

            Parameters:
                criterion: The desired cp count as a CpFilter.

            Returns:
                A list of modules, that fulfill this criterion.
        """
        if modules is None:
            modules = self.module_list

        result: list[Module] = []
        cp: list[str]
        if criterion == CpFilter.LESS_THAN_5:
            for module in modules:
                cp = re.findall(r"\d+", module.credit_points)
                if any(int(n) < 5 for n in cp) or (len(cp)==0 and not self.remove_invalid):
                    result.append(module)
            # return [m for m in modules if int(m.credit_points)<5]
        elif criterion == CpFilter.EQUALS_5:
            for module in modules:
                cp = re.findall(r"\d+", module.credit_points)
                if any(int(n) == 5 for n in cp) or (len(cp)==0 and not self.remove_invalid):
                    result.append(module)
        elif criterion == CpFilter.GREATER_THAN_5:
            for module in modules:
                cp = re.findall(r"\d+", module.credit_points)
                if any(int(n) > 5 for n in cp) or (len(cp)==0 and not self.remove_invalid):
                    result.append(module)

        logger.debug(f"filtered list -> {len(result)}/{len(modules)}   -    (cp filter)")
        return result


    # pylint: disable=R0912 # (too-many-branches)
    def filter_sws(self, criterion: SwsFilter, modules: list[Module] | None = None) -> list[Module]:
        """ Retrieves the a list of modules that fulfill the criterion.
                but this function is flawed, since the sws information
                is provided as a non standardized string!

            Parameters:
                criterion: The desired sws count as a SwsFilter.

            Returns:
                A list of modules, that fulfill this criterion.
        """
        if modules is None:
            modules = self.module_list

        result: list[Module] = []
        sws: list[str]
        if criterion == SwsFilter.LESS_THAN_3:
            for module in modules:
                sws = re.findall(
                    r'\d+SWS',
                    module.get_teaching_form_sws().replace('\n', '').replace(' ', '').upper()
                )
                if len(sws)==0:
                    if not self.remove_invalid:
                        result.append(module)
                else:
                    sws_sum = 0
                    for x in sws:
                        sws_sum += int(x.replace("SWS", ""))
                    if sws_sum < 3:
                        result.append(module)
        elif criterion == SwsFilter.EQUALS_3:
            for module in modules:
                sws = re.findall(
                    r'\d+SWS',
                    module.get_teaching_form_sws().replace('\n', '').replace(' ', '').upper()
                )
                if len(sws)==0:
                    if not self.remove_invalid:
                        result.append(module)
                else:
                    sws_sum = 0
                    for x in sws:
                        sws_sum += int(x.replace("SWS", ""))
                    if sws_sum == 3:
                        result.append(module)
        elif criterion == SwsFilter.GREATER_THAN_3:
            for module in modules:
                sws = re.findall(
                    r'\d+SWS',
                    module.get_teaching_form_sws().replace('\n', '').replace(' ', '').upper()
                )
                if len(sws)==0:
                    if not self.remove_invalid:
                        result.append(module)
                else:
                    sws_sum = 0
                    for x in sws:
                        sws_sum += int(x.replace("SWS", ""))
                    if sws_sum > 3:
                        result.append(module)

        logger.debug(f"filtered list -> {len(result)}/{len(modules)}   -    (sws filter)")
        return result


    def filter_semesterplan(
        self,
        semester: int,
        study_course: StudyCourse,
        spo: int | None = None,
        winter_semester: bool = True,
        modules: list[Module] | None = None,
    ) -> list[Module]:
        """ Filter modules based on semesterplan for a specific semester.
        
            This method filters the module list to only include modules that are
            part of a specific semester in the standard curriculum (semesterplan).
            
            Parameters:
                semester: The semester number (1-indexed, e.g., 1 for first semester)
                studyCourse: The study course to filter for (e.g., StudyCourse.INFORMATIK)
                spo: The SPO (Studien- und Prüfungsordnung) year. If None, uses the newest
                    available SPO. If provided SPO doesn't exist, tries to find the closest
                    older SPO, or if none exists, the next newer SPO.
                winterSemester: Whether the semesterplan starts in winter semester
                modules: List of modules to filter (defaults to all modules)
                
            Returns:
                List of modules that belong to the specified semester according to
                the semesterplan. Returns empty list if semester doesn't exist or
                no matching semesterplan is found.
        """
        if modules is None:
            modules = self.module_list

        manager: SemesterplansManager = get_semesterplans_manager()

        semesterplan: Semesterplan|None = manager.get_best_matching_plan(
            study_course = study_course,
            spo = spo,
            winter_semester = winter_semester
        )

        if semesterplan is None:
            # pylint: disable=C0301 # (line-too-long)
            logger.error(f"No valid semesterplan found for '{study_course.name}', {spo} start {'winter' if winter_semester else 'summer'} semester")
            return []

        semester = min(max(0, semester-1), len(semesterplan.semesters)-1)

        semester_modules: list[SemestereplanModule] = semesterplan.semesters[semester]

        result: list[Module] = []
        for module in semester_modules:
            # match identification
            if module.identification is not None:
                match: Module|None = next(
                    (m for m in modules if m.id_==module.identification),
                    None
                )
                if match is not None:
                    result.append(match)
                    continue
            # match title
            if len(module.title.strip().lstrip())>0:
                match = next(
                    (m for m in modules if m.get_title(LanguageCode.DE)==module.title or \
                    m.get_title(LanguageCode.EN)==module.title)
                    , None
                )
                if match is not None:
                    result.append(match)
                    continue
            # creating dummy Module
            id_: int = -1
            if module.identification is not None:
                id_ = module.identification
            result.append(
                Module(
                    id_ = id_,
                    language = LanguageCode.DE,
                    title = module.title.strip().lstrip(),
                    credit_points = f"{module.credit_points} CP",
                    # usability is missing
                )
            )

        logger.debug(f"filtered list -> {len(result)}/{len(modules)}   -    (semesterplan filter)")
        return result


    # def filter_usability(
    #     self,
    #     criterion: SwsFilter,
    #     modules: list[Module] | None = None
    # ) -> list[Module]:
    #     return []


    def filter_semester_position(
        self,
        markers: list[str],
        modules: list[Module] | None = None
    ) -> list[Module]:
        """ Keeps modules that are taught in one of the wanted semester positions.

            The position is stored as a selection id and only the tables api knows the
            label behind it. Hardcoding the ids here would break as soon as someone
            reorders the selection, so the rendered text is matched instead.

            Parameters:
                markers: Lowercase fragments, for example `["somm"]` or `["wint", "jede"]`.
                modules: List of modules to filter (defaults to all modules).

            Returns:
                A list of modules whose semester position contains one of the markers.
        """
        if modules is None:
            modules = self.module_list

        result: list[Module] = [
            module for module in modules
            if any(marker in module.get_semester_position().lower() for marker in markers)
        ]

        logger.debug(f"filtered list -> {len(result)}/{len(modules)}   -    (semester position)")
        return result


    def filter_exam_type(
        self,
        markers: list[str],
        modules: list[Module] | None = None
    ) -> list[Module]:
        """ Keeps modules whose study or exam performance mentions one of the markers.

            The field is free text, so both languages are searched.

            Parameters:
                markers: Lowercase fragments, for example `["klausur", "written"]`.
                modules: List of modules to filter (defaults to all modules).

            Returns:
                A list of modules whose exam performance contains one of the markers.
        """
        if modules is None:
            modules = self.module_list

        result: list[Module] = []
        for module in modules:
            haystack: str = (
                module.get_study_exam_type(LanguageCode.DE)
                + " "
                + module.get_study_exam_type(LanguageCode.EN)
            ).lower()
            if any(marker in haystack for marker in markers):
                result.append(module)

        logger.debug(f"filtered list -> {len(result)}/{len(modules)}   -    (exam type)")
        return result


    def filter_category(
        self,
        key: str,
        modules: list[Module] | None = None
    ) -> list[Module]:
        """ Filter modules based on predifined categorys.
        
            This method filters the module list to only include modules that are
            somewhat related to the provided categor.
            
            Parameters:
                key: The semester number (1-indexed, e.g., 1 for first semester)
                modules: List of modules to filter (defaults to all modules)
                
            Returns:
                List of modules that belong to the specified category according to the
                `MODULE_FILTER_CATEGORIES` dictionary found in `util.filter_categorys`
                (sorted by amount of matching values).

                Returns emptylist if category doesn't exist.
        """
        if key not in MODULE_FILTER_CATEGORIES:
            return []

        if modules is None:
            modules = self.module_list

        class ModuleMatch(NamedTuple):
            """ Named Tuple for module sorting based on a score value."""
            module: Module
            score: int

        scored_modules: list[ModuleMatch] = []
        for module in modules:
            score: int = 0
            for keyword in MODULE_FILTER_CATEGORIES[key]:
                score += module.get_title(LanguageCode.DE).count(keyword)
                score += module.get_learning_goals(LanguageCode.DE).count(keyword)
                score += module.get_content(LanguageCode.DE).count(keyword)
                score += module.get_recommended_prerequisites(LanguageCode.DE).count(keyword)
                score += module.get_literature(LanguageCode.DE).count(keyword)

                score += module.get_title(LanguageCode.EN).count(keyword)
                score += module.get_learning_goals(LanguageCode.EN).count(keyword)
                score += module.get_content(LanguageCode.EN).count(keyword)
                score += module.get_recommended_prerequisites(LanguageCode.EN).count(keyword)
                score += module.get_literature(LanguageCode.EN).count(keyword)

            if score > 0:
                scored_modules.append(
                    ModuleMatch(module, score)
                )

        scored_modules.sort(key=lambda m: m.score, reverse=True)

        result: list[Module] = []
        for module_match in scored_modules:
            result.append(module_match.module)

        logger.debug(f"filtered list -> {len(result)}/{len(modules)}   -    (category filter)")
        return result




if __name__ == "__main__":
    module_filter: ModulesFilter = ModulesFilter(remove_invalid=True)

    _ = module_filter.filter_cp(CpFilter.GREATER_THAN_5)
    _ = module_filter.filter_sws(SwsFilter.EQUALS_3)
    _ = module_filter.filter_semesterplan(
        study_course=StudyCourse.BSC_CV,
        semester=2,
    )
    _ = module_filter.filter_category("ComputerGame")

    for m in _[:10]:
        print(m.get_title())
