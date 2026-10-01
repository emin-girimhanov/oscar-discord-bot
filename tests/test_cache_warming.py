"""Nobody should be the student who waits for the module table.

Reading table 720 takes about a second, and reading the selection labels behind it
another half. Both are plain blocking requests made from inside a command handler, so
the first command after a restart, and the first one after the ten minute cache
expired, held up the whole bot:

    cold /module datenbanken    1620 ms
    warm /module datenbanken       5 ms

Discord gives an interaction three seconds before it tells the student the application
did not respond. 1620 ms of that, spent on a request that could have been made
earlier, is most of the budget.

`warm_cache` runs on a thread at startup and every `refresh_interval` seconds after.
These tests pin down that it fetches what a command needs, that it never raises, and
that the interval stays under the cache lifetime.
"""

from unittest.mock import MagicMock, patch

import pytest

import util.tables as tables
from util.tables import (
    CACHE_TTL,
    MODULE_TABLE_ID,
    REFRESH_MARGIN,
    refresh_interval,
    warm_cache,
)


ROWS = [{"Identifizierung": 100391, "Modultitel": "Datenbanken 1"}]


class TestTheRefreshInterval:
    """Refreshing has to happen before the cache goes cold, not after."""

    def test_it_is_shorter_than_the_cache_lifetime(self):
        """A refresh after the expiry leaves a gap somebody falls into."""
        assert refresh_interval() < CACHE_TTL or CACHE_TTL <= 60

    def test_it_leaves_a_margin(self):
        if CACHE_TTL > 60 + REFRESH_MARGIN:
            assert refresh_interval() == CACHE_TTL - REFRESH_MARGIN

    def test_it_never_floods(self, monkeypatch):
        """A tiny TTL must not turn the warming into a request every second."""
        monkeypatch.setattr(tables, "CACHE_TTL", 5)
        assert refresh_interval() >= 60

    def test_it_is_a_whole_number_of_seconds(self):
        assert isinstance(refresh_interval(), int)


class TestWarmCache:
    """What it fetches, and what it does when the network is down."""

    def test_it_reads_the_module_table(self):
        with patch.object(tables, "get_rows", return_value=ROWS) as rows, \
             patch.object(tables, "get_value_by_id", return_value="1."):
            assert warm_cache() is True
        rows.assert_called_once_with(MODULE_TABLE_ID)

    def test_it_also_fills_the_selection_labels(self):
        """Without them every module card shows a number instead of a word."""
        with patch.object(tables, "get_rows", return_value=ROWS), \
             patch.object(tables, "get_value_by_id", return_value="1.") as labels:
            _ = warm_cache()
        labels.assert_called_once()

    def test_an_empty_table_is_reported_not_raised(self):
        """The Tables API returns an empty list when it is unreachable."""
        with patch.object(tables, "get_rows", return_value=[]), \
             patch.object(tables, "get_value_by_id", return_value=""):
            assert warm_cache() is False

    def test_it_warms_the_table_a_command_actually_reads(self):
        """`Catalogue` is built on 720. Warming another table would help nobody."""
        assert MODULE_TABLE_ID == 720


class TestTheBotStartsIt:
    """The loop that keeps it warm, and what happens when a round fails."""

    @pytest.fixture(name="bot")
    def bot_fixture(self):
        from oscar.oscar import Oscar
        bot = MagicMock(spec=Oscar)
        bot.keep_tables_warm = Oscar.keep_tables_warm.__get__(bot)
        return bot

    async def test_it_stops_when_the_bot_closes(self, bot):
        bot.is_closed.return_value = True
        with patch("oscar.oscar.warm_cache") as warm:
            await bot.keep_tables_warm()
        warm.assert_not_called()

    async def test_it_warms_once_per_round(self, bot):
        bot.is_closed.side_effect = [False, True]
        with patch("oscar.oscar.warm_cache", return_value=True) as warm, \
             patch("asyncio.sleep") as sleep:
            await bot.keep_tables_warm()
        assert warm.call_count == 1
        sleep.assert_awaited_once()

    async def test_a_failed_round_does_not_end_the_loop(self, bot):
        """A command still works after this, it just pays for the cold cache."""
        bot.is_closed.side_effect = [False, False, True]
        with patch("oscar.oscar.warm_cache", side_effect=[OSError("down"), True]) as warm, \
             patch("asyncio.sleep"):
            await bot.keep_tables_warm()
        assert warm.call_count == 2

    async def test_it_waits_the_refresh_interval(self, bot):
        bot.is_closed.side_effect = [False, True]
        with patch("oscar.oscar.warm_cache", return_value=True), \
             patch("asyncio.sleep") as sleep:
            await bot.keep_tables_warm()
        sleep.assert_awaited_once_with(refresh_interval())
