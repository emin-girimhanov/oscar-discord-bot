"""Comprehensive tests for the modules_filter module (ModulesFilter, CpFilter, SwsFilter)."""

import pytest
from unittest.mock import patch, MagicMock
from util.modules_filter import ModulesFilter, CpFilter, SwsFilter
from util.module import Module
from util.enums import LanguageCode


# --- Fixtures ---

@pytest.fixture
def filter_test_modules():
    """Creates a list of test modules with varying CP and SWS values."""
    return [
        Module(id_=1, language=LanguageCode.DE, credit_points="3", teaching_form_sws="2SWS"),
        Module(id_=2, language=LanguageCode.DE, credit_points="5", teaching_form_sws="3SWS"),
        Module(id_=3, language=LanguageCode.DE, credit_points="10", teaching_form_sws="4SWS"),
    ]


@pytest.fixture
def mf():
    """Returns a ModulesFilter instance with an empty module list."""
    with patch("util.modules_filter.get_module_list", return_value=[]):
        yield ModulesFilter()


# --- CpFilter enum tests ---

class TestCpFilter:
    """Tests for the CpFilter enum."""

    @pytest.mark.parametrize("filter_val, expected_name, expected_value", [
        (CpFilter.LESS_THAN_5, "LESS_THAN_5", 0),
        (CpFilter.EQUALS_5, "EQUALS_5", 1),
        (CpFilter.GREATER_THAN_5, "GREATER_THAN_5", 2),
    ])
    def test_cp_filter_values(self, filter_val, expected_name, expected_value):
        assert filter_val.name == expected_name
        assert filter_val.value == expected_value

    def test_cp_filter_count(self):
        assert len(CpFilter) == 3

    def test_cp_filter_is_int_enum(self):
        for member in CpFilter:
            assert isinstance(member, int)


class TestSwsFilter:
    """Tests for the SwsFilter enum."""

    @pytest.mark.parametrize("filter_val, expected_name, expected_value", [
        (SwsFilter.LESS_THAN_3, "LESS_THAN_3", 0),
        (SwsFilter.EQUALS_3, "EQUALS_3", 1),
        (SwsFilter.GREATER_THAN_3, "GREATER_THAN_3", 2),
    ])
    def test_sws_filter_values(self, filter_val, expected_name, expected_value):
        assert filter_val.name == expected_name
        assert filter_val.value == expected_value

    def test_sws_filter_count(self):
        assert len(SwsFilter) == 3

    def test_sws_filter_is_int_enum(self):
        for member in SwsFilter:
            assert isinstance(member, int)


# --- ModulesFilter credit points filtering tests ---

class TestModulesFilterCpFiltering:
    """Tests for credit points filtering in ModulesFilter."""

    def test_cp_less_than_5(self, mf, filter_test_modules):
        result = mf.filter_cp(CpFilter.LESS_THAN_5, filter_test_modules)
        assert len(result) == 1
        assert result[0].id_ == 1

    def test_cp_equals_5(self, mf, filter_test_modules):
        result = mf.filter_cp(CpFilter.EQUALS_5, filter_test_modules)
        assert len(result) == 1
        assert result[0].id_ == 2

    def test_cp_greater_than_5(self, mf, filter_test_modules):
        result = mf.filter_cp(CpFilter.GREATER_THAN_5, filter_test_modules)
        assert len(result) == 1
        assert result[0].id_ == 3

    def test_cp_less_than_5_no_match(self, mf):
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5", teaching_form_sws="2SWS"),
            Module(id_=2, language=LanguageCode.DE, credit_points="10", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.LESS_THAN_5, modules)
        assert len(result) == 0

    def test_cp_greater_than_5_no_match(self, mf):
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="3", teaching_form_sws="2SWS"),
            Module(id_=2, language=LanguageCode.DE, credit_points="5", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.GREATER_THAN_5, modules)
        assert len(result) == 0

    def test_cp_non_numeric_string_not_removed(self, mf):
        """Module with non-numeric credit_points included when remove_invalid=False."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="N/A", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.LESS_THAN_5, modules)
        # When no digits found and remove_invalid is False, module is included
        assert len(result) == 1

    def test_cp_non_numeric_string_removed_when_remove_invalid(self):
        """Module with non-numeric credit_points excluded when remove_invalid=True."""
        with patch("util.modules_filter.get_module_list", return_value=[]):
            mf = ModulesFilter(remove_invalid=True)
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="N/A", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.LESS_THAN_5, modules)
        assert len(result) == 0

    def test_cp_empty_string_not_removed(self, mf):
        """Module with empty credit_points included when remove_invalid=False."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.EQUALS_5, modules)
        assert len(result) == 1

    def test_cp_empty_string_removed_when_remove_invalid(self):
        """Module with empty credit_points excluded when remove_invalid=True."""
        with patch("util.modules_filter.get_module_list", return_value=[]):
            mf = ModulesFilter(remove_invalid=True)
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.EQUALS_5, modules)
        assert len(result) == 0

    def test_cp_uses_module_list_when_no_modules_arg(self, mf):
        """When modules argument is None, filter_cp uses self.module_list."""
        mf.module_list = [
            Module(id_=1, language=LanguageCode.DE, credit_points="3", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.LESS_THAN_5)
        assert len(result) == 1
        assert result[0].id_ == 1

    def test_cp_boundary_exactly_5(self, mf):
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5", teaching_form_sws="2SWS"),
        ]
        lt5 = mf.filter_cp(CpFilter.LESS_THAN_5, modules)
        eq5 = mf.filter_cp(CpFilter.EQUALS_5, modules)
        gt5 = mf.filter_cp(CpFilter.GREATER_THAN_5, modules)
        assert len(lt5) == 0
        assert len(eq5) == 1
        assert len(gt5) == 0

    def test_cp_multiple_modules_same_cp(self, mf):
        modules = [
            Module(id_=i, language=LanguageCode.DE, credit_points="5", teaching_form_sws="2SWS")
            for i in range(5)
        ]
        result = mf.filter_cp(CpFilter.EQUALS_5, modules)
        assert len(result) == 5

    def test_cp_credit_points_with_spaces(self, mf):
        """Credit points like ' 3 ' should still parse correctly."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points=" 3 ", teaching_form_sws="2SWS"),
        ]
        result = mf.filter_cp(CpFilter.LESS_THAN_5, modules)
        assert len(result) == 1


# --- ModulesFilter SWS filtering tests ---

class TestModulesFilterSwsFiltering:
    """Tests for SWS (hours per week) filtering in ModulesFilter."""

    def test_sws_less_than_3(self, mf, filter_test_modules):
        result = mf.filter_sws(SwsFilter.LESS_THAN_3, filter_test_modules)
        assert len(result) == 1
        assert result[0].id_ == 1

    def test_sws_equals_3(self, mf, filter_test_modules):
        result = mf.filter_sws(SwsFilter.EQUALS_3, filter_test_modules)
        assert len(result) == 1
        assert result[0].id_ == 2

    def test_sws_greater_than_3(self, mf, filter_test_modules):
        result = mf.filter_sws(SwsFilter.GREATER_THAN_3, filter_test_modules)
        assert len(result) == 1
        assert result[0].id_ == 3

    def test_sws_complex_format(self, mf):
        """SWS value like 'Vorlesung (3 SWS)' should extract digits and SWS."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5",
                   teaching_form_sws="Vorlesung (3 SWS)"),
        ]
        # Parsing: the code uppercases and removes spaces: "VORLESUNG(3SWS)" -> finds "3SWS"
        result = mf.filter_sws(SwsFilter.EQUALS_3, modules)
        assert len(result) == 1

    def test_sws_multiple_entries_summed(self, mf):
        """SWS with multiple entries are summed up. '2SWS' + '2SWS' = 4 total."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5",
                   teaching_form_sws="Vorlesung (2 SWS)\nÜbung (2 SWS)"),
        ]
        # After parsing: finds "2SWS" + "2SWS" = sum 4 -> > 3
        result = mf.filter_sws(SwsFilter.GREATER_THAN_3, modules)
        assert len(result) == 1

    def test_sws_empty_string_not_removed(self, mf):
        """Empty SWS with remove_invalid=False should include the module."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5", teaching_form_sws=""),
        ]
        result = mf.filter_sws(SwsFilter.LESS_THAN_3, modules)
        assert len(result) == 1

    def test_sws_empty_string_removed_when_remove_invalid(self):
        """Empty SWS with remove_invalid=True should exclude the module."""
        with patch("util.modules_filter.get_module_list", return_value=[]):
            mf = ModulesFilter(remove_invalid=True)
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5", teaching_form_sws=""),
        ]
        result = mf.filter_sws(SwsFilter.LESS_THAN_3, modules)
        assert len(result) == 0

    def test_sws_no_number_in_string_not_removed(self, mf):
        """SWS with no parseable numbers and remove_invalid=False."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5",
                   teaching_form_sws="Vorlesung"),
        ]
        result = mf.filter_sws(SwsFilter.LESS_THAN_3, modules)
        assert len(result) == 1

    def test_sws_uses_module_list_when_no_modules_arg(self, mf):
        """When modules argument is None, filter_sws uses self.module_list."""
        mf.module_list = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5", teaching_form_sws="3SWS"),
        ]
        result = mf.filter_sws(SwsFilter.EQUALS_3)
        assert len(result) == 1


# --- Combined CP + SWS filtering tests ---

class TestModulesFilterCombinedFiltering:
    """Tests for chaining filter_cp and filter_sws sequentially."""

    def test_combined_cp_then_sws(self, mf, filter_test_modules):
        """Filter by CP first, then by SWS on the result."""
        cp_result = mf.filter_cp(CpFilter.EQUALS_5, filter_test_modules)
        sws_result = mf.filter_sws(SwsFilter.EQUALS_3, cp_result)
        assert len(sws_result) == 1
        assert sws_result[0].id_ == 2

    def test_combined_no_match(self, mf, filter_test_modules):
        """No module has CP > 5 AND SWS < 3."""
        cp_result = mf.filter_cp(CpFilter.GREATER_THAN_5, filter_test_modules)
        sws_result = mf.filter_sws(SwsFilter.LESS_THAN_3, cp_result)
        assert len(sws_result) == 0

    def test_combined_sws_then_cp(self, mf, filter_test_modules):
        """Filter by SWS first, then by CP."""
        sws_result = mf.filter_sws(SwsFilter.GREATER_THAN_3, filter_test_modules)
        cp_result = mf.filter_cp(CpFilter.GREATER_THAN_5, sws_result)
        assert len(cp_result) == 1
        assert cp_result[0].id_ == 3


# --- Edge case tests ---

class TestModulesFilterEdgeCases:
    """Tests for edge cases in ModulesFilter."""

    def test_empty_modules_list(self, mf):
        result = mf.filter_cp(CpFilter.EQUALS_5, [])
        assert result == []

    def test_filter_sws_empty_list(self, mf):
        result = mf.filter_sws(SwsFilter.EQUALS_3, [])
        assert result == []

    def test_single_module(self, mf):
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5", teaching_form_sws="3SWS"),
        ]
        result = mf.filter_cp(CpFilter.EQUALS_5, modules)
        assert len(result) == 1

    def test_modules_filter_init_calls_get_module_list(self):
        """ModulesFilter.__init__ should call get_module_list to fetch modules."""
        with patch("util.modules_filter.get_module_list") as mock_get_modules:
            mock_get_modules.return_value = []
            _mf = ModulesFilter()
            mock_get_modules.assert_called_once_with()

    def test_modules_filter_init_with_remove_invalid(self):
        """Test that remove_invalid flag is correctly set."""
        with patch("util.modules_filter.get_module_list", return_value=[]):
            mf_false = ModulesFilter(remove_invalid=False)
            mf_true = ModulesFilter(remove_invalid=True)
        assert mf_false.remove_invalid is False
        assert mf_true.remove_invalid is True

    def test_modules_with_boundary_cp_values(self, mf):
        """Test filtering with boundary values at exactly 5."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="4", teaching_form_sws="2SWS"),
            Module(id_=2, language=LanguageCode.DE, credit_points="5", teaching_form_sws="2SWS"),
            Module(id_=3, language=LanguageCode.DE, credit_points="6", teaching_form_sws="2SWS"),
        ]

        lt5 = mf.filter_cp(CpFilter.LESS_THAN_5, modules)
        eq5 = mf.filter_cp(CpFilter.EQUALS_5, modules)
        gt5 = mf.filter_cp(CpFilter.GREATER_THAN_5, modules)

        assert len(lt5) == 1 and lt5[0].id_ == 1
        assert len(eq5) == 1 and eq5[0].id_ == 2
        assert len(gt5) == 1 and gt5[0].id_ == 3

    def test_modules_with_boundary_sws_values(self, mf):
        """Test filtering with boundary values at exactly 3."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="5", teaching_form_sws="2SWS"),
            Module(id_=2, language=LanguageCode.DE, credit_points="5", teaching_form_sws="3SWS"),
            Module(id_=3, language=LanguageCode.DE, credit_points="5", teaching_form_sws="4SWS"),
        ]

        lt3 = mf.filter_sws(SwsFilter.LESS_THAN_3, modules)
        eq3 = mf.filter_sws(SwsFilter.EQUALS_3, modules)
        gt3 = mf.filter_sws(SwsFilter.GREATER_THAN_3, modules)

        assert len(lt3) == 1 and lt3[0].id_ == 1
        assert len(eq3) == 1 and eq3[0].id_ == 2
        assert len(gt3) == 1 and gt3[0].id_ == 3

    def test_filter_returns_new_list(self, mf, filter_test_modules):
        """Filter result should be a new list, not a reference to the input."""
        result = mf.filter_cp(CpFilter.EQUALS_5, filter_test_modules)
        assert result is not filter_test_modules

    def test_credit_points_with_multiple_numbers(self, mf):
        """Credit points string '3-5' has two numbers; 'any' check should match."""
        modules = [
            Module(id_=1, language=LanguageCode.DE, credit_points="3-5", teaching_form_sws="2SWS"),
        ]
        # "3-5" -> findall gives ["3", "5"]
        # LESS_THAN_5: any(int(n) < 5 for n in ["3", "5"]) -> True (3 < 5)
        lt5 = mf.filter_cp(CpFilter.LESS_THAN_5, modules)
        assert len(lt5) == 1
        # EQUALS_5: any(int(n) == 5 for n in ["3", "5"]) -> True (5 == 5)
        eq5 = mf.filter_cp(CpFilter.EQUALS_5, modules)
        assert len(eq5) == 1


# --- Semester position filter tests ---

class TestFilterSemesterPosition:
    """Tests for filter_semester_position.

    The position is a selection id and only the tables api knows its label, so the
    filter matches the rendered text. These tests stand in for that api.
    """

    @staticmethod
    def _modules():
        return [
            Module(id_=1, language=LanguageCode.DE, semester_position=0),
            Module(id_=2, language=LanguageCode.DE, semester_position=1),
            Module(id_=3, language=LanguageCode.DE, semester_position=2),
        ]

    @staticmethod
    def _labels(id_, key):
        assert key == "semesterlage"
        return {0: "Wintersemester", 1: "Sommersemester", 2: "jedes Semester"}[id_]

    def test_winter_only(self, mf):
        with patch("util.module.get_value_by_id", side_effect=self._labels):
            result = mf.filter_semester_position(["wint"], self._modules())
        assert [m.id_ for m in result] == [1]

    def test_summer_only(self, mf):
        with patch("util.module.get_value_by_id", side_effect=self._labels):
            result = mf.filter_semester_position(["somm"], self._modules())
        assert [m.id_ for m in result] == [2]

    def test_two_markers_match_both(self, mf):
        with patch("util.module.get_value_by_id", side_effect=self._labels):
            result = mf.filter_semester_position(["wint", "jede"], self._modules())
        assert [m.id_ for m in result] == [1, 3]

    def test_unknown_marker_matches_nothing(self, mf):
        with patch("util.module.get_value_by_id", side_effect=self._labels):
            result = mf.filter_semester_position(["gibtesnicht"], self._modules())
        assert result == []

    def test_uses_module_list_when_no_modules_arg(self, mf):
        mf.module_list = self._modules()
        with patch("util.module.get_value_by_id", side_effect=self._labels):
            result = mf.filter_semester_position(["somm"])
        assert [m.id_ for m in result] == [2]


# --- Exam type filter tests ---

class TestFilterExamType:
    """Tests for filter_exam_type, which searches the free text exam performance."""

    @staticmethod
    def _modules():
        return [
            Module(id_=1, language=LanguageCode.DE, study_exam_type="Klausur 90 min"),
            Module(id_=2, language=LanguageCode.DE, study_exam_type="mündliche Prüfung"),
            Module(id_=3, language=LanguageCode.DE, study_exam_type=""),
        ]

    def test_written_exam(self, mf):
        result = mf.filter_exam_type(["klausur", "written"], self._modules())
        assert [m.id_ for m in result] == [1]

    def test_oral_exam(self, mf):
        result = mf.filter_exam_type(["mündlich", "oral"], self._modules())
        assert [m.id_ for m in result] == [2]

    def test_empty_text_never_matches(self, mf):
        result = mf.filter_exam_type(["klausur"], self._modules())
        assert 3 not in [m.id_ for m in result]

    def test_match_is_case_insensitive(self, mf):
        modules = [Module(id_=1, language=LanguageCode.DE, study_exam_type="KLAUSUR")]
        result = mf.filter_exam_type(["klausur"], modules)
        assert len(result) == 1

    def test_no_markers_matches_nothing(self, mf):
        result = mf.filter_exam_type([], self._modules())
        assert result == []

    def test_uses_module_list_when_no_modules_arg(self, mf):
        mf.module_list = self._modules()
        result = mf.filter_exam_type(["klausur"])
        assert [m.id_ for m in result] == [1]
