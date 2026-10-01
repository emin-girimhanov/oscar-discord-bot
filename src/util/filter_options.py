""" This module holds the option catalogue behind the `/filter` mask.

    The mask used to be a list of German button labels, and the search read those
    labels back. That had two consequences. A label only exists once it is rendered,
    so an English mask could not be matched, and every criterion was a single value,
    so a second click in the same row quietly replaced the first one.

    The catalogue here separates the two. A button carries a stable `value`, and the
    label is only what the student reads. `apply_selection` turns a set of values into
    a module list: several values in one group are an or, different groups are an and.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import NamedTuple

from util.module import Module
from util.modules_filter import CpFilter, SwsFilter, ModulesFilter


class FilterGroup(NamedTuple):
    """ One row of the mask.

        Attributes:
            key: The name of the group. Values of one group are combined as an or.
            heading_key: The key of the row heading in `translations.FILTER_TEXTS`.
            values: The option values of the row, in the order they are shown. Each
                value is also the key of its label in `translations.FILTER_TEXTS`.
    """
    key: str
    heading_key: str
    values: tuple[str, ...]


GROUP_CP: str = "cp"
GROUP_SWS: str = "sws"
GROUP_EXAM: str = "exam"
GROUP_POSITION: str = "position"
GROUP_CATEGORY: str = "category"


FILTER_GROUPS: tuple[FilterGroup, ...] = (
    FilterGroup(GROUP_CP, "heading_cp", ("cp_lt_5", "cp_eq_5", "cp_gt_5")),
    FilterGroup(GROUP_SWS, "heading_sws", ("sws_lt_3", "sws_eq_3", "sws_gt_3")),
    FilterGroup(GROUP_EXAM, "heading_exam", ("exam_written", "exam_oral")),
    FilterGroup(
        GROUP_POSITION,
        "heading_position",
        ("position_summer", "position_winter", "position_every"),
    ),
    FilterGroup(
        GROUP_CATEGORY,
        "heading_category",
        ("interest_ai", "interest_games", "interest_systems", "interest_scientific"),
    ),
)


CP_CRITERIA: dict[str, CpFilter] = {
    "cp_lt_5": CpFilter.LESS_THAN_5,
    "cp_eq_5": CpFilter.EQUALS_5,
    "cp_gt_5": CpFilter.GREATER_THAN_5,
}

SWS_CRITERIA: dict[str, SwsFilter] = {
    "sws_lt_3": SwsFilter.LESS_THAN_3,
    "sws_eq_3": SwsFilter.EQUALS_3,
    "sws_gt_3": SwsFilter.GREATER_THAN_3,
}

# The semester position is a selection in the table and only the api knows the label
# behind the id, so the rendered text is matched. Both spellings are listed, because
# the table renders the label in the language of the module.
POSITION_MARKERS: dict[str, tuple[str, ...]] = {
    "position_summer": ("somm", "summer"),
    "position_winter": ("wint",),
    "position_every": ("jede", "every", "each"),
}

# The study and examination performance is free text, so both languages are searched.
EXAM_MARKERS: dict[str, tuple[str, ...]] = {
    "exam_written": ("klausur", "written"),
    "exam_oral": ("mündlich", "muendlich", "oral"),
}

# The keys of `util.filter_categorys.MODULE_FILTER_CATEGORIES`.
CATEGORY_KEYS: dict[str, str] = {
    "interest_ai": "AI",
    "interest_games": "ComputerGame",
    "interest_systems": "SystemsEngineering",
    "interest_scientific": "ScientificComputing",
}


def _union(parts: Iterable[list[Module]]) -> list[Module]:
    """ Merges the results of one group into an or.

        Two modules are the same module when they are the same object. Every part
        comes out of the same source list, so identity is enough and the modules do
        not have to be comparable.

        Parameters:
            parts: One result list per selected value of the group.

        Returns:
            Every module that at least one part kept, each one once, in the order it
            was first seen. With a single part the order is the one of that part, so
            the ranking of `filter_category` survives.
    """
    merged: list[Module] = []
    seen: set[int] = set()

    for part in parts:
        for module in part:
            if id(module) not in seen:
                seen.add(id(module))
                merged.append(module)

    return merged


def _markers(values: Sequence[str], table: Mapping[str, tuple[str, ...]]) -> list[str]:
    """ Collects the text fragments of every selected value of a group.

        Parameters:
            values: The selected values.
            table: The fragments belonging to each value.

        Returns:
            All fragments in one list. `filter_semester_position` and
            `filter_exam_type` already keep a module that matches any of them, so the
            or of this group needs no further work.
    """
    markers: list[str] = []
    for value in values:
        markers.extend(table.get(value, ()))
    return markers


def apply_selection(
    selection: Mapping[str, Sequence[str]],
    module_filter: ModulesFilter,
    modules: list[Module] | None = None,
) -> list[Module]:
    """ Turns the pressed buttons of the mask into a module list.

        Several values of one group are an or: a student who takes a module with 5 or
        with 6 credit points selects both and gets both. Different groups are an and:
        5 credit points and a written exam means both have to hold.

        Parameters:
            selection: Group key to the values selected in that group.
            module_filter: The filter the module list is taken from.
            modules: The list to narrow down, defaults to all modules.

        Returns:
            The modules that fulfill every group. An empty selection returns the
            whole list.
    """
    result: list[Module] = module_filter.module_list if modules is None else modules

    cp_criteria: list[CpFilter] = [
        CP_CRITERIA[value] for value in selection.get(GROUP_CP, ()) if value in CP_CRITERIA
    ]
    if cp_criteria:
        result = _union(
            module_filter.filter_cp(criterion, modules=result) for criterion in cp_criteria
        )

    sws_criteria: list[SwsFilter] = [
        SWS_CRITERIA[value] for value in selection.get(GROUP_SWS, ()) if value in SWS_CRITERIA
    ]
    if sws_criteria:
        result = _union(
            module_filter.filter_sws(criterion, modules=result) for criterion in sws_criteria
        )

    position_markers: list[str] = _markers(selection.get(GROUP_POSITION, ()), POSITION_MARKERS)
    if position_markers:
        result = module_filter.filter_semester_position(position_markers, modules=result)

    exam_markers: list[str] = _markers(selection.get(GROUP_EXAM, ()), EXAM_MARKERS)
    if exam_markers:
        result = module_filter.filter_exam_type(exam_markers, modules=result)

    categories: list[str] = [
        CATEGORY_KEYS[value]
        for value in selection.get(GROUP_CATEGORY, ())
        if value in CATEGORY_KEYS
    ]
    if categories:
        result = _union(
            module_filter.filter_category(category, modules=result) for category in categories
        )

    return result
