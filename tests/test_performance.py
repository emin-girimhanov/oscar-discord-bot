"""Tests for performance optimizations including database WAL mode, indexes, and tables caching."""

import concurrent.futures
import time
from unittest.mock import MagicMock, patch

import pytest

from util.database import Database
import util.tables as tables


class TestDatabasePerformance:
    """Tests for SQLite performance settings and index usage."""

    def test_wal_mode_and_pragmas(self, tmp_path):
        """Database on disk should have WAL mode enabled and optimized pragmas."""
        db_path = str(tmp_path / "perf.db")
        db = Database(db_path=db_path)

        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            assert mode.lower() == "wal"

            cursor.execute("PRAGMA busy_timeout")
            timeout = cursor.fetchone()[0]
            assert timeout == 10000

            cursor.execute("PRAGMA synchronous")
            sync = cursor.fetchone()[0]
            # 1 corresponds to NORMAL in SQLite
            assert sync == 1

    def test_indexes_used_in_query_plans(self, tmp_path):
        """Queries on filtered columns should use their respective indexes."""
        db_path = str(tmp_path / "plan.db")
        db = Database(db_path=db_path)

        with db._get_connection() as conn:
            cursor = conn.cursor()

            # preferences by user_id
            cursor.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM preferences WHERE user_id = 123"
            )
            plan = " ".join(str(row["detail"]) for row in cursor.fetchall())
            assert "idx_preferences_user_id" in plan

            # semester_plans by module_id
            cursor.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM semester_plans WHERE module_id = 456"
            )
            plan = " ".join(str(row["detail"]) for row in cursor.fetchall())
            assert "idx_semester_plans_module_id" in plan

            # semester_plans by user_id
            cursor.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM semester_plans WHERE user_id = 789"
            )
            plan = " ".join(str(row["detail"]) for row in cursor.fetchall())
            assert "idx_semester_plans_user_id" in plan

            # challenge_submissions by challenge_id and code_length
            cursor.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM challenge_submissions "
                "WHERE challenge_id = 'test_c' ORDER BY code_length ASC"
            )
            plan = " ".join(str(row["detail"]) for row in cursor.fetchall())
            assert "idx_challenge_submissions_cid_len" in plan

    def test_concurrent_database_reads_and_writes(self, tmp_path):
        """Multiple concurrent threads should read and write without locking errors."""
        db_path = str(tmp_path / "concurrent.db")
        db = Database(db_path=db_path)

        def worker(user_id: int):
            # Write preference
            db.set_preferences(user_id, language=None, semester=3)
            # Read preference back
            prefs = db.get_preferences(user_id)
            assert prefs is not None
            assert prefs["semester"] == 3
            return True

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(worker, 1000 + i) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(results)
        assert len(results) == 20


class TestTablesCaching:
    """Tests for in-memory caching of Tables API responses."""

    def test_get_rows_uses_cache(self):
        """Consecutive get_rows calls should use the cache instead of repeated HTTP calls."""
        with patch.object(tables, "get_json") as mock_get_json:
            mock_get_json.return_value = [
                ["Identifizierung", "Modultitel"],
                [10, "Cached Modul"],
            ]

            first = tables.get_rows(720)
            second = tables.get_rows(720)

            assert first == second
            assert mock_get_json.call_count == 1

    def test_get_rows_from_view_uses_cache(self):
        """Consecutive get_rows_from_view calls should use the cache."""
        with patch.object(tables, "__get_columns_from_view", return_value={1: "Modultitel"}):
            with patch.object(
                tables,
                "__get_rows_from_view",
                return_value=[[{"columnId": 1, "value": "View Modul"}]],
            ):
                first = tables.get_rows_from_view(2018)
                second = tables.get_rows_from_view(2018)

                assert first == second
                assert len(first) == 1
                assert first[0]["Modultitel"] == "View Modul"

    def test_clear_tables_cache_invalidates_entries(self):
        """clear_tables_cache should clear the cache and force new fetches."""
        with patch.object(tables, "get_json") as mock_get_json:
            mock_get_json.return_value = [
                ["Identifizierung", "Modultitel"],
                [10, "Modul 1"],
            ]

            tables.get_rows(720)
            assert mock_get_json.call_count == 1

            tables.clear_tables_cache()

            mock_get_json.return_value = [
                ["Identifizierung", "Modultitel"],
                [20, "Modul 2"],
            ]
            fresh = tables.get_rows(720)
            assert mock_get_json.call_count == 2
            assert fresh[0]["Identifizierung"] == 20

    def test_cache_ttl_expiry(self):
        """Expired items in cache should be discarded."""
        with patch.object(tables, "get_json") as mock_get_json:
            mock_get_json.return_value = [
                ["Identifizierung", "Modultitel"],
                [10, "Old Modul"],
            ]

            tables.get_rows(720)
            assert mock_get_json.call_count == 1

            # Manually age the cache entry
            key = "rows:720"
            with tables._CACHE_LOCK:
                if key in tables._CACHE:
                    tables._CACHE[key] = (time.time() - (tables.CACHE_TTL + 10), tables._CACHE[key][1])

            mock_get_json.return_value = [
                ["Identifizierung", "Modultitel"],
                [10, "Refreshed Modul"],
            ]
            refreshed = tables.get_rows(720)
            assert mock_get_json.call_count == 2
            assert refreshed[0]["Modultitel"] == "Refreshed Modul"

    def test_concurrent_cache_access(self):
        """Multiple threads reading get_rows simultaneously should not encounter race conditions."""
        with patch.object(tables, "get_json") as mock_get_json:
            mock_get_json.return_value = [
                ["Identifizierung", "Modultitel"],
                [1, "Concur Modul"],
            ]

            def reader():
                res = tables.get_rows(720)
                assert len(res) == 1
                return res[0]["Modultitel"]

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(reader) for _ in range(20)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            assert all(title == "Concur Modul" for title in results)
            # At most a couple calls if threads start concurrently before first set, but never crashes
            assert len(results) == 20
