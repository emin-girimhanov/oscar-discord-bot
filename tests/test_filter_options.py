"""Tests for `/filter` option catalogue, multi-selection logic and result sorting.

Before this change, `/filter` allowed only one value per category: clicking 5 CP and
then >5 CP silently replaced the first choice. Combining categories as AND while
allowing OR inside each category is what students expect when narrowing down electives.
Sorting the results by credit points or title prevents endless paging through unsorted lists.
"""

from unittest.mock import MagicMock
import pytest

from util.enums import LanguageCode
from util.filter_options import (
    FILTER_GROUPS,
    GROUP_CATEGORY,
    GROUP_CP,
    GROUP_EXAM,
    GROUP_POSITION,
    GROUP_SWS,
    apply_selection,
)
from util.modules_filter import ModulesFilter, SortKey, sort_modules
from util.translations import FILTER_TEXTS


def make_filter_module(
    id_: int = 1,
    title_de: str = "Datenbanken",
    title_en: str = "Databases",
    credit_points: str = "5",
    sws: str = "3",
    exam: str = "Klausur",
    semester: str = "Sommersemester",
    category_matches: bool = True,
):
    """A module mock with the fields read by `apply_selection` and `sort_modules`."""
    module = MagicMock()
    module.id_ = id_
    module.credit_points = credit_points

    def _get_title(lang: LanguageCode) -> str:
        return title_en if lang == LanguageCode.EN else title_de

    module.get_title.side_effect = _get_title
    module.get_teaching_form_sws.return_value = sws
    module.get_study_exam_type.return_value = exam
    module.get_semester_position.return_value = semester

    return module


class TestFilterTranslations:
    """Verifies that every group and option is translated in DE and EN."""

    def test_every_group_heading_is_translated(self):
        for group in FILTER_GROUPS:
            assert group.heading_key in FILTER_TEXTS
            assert LanguageCode.DE in FILTER_TEXTS[group.heading_key]
            assert LanguageCode.EN in FILTER_TEXTS[group.heading_key]
            assert FILTER_TEXTS[group.heading_key][LanguageCode.DE].strip()
            assert FILTER_TEXTS[group.heading_key][LanguageCode.EN].strip()

    def test_every_option_value_is_translated(self):
        for group in FILTER_GROUPS:
            for value in group.values:
                assert value in FILTER_TEXTS
                assert LanguageCode.DE in FILTER_TEXTS[value]
                assert LanguageCode.EN in FILTER_TEXTS[value]
                assert FILTER_TEXTS[value][LanguageCode.DE].strip()
                assert FILTER_TEXTS[value][LanguageCode.EN].strip()


class TestApplySelection:
    """Tests multi-selection: OR inside a category, AND across categories."""

    def test_empty_selection_returns_all_modules(self):
        m1 = make_filter_module(id_=1)
        m2 = make_filter_module(id_=2)
        mf = ModulesFilter()
        res = apply_selection({}, mf, modules=[m1, m2])
        assert res == [m1, m2]

    def test_or_within_credit_points(self):
        """Picking < 5 CP and > 5 CP returns both, but excludes = 5 CP."""
        m_small = make_filter_module(id_=1, credit_points="3")
        m_exact = make_filter_module(id_=2, credit_points="5")
        m_large = make_filter_module(id_=3, credit_points="6")
        mf = ModulesFilter()

        selection = {GROUP_CP: ["cp_lt_5", "cp_gt_5"]}
        res = apply_selection(selection, mf, modules=[m_small, m_exact, m_large])
        assert m_small in res
        assert m_large in res
        assert m_exact not in res

    def test_and_between_credit_points_and_exam(self):
        """Picking 5 CP AND written exam requires both criteria to hold."""
        m_fit = make_filter_module(id_=1, credit_points="5", exam="Klausur")
        m_wrong_cp = make_filter_module(id_=2, credit_points="6", exam="Klausur")
        m_wrong_exam = make_filter_module(id_=3, credit_points="5", exam="Mündliche Prüfung")
        mf = ModulesFilter()

        selection = {
            GROUP_CP: ["cp_eq_5"],
            GROUP_EXAM: ["exam_written"],
        }
        res = apply_selection(selection, mf, modules=[m_fit, m_wrong_cp, m_wrong_exam])
        assert res == [m_fit]

    def test_exam_type_in_english(self):
        """Matches English exam labels as well."""
        m_en = make_filter_module(id_=1, exam="Written exam")
        m_oral = make_filter_module(id_=2, exam="Oral examination")
        mf = ModulesFilter()

        selection = {GROUP_EXAM: ["exam_written"]}
        res = apply_selection(selection, mf, modules=[m_en, m_oral])
        assert res == [m_en]

    def test_semester_position_in_both_languages(self):
        """Matches both German and English semester markers."""
        m_summer_de = make_filter_module(id_=1, semester="Sommersemester")
        m_summer_en = make_filter_module(id_=2, semester="Summer semester")
        m_winter = make_filter_module(id_=3, semester="Wintersemester")
        mf = ModulesFilter()

        selection = {GROUP_POSITION: ["position_summer"]}
        res = apply_selection(selection, mf, modules=[m_summer_de, m_summer_en, m_winter])
        assert m_summer_de in res
        assert m_summer_en in res
        assert m_winter not in res


class TestSortModules:
    """Tests ordering module lists by credit points and title."""

    def test_sort_by_credit_points_ascending(self):
        m3 = make_filter_module(id_=1, credit_points="3 CP")
        m5 = make_filter_module(id_=2, credit_points="5 CP")
        m10 = make_filter_module(id_=3, credit_points="10 CP")

        sorted_list = sort_modules([m10, m3, m5], SortKey.CREDIT_POINTS, descending=False)
        assert sorted_list == [m3, m5, m10]

    def test_sort_by_credit_points_descending(self):
        m3 = make_filter_module(id_=1, credit_points="3")
        m5 = make_filter_module(id_=2, credit_points="5")
        m10 = make_filter_module(id_=3, credit_points="10")

        sorted_list = sort_modules([m3, m10, m5], SortKey.CREDIT_POINTS, descending=True)
        assert sorted_list == [m10, m5, m3]

    def test_sort_by_credit_points_missing_stays_at_end(self):
        """Modules without CP are kept at the end in both directions."""
        m5 = make_filter_module(id_=1, credit_points="5")
        m_none = make_filter_module(id_=2, credit_points="")

        asc = sort_modules([m_none, m5], SortKey.CREDIT_POINTS, descending=False)
        assert asc == [m5, m_none]

        desc = sort_modules([m_none, m5], SortKey.CREDIT_POINTS, descending=True)
        assert desc == [m5, m_none]

    def test_sort_by_title_german(self):
        m_a = make_filter_module(id_=1, title_de="Algorithmen")
        m_b = make_filter_module(id_=2, title_de="Betriebssysteme")
        m_d = make_filter_module(id_=3, title_de="Datenbanken")

        sorted_asc = sort_modules([m_d, m_a, m_b], SortKey.TITLE, descending=False, language=LanguageCode.DE)
        assert sorted_asc == [m_a, m_b, m_d]

        sorted_desc = sort_modules([m_d, m_a, m_b], SortKey.TITLE, descending=True, language=LanguageCode.DE)
        assert sorted_desc == [m_d, m_b, m_a]

    def test_sort_by_title_english(self):
        m_a = make_filter_module(id_=1, title_en="Algorithms")
        m_b = make_filter_module(id_=2, title_en="Databases")
        m_o = make_filter_module(id_=3, title_en="Operating Systems")

        sorted_asc = sort_modules([m_o, m_a, m_b], SortKey.TITLE, descending=False, language=LanguageCode.EN)
        assert sorted_asc == [m_a, m_b, m_o]
