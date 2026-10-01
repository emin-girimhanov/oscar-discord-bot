"""Comprehensive tests for the enums module (LanguageCode and StudyCourse)."""

import pytest
from util.enums import LanguageCode, StudyCourse


class TestLanguageCode:
    """Tests for the LanguageCode enum."""

    # --- from_language_code ---

    @pytest.mark.parametrize("code, expected", [
        ("de", LanguageCode.DE),
        ("en", LanguageCode.EN),
        ("DE", LanguageCode.DE),
        ("EN", LanguageCode.EN),
        ("De", LanguageCode.DE),
        ("En", LanguageCode.EN),
    ])
    def test_from_language_code_valid(self, code, expected):
        assert LanguageCode.from_language_code(code) == expected

    @pytest.mark.parametrize("invalid_code", [
        "fr", "", "es", "jp", "   ", "d", "e", "dee", "enn", "123",
    ])
    def test_from_language_code_invalid(self, invalid_code):
        with pytest.raises(KeyError):
            LanguageCode.from_language_code(invalid_code)

    # --- valid_languages ---

    def test_valid_languages_contents(self):
        valid = LanguageCode.valid_languages()
        assert "en" in valid
        assert "de" in valid
        assert len(valid) == 2

    def test_valid_languages_returns_list(self):
        valid = LanguageCode.valid_languages()
        assert isinstance(valid, list)

    def test_valid_languages_are_lowercase(self):
        for lang in LanguageCode.valid_languages():
            assert lang == lang.lower()

    # --- values ---

    def test_values_contents(self):
        values = LanguageCode.values()
        assert 0 in values
        assert 1 in values
        assert len(values) == 2

    def test_values_returns_list_of_ints(self):
        values = LanguageCode.values()
        assert isinstance(values, list)
        assert all(isinstance(v, int) for v in values)

    # --- name property ---

    @pytest.mark.parametrize("enum_member, expected_name, expected_value", [
        (LanguageCode.DE, "de", 1),
        (LanguageCode.EN, "en", 0),
    ])
    def test_enum_attributes(self, enum_member, expected_name, expected_value):
        assert enum_member.name == expected_name
        assert int(enum_member) == expected_value

    def test_name_is_always_lowercase(self):
        """The overridden name property must return lowercase."""
        for member in LanguageCode:
            assert member.name == member.name.lower()

    # --- IntEnum behavior ---

    def test_is_int_enum(self):
        assert isinstance(LanguageCode.DE, int)
        assert isinstance(LanguageCode.EN, int)

    def test_can_be_used_in_arithmetic(self):
        assert LanguageCode.DE + LanguageCode.EN == 1

    def test_equality_with_int(self):
        assert LanguageCode.EN == 0
        assert LanguageCode.DE == 1

    def test_comparison_with_int(self):
        assert LanguageCode.EN < LanguageCode.DE

    # --- iteration ---

    def test_iteration(self):
        members = list(LanguageCode)
        assert len(members) == 2
        assert LanguageCode.EN in members
        assert LanguageCode.DE in members


class TestStudyCourse:
    """Tests for the StudyCourse enum."""

    # --- from_str ---

    @pytest.mark.parametrize("course_str, expected", [
        ("BSC_INF", StudyCourse.BSC_INF),
        ("bsc_inf", StudyCourse.BSC_INF),
        ("Bsc_Inf", StudyCourse.BSC_INF),
        ("msc_dke", StudyCourse.MSC_DKE),
        ("MSC_DKE", StudyCourse.MSC_DKE),
        ("BSC_CV", StudyCourse.BSC_CV),
        ("BSC_INGINF", StudyCourse.BSC_INGINF),
        ("BSC_WIF", StudyCourse.BSC_WIF),
        ("BSC_INF_BILINGUAL", StudyCourse.BSC_INF_BILINGUAL),
        ("MSC_INF", StudyCourse.MSC_INF),
        ("MSC_INGINF", StudyCourse.MSC_INGINF),
        ("MSC_WIF", StudyCourse.MSC_WIF),
        ("MSC_DE", StudyCourse.MSC_DE),
        ("MSC_VC", StudyCourse.MSC_VC),
    ])
    def test_from_str_valid(self, course_str, expected):
        assert StudyCourse.from_str(course_str) == expected

    @pytest.mark.parametrize("invalid_str", [
        "INVALID_COURSE", "", "BSC", "MSC", "123", "bsc", "msc",
        "BSC_", "MSC_", "INF", "DKE", " BSC_INF", "BSC_INF ",
    ])
    def test_from_str_invalid(self, invalid_str):
        with pytest.raises(ValueError):
            StudyCourse.from_str(invalid_str)

    # --- values ---

    def test_values_count(self):
        values = StudyCourse.values()
        assert len(values) == 11

    def test_values_contains_all(self):
        values = StudyCourse.values()
        for member in StudyCourse:
            assert member.value in values

    def test_values_returns_list_of_ints(self):
        values = StudyCourse.values()
        assert isinstance(values, list)
        assert all(isinstance(v, int) for v in values)

    # --- course values ---

    @pytest.mark.parametrize("course, value", [
        (StudyCourse.BSC_INF, 0),
        (StudyCourse.BSC_CV, 1),
        (StudyCourse.BSC_INGINF, 2),
        (StudyCourse.BSC_WIF, 3),
        (StudyCourse.BSC_INF_BILINGUAL, 4),
        (StudyCourse.MSC_INF, 5),
        (StudyCourse.MSC_INGINF, 6),
        (StudyCourse.MSC_WIF, 7),
        (StudyCourse.MSC_DKE, 8),
        (StudyCourse.MSC_DE, 9),
        (StudyCourse.MSC_VC, 10),
    ])
    def test_course_values(self, course, value):
        assert course == value

    # --- IntEnum behavior ---

    def test_is_int_enum(self):
        for member in StudyCourse:
            assert isinstance(member, int)

    def test_iteration(self):
        members = list(StudyCourse)
        assert len(members) == 11

    def test_values_are_contiguous(self):
        """Verify course values go from 0 to 10 without gaps."""
        values = sorted(StudyCourse.values())
        assert values == list(range(11))
