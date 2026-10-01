"""The Tables API sends a column as null, and `dict.get` does not treat that as missing.

`Module.from_tables_dict` reads every field with `data.get(key, default)`. That default
only applies when the **key** is absent. The api sends the key with a null value
instead, and 15 of the 410 rows have `Fachsemester: null`.

So `Module._academic_semester`, typed `int`, held `None`. `/suggest` scores every
module in the catalogue and compares that field against the student's semester:

    TypeError: '>' not supported between instances of 'NoneType' and 'int'

The whole command died on the first of those 15 modules it reached. The student saw
"the application did not respond".

`without_nulls` drops the null columns before the row is read, so every default below
behaves the way it promises. These tests fail if a null ever reaches a field again.
"""

import pytest

from util.enums import ModuleLanguage, StudyCourse
from util.module import Module, without_nulls
from util.suggestions import UserContext, _score_single_module


# One row in the shape the api returns it, with the columns that came back null.
ROW_WITH_NULLS: dict = {
    "Identifizierung": 120282,
    "Modulsprache": ModuleLanguage.EN.value,
    "Modultitel": "Selected Chapters of IT Security 1",
    "Fachsemester": None,
    "Semesterlage": None,
    "Dauer": None,
    "Niveau": None,
    "Credit Points": "5",
    "Inhalt": "Security topics.",
}


class TestWithoutNulls:
    """The one line that makes every default below it true."""

    def test_a_null_column_is_dropped(self):
        assert "Fachsemester" not in without_nulls(ROW_WITH_NULLS)

    def test_everything_else_survives(self):
        cleaned = without_nulls(ROW_WITH_NULLS)
        assert cleaned["Identifizierung"] == 120282
        assert cleaned["Credit Points"] == "5"

    def test_an_empty_string_is_not_a_null(self):
        """Only `None` goes. An empty title is still a title the api sent."""
        assert without_nulls({"Modultitel": ""}) == {"Modultitel": ""}

    def test_a_zero_is_not_a_null(self):
        assert without_nulls({"Status": 0}) == {"Status": 0}

    def test_an_empty_row_stays_empty(self):
        assert without_nulls({}) == {}


class TestAModuleBuiltFromNulls:
    """What the 15 rows produce now."""

    @pytest.fixture(name="module")
    def module_fixture(self) -> Module:
        return Module.from_tables_dict(ROW_WITH_NULLS)  # pyright: ignore[reportArgumentType]

    def test_it_builds_at_all(self, module: Module):
        assert module.id_ == 120282

    @pytest.mark.parametrize(
        "attribute",
        ["_academic_semester", "_semester_position", "_duration"],
    )
    def test_the_number_fields_are_numbers(self, module: Module, attribute: str):
        assert isinstance(getattr(module, attribute), int)

    def test_the_missing_number_falls_back_to_the_default(self, module: Module):
        assert module._academic_semester == -1  # pylint: disable=protected-access

    def test_the_list_field_is_a_list(self, module: Module):
        assert module.get_level() == []

    def test_the_title_still_arrives(self, module: Module):
        assert "Selected Chapters" in module.get_title()


class TestScoringSurvivesIt:
    """The crash itself, reproduced."""

    CONTEXT = UserContext(saved_ids=set(), major=StudyCourse.BSC_WIF, semester=5)

    def test_a_module_from_a_null_row_can_be_scored(self):
        module = Module.from_tables_dict(ROW_WITH_NULLS)  # pyright: ignore[reportArgumentType]
        _score_single_module(module, "ALL", self.CONTEXT)

    def test_a_module_whose_semester_is_none_can_be_scored(self):
        """A caller may build its own modules and hand them in."""
        module = Module(id_=1, language=ModuleLanguage.DE, title="Test", credit_points="5")
        module._academic_semester = None  # pyright: ignore[reportAttributeAccessIssue]  # pylint: disable=protected-access
        _score_single_module(module, "ALL", self.CONTEXT)

    def test_a_real_semester_still_scores_higher(self):
        """The guard must not switch the matching off."""
        matching = Module(
            id_=1, language=ModuleLanguage.DE, title="Test",
            credit_points="5", academic_semester=5,
        )
        without = Module(
            id_=2, language=ModuleLanguage.DE, title="Test",
            credit_points="5", academic_semester=-1,
        )
        better = _score_single_module(matching, "ALL", self.CONTEXT)
        plain = _score_single_module(without, "ALL", self.CONTEXT)
        assert better is not None and plain is not None
        assert better.score > plain.score
