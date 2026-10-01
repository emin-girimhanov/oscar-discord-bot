""" This module contains the communication logic with the sqlite database.

    It's used for storing persistent data.
"""
# pylint: disable=too-many-lines


import os
import sqlite3
from sqlite3 import Connection, Cursor
import time

from contextlib import contextmanager
from typing import Any, overload
from pathlib import Path
from loguru import logger


from util.module import Module
from util.tables import get_rows_from_view
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.typed_dicts import (
    ChallengeSubmissionDict,
    CohortStatsDict,
    FeedbackReviewDict,
    FeedbackDict,
    LeaderboardEntryDict,
    MajorDistDict,
    ModuleRatingDict,
    PrefsDict,
    TopModuleDict,
    UserDataDict,
)



def _from_module_table(module_id: int) -> tuple[str | None, str | None, str | None]:
    """ Looks a module up in the module table, for the ones view 2018 does not hold.

        View 2018 holds 118 rows, the module table 292. Every module the view lacks
        ended in an assertion, so "add to my plan" failed for 204 of the 292 modules a
        student can open. The module table is what `/module` reads, so whatever has a
        card can be saved as well. It is kept warm, this costs no request.

        Parameters:
            module_id: The module number.

        Returns:
            The language, the german and the english title, or three times `None`
            when the module table does not know the number either.
    """
    try:
        known: Module = Module.from_id(module_id)
    except IndexError:
        return None, None, None

    return (
        ModuleLanguage(known.language).name,
        known.get_title(LanguageCode.DE),
        known.get_title(LanguageCode.EN),
    )


def _catalogue_entry(
    module_id: int, language: str
) -> tuple[str | None, str | None, str | None]:
    """ Finds the language and the titles of a module that is only known by its number.

        View 2018 is asked first. A row in the requested language wins, any other row
        of the module is second best. `_from_module_table` covers what the view lacks.

        Parameters:
            module_id: The module number.
            language: The language the caller would like, as a lowercase code.

        Returns:
            The language, the german and the english title. Three times `None` when
            nobody knows the module. A module without an english title is still a
            module, so the german title stands in for it.
    """
    found: tuple[str | None, str | None, str | None] = (None, None, None)
    modules_view: list[dict[str, str | int | list[int]]] = get_rows_from_view(2018)
    for module in modules_view:
        if module["Identifizierung"] != module_id:
            continue
        found = (
            ModuleLanguage(module.get("Modulsprache", 1)).name,
            str(module.get("Modultitel", "")),
            str(module.get("Modultitel (englisch)", "")),
        )
        if module["Modulsprache"] == ModuleLanguage.from_language_code(language):
            break

    if not (found[0] and found[1]):
        found = _from_module_table(module_id)

    return found[0], found[1], found[2] or found[1]


# pylint: disable=too-many-public-methods
class Database():
    """ Class for handling database operations.

        Version: `8`
    """

    # The database version should be incremented when the schema changes
    # and migration steps are added to the `_migrate_db` method.
    DB_VERSION: int = 8

    db_path: str


    def __init__(self, db_path: str|None = None):
        """ Initialize database connection.

            Parameters:
                db_path: Path to database file. Defaults to `OSCAR_DB_PATH`,
                    then ./database/oscar.db
        """
        if db_path is None:
            # the container points this at its /database volume, so data survives image updates
            db_path = os.environ.get("OSCAR_DB_PATH")
            if db_path:
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        if not db_path:
            logger.debug("Missing a DB path")
            db_dir: Path = Path(__file__).parent / "database"
            logger.debug(f"Choosing DB dirctory as '{db_dir}'")
            logger.info("Ensuring the folder exists")
            db_dir.mkdir(exist_ok=True)
            logger.success(f"'{db_dir}' should now exist")
            db_path = str(db_dir / "oscar.db")
        logger.success(f"DB path has been set to '{db_path}'")

        self.db_path = str(db_path)
        self._init_db()


    @contextmanager
    def _get_connection(self):
        """ Context manager for database connections."""
        logger.debug(f"Opening DB connection to '{self.db_path}'")
        conn: Connection = sqlite3.connect(self.db_path, timeout=10.0)
        # Ensures foreign key constraints are enforced
        _ = conn.execute("PRAGMA foreign_keys = ON")
        _ = conn.execute("PRAGMA busy_timeout = 10000")
        _ = conn.execute("PRAGMA synchronous = NORMAL")
        _ = conn.execute("PRAGMA cache_size = -64000")
        _ = conn.execute("PRAGMA temp_store = MEMORY")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            logger.debug(f"Closed DB connection to {self.db_path}")

    def _init_db(self):
        """ Handles database creation or migration if
            [`PRAGMA schema.user_version`](https://www.sqlite.org/pragma.html#pragma_user_version)
            is outdated.
        """
        # pylint: disable=too-many-statements

        with self._get_connection() as conn:
            _ = conn.execute("PRAGMA journal_mode = WAL")
            cursor: Cursor = conn.cursor()
            _ = cursor.execute("PRAGMA user_version")
            version: int = cursor.fetchone()[0]  # pyright: ignore[reportAny]

            logger.debug(f"Current DB user_version={version}, target DB_VERSION={self.DB_VERSION}")

            if not version < self.DB_VERSION:
                return

            logger.warning(
                f"Database version {version} is outdated. Migrating to {self.DB_VERSION}..."
            )

            # Migration v1 - Initial db setup
            # - added preferences and users table
            if version < 1:
                logger.info("Applying migration for version 1 ...")

                # -------------------  CREATE TABLE users  --------------------
                _ = cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id   INTEGER PRIMARY KEY,
                        name TEXT
                    )
                """)

                # ----------------  CREATE TABLE preferences  -----------------
                _ = cursor.execute("""
                    CREATE TABLE IF NOT EXISTS preferences (
                        user_id  INTEGER,
                        language TEXT    DEFAULT 'en',
                        semester INTEGER,
                        major    TEXT,

                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )
                """)

            # Migration v2
            # - updated preferences and users table.
            # - added modules and semesterplans table
            if version < 2:
                logger.info("Applying migration for version 2 ...")

                # --------------------  ALTER TABLE users  --------------------
                _ = cursor.execute("ALTER TABLE users RENAME TO users_old")
                _ = cursor.execute("""
                    CREATE TABLE users (
                        id   INTEGER PRIMARY KEY,
                        name TEXT
                    )
                """)
                _ = cursor.execute("""
                    INSERT INTO users(id, name)
                    SELECT * FROM users_old
                """)

                # -----------------  ALTER TABLE preferences  -----------------
                _ = cursor.execute("ALTER TABLE preferences RENAME TO preferences_old")
                _ = cursor.execute("""
                    CREATE TABLE preferences (
                        user_id  INTEGER,
                        language VARCHAR(2) DEFAULT 'en',
                        semester INTEGER,
                        major    TEXT,

                        FOREIGN KEY(user_id) REFERENCES users(id)
                            ON DELETE CASCADE,

                        CONSTRAINT valid_language CHECK(language IN ('de', 'en'))
                    )
                """)
                _ = cursor.execute("""
                    INSERT INTO preferences(user_id, language, semester, major)
                    SELECT * FROM preferences_old
                """)

                # -----------------------  DROP TABLES ------------------------
                _ = cursor.execute("DROP TABLE preferences_old")
                _ = cursor.execute("DROP TABLE users_old")

                # ------------------  CREATE TABLE modules  -------------------
                _ = cursor.execute("""
                    CREATE TABLE modules (
                        id       INTEGER,
                        language VARCHAR(2) DEFAULT 'de',
                        title    TEXT,
                        title_en TEXT,

                        PRIMARY KEY(id, language),

                        CONSTRAINT valid_language CHECK(language IN ('de', 'en'))
                    )
                """)

                # ---------------  CREATE TABLE semester_plans  ---------------
                _ = cursor.execute("""
                    CREATE TABLE semester_plans (
                        user_id   INTEGER,
                        module_id INTEGER,
                        language  VARCHAR(2) DEFAULT 'de',

                        UNIQUE(user_id, module_id),

                        FOREIGN KEY(user_id) REFERENCES users(id)
                            ON DELETE CASCADE,

                        FOREIGN KEY(module_id, language) REFERENCES modules(id, language)
                            ON DELETE CASCADE
                    )
                """)

            # Migration v3
            # - added feedback table
            if version < 3:
                logger.info("Applying migration for version 3 ...")

                # -------------------  CREATE TABLE feedback  -------------------
                _ = cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        language VARCHAR(2) DEFAULT 'en',
                        time INTEGER ,

                        intuitiveness INTEGER,
                        discoverability INTEGER,
                        usefulness INTEGER,

                        improvements TEXT,
                        wishes TEXT,
                        bugs TEXT,

                        FOREIGN KEY(user_id) REFERENCES users(id)
                            ON DELETE CASCADE,

                        CHECK(intuitiveness >= 1 AND
                              intuitiveness <= 4)
                        CHECK(discoverability >= 1 AND
                              discoverability <= 4)
                        CHECK(usefulness >= 1 AND
                              usefulness <= 4)
                    )
                """)
                # wie intuitiv die bedienung von 1-4
                # wie gut lassen sich module finden und planen 1-4
                # wie sinvoll sind die Informationen die wir liefern 1-4
                # was verbessert werden muss
                # was man sich noch wünscht
                # feld für gefundene bugs

            # Migration v4
            # - add spo and is wintersemester columns to preferences table
            if version < 4:
                logger.info("Applying migration for version 4 ...")

                # -------------------  CREATE TABLE feedback  -------------------
                _ = cursor.execute("ALTER TABLE preferences ADD spo INTEGER;")
                _ = cursor.execute("ALTER TABLE preferences ADD winter_semester INTEGER;")
                # winter semester should be a boolean (e.g. 0 or 1)

            # Migration v5
            # - add study_buddies table for opt-in study group matching
            if version < 5:
                logger.info("Applying migration for version 5 ...")

                _ = cursor.execute("""
                    CREATE TABLE IF NOT EXISTS study_buddies (
                        user_id INTEGER,
                        module_id INTEGER,
                        time INTEGER,

                        PRIMARY KEY(user_id, module_id),

                        FOREIGN KEY(user_id) REFERENCES users(id)
                            ON DELETE CASCADE
                    )
                """)

            # Migration v6
            # - add module_ratings table for student module evaluations and difficulty
            if version < 6:
                logger.info("Applying migration for version 6 ...")

                _ = cursor.execute("""
                    CREATE TABLE IF NOT EXISTS module_ratings (
                        user_id INTEGER,
                        module_id INTEGER,
                        rating INTEGER,
                        difficulty INTEGER,
                        comment TEXT,
                        timestamp INTEGER,

                        PRIMARY KEY(user_id, module_id),

                        FOREIGN KEY(user_id) REFERENCES users(id)
                            ON DELETE CASCADE,

                        CHECK(rating >= 1 AND rating <= 5),
                        CHECK(difficulty >= 1 AND difficulty <= 5)
                    )
                """)

            # Migration v7
            # - add challenge_submissions table for weekly code golf challenges
            if version < 7:
                logger.info("Applying migration for version 7 ...")

                _ = cursor.execute("""
                    CREATE TABLE IF NOT EXISTS challenge_submissions (
                        user_id INTEGER NOT NULL,
                        challenge_id TEXT NOT NULL,
                        language TEXT NOT NULL,
                        code_length INTEGER NOT NULL,
                        code_snippet TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,

                        PRIMARY KEY(user_id, challenge_id),

                        FOREIGN KEY(user_id) REFERENCES users(id)
                            ON DELETE CASCADE
                    )
                """)

            # Migration v8
            # - add database indexes for foreign keys and frequently queried columns
            if version < 8:
                logger.info("Applying migration for version 8 ...")

                _ = cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_preferences_user_id "
                    "ON preferences(user_id)"
                )
                _ = cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_semester_plans_user_id "
                    "ON semester_plans(user_id)"
                )
                _ = cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_semester_plans_module_id "
                    "ON semester_plans(module_id)"
                )
                _ = cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_feedback_user_id "
                    "ON feedback(user_id)"
                )
                _ = cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_study_buddies_module_id "
                    "ON study_buddies(module_id)"
                )
                _ = cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_module_ratings_module_id "
                    "ON module_ratings(module_id)"
                )
                _ = cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_challenge_submissions_cid_len "
                    "ON challenge_submissions(challenge_id, code_length ASC)"
                )


            _ = cursor.execute(f"PRAGMA user_version = {self.DB_VERSION}")
            conn.commit()
            logger.success("Database migration complete.")



    def _check_user(self, user_id: int) -> None:
        """ Creates a user entry in the users table if it doenst yet exist

            Parameters
                user_id: the users discord id.
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Ensure user exists (create with None name if missing)
            _ = cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                _ = cursor.execute(
                    "INSERT INTO users (id, name) VALUES (?, NULL)", (user_id,)
                )

            conn.commit()


    def _check_module(self, module_id:int, language: LanguageCode) -> tuple[int, str] | None:
        """ Checks if a module exists in the database.

            Parameters:
                module_id: the modules id.
                language: the modules language.

            Returns:
                Tuple of (module_id, language) if the module exists.

                Language might differ if module is not available in the
                requested language.

                None if the module does not exist.

        """

        result: sqlite3.Row | None

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # if the module exists, just return it
            _ = cursor.execute(
                "SELECT id, language FROM modules WHERE id = ? AND language = ?",
                (module_id, language.name)
            )
            result = cursor.fetchone()  # pyright: ignore[reportAny]
            if result:
                return(result["id"], result["language"])

            # else try to fetch it from the tables api
            self.add_module(module_id, language)

            # try again to find it
            _ = cursor.execute(
                "SELECT id, language FROM modules WHERE id = ? AND language = ?",
                (module_id, language.name)
            )
            result = cursor.fetchone()  # pyright: ignore[reportAny]
            if result:
                return(result["id"], result["language"])

            # else try to find it in any other language
            _ = cursor.execute("SELECT id, language FROM modules WHERE id = ?", (module_id,))
            result = cursor.fetchone()  # pyright: ignore[reportAny]
            if result:
                return(result["id"], result["language"])

        # couldn't find module in any way
        logger.error(f"can't find module with the id: {module_id} in our or the tables tadabase")
        return None


    # one parameter per preferences column, bundling them would touch every call site
    def set_preferences(  # pylint: disable=R0913,R0917  # (too-many-(positional-)arguments)
        self,
        user_id: int,
        language: LanguageCode | None = None,
        semester: int | None = None,
        major: str | None = None,
        spo: int | None = None,
        winter_semester: bool = True
    ) -> None:
        """ Update the users preferences in the database.

            Parameters:
                user_id:  the users discord id.
                language: prefered language (e.g. <LanguageCode.EN>).
                semester: integer representing the current semester.
                major:    the users course of study.
                spo:      usually the users enrollment year or the next lower spo
                winter_semester: weather the user has started to study in the winter semester
        """

        self._check_user(user_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if preferences exist
            _ = cursor.execute(
                "SELECT user_id FROM preferences WHERE user_id = ?", (user_id,)
            )

            if cursor.fetchone():
                # Update existing preferences
                updates: list[str] = []
                params: list[str|int] = []
                if language is not None:
                    updates.append("language = ?")
                    params.append(language.name)
                if semester is not None:
                    updates.append("semester = ?")
                    params.append(semester)
                if major is not None:
                    updates.append("major = ?")
                    params.append(major)
                if spo is not None:
                    updates.append("spo = ?")
                    params.append(spo)
                updates.append("winter_semester = ?")
                params.append(winter_semester)

                if updates:
                    params.append(user_id)
                    query = (
                        f"UPDATE preferences SET {', '.join(updates)} WHERE user_id = ?"
                    )
                    _ = cursor.execute(query, params)
            else:
                # Insert new preferences
                _ = cursor.execute(
                    """
                    INSERT INTO preferences
                        (user_id, language, semester, major, spo, winter_semester)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        language.name if language else "en",
                        semester,
                        major,
                        spo,
                        winter_semester,
                    ),
                )

            conn.commit()

    def get_preferences(self, user_id: int) -> PrefsDict | None:
        """ Retrieve a user's preferences as a dictionary.

            Parameters:
                user_id:  the users discord id.

            Returns:
                dictonary corresponding to the row for the users preferences
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
            row: sqlite3.Row | None = cursor.fetchone()  # pyright: ignore[reportAny]

            if not row:
                return None

            prefs: PrefsDict = PrefsDict(
                user_id = int(row["user_id"]),  # pyright: ignore[reportAny]
                # pylint: disable=C0301 # (line-too-long)
                language = LanguageCode.from_language_code(str(row["language"])),  # pyright: ignore[reportAny]
                # semester = int(row["semester"]),
            )

            try:
                major: StudyCourse = StudyCourse.from_str(
                    str(row["major"])  # pyright: ignore[reportAny]
                )
                prefs["major"] = major
            except ValueError:
                logger.warning(f"User ({user_id}) has invalid major '{row['major']}'")

            if row["semester"] is not None:
                prefs["semester"] = int(row["semester"])  # pyright: ignore[reportAny]

            if row["spo"] is not None:
                prefs["spo"] = row["spo"] # pyright: ignore[reportAny]

            prefs["winter_semester"] = bool(row["winter_semester"]) # pyright: ignore[reportAny]

            return prefs


    def get_users(self) -> list[int] | None:
        """Fetches all users

            Returns:
                List of user (discord) id's.
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("SELECT id FROM users")
            rows: list[sqlite3.Row] = cursor.fetchall()
            return [row["id"] for row in rows] if rows else None


    @overload
    def add_module(
        self,
        module_id: int,
        language: LanguageCode,
        title: str,
        title_en: str
    )-> None: ...
    @overload
    def add_module(self, module_id: int, language: LanguageCode = LanguageCode.DE)-> None: ...
    @overload
    def add_module(self, module: Module)-> None: ...
    # pylint: disable=C0301 # (line-too-long)
    def add_module(self, *args, **kwargs) -> None:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        """ Adds a module to the database.

            Parameters:
                module:     the module to add.

                module_id:  the modules id.
                language:   the modules language.
                title:      the modules title in german.
                title_en:   the modules title in english.
        """
        # pylint: disable=C0301 # (line-too-long)
        if len(args) == 0 or len(args) > 4 or len(kwargs) > 0:  # pyright: ignore[reportUnknownArgumentType]
            raise TypeError("Invalid arguments for add_module")

        module_id: int | None = None
        language: str = "de"
        title: str = ""
        title_en: str = ""

        # pylint: disable=C0301 # (line-too-long)
        if len(args) == 1 and isinstance(args[0], Module):  # pyright: ignore[reportUnknownArgumentType]
            module = args[0]
            module_id = module.id_
            language = module.language.name
            title = module.get_title(LanguageCode.DE)
            title_en = module.get_title(LanguageCode.EN)
        elif len(args) <= 2 and len(args) >= 1:  # pyright: ignore[reportUnknownArgumentType]
            module_id = int(args[0])               # pyright: ignore[reportUnknownArgumentType]
            if len(args) == 2:                   # pyright: ignore[reportUnknownArgumentType]
                language = ModuleLanguage(args[1]).name

            temp_language, temp_title, temp_title_en = _catalogue_entry(module_id, language)

            assert temp_language and temp_title and temp_title_en, \
                f"Module {module_id} not found in catalogue."
            assert temp_language in ModuleLanguage.valid_languages(), "Unknown module language."

            if language != temp_language:
                logger.warning(f"Module {module_id} not found in language '{language}'. \
Using '{temp_language}' instead.")

            language = temp_language
            title = temp_title
            title_en = temp_title_en

        elif len(args) >= 3:                    # pyright: ignore[reportUnknownArgumentType]
            module_id = int(args[0])              # pyright: ignore[reportUnknownArgumentType]
            language = ModuleLanguage(args[1]).name
            title = str(args[2])           # pyright: ignore[reportUnknownArgumentType]
            if len(args) >= 4:                  # pyright: ignore[reportUnknownArgumentType]
                title_en = str(args[3])    # pyright: ignore[reportUnknownArgumentType]

        assert module_id, "Module id is required."

        # The cache keeps one row per bot language, see the `valid_language` constraint.
        # A module that is taught in both languages is stored as german, its row holds
        # the english title as well, so nothing gets lost.
        if language not in LanguageCode.valid_languages():
            language = LanguageCode.DE.name

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                INSERT OR REPLACE INTO modules (id, language, title, title_en)
                VALUES (?, ?, ?, ?)
                """,
                (module_id, language, title, title_en)
            )
            conn.commit()

    def get_module(self, module_id: int, language: LanguageCode) -> Module | None:
        """Fetches a module from the database.

            Parameters:
                module_id:  the modules id.
                language:   the modules language.
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("SELECT * FROM modules WHERE id = ?", (module_id,))
            rows: list[sqlite3.Row] = cursor.fetchall()

            if not rows:
                return None

            # Try to find the module with the requested language
            for row in rows:
                if row["language"] == language:
                    return Module(
                        id_ = row["id"],            # pyright: ignore[reportAny]
                        language = row["language"], # pyright: ignore[reportAny]
                        title = row["title"],       # pyright: ignore[reportAny]
                        title_en = row["title_en"], # pyright: ignore[reportAny]
                    )
            # Fallback: return the first module found (any language)
            row = rows[0]
            return Module(
                id_ = row["id"],             # pyright: ignore[reportAny]
                language = row["language"], # pyright: ignore[reportAny]
                title = row["title"],       # pyright: ignore[reportAny]
                title_en = row["title_en"], # pyright: ignore[reportAny]
            )


    def add_to_semesterplan(
        self,
        user_id: int,
        module_id: int,
        language: LanguageCode = LanguageCode.DE
    )-> None:
        """Adds a module to the users semester plan.

            Parameters:
                user_id:   the users discord id.
                module_id: the modules id.
                language:  the modules language.
        """
        self._check_user(user_id)
        checked_module: tuple[int, str] | None  = self._check_module(module_id, language)

        if not checked_module:
            # asserts are stripped with -O and the button callback only shows a generic error
            raise KeyError(f"can't find information on the module with the id: {module_id}")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                INSERT OR REPLACE INTO semester_plans (user_id, module_id, language)
                VALUES (?, ?, ?)
            """, (user_id, checked_module[0], checked_module[1]))
            conn.commit()


    def remove_from_semesterplan(self, user_id:int, module_id:int)-> None:
        """Removes a module from the users semester plan.

            Parameters:
                user_id:   the users discord id.
                module_id: the modules id.
                language:  the modules language.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                DELETE FROM semester_plans
                WHERE user_id = ? AND module_id = ?
            """, (user_id, module_id))
            conn.commit()


    def get_semesterplan(self, user_id:int)-> list[Module]:
        """Fetches the semester plan for a user.

            Parameters:
                user_id: the users discord id.

            Returns:
                List of modules in the users semester plan.
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                SELECT m.id, m.language, m.title, m.title_en
                FROM semester_plans sp
                JOIN modules m ON sp.module_id = m.id AND sp.language = m.language
                WHERE sp.user_id = ?
            """, (user_id,))
            rows: list[sqlite3.Row] = cursor.fetchall()

            result: list[Module] = []
            for row in rows:
                result.append(
                    Module(
                        id_ = row["id"],            # pyright: ignore[reportAny]
                        language = row["language"], # pyright: ignore[reportAny]
                        title = row["title"],       # pyright: ignore[reportAny]
                        title_en = row["title_en"], # pyright: ignore[reportAny]
                    )
                )
            return result


    def send_feedback_dict(self, feedback: FeedbackDict):
        """ Sends user feedback to the database."""
        self.send_feedback(
            user_id = feedback["user_id"],
            intuitiveness = feedback["intuitiveness"],
            discoverability = feedback["discoverability"],
            usefulness = feedback["usefulness"],
            improvements = feedback.get("improvements", ""),
            wishes = feedback.get("wishes", ""),
            bugs = feedback.get("bugs", "")
        )

    # pylint: disable=R0913  # (too-many-arguments)
    # pylint: disable=R0917  # (too-many-positional-arguments)
    def send_feedback(self,
        user_id: int,
        intuitiveness: int,
        discoverability: int,
        usefulness: int,
        improvements: str = "",
        wishes: str = "",
        bugs: str = "")-> None:
        """ Sends user feedback to the database."""

        # check that user exists
        self._check_user(user_id)

        # get user language
        language: str = "en"
        prefs: PrefsDict | None = self.get_preferences(user_id)
        if prefs:
            language = prefs["language"].name

        timestamp: int = int(time.time())
        # as Unix Time, the number of seconds since 1970-01-01 00:00:00 UTC.

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                INSERT INTO feedback (user_id, language, time,
                                      intuitiveness, discoverability, usefulness,
                                      improvements, wishes, bugs)
                VALUES (?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?)
                """,
                (user_id, language, timestamp,
                 intuitiveness, discoverability, usefulness,
                 improvements, wishes, bugs)
            )
            conn.commit()


    def get_feedback(self)-> list[FeedbackReviewDict]:
        """ Fetches all feedback from the database, sorted by ccreation date."""
        result: list[FeedbackReviewDict] = []

        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            _ = cursor.execute("SELECT * FROM feedback")
            rows: list[sqlite3.Row] = cursor.fetchall()

            if rows:
                for row in rows:
                    result.append(
                        FeedbackReviewDict(
                            id = row["id"],                             # pyright: ignore[reportAny]
                            user_id = row["user_id"],                   # pyright: ignore[reportAny]
                            language = row["language"],                 # pyright: ignore[reportAny]
                            timestamp = row["time"],                    # pyright: ignore[reportAny]
                            intuitiveness = row["intuitiveness"],       # pyright: ignore[reportAny]
                            discoverability = row["discoverability"],   # pyright: ignore[reportAny]
                            usefulness = row["usefulness"],             # pyright: ignore[reportAny]
                            improvements = row["improvements"],         # pyright: ignore[reportAny]
                            wishes = row["wishes"],                     # pyright: ignore[reportAny]
                            bugs = row["bugs"],                         # pyright: ignore[reportAny]
                        )
                    )

        result.sort(key=lambda x: x["timestamp"])

        return result


    def delete_feedback(self, feedback_id: int) -> None:
        """ Deletes feedback from the database by its id."""

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "DELETE FROM feedback WHERE id = ?", (feedback_id,)
            )
            conn.commit()


    def export_user_data(self, user_id: int) -> UserDataDict:
        """ Collects every row the database stores against one discord id.

            The rows are handed over as they are stored. A student asking what we
            hold about them gets the stored values, not a nicer reading of them.

            The semester plan is read with a LEFT JOIN on purpose. An INNER JOIN,
            as `get_semesterplan` uses it, drops a saved module whose title is not
            in the `modules` cache, and an export may not lose a row silently.

            Parameters:
                user_id: the users discord id.

            Returns:
                One entry per table that carries a discord id. Empty for a student
                who never used the bot.
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()

            _ = cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,))
            account: sqlite3.Row | None = cursor.fetchone()  # pyright: ignore[reportAny]

            _ = cursor.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
            preferences: sqlite3.Row | None = cursor.fetchone()  # pyright: ignore[reportAny]

            _ = cursor.execute("""
                SELECT sp.module_id, sp.language, m.title, m.title_en
                FROM semester_plans sp
                LEFT JOIN modules m ON sp.module_id = m.id AND sp.language = m.language
                WHERE sp.user_id = ?
                ORDER BY sp.module_id
            """, (user_id,))
            plan: list[sqlite3.Row] = cursor.fetchall()

            _ = cursor.execute(
                "SELECT * FROM feedback WHERE user_id = ? ORDER BY time", (user_id,)
            )
            feedback: list[sqlite3.Row] = cursor.fetchall()

            _ = cursor.execute(
                "SELECT module_id, time FROM study_buddies WHERE user_id = ? ORDER BY module_id",
                (user_id,)
            )
            buddies: list[sqlite3.Row] = cursor.fetchall()

            _ = cursor.execute(
                "SELECT module_id, rating, difficulty, comment, timestamp "
                "FROM module_ratings WHERE user_id = ? ORDER BY module_id",
                (user_id,)
            )
            ratings: list[sqlite3.Row] = cursor.fetchall()

            _ = cursor.execute(
                "SELECT challenge_id, language, code_length, code_snippet, timestamp "
                "FROM challenge_submissions WHERE user_id = ? ORDER BY challenge_id",
                (user_id,)
            )
            submissions: list[sqlite3.Row] = cursor.fetchall()

        return UserDataDict(
            user_id = user_id,
            account = dict(account) if account else None,
            preferences = dict(preferences) if preferences else None,
            semester_plan = [dict(row) for row in plan],
            feedback = [dict(row) for row in feedback],
            study_buddies = [dict(row) for row in buddies],
            module_ratings = [dict(row) for row in ratings],
            challenge_submissions = [dict(row) for row in submissions],
        )


    def delete_user_data(self, user_id: int) -> dict[str, int]:
        """ Removes every row the database stores against one discord id.

            The child rows are deleted by hand although every one of them declares
            `ON DELETE CASCADE`. The cascade does run, because `_get_connection`
            turns `PRAGMA foreign_keys` on, but that pragma is set per connection
            and sqlite leaves it off by default. A command that promises a student
            their data is gone may not rest on a setting that fails silently.

            Parameters:
                user_id: the users discord id.

            Returns:
                How many rows were removed, per table. All zero for a student who
                never used the bot, so calling this twice is harmless.
        """

        removed: dict[str, int] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for table in (
                "preferences",
                "semester_plans",
                "feedback",
                "study_buddies",
                "module_ratings",
                "challenge_submissions",
            ):
                # the table names are literals from this tuple, never user input
                _ = cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
                removed[table] = cursor.rowcount

            _ = cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            removed["users"] = cursor.rowcount

            conn.commit()

        logger.info(f"Deleted the stored data of user ({user_id}): {removed}")
        return removed


    def join_study_buddy(self, user_id: int, module_id: int) -> bool:
        """ Opts a student in to study buddy matching for a module.

            Parameters:
                user_id: the student's discord id.
                module_id: the module identification id.

            Returns:
                True if newly added, False if already registered.
        """
        self._check_user(user_id)
        now = int(time.time())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "INSERT OR IGNORE INTO study_buddies(user_id, module_id, time) VALUES (?, ?, ?)",
                (user_id, module_id, now)
            )
            conn.commit()
            return cursor.rowcount > 0


    def leave_study_buddy(self, user_id: int, module_id: int) -> bool:
        """ Opts a student out of study buddy matching for a module.

            Parameters:
                user_id: the student's discord id.
                module_id: the module identification id.

            Returns:
                True if removed, False if was not registered.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "DELETE FROM study_buddies WHERE user_id = ? AND module_id = ?",
                (user_id, module_id)
            )
            conn.commit()
            return cursor.rowcount > 0


    def is_study_buddy(self, user_id: int, module_id: int) -> bool:
        """ Checks if a student is opted in as a study buddy for a module."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT 1 FROM study_buddies WHERE user_id = ? AND module_id = ?",
                (user_id, module_id)
            )
            return cursor.fetchone() is not None


    def get_study_buddies(self, module_id: int) -> list[int]:
        """ Returns the list of student discord IDs who opted in for this module."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT user_id FROM study_buddies WHERE module_id = ? ORDER BY time",
                (module_id,)
            )
            return [int(row["user_id"]) for row in cursor.fetchall()]


    def get_study_buddy_modules(self, user_id: int) -> list[int]:
        """ Returns the list of module IDs the student has opted in for."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT module_id FROM study_buddies WHERE user_id = ? ORDER BY module_id",
                (user_id,)
            )
            return [int(row["module_id"]) for row in cursor.fetchall()]


    def get_study_buddy_count(self, module_id: int) -> int:
        """ Returns the count of students who opted in for this module."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT COUNT(*) FROM study_buddies WHERE module_id = ?",
                (module_id,)
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0


    def get_module_planner_count(self, module_id: int) -> int:
        """ Returns the anonymous count of students who have this module in their plan."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT COUNT(DISTINCT user_id) FROM semester_plans WHERE module_id = ?",
                (module_id,)
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0


    def rate_module(
        self,
        user_id: int,
        module_id: int,
        rating: int,
        difficulty: int,
        comment: str | None = None,
    ) -> None:
        """ Stores or updates a student's rating and difficulty evaluation for a module.

            Parameters:
                user_id: The student's discord id.
                module_id: The module identifier.
                rating: Overall rating (1-5 stars).
                difficulty: Subjective difficulty (1-5, 1=easy, 5=hard).
                comment: Optional review or advice for future students.
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")
        if not 1 <= difficulty <= 5:
            raise ValueError("Difficulty must be between 1 and 5.")

        self._check_user(user_id)
        now = int(time.time())
        clean_comment = comment.strip() if comment else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                INSERT INTO module_ratings (user_id, module_id, rating, difficulty, comment, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, module_id) DO UPDATE SET
                    rating = excluded.rating,
                    difficulty = excluded.difficulty,
                    comment = excluded.comment,
                    timestamp = excluded.timestamp
            """, (user_id, module_id, rating, difficulty, clean_comment, now))
            conn.commit()


    def get_module_ratings(self, module_id: int) -> ModuleRatingDict:
        """ Returns aggregated ratings and difficulty statistics for a module.

            Parameters:
                module_id: The module identifier.

            Returns:
                Dictionary with count, avg_rating, and avg_difficulty.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                SELECT COUNT(*) as count, AVG(rating) as avg_rating, AVG(difficulty) as avg_difficulty
                FROM module_ratings
                WHERE module_id = ?
            """, (module_id,))
            row = cursor.fetchone()
            if row and row["count"] > 0:
                return {
                    "count": int(row["count"]),
                    "avg_rating": round(float(row["avg_rating"]), 1),
                    "avg_difficulty": round(float(row["avg_difficulty"]), 1),
                }
            return {
                "count": 0,
                "avg_rating": None,
                "avg_difficulty": None,
            }


    def get_user_module_rating(self, user_id: int, module_id: int) -> dict[str, Any] | None:
        """ Returns a student's own rating for a module if already submitted.

            Parameters:
                user_id: The student's discord id.
                module_id: The module identifier.

            Returns:
                Rating dict or None if unrated.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                SELECT rating, difficulty, comment, timestamp
                FROM module_ratings
                WHERE user_id = ? AND module_id = ?
            """, (user_id, module_id))
            row = cursor.fetchone()
            if row:
                return {
                    "rating": int(row["rating"]),
                    "difficulty": int(row["difficulty"]),
                    "comment": row["comment"],
                    "timestamp": int(row["timestamp"]),
                }
            return None


    def get_module_comments(self, module_id: int, limit: int = 5) -> list[dict[str, Any]]:
        """ Returns recent student reviews/comments for a module.

            Parameters:
                module_id: The module identifier.
                limit: Maximum number of comments to return.

            Returns:
                List of dicts with rating, difficulty, comment, timestamp.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                SELECT rating, difficulty, comment, timestamp
                FROM module_ratings
                WHERE module_id = ? AND comment IS NOT NULL AND TRIM(comment) != ''
                ORDER BY timestamp DESC
                LIMIT ?
            """, (module_id, limit))
            return [
                {
                    "rating": int(r["rating"]),
                    "difficulty": int(r["difficulty"]),
                    "comment": str(r["comment"]),
                    "timestamp": int(r["timestamp"]),
                }
                for r in cursor.fetchall()
            ]


    # pylint: disable=too-many-locals
    def get_cohort_statistics(
        self,
        major: StudyCourse | str | int | None = None,
        semester: int | None = None,
        min_cohort_size: int = 3,
    ) -> CohortStatsDict:
        """ Returns aggregated, privacy-preserving statistics for a cohort of students.

            To prevent individual fingerprinting (k-anonymity), detailed metrics
            and module breakdowns are only returned when at least `min_cohort_size`
            students are present in the cohort.

            Parameters:
                major: Filter by study course (major), e.g. 'BSC_INF' or StudyCourse.BSC_INF.
                semester: Filter by semester, e.g. 1, 2, 3...
                min_cohort_size: Minimum cohort size required to disclose metrics (default: 3).

            Returns:
                CohortStatsDict containing aggregated statistics.
        """
        major_str: str | None = None
        if major is not None:
            if hasattr(major, "name"):
                major_str = str(major.name)
            else:
                major_str = str(major)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            _ = cursor.execute("""
                SELECT user_id, semester, major
                FROM preferences
                WHERE major IS NOT NULL AND TRIM(major) != ''
            """)
            all_prefs = cursor.fetchall()

            user_majors: dict[int, tuple[int | None, str]] = {}
            for row in all_prefs:
                u_id = int(row["user_id"])
                u_sem = int(row["semester"]) if row["semester"] is not None else None
                u_maj = str(row["major"])
                user_majors[u_id] = (u_sem, u_maj)

            total_registered = len(user_majors)

            major_counts: dict[str, int] = {}
            for _, u_maj in user_majors.values():
                major_counts[u_maj] = major_counts.get(u_maj, 0) + 1

            major_distribution: list[MajorDistDict] = [
                {
                    "major": m,
                    "count": cnt,
                    "percentage": int(round((cnt / total_registered) * 100)) if total_registered > 0 else 0,
                }
                for m, cnt in sorted(major_counts.items(), key=lambda x: x[1], reverse=True)
            ]

            major_user_ids = [
                uid for uid, (_, u_maj) in user_majors.items()
                if major_str is None or u_maj.lower() == major_str.lower()
            ]
            major_size = len(major_user_ids)

            cohort_user_ids = [
                uid for uid in major_user_ids
                if semester is None or user_majors[uid][0] == semester
            ]
            cohort_size = len(cohort_user_ids)

            if cohort_size < min_cohort_size:
                return {
                    "has_sufficient_data": False,
                    "min_cohort_size": min_cohort_size,
                    "cohort_size": cohort_size,
                    "major_size": major_size,
                    "total_registered_students": total_registered,
                    "avg_modules_planned": None,
                    "avg_cp_planned": None,
                    "top_modules": [],
                    "major_distribution": major_distribution,
                }

            placeholders = ",".join("?" for _ in cohort_user_ids)
            _ = cursor.execute(f"""
                SELECT sp.user_id, sp.module_id, m.title, m.title_en
                FROM semester_plans sp
                LEFT JOIN modules m ON sp.module_id = m.id AND sp.language = m.language
                WHERE sp.user_id IN ({placeholders})
            """, tuple(cohort_user_ids))
            plan_rows = cursor.fetchall()

            user_plans: dict[int, list[int]] = {uid: [] for uid in cohort_user_ids}
            module_counts_map: dict[int, int] = {}
            module_info: dict[int, tuple[str, str]] = {}

            for r in plan_rows:
                uid = int(r["user_id"])
                mid = int(r["module_id"])
                if uid in user_plans:
                    user_plans[uid].append(mid)
                module_counts_map[mid] = module_counts_map.get(mid, 0) + 1
                if mid not in module_info:
                    t_de = str(r["title"] or f"Modul {mid}")
                    t_en = str(r["title_en"] or t_de)
                    module_info[mid] = (t_de, t_en)

            total_planned_modules = sum(len(mods) for mods in user_plans.values())
            avg_modules = round(total_planned_modules / cohort_size, 1) if cohort_size > 0 else 0.0
            avg_cp = round(avg_modules * 5.0, 1)

            sorted_modules = sorted(module_counts_map.items(), key=lambda x: x[1], reverse=True)[:5]
            top_modules: list[TopModuleDict] = [
                {
                    "id": mid,
                    "title": module_info.get(mid, (f"Modul {mid}", f"Module {mid}"))[0],
                    "title_en": module_info.get(mid, (f"Modul {mid}", f"Module {mid}"))[1],
                    "count": cnt,
                    "percentage": int(round((cnt / cohort_size) * 100)),
                }
                for mid, cnt in sorted_modules
            ]

            return {
                "has_sufficient_data": True,
                "min_cohort_size": min_cohort_size,
                "cohort_size": cohort_size,
                "major_size": major_size,
                "total_registered_students": total_registered,
                "avg_modules_planned": avg_modules,
                "avg_cp_planned": avg_cp,
                "top_modules": top_modules,
                "major_distribution": major_distribution,
            }

    def submit_challenge_solution(
        self, user_id: int, challenge_id: str, language: str, code_snippet: str
    ) -> tuple[bool, int, int]:
        """ Records or updates a code golf solution submission.

            If a user already submitted a solution for the challenge, their submission
            is updated only if the new submission is shorter in byte length (or equal).
            Leading/trailing whitespace and surrounding markdown backticks are stripped.

            Parameters:
                user_id: Discord ID of the student.
                challenge_id: Identifier of the challenge.
                language: Programming language used.
                code_snippet: The raw code submitted.

            Returns:
                tuple of (is_new_best, previous_length, new_length)
                is_new_best is True if recorded or improved, False if existing was shorter.
        """
        cleaned_code = code_snippet.strip()
        if cleaned_code.startswith("```") and cleaned_code.endswith("```"):
            lines = cleaned_code.splitlines()
            if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
                cleaned_code = "\n".join(lines[1:-1]).strip()

        byte_length = len(cleaned_code.encode("utf-8"))
        now = int(time.time())

        self._check_user(user_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT code_length FROM challenge_submissions "
                "WHERE user_id = ? AND challenge_id = ?",
                (user_id, challenge_id),
            )
            row = cursor.fetchone()

            if row is not None:
                prev_len = int(row["code_length"])
                if byte_length <= prev_len:
                    _ = cursor.execute(
                        "UPDATE challenge_submissions "
                        "SET language = ?, code_length = ?, code_snippet = ?, timestamp = ? "
                        "WHERE user_id = ? AND challenge_id = ?",
                        (language.strip(), byte_length, cleaned_code, now, user_id, challenge_id),
                    )
                    conn.commit()
                    return True, prev_len, byte_length
                return False, prev_len, byte_length

            _ = cursor.execute(
                "INSERT INTO challenge_submissions "
                "(user_id, challenge_id, language, code_length, code_snippet, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, challenge_id, language.strip(), byte_length, cleaned_code, now),
            )
            conn.commit()
            return True, 0, byte_length

    def get_challenge_leaderboard(
        self, challenge_id: str, limit: int = 10
    ) -> list[LeaderboardEntryDict]:
        """ Retrieves top submissions for a challenge, ordered by code length ascending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT cs.user_id, u.name, cs.language, cs.code_length, cs.timestamp "
                "FROM challenge_submissions cs "
                "JOIN users u ON cs.user_id = u.id "
                "WHERE cs.challenge_id = ? "
                "ORDER BY cs.code_length ASC, cs.timestamp ASC "
                "LIMIT ?",
                (challenge_id, limit),
            )
            rows = cursor.fetchall()

        leaderboard: list[LeaderboardEntryDict] = []
        for idx, row in enumerate(rows, start=1):
            leaderboard.append(
                LeaderboardEntryDict(
                    user_id=int(row["user_id"]),
                    name=str(row["name"]) if row["name"] else None,
                    language=str(row["language"]),
                    code_length=int(row["code_length"]),
                    timestamp=int(row["timestamp"]),
                    rank=idx,
                )
            )
        return leaderboard

    def get_user_challenge_submission(
        self, user_id: int, challenge_id: str
    ) -> ChallengeSubmissionDict | None:
        """ Returns the user's submission for a challenge, if one exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT user_id, challenge_id, language, code_length, code_snippet, timestamp "
                "FROM challenge_submissions WHERE user_id = ? AND challenge_id = ?",
                (user_id, challenge_id),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return ChallengeSubmissionDict(
            user_id=int(row["user_id"]),
            challenge_id=str(row["challenge_id"]),
            language=str(row["language"]),
            code_length=int(row["code_length"]),
            code_snippet=str(row["code_snippet"]),
            timestamp=int(row["timestamp"]),
        )

    def get_user_challenge_submissions(
        self, user_id: int
    ) -> list[ChallengeSubmissionDict]:
        """ Returns all challenge submissions made by a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                "SELECT user_id, challenge_id, language, code_length, code_snippet, timestamp "
                "FROM challenge_submissions WHERE user_id = ? ORDER BY timestamp DESC",
                (user_id,),
            )
            rows = cursor.fetchall()

        return [
            ChallengeSubmissionDict(
                user_id=int(row["user_id"]),
                challenge_id=str(row["challenge_id"]),
                language=str(row["language"]),
                code_length=int(row["code_length"]),
                code_snippet=str(row["code_snippet"]),
                timestamp=int(row["timestamp"]),
            )
            for row in rows
        ]



# For assertion of a singleton instance
_db_instance = None

def get_database() -> Database:
    """Get or create the database singleton."""
    # pylint: disable=W0603 # (global-statement)
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance







def get_user_language(user_id: int) -> LanguageCode:
    """Liest die Sprache eines Benutzers aus der Datenbank."""
    _db: Database = get_database()
    prefs: PrefsDict | None = _db.get_preferences(user_id)

    if not prefs:
        logger.warning(f"User ({user_id}) has no prefered language set, defaulting to EN")
        return LanguageCode.EN
    return prefs["language"]







# TODO: some modules can have three versions (de, en, de (but with another title))
# see module 110321 for example



if __name__ == "__main__":
    db: Database = get_database()
    db.set_preferences(
        user_id=515896235081859091,
        language=LanguageCode.DE,
        semester=6,
        major="B-CV",
        spo=2017,
        winter_semester=False
    )

    print(db.get_preferences(515896235081859091))
    print()
    print(db.get_users())

    db.add_module(123456, LanguageCode.DE, "Ein Modul", "A Module")
    db.add_module(Module(
        id_=654321,
        language=LanguageCode.EN,
        title="Ein anderes Modul en",
        title_en="Another Module en"
    ))
    db.add_module(Module(
        id_=654321,
        language=LanguageCode.DE,
        title="Ein anderes Modul de",
        title_en="Another Module de"
    ))
    db.add_module(501325)                   # should be "Mathematik M1d"
    db.add_module(501325, LanguageCode.EN)  # should be "Mathematik M1e"
    db.add_module(110463, LanguageCode.DE)  # this should only be available in en

    print(db.get_module(123456, LanguageCode.EN))
    print()


    db.add_to_semesterplan(515896235081859091, 123456, LanguageCode.DE)
    db.add_to_semesterplan(515896235081859091, 654321, LanguageCode.DE)
    db.add_to_semesterplan(515896235081859091, 654321, LanguageCode.EN)
    # should not yet exist in modules table
    db.add_to_semesterplan(515896235081859091, 102809)
    print(db.get_semesterplan(515896235081859091))

    db.send_feedback(
        user_id=515896235081859091,
        intuitiveness=4,
        discoverability=3,
        usefulness=4,
        improvements="Everything is fine.",
        wishes="More modules.",
        bugs="No bugs found."
    )
    db.send_feedback(
        user_id=515896235081859091,
        intuitiveness=2,
        discoverability=2,
        usefulness=3
    )
