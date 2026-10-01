""" This module marks a standard study plan against the modules a student saved.

    OSCAR stores no grades and has no way to read them from the university. A marked
    box therefore means "this module is in your plan", never "you passed it". Every
    name in here says planned, so the promise cannot drift while the code is edited.

    A plan box is either a named module, which carries a module number, or an elective
    slot, which carries none. A named box is covered by the saved module with that
    number. An elective box is covered by a saved module whose usability ids for this
    programme overlap the ids of the slot, the same rule `/semesterplan` already uses
    for a single semester.

    One saved module covers at most one box. A plan lists the same elective twice, for
    example two `Anwendungsfach` boxes in one semester, and counting one saved module
    for both of them would show progress the student does not have.
"""

from util.database import get_database
from util.enums import StudyCourse
from util.module import Module
from util.semesterplans import SemestereplanModule, Semesterplan


class PlanProgress:
    """ How much of a standard study plan the saved modules already cover.

        Attributes:
            plan: The plan that was marked.
            covered: One flag per box, in the shape of `plan.semesters`.
    """

    def __init__(self, plan: Semesterplan, covered: list[list[bool]]):
        self.plan: Semesterplan = plan
        self.covered: list[list[bool]] = covered

    @property
    def has_any(self) -> bool:
        """ Whether at least one box of the plan is covered."""
        return any(any(semester) for semester in self.covered)

    def semester_credits(self, index: int) -> tuple[int, int]:
        """ The planned and the total credit points of one semester.

            Parameters:
                index: The zero based semester, so the first semester sits at 0.

            Returns:
                A pair of planned credit points and credit points in the plan.
        """
        semester: list[SemestereplanModule] = self.plan.semesters[index]
        total: int = sum(module.credit_points for module in semester)
        planned: int = sum(
            module.credit_points
            for module, is_covered in zip(semester, self.covered[index])
            if is_covered
        )
        return planned, total

    @property
    def credits(self) -> tuple[int, int]:
        """ The planned and the total credit points of the whole plan."""
        planned: int = 0
        total: int = 0
        for index in range(len(self.plan.semesters)):
            semester_planned, semester_total = self.semester_credits(index)
            planned += semester_planned
            total += semester_total
        return planned, total


def _maximum_matching(candidates: list[list[int]], module_count: int) -> list[bool]:
    """ Assigns modules to slots so that as many slots as possible are covered.

        A greedy pass is not enough here. A module that fits a broad slot and a narrow
        one is eaten by whichever slot comes first, and the other slot then reads as
        missing although the student does have a module for it. This walks augmenting
        paths instead, so the answer never depends on the order of the plan.

        Parameters:
            candidates: For every slot the modules that could cover it.
            module_count: How many modules are on offer.

        Returns:
            One flag per slot, `True` when the slot got a module.
    """
    assigned_to: list[int | None] = [None] * module_count

    def _augment(slot: int, seen: set[int]) -> bool:
        for module in candidates[slot]:
            if module in seen:
                continue
            seen.add(module)
            taken_by: int | None = assigned_to[module]
            if taken_by is None or _augment(taken_by, seen):
                assigned_to[module] = slot
                return True
        return False

    return [_augment(slot, set()) for slot in range(len(candidates))]


def _covers_elective(slot: SemestereplanModule, module: Module, major: StudyCourse) -> bool:
    """ Whether a saved module may fill an elective slot of this programme.

        An elective slot names no module, it names the usability ids that a module has
        to carry to be allowed there. A slot without any id stays open, because then
        nothing tells us what belongs in it.
    """
    return bool(set(slot.usability) & set(module.get_usability_ids(major)))


def match_plan(  # pylint: disable=too-many-locals
    plan: Semesterplan, modules: list[Module], major: StudyCourse
) -> PlanProgress:
    """ Marks every box of the plan against the modules a student saved.

        Named boxes are matched first, by module number. Only the modules left over
        are offered to the elective slots, so a compulsory module cannot be counted as
        somebody's elective as well.

        Parameters:
            plan: The standard study plan of the programme.
            modules: The modules the student saved, loaded in full.
            major: The programme, it decides which usability ids are read.

        Returns:
            The plan together with one flag per box.
    """
    boxes: list[SemestereplanModule] = [box for semester in plan.semesters for box in semester]
    covered: list[bool] = [False] * len(boxes)
    used: list[bool] = [False] * len(modules)

    for index, box in enumerate(boxes):
        if box.identification is None:
            continue
        for position, module in enumerate(modules):
            if not used[position] and module.id_ == box.identification:
                used[position] = True
                covered[index] = True
                break

    free: list[Module] = [module for position, module in enumerate(modules) if not used[position]]
    electives: list[int] = [
        index for index, box in enumerate(boxes) if box.identification is None
    ]
    candidates: list[list[int]] = [
        [
            position for position, module in enumerate(free)
            if _covers_elective(boxes[index], module, major)
        ]
        for index in electives
    ]
    for index, is_covered in zip(electives, _maximum_matching(candidates, len(free))):
        covered[index] = is_covered

    nested: list[list[bool]] = []
    start: int = 0
    for semester in plan.semesters:
        nested.append(covered[start: start + len(semester)])
        start += len(semester)

    return PlanProgress(plan, nested)


def load_saved_modules(user_id: int) -> list[Module]:
    """ The modules a student saved, reloaded from the catalogue.

        The database keeps only the id, the language and the title of a saved module.
        Matching an elective slot needs the usability ids, which live on the full
        module, so every saved row is looked up again. A module that has meanwhile
        left the catalogue is skipped instead of breaking the whole plan.

        Parameters:
            user_id: The discord id of the student.

        Returns:
            The saved modules, in the order they were saved.
    """
    saved: list[Module] = []
    for stored in get_database().get_semesterplan(user_id):
        try:
            saved.append(Module.from_id(stored.id_))
        except IndexError:
            continue
    return saved
