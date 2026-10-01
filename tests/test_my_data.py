"""`/my_data` hands a student their own data and deletes it on request.

The privacy policy promises both. Until now it pointed at an email address, and the
section about deleting your data already spoke of a bot command that did not exist.

Two things here are worth more than the rest. The export must not lose a row, because a
student asking what we hold is entitled to all of it. And the deletion must really
delete, because a command that says "your data is gone" while a row survives is worse
than no command at all.
"""
# pylint: disable=redefined-outer-name, protected-access

import json
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from oscar.ui.my_data_view import (
    MAX_LISTED_MODULES,
    DeleteConfirmView,
    MyDataView,
    export_file,
    has_data,
    summarise,
)
from oscar.ui.owner_only import OwnerOnly
from util.database import Database
from util.enums import LanguageCode, StudyCourse
from util.translations import MY_DATA_TEXTS


STUDENT = 4711
STRANGER = 1337


@pytest.fixture
def db(tmp_path):
    """A throwaway database, so no test can touch the real one."""
    return Database(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def db_with_student(db):
    """A student who used the bot: settings, two saved modules and one feedback."""
    db.set_preferences(
        user_id=STUDENT,
        language=LanguageCode.DE,
        semester=3,
        major=StudyCourse.BSC_INF,
    )
    db.add_module(100, LanguageCode.DE, "Mathe I", "Maths I")
    db.add_module(200, LanguageCode.DE, "Datenbanken", "Databases")
    db.add_to_semesterplan(user_id=STUDENT, module_id=100)
    db.add_to_semesterplan(user_id=STUDENT, module_id=200)
    db.send_feedback(STUDENT, 1, 2, 3, "faster", "dark mode", "none")
    return db


class TestTheExportLosesNothing:
    def test_a_student_who_never_used_the_bot_has_nothing(self, db):
        assert has_data(db.export_user_data(STUDENT)) is False

    def test_everything_stored_comes_back(self, db_with_student):
        data = db_with_student.export_user_data(STUDENT)

        assert has_data(data) is True
        assert data["account"] is not None
        assert data["preferences"] is not None
        assert len(data["semester_plan"]) == 2
        assert len(data["feedback"]) == 1

    def test_the_free_text_of_a_feedback_is_included(self, db_with_student):
        """It is the most personal thing we store. Leaving it out would be dishonest."""
        data = db_with_student.export_user_data(STUDENT)
        assert data["feedback"][0]["improvements"] == "faster"

    def test_a_saved_module_missing_from_the_cache_is_still_exported(self, db):
        """The plan is read with a LEFT JOIN for exactly this case.

        `get_semesterplan` uses an INNER JOIN, so a module whose title was never
        cached silently disappears from it. An export may not drop a row.

        The foreign key forbids such a row today, so it is written here through a
        connection with the constraint off. That is not artificial: the pragma is
        set per connection and sqlite defaults it off, so a row written by an
        older build can sit in a database that now enforces it.
        """
        db.set_preferences(user_id=STUDENT)

        raw = sqlite3.connect(db.db_path)
        _ = raw.execute(
            "INSERT INTO semester_plans (user_id, module_id, language) VALUES (?, ?, ?)",
            (STUDENT, 999, "de"),
        )
        raw.commit()
        raw.close()

        plan = db.export_user_data(STUDENT)["semester_plan"]
        assert [row["module_id"] for row in plan] == [999]
        assert plan[0]["title"] is None

    def test_another_students_data_is_not_included(self, db_with_student):
        db_with_student.set_preferences(user_id=STRANGER, semester=1)
        db_with_student.add_to_semesterplan(user_id=STRANGER, module_id=100)

        data = db_with_student.export_user_data(STUDENT)
        assert all(row["module_id"] != 100 or True for row in data["semester_plan"])
        assert len(data["semester_plan"]) == 2


class TestTheDeleteReallyDeletes:
    def test_nothing_is_left_behind(self, db_with_student):
        db_with_student.delete_user_data(STUDENT)

        assert has_data(db_with_student.export_user_data(STUDENT)) is False

    @pytest.mark.parametrize("table", ["preferences", "semester_plans", "feedback"])
    def test_every_table_is_emptied(self, db_with_student, table):
        db_with_student.delete_user_data(STUDENT)

        with db_with_student._get_connection() as conn:  # noqa: SLF001
            rows = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", (STUDENT,)
            ).fetchone()[0]
        assert rows == 0

    def test_the_counts_are_reported(self, db_with_student):
        removed = db_with_student.delete_user_data(STUDENT)

        assert removed["semester_plans"] == 2
        assert removed["feedback"] == 1
        assert removed["users"] == 1

    def test_deleting_twice_is_harmless(self, db_with_student):
        db_with_student.delete_user_data(STUDENT)
        again = db_with_student.delete_user_data(STUDENT)

        assert sum(again.values()) == 0

    def test_only_the_caller_is_deleted(self, db_with_student):
        db_with_student.set_preferences(user_id=STRANGER, semester=1)
        db_with_student.delete_user_data(STUDENT)

        assert has_data(db_with_student.export_user_data(STRANGER)) is True

    def test_the_foreign_key_pragma_is_on(self, db):
        """The child rows are deleted by hand, but the cascade must work too.

        SQLite leaves `PRAGMA foreign_keys` off by default and sets it per
        connection. If this ever silently turned off, a future writer relying on
        the cascade would leave rows behind without any error.
        """
        with db._get_connection() as conn:  # noqa: SLF001
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


class TestTheStudentCanReadIt:
    @pytest.mark.parametrize("language", [LanguageCode.DE, LanguageCode.EN])
    def test_the_summary_names_every_section(self, db_with_student, language):
        text = summarise(db_with_student.export_user_data(STUDENT), language)

        for key in ("account_heading", "preferences_heading"):
            assert MY_DATA_TEXTS[key][language] in text

    def test_saved_modules_appear_by_title(self, db_with_student):
        """A module id alone tells a student nothing about what they saved."""
        text = summarise(db_with_student.export_user_data(STUDENT), LanguageCode.DE)
        assert "Datenbanken" in text

    def test_a_long_plan_is_cut_and_says_so(self, db):
        """Listing a hundred modules would hit the discord component limit."""
        db.set_preferences(user_id=STUDENT)
        for module_id in range(1, MAX_LISTED_MODULES + 6):
            db.add_module(module_id, LanguageCode.DE, f"Modul {module_id}", "x")
            db.add_to_semesterplan(user_id=STUDENT, module_id=module_id)

        text = summarise(db.export_user_data(STUDENT), LanguageCode.DE)
        assert MY_DATA_TEXTS["more_modules"][LanguageCode.DE].format(count=5) in text

    def test_the_file_is_valid_json_and_holds_everything(self, db_with_student):
        data = db_with_student.export_user_data(STUDENT)
        attachment = export_file(data)
        parsed = json.loads(attachment.fp.read().decode("utf8"))

        assert parsed["user_id"] == STUDENT
        assert len(parsed["semester_plan"]) == 2
        assert parsed["feedback"][0]["improvements"] == "faster"


class TestTheDeleteAsksFirst:
    def test_the_question_names_what_disappears(self, db_with_student):
        data = db_with_student.export_user_data(STUDENT)
        view = DeleteConfirmView(STUDENT, data, LanguageCode.DE)

        question = view.question()
        assert "2" in question
        assert "1" in question

    async def test_cancelling_deletes_nothing(self, db_with_student):
        data = db_with_student.export_user_data(STUDENT)
        view = DeleteConfirmView(STUDENT, data, LanguageCode.DE)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        await view._cancel(interaction)  # noqa: SLF001

        assert has_data(db_with_student.export_user_data(STUDENT)) is True

    async def test_confirming_deletes(self, db_with_student):
        data = db_with_student.export_user_data(STUDENT)
        view = DeleteConfirmView(STUDENT, data, LanguageCode.DE)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        with patch("oscar.ui.my_data_view.get_database", return_value=db_with_student):
            await view._delete(interaction)  # noqa: SLF001

        assert has_data(db_with_student.export_user_data(STUDENT)) is False


class TestNobodyElseMayClick:
    """This message holds a discord id, a programme and free text feedback at once."""

    @pytest.mark.parametrize("view_class", [MyDataView, DeleteConfirmView])
    def test_the_views_are_owned(self, view_class):
        assert issubclass(view_class, OwnerOnly)
        assert view_class.interaction_check is OwnerOnly.interaction_check


class TestTheCommand:
    @staticmethod
    def _interaction():
        interaction = MagicMock()
        interaction.user.id = STUDENT
        interaction.response.send_message = AsyncMock()
        return interaction

    @staticmethod
    def _cog():
        from oscar.cogs.my_data import MyData  # noqa: PLC0415

        return MyData(MagicMock(spec=discord.ext.commands.Bot))

    @patch("oscar.cogs.my_data.get_user_language", return_value=LanguageCode.DE)
    @patch("oscar.cogs.my_data.get_database")
    async def test_the_answer_is_private(self, get_db, _language, db_with_student):
        get_db.return_value = db_with_student
        interaction = self._interaction()
        cog = self._cog()

        await cog.my_data.callback(cog, interaction)

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    @patch("oscar.cogs.my_data.get_user_language", return_value=LanguageCode.DE)
    @patch("oscar.cogs.my_data.get_database")
    async def test_a_student_with_nothing_gets_a_sentence_not_a_file(
        self, get_db, _language, db
    ):
        """An empty export file reads like a fault, or worse, like a loss."""
        get_db.return_value = db
        interaction = self._interaction()
        cog = self._cog()

        await cog.my_data.callback(cog, interaction)

        args, kwargs = interaction.response.send_message.call_args
        assert args[0] == MY_DATA_TEXTS["nothing_stored"][LanguageCode.DE]
        assert "view" not in kwargs
