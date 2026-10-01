"""Tests for `/standard_plan` progress marking and elective bipartite matching.

A student in higher semesters wants to see what modules in their standard curriculum
are already in their plan, and which ones are still open. OSCAR stores no grades, so
a checkmark indicates that a module is planned, never that it has been passed.
Elective slots have no module numbers and are matched via usability IDs using maximum
bipartite matching so slot order does not affect the outcome.
"""

from unittest.mock import MagicMock
import pytest

from util.enums import LanguageCode, StudyCourse
from util.module import Module
from util.plan_progress import (
    PlanProgress,
    _covers_elective,
    _maximum_matching,
    match_plan,
)
from util.semesterplans import SemestereplanModule, Semesterplan
from util.translations import HELP_ANSWERS, PLAN_PROGRESS_TEXTS


def make_test_module(id_: int, usability_ids: list[int] | None = None) -> Module:
    """Creates a mock module with id and usability ids."""
    module = MagicMock(spec=Module)
    module.id_ = id_
    module.get_usability_ids.return_value = usability_ids or []
    return module


def make_slot(
    title: str = "Test Modul",
    cp: int = 5,
    identification: int | None = None,
    usability: list[int] | None = None,
) -> SemestereplanModule:
    """Creates a semester plan box (compulsory if identification given, elective if None)."""
    return SemestereplanModule(
        title,
        cp,
        identification=identification,
        usability=usability or [],
    )


class TestPlanProgressTexts:
    """Verifies that all text keys exist in German and English."""

    @pytest.mark.parametrize("key", [
        "legend",
        "no_grades",
        "summary",
        "semester_marked",
        "semester_plain",
        "nothing_saved",
    ])
    def test_text_keys_exist_in_both_languages(self, key):
        assert key in PLAN_PROGRESS_TEXTS
        assert LanguageCode.DE in PLAN_PROGRESS_TEXTS[key]
        assert LanguageCode.EN in PLAN_PROGRESS_TEXTS[key]
        assert PLAN_PROGRESS_TEXTS[key][LanguageCode.DE].strip()
        assert PLAN_PROGRESS_TEXTS[key][LanguageCode.EN].strip()

    def test_help_answer_explains_plan_progress(self):
        for lang in (LanguageCode.DE, LanguageCode.EN):
            assert "standard_plan" in HELP_ANSWERS
            text = HELP_ANSWERS["standard_plan"][lang]
            assert "Haken" in text or "tick" in text


class TestBipartiteMatching:
    """Tests the maximum matching algorithm on candidate assignments."""

    def test_single_slot_single_candidate(self):
        # 1 slot, 1 module that fits
        candidates = [[0]]
        res = _maximum_matching(candidates, 1)
        assert res == [True]

    def test_slot_cannot_be_filled(self):
        # 1 slot, no candidate
        candidates = [[]]
        res = _maximum_matching(candidates, 0)
        assert res == [False]

    def test_augmenting_path_reassignment(self):
        """Slot 0 can take mod 0. Slot 1 can take mod 0 or mod 1.
        Both slots should be covered, even if slot 0 greedily grabbed mod 0 first.
        """
        candidates = [
            [0],     # slot 0 only fits mod 0
            [0, 1],  # slot 1 fits mod 0 or 1
        ]
        res = _maximum_matching(candidates, 2)
        assert res == [True, True]


def make_plan(semesters: list[list[SemestereplanModule]]) -> Semesterplan:
    """Helper to create a test Semesterplan."""
    return Semesterplan(
        spo=2024,
        study_course=StudyCourse.BSC_INF,
        winter_semester=True,
        title="Informatik",
        semesters=semesters,
    )


class TestMatchPlan:
    """Tests matching saved modules against compulsory and elective slots."""

    def test_compulsory_module_matching(self):
        plan = make_plan([
            [make_slot("AuD", cp=5, identification=101)],
            [make_slot("TI", cp=5, identification=102)],
        ])
        saved = [make_test_module(101)]
        progress = match_plan(plan, saved, StudyCourse.BSC_INF)

        assert progress.covered == [[True], [False]]
        assert progress.credits == (5, 10)
        assert progress.semester_credits(0) == (5, 5)
        assert progress.semester_credits(1) == (0, 5)

    def test_compulsory_module_not_reused_for_elective(self):
        """A module that covers a compulsory slot cannot also fill an elective."""
        plan = make_plan([
            [
                make_slot("AuD", cp=5, identification=101, usability=[10]),
                make_slot("WPF 1", cp=5, identification=None, usability=[10]),
            ]
        ])
        saved = [make_test_module(101, usability_ids=[10])]
        progress = match_plan(plan, saved, StudyCourse.BSC_INF)

        # Only the compulsory slot gets the module, elective remains open
        assert progress.covered == [[True, False]]
        assert progress.credits == (5, 10)

    def test_elective_slot_matched_by_usability(self):
        plan = make_plan([
            [make_slot("WPF INF", cp=5, identification=None, usability=[42])]
        ])
        m_fit = make_test_module(201, usability_ids=[42])
        progress = match_plan(plan, [m_fit], StudyCourse.BSC_INF)

        assert progress.covered == [[True]]
        assert progress.credits == (5, 5)

    def test_elective_slot_without_matching_usability_remains_open(self):
        plan = make_plan([
            [make_slot("WPF INF", cp=5, identification=None, usability=[42])]
        ])
        m_other = make_test_module(202, usability_ids=[99])
        progress = match_plan(plan, [m_other], StudyCourse.BSC_INF)

        assert progress.covered == [[False]]
        assert progress.credits == (0, 5)


class TestCoversElective:
    """Tests the usability overlap helper."""

    def test_matching_usability_id(self):
        slot = make_slot(usability=[1, 2, 3])
        mod = make_test_module(1, usability_ids=[3, 4])
        assert _covers_elective(slot, mod, StudyCourse.BSC_INF) is True

    def test_no_usability_overlap(self):
        slot = make_slot(usability=[1, 2])
        mod = make_test_module(1, usability_ids=[3, 4])
        assert _covers_elective(slot, mod, StudyCourse.BSC_INF) is False

