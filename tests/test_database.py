"""Comprehensive tests for the database module using in-memory SQLite."""
# pylint: disable=redefined-outer-name, protected-access, import-outside-toplevel

from unittest.mock import patch
import pytest

from util.database import Database, get_database, get_user_language
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.module import Module


# --- Fixtures ---

@pytest.fixture
def db(tmp_path):
    """
    Ein Fixture bereitet eine Umgebung für den Test vor.
    'tmp_path' ist ein spezieller Order (bereitgestellt von pytest),
    der nach dem Test gelöscht wird.
    So bleibt deine echte Datenbank unberührt!
    """
    db_path = str(tmp_path / "test.db")
    return Database(db_path=db_path)


@pytest.fixture
def db_with_user(db): # pylint: disable=redefined-outer-name
    """Database with a pre-existing user."""
    db.set_preferences(user_id=12345)
    return db


@pytest.fixture
def db_with_module(db_with_user): # pylint: disable=redefined-outer-name
    """Database with a pre-existing user and module."""
    db_with_user.add_module(100, LanguageCode.DE, "Mathe I", "Math I")
    return db_with_user


# --- Database initialization and migration tests ---

class TestDatabaseInit:
    """Tests for Database initialization and migrations."""

    def test_init_creates_database(self, tmp_path):
        db_path = str(tmp_path / "new.db")
        db = Database(db_path=db_path)
        assert db.db_path == db_path

    def test_init_default_path(self):
        """Default path should be under util/database/oscar.db."""
        with patch("util.database.Path.mkdir"), \
             patch.object(Database, "_init_db"):
            db = Database()
            assert "oscar.db" in db.db_path

    def test_db_version_is_8(self, db):
        assert db.DB_VERSION == 8

    def test_migration_creates_tables(self, db):
        """All tables (users, preferences, modules, semester_plans, feedback,
        study_buddies, module_ratings, challenge_submissions) should exist."""

        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = {row["name"] for row in cursor.fetchall()}
        assert "users" in tables
        assert "preferences" in tables
        assert "modules" in tables
        assert "semester_plans" in tables
        assert "feedback" in tables
        assert "study_buddies" in tables
        assert "module_ratings" in tables
        assert "challenge_submissions" in tables

    def test_migration_creates_indexes(self, db):
        """Indexes for performance should exist."""
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
            )
            indexes = {row["name"] for row in cursor.fetchall()}
        assert "idx_preferences_user_id" in indexes
        assert "idx_semester_plans_user_id" in indexes
        assert "idx_semester_plans_module_id" in indexes
        assert "idx_feedback_user_id" in indexes
        assert "idx_study_buddies_module_id" in indexes
        assert "idx_module_ratings_module_id" in indexes
        assert "idx_challenge_submissions_cid_len" in indexes

    def test_user_version_is_set(self, db):
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
        assert version == db.DB_VERSION

    def test_reinit_does_not_fail(self, tmp_path):
        """Creating Database twice on same path should not error (no re-migration)."""
        db_path = str(tmp_path / "reuse.db")
        Database(db_path=db_path)
        Database(db_path=db_path)


# --- _check_user tests ---

class TestCheckUser:
    def test_creates_new_user(self, db):
        """
        Ein einfacher Test: Wir fügen einen User hinzu und schauen,
        ob er danach wirklich in der Tabelle steht.
        """
        # Aktion: Methode aufrufen
        db.set_preferences(user_id=99999)
        # Überprüfung: Schauen, ob die ID in der Datenbank existiert
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (99999,))
            # 'assert' prüft, ob die Bedingung wahr ist. Falls nicht, schlägt der Test fehl.
            assert cursor.fetchone() is not None

    def test_existing_user_not_duplicated(self, db):
        db.set_preferences(user_id=99999)
        db.set_preferences(user_id=99999)
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE id = ?", (99999,))
            assert cursor.fetchone()["cnt"] == 1


# --- Preferences tests ---

class TestPreferences:
    def test_set_and_get_preferences(self, db):
        db.set_preferences(
            user_id=111,
            language=LanguageCode.DE,
            semester=3,
            major="BSC_INF",
        )
        prefs = db.get_preferences(111)
        assert prefs is not None
        assert prefs["user_id"] == 111
        assert prefs["language"] == LanguageCode.DE
        assert prefs["semester"] == 3
        assert prefs["major"] == StudyCourse.BSC_INF

    def test_get_preferences_nonexistent_user(self, db):
        prefs = db.get_preferences(99999)
        assert prefs is None

    def test_set_preferences_update_language(self, db):
        db.set_preferences(user_id=111, language=LanguageCode.EN)
        db.set_preferences(user_id=111, language=LanguageCode.DE)
        prefs = db.get_preferences(111)
        assert prefs["language"] == LanguageCode.DE

    def test_set_preferences_update_semester(self, db):
        db.set_preferences(user_id=111, language=LanguageCode.EN, semester=1)
        db.set_preferences(user_id=111, semester=5)
        prefs = db.get_preferences(111)
        assert prefs["semester"] == 5

    def test_set_preferences_update_major(self, db):
        db.set_preferences(user_id=111, language=LanguageCode.EN, major="BSC_INF")
        db.set_preferences(user_id=111, major="MSC_DKE")
        prefs = db.get_preferences(111)
        assert prefs["major"] == StudyCourse.MSC_DKE

    def test_set_preferences_no_updates(self, db):
        """Calling set_preferences with no changes should not error."""
        db.set_preferences(user_id=111, language=LanguageCode.EN)
        db.set_preferences(user_id=111)  # no fields changed
        prefs = db.get_preferences(111)
        assert prefs is not None

    def test_preferences_default_language_en(self, db):
        """When language is None, default should be 'en'."""
        db.set_preferences(user_id=111)
        prefs = db.get_preferences(111)
        assert prefs is not None
        assert prefs["language"] == LanguageCode.EN

    def test_preferences_invalid_major(self, db):
        """Invalid major should be silently ignored in get_preferences."""
        db.set_preferences(user_id=111, language=LanguageCode.EN, major="INVALID")
        prefs = db.get_preferences(111)
        assert prefs is not None
        assert "major" not in prefs

    def test_preferences_none_semester(self, db):
        """When semester is None, it should not appear in prefs."""
        db.set_preferences(user_id=111, language=LanguageCode.EN)
        prefs = db.get_preferences(111)
        assert "semester" not in prefs


# --- get_users tests ---

class TestGetUsers:
    def test_get_users_empty(self, db):
        result = db.get_users()
        assert result is None

    def test_get_users_with_entries(self, db):
        db.set_preferences(user_id=111)
        db.set_preferences(user_id=222)
        result = db.get_users()
        assert result is not None
        assert 111 in result
        assert 222 in result


# --- add_module tests ---

class TestAddModule:
    def test_add_module_with_all_args(self, db):
        db.add_module(100, LanguageCode.DE, "Mathe I", "Math I")
        mod = db.get_module(100, LanguageCode.DE)
        assert mod is not None
        assert mod.id_ == 100

    def test_add_module_from_module_object(self, db):
        module = Module(
            id_=200,
            language=LanguageCode.EN,
            title="Informatik I",
            title_en="Computer Science I",
        )
        db.add_module(module)
        mod = db.get_module(200, LanguageCode.EN)
        assert mod is not None
        assert mod.id_ == 200

    def test_add_module_replace_existing(self, db):
        db.add_module(100, LanguageCode.DE, "Mathe I", "Math I")
        db.add_module(100, LanguageCode.DE, "Mathe I (updated)", "Math I (updated)")
        mod = db.get_module(100, LanguageCode.DE)
        assert mod is not None

    def test_add_module_from_id_fetches_from_tables(self, db):
        """Adding module by ID only should fetch it from tables API."""
        with patch("util.database.get_rows_from_view") as mock_view:
            mock_view.return_value = [
                {
                    "Identifizierung": 501,
                    "Modulsprache": LanguageCode.DE,
                    "Modultitel": "Testmodul",
                    "Modultitel (englisch)": "Test Module",
                },
            ]
            db.add_module(501)
            mod = db.get_module(501, LanguageCode.DE)
            assert mod is not None

    def test_add_module_invalid_args(self, db):
        with pytest.raises(TypeError):
            db.add_module()

    def test_add_module_too_many_args(self, db):
        with pytest.raises(TypeError):
            db.add_module(1, 2, 3, 4, 5)

    def test_add_module_kwargs_not_allowed(self, db):
        with pytest.raises(TypeError):
            db.add_module(module_id=100, language=LanguageCode.DE)

    def test_add_module_three_args(self, db):
        """Three args: module_id, language, title (no title_en)."""
        db.add_module(300, LanguageCode.DE, "Physik I")
        mod = db.get_module(300, LanguageCode.DE)
        assert mod is not None


# --- get_module tests ---

class TestGetModule:
    def test_get_module_found(self, db_with_module):
        mod = db_with_module.get_module(100, LanguageCode.DE)
        assert mod is not None
        assert mod.id_ == 100

    def test_get_module_not_found(self, db):
        mod = db.get_module(999, LanguageCode.DE)
        assert mod is None

    def test_get_module_fallback_language(self, db):
        """If module exists only in DE, requesting EN should return DE version."""
        db.add_module(100, LanguageCode.DE, "Mathe", "Math")
        mod = db.get_module(100, LanguageCode.EN)
        assert mod is not None
        assert mod.id_ == 100

    def test_get_module_exact_language_match(self, db):
        db.add_module(100, LanguageCode.DE, "Mathe DE", "Math DE")
        db.add_module(100, LanguageCode.EN, "Mathe EN", "Math EN")
        mod = db.get_module(100, LanguageCode.EN)
        assert mod is not None


# --- _check_module tests ---

class TestCheckModule:
    def test_check_module_exists(self, db_with_module):
        result = db_with_module._check_module(100, LanguageCode.DE) # pylint: disable=protected-access
        assert result is not None
        assert result[0] == 100

    def test_check_module_not_found(self, db):
        """Module not in DB and not in tables API should raise AssertionError."""
        with patch("util.database.get_rows_from_view", return_value=[]), \
             patch("util.database.Module.from_id", side_effect=IndexError):
            with pytest.raises(AssertionError):
                db._check_module(999, LanguageCode.DE) # pylint: disable=protected-access

    def test_a_module_the_view_lacks_comes_from_the_module_table(self, db):
        """ View 2018 holds 118 of the 292 modules. "Add to my plan" failed for the
            other 204, although every one of them has a card in `/module`.
        """
        known = Module(
            id_=120501,
            language=ModuleLanguage.EN,
            title="Decision Support Project",
            title_en="Decision Support Project",
        )
        with patch("util.database.get_rows_from_view", return_value=[]), \
             patch("util.database.Module.from_id", return_value=known) as from_id:
            db.add_to_semesterplan(12345, 120501)

        from_id.assert_called_once_with(120501)
        plan = db.get_semesterplan(12345)
        assert [module.id_ for module in plan] == [120501]

    def test_the_module_table_is_not_asked_when_the_view_knows(self, db):
        with patch("util.database.get_rows_from_view", return_value=[
            {
                "Identifizierung": 501,
                "Modulsprache": LanguageCode.DE,
                "Modultitel": "API Modul",
                "Modultitel (englisch)": "API Module",
            },
        ]), patch("util.database.Module.from_id") as from_id:
            db.add_module(501)

        from_id.assert_not_called()

    def test_a_module_without_an_english_title_can_be_saved(self, db):
        """An empty english title used to fail the same assertion as an unknown id."""
        with patch("util.database.get_rows_from_view", return_value=[
            {
                "Identifizierung": 502,
                "Modulsprache": LanguageCode.DE,
                "Modultitel": "Nur Deutsch",
                "Modultitel (englisch)": "",
            },
        ]):
            db.add_module(502)

        saved = db.get_module(502, LanguageCode.DE)
        assert saved is not None
        assert saved.get_title(LanguageCode.EN) == "Nur Deutsch"

    def test_check_module_fetches_from_api(self, db):
        """Module not in DB but available from API should be added."""
        with patch("util.database.get_rows_from_view") as mock_view:
            mock_view.return_value = [
                {
                    "Identifizierung": 501,
                    "Modulsprache": LanguageCode.DE,
                    "Modultitel": "API Modul",
                    "Modultitel (englisch)": "API Module",
                },
            ]
            result = db._check_module(501, LanguageCode.DE) # pylint: disable=protected-access
            assert result is not None

    def test_check_module_fallback_any_language(self, db):
        """Module in DB but different language should still return DE fallback."""
        db.add_module(100, LanguageCode.DE, "Mathe", "Math")
        # _check_module for EN calls add_module(100, EN) which queries the API.
        # The API returns no EN match, but the module data is found in any language (DE).
        with patch("util.database.get_rows_from_view", return_value=[
            {
                "Identifizierung": 100,
                "Modulsprache": LanguageCode.DE,
                "Modultitel": "Mathe",
                "Modultitel (englisch)": "Math",
            }
        ]):
            result = db._check_module(100, LanguageCode.EN) # pylint: disable=protected-access
            assert result is not None


# --- Semesterplan tests ---

class TestSemesterplan:
    def test_add_to_semesterplan(self, db_with_module):
        db_with_module.add_to_semesterplan(12345, 100, LanguageCode.DE)
        plan = db_with_module.get_semesterplan(12345)
        assert len(plan) == 1
        assert plan[0].id_ == 100

    def test_add_to_semesterplan_duplicate(self, db_with_module):
        db_with_module.add_to_semesterplan(12345, 100, LanguageCode.DE)
        db_with_module.add_to_semesterplan(12345, 100, LanguageCode.DE)
        plan = db_with_module.get_semesterplan(12345)
        assert len(plan) == 1

    def test_remove_from_semesterplan(self, db_with_module):
        db_with_module.add_to_semesterplan(12345, 100, LanguageCode.DE)
        db_with_module.remove_from_semesterplan(12345, 100)
        plan = db_with_module.get_semesterplan(12345)
        assert len(plan) == 0

    def test_get_semesterplan_empty(self, db_with_user):
        plan = db_with_user.get_semesterplan(12345)
        assert plan == []

    def test_semesterplan_multiple_modules(self, db_with_module):
        db_with_module.add_module(200, LanguageCode.DE, "Physik I", "Physics I")
        db_with_module.add_to_semesterplan(12345, 100, LanguageCode.DE)
        db_with_module.add_to_semesterplan(12345, 200, LanguageCode.DE)
        plan = db_with_module.get_semesterplan(12345)
        assert len(plan) == 2

    def test_add_to_semesterplan_unknown_module_raises(self, db_with_user):
        """Adding a module that doesn't exist should raise AssertionError."""
        with patch("util.database.get_rows_from_view", return_value=[]), \
             patch("util.database.Module.from_id", side_effect=IndexError):
            with pytest.raises(AssertionError):
                db_with_user.add_to_semesterplan(12345, 999)


# --- Feedback tests ---

class TestFeedback:
    def test_send_and_get_feedback(self, db):
        db.send_feedback(
            user_id=111,
            intuitiveness=4,
            discoverability=3,
            usefulness=4,
            improvements="Good",
            wishes="More features",
            bugs="None",
        )
        feedback = db.get_feedback()
        assert len(feedback) == 1
        assert feedback[0]["user_id"] == 111
        assert feedback[0]["intuitiveness"] == 4
        assert feedback[0]["discoverability"] == 3
        assert feedback[0]["usefulness"] == 4
        assert feedback[0]["improvements"] == "Good"

    def test_send_feedback_dict(self, db):
        fb_dict = {
            "user_id": 111,
            "intuitiveness": 3,
            "discoverability": 2,
            "usefulness": 1,
            "improvements": "Less bugs",
            "wishes": "Dark mode",
            "bugs": "Crash on start",
        }
        db.send_feedback_dict(fb_dict)
        feedback = db.get_feedback()
        assert len(feedback) == 1

    def test_send_feedback_minimal(self, db):
        """Send feedback with only required fields (no optional text)."""
        db.send_feedback(user_id=111, intuitiveness=1, discoverability=1, usefulness=1)
        feedback = db.get_feedback()
        assert len(feedback) == 1
        assert feedback[0]["improvements"] == ""

    def test_get_feedback_empty(self, db):
        feedback = db.get_feedback()
        assert feedback == []

    def test_get_feedback_sorted_by_time(self, db):
        db.send_feedback(user_id=111, intuitiveness=1, discoverability=1, usefulness=1)
        db.send_feedback(user_id=222, intuitiveness=2, discoverability=2, usefulness=2)
        feedback = db.get_feedback()
        assert len(feedback) == 2
        assert feedback[0]["timestamp"] <= feedback[1]["timestamp"]

    def test_delete_feedback(self, db):
        db.send_feedback(user_id=111, intuitiveness=1, discoverability=1, usefulness=1)
        feedback = db.get_feedback()
        assert len(feedback) == 1
        db.delete_feedback(feedback[0]["id"])
        assert db.get_feedback() == []

    def test_feedback_uses_user_language(self, db):
        """Feedback should store the user's preferred language."""
        db.set_preferences(user_id=111, language=LanguageCode.DE)
        db.send_feedback(user_id=111, intuitiveness=4, discoverability=4, usefulness=4)
        feedback = db.get_feedback()
        assert feedback[0]["language"] == "de"

    def test_feedback_default_language_en(self, db):
        """Without preferences, feedback language should default to 'en'."""
        db.send_feedback(user_id=999, intuitiveness=1, discoverability=1, usefulness=1)
        feedback = db.get_feedback()
        assert feedback[0]["language"] == "en"


# --- Singleton tests ---

class TestSingleton:
    def test_get_database_returns_same_instance(self):
        import util.database as db_module
        original = db_module._db_instance # pylint: disable=protected-access
        try:
            db_module._db_instance = None # pylint: disable=protected-access
            with patch("util.database.Database.__init__", return_value=None) as mock_init: # pylint: disable=protected-access
                db1 = get_database()
                db2 = get_database()
                assert db1 is db2
                mock_init.assert_called_once()
        finally:
            db_module._db_instance = original # pylint: disable=protected-access


# --- get_user_language tests ---

class TestGetUserLanguage:
    def test_get_user_language_with_prefs(self, db):
        import util.database as db_module
        original = db_module._db_instance # pylint: disable=protected-access
        try:
            db_module._db_instance = db # pylint: disable=protected-access
            db.set_preferences(user_id=111, language=LanguageCode.DE)
            lang = get_user_language(111)
            assert lang == LanguageCode.DE
        finally:
            db_module._db_instance = original # pylint: disable=protected-access

    def test_get_user_language_no_prefs(self, db):
        import util.database as db_module
        original = db_module._db_instance # pylint: disable=protected-access
        try:
            db_module._db_instance = db # pylint: disable=protected-access
            lang = get_user_language(99999)
            assert lang == LanguageCode.EN
        finally:
            db_module._db_instance = original # pylint: disable=protected-access


# --- Module ratings tests ---

class TestModuleRatings:
    def test_unrated_module_returns_zero_count(self, db):
        ratings = db.get_module_ratings(999)
        assert ratings["count"] == 0
        assert ratings["avg_rating"] is None
        assert ratings["avg_difficulty"] is None

    def test_rate_module_and_get_ratings(self, db):
        db.rate_module(user_id=1, module_id=100, rating=4, difficulty=3, comment="Good course")
        db.rate_module(user_id=2, module_id=100, rating=5, difficulty=4)

        ratings = db.get_module_ratings(100)
        assert ratings["count"] == 2
        assert ratings["avg_rating"] == 4.5
        assert ratings["avg_difficulty"] == 3.5

    def test_rate_module_updates_existing_rating(self, db):
        db.rate_module(user_id=1, module_id=100, rating=2, difficulty=5)
        db.rate_module(user_id=1, module_id=100, rating=5, difficulty=2, comment="Changed mind")

        ratings = db.get_module_ratings(100)
        assert ratings["count"] == 1
        assert ratings["avg_rating"] == 5.0
        assert ratings["avg_difficulty"] == 2.0

        user_rating = db.get_user_module_rating(user_id=1, module_id=100)
        assert user_rating is not None
        assert user_rating["rating"] == 5
        assert user_rating["difficulty"] == 2
        assert user_rating["comment"] == "Changed mind"

    def test_get_user_module_rating_none_when_unrated(self, db):
        assert db.get_user_module_rating(user_id=999, module_id=100) is None

    def test_invalid_rating_raises_value_error(self, db):
        with pytest.raises(ValueError):
            db.rate_module(user_id=1, module_id=100, rating=0, difficulty=3)
        with pytest.raises(ValueError):
            db.rate_module(user_id=1, module_id=100, rating=6, difficulty=3)

    def test_invalid_difficulty_raises_value_error(self, db):
        with pytest.raises(ValueError):
            db.rate_module(user_id=1, module_id=100, rating=3, difficulty=0)
        with pytest.raises(ValueError):
            db.rate_module(user_id=1, module_id=100, rating=3, difficulty=6)

    def test_get_module_comments(self, db):
        db.rate_module(user_id=1, module_id=200, rating=4, difficulty=2, comment="Helpful tutor")
        db.rate_module(user_id=2, module_id=200, rating=5, difficulty=3, comment="Loved the labs")
        db.rate_module(user_id=3, module_id=200, rating=3, difficulty=4, comment=None)

        comments = db.get_module_comments(200)
        assert len(comments) == 2
        comment_texts = {c["comment"] for c in comments}
        assert "Helpful tutor" in comment_texts
        assert "Loved the labs" in comment_texts


# --- Challenge Submissions tests ---

class TestChallengeSubmissions:
    def test_submit_new_solution(self, db):
        code = "print(1)"
        is_best, prev_len, new_len = db.submit_challenge_solution(
            user_id=1,
            challenge_id="fizzbuzz",
            language="python",
            code_snippet=code,
        )
        assert is_best is True
        assert prev_len == 0
        assert new_len == len(code.encode("utf-8"))

        sub = db.get_user_challenge_submission(1, "fizzbuzz")
        assert sub is not None
        assert sub["language"] == "python"
        assert sub["code_length"] == new_len
        assert sub["code_snippet"] == code

    def test_submit_strips_markdown_codeblocks(self, db):
        raw_code = "```python\nfor i in range(10): print(i)\n```"
        expected = "for i in range(10): print(i)"
        is_best, _prev_len, new_len = db.submit_challenge_solution(
            user_id=1,
            challenge_id="primes",
            language="python",
            code_snippet=raw_code,
        )
        assert is_best is True
        assert new_len == len(expected.encode("utf-8"))
        sub = db.get_user_challenge_submission(1, "primes")
        assert sub is not None
        assert sub["code_snippet"] == expected

    def test_submit_better_and_worse_scores(self, db):
        longer_code = "def f(): return 42"
        db.submit_challenge_solution(
            user_id=1, challenge_id="calc", language="python", code_snippet=longer_code
        )
        sub1 = db.get_user_challenge_submission(1, "calc")
        assert sub1 is not None
        len1 = sub1["code_length"]

        # Shorter code improves
        shorter_code = "lambda: 42"
        is_best, prev_len, new_len = db.submit_challenge_solution(
            user_id=1, challenge_id="calc", language="python", code_snippet=shorter_code
        )
        assert is_best is True
        assert prev_len == len1
        assert new_len < len1

        # Worse code is rejected as new best
        worse_code = "def calculation_of_number(): return 42"
        is_best_worse, p_len, w_len = db.submit_challenge_solution(
            user_id=1, challenge_id="calc", language="python", code_snippet=worse_code
        )
        assert is_best_worse is False
        assert p_len == new_len
        assert w_len > new_len
        # Stored submission remains the shorter one
        sub_after = db.get_user_challenge_submission(1, "calc")
        assert sub_after is not None
        assert sub_after["code_length"] == new_len

    def test_leaderboard_ordering_and_ranks(self, db):
        db.submit_challenge_solution(1, "golf1", "python", "x = 10; print(x)")  # 17 bytes
        db.submit_challenge_solution(2, "golf1", "python", "p=1")              # 3 bytes
        db.submit_challenge_solution(3, "golf1", "python", "print(1)")         # 8 bytes

        lb = db.get_challenge_leaderboard("golf1", limit=10)
        assert len(lb) == 3
        assert lb[0]["user_id"] == 2
        assert lb[0]["rank"] == 1
        assert lb[0]["code_length"] == 3

        assert lb[1]["user_id"] == 3
        assert lb[1]["rank"] == 2
        assert lb[1]["code_length"] == 8

        assert lb[2]["user_id"] == 1
        assert lb[2]["rank"] == 3
        assert lb[2]["code_length"] == 16

    def test_get_user_challenge_submissions_list(self, db):
        db.submit_challenge_solution(1, "c1", "python", "a=1")
        db.submit_challenge_solution(1, "c2", "js", "b=2")
        subs = db.get_user_challenge_submissions(1)
        assert len(subs) == 2
        cids = {s["challenge_id"] for s in subs}
        assert cids == {"c1", "c2"}

    def test_export_and_delete_user_data_includes_challenges(self, db):
        db.submit_challenge_solution(1, "c1", "python", "a=1")
        export = db.export_user_data(1)
        assert "challenge_submissions" in export
        assert len(export["challenge_submissions"]) == 1
        assert export["challenge_submissions"][0]["challenge_id"] == "c1"

        removed = db.delete_user_data(1)
        assert removed.get("challenge_submissions") == 1
        assert db.get_user_challenge_submission(1, "c1") is None
