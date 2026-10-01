import pytest
from unittest.mock import MagicMock, patch
import discord
import os
import sys
import pkgutil
import importlib

# Ensure src is in path so we can import 'oscar'
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from oscar.oscar import Oscar
import oscar.cogs

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("DISCORD_SERVER_ID", "123456789")
    monkeypatch.setenv("BOT_TOKEN", "dummy_token")
    monkeypatch.setenv("TABLES_URL", "http://dummy")
    monkeypatch.setenv("TABLES_USERNAME", "dummy")
    monkeypatch.setenv("TABLES_PASSWORD", "dummy")

@pytest.fixture
def mock_bot(mock_env):
    """Fixture to create a bot instance with mocked internals."""
    intents = discord.Intents.default()
    bot = Oscar(command_prefix="!", intents=intents)

    # Mock network-dependent methods
    bot.login = MagicMock()
    bot.connect = MagicMock()
    # Mock tree sync to prevent API calls
    bot.tree.sync = MagicMock()
    bot.tree.copy_global_to = MagicMock()

    return bot

async def test_bot_initialization(mock_bot):
    """Test that the bot can be initialized without errors."""
    assert mock_bot is not None
    assert mock_bot.server_id == "123456789"
    # Basic check passed if fixture setup didn't crash

async def test_bot_has_bot_token(mock_bot):
    """Test that the bot token is set correctly."""
    assert mock_bot.bot_token == "dummy_token"

async def test_bot_missing_server_id(monkeypatch):
    """Test that missing DISCORD_SERVER_ID raises RuntimeError."""
    # Oscar.__init__ calls load_dotenv, which would refill the variable we delete
    # below from a developer's own .env file. Self hosting creates exactly that file.
    monkeypatch.setattr("oscar.oscar.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("BOT_TOKEN", "dummy_token")
    monkeypatch.setenv("TABLES_URL", "http://dummy")
    monkeypatch.setenv("TABLES_USERNAME", "dummy")
    monkeypatch.setenv("TABLES_PASSWORD", "dummy")
    monkeypatch.delenv("DISCORD_SERVER_ID", raising=False)

    intents = discord.Intents.default()
    with pytest.raises(RuntimeError):
        Oscar(command_prefix="!", intents=intents)

async def test_bot_missing_bot_token(monkeypatch):
    """Test that missing BOT_TOKEN raises RuntimeError."""
    # same reason as above, a local .env must not decide whether this test passes
    monkeypatch.setattr("oscar.oscar.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("DISCORD_SERVER_ID", "123456789")
    monkeypatch.setenv("TABLES_URL", "http://dummy")
    monkeypatch.setenv("TABLES_USERNAME", "dummy")
    monkeypatch.setenv("TABLES_PASSWORD", "dummy")
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    intents = discord.Intents.default()
    with pytest.raises(RuntimeError):
        Oscar(command_prefix="!", intents=intents)

async def test_load_all_cogs(mock_bot):
    """
    Smoke test: Iterates through all cogs in src/oscar/cogs
    and verifies they can be loaded by the bot.
    This catches syntax errors and import errors in cogs.
    """

    # Mock external dependencies used by cogs on import/init
    with patch("util.tables.get_rows_from_view", return_value=[]), \
         patch("util.tables.get_scheme", return_value={"columns": []}), \
         patch("util.tables.get_defaults", return_value={}):

        # We walk through the 'oscar.cogs' package
        package = oscar.cogs
        prefix = package.__name__ + "."

        loaded_extensions = []
        failed_extensions = []

        for _, name, _ in pkgutil.walk_packages(package.__path__, prefix):
            try:
                # load_extension calls the setup(bot) function in the cog
                await mock_bot.load_extension(name)
                loaded_extensions.append(name)
            except Exception as e:
                failed_extensions.append((name, str(e)))

        # Assert that we loaded at least something (assuming there are cogs)
        assert len(loaded_extensions) > 0, "No cogs were loaded!"

        # Fail if any cogs failed to load
        if failed_extensions:
            error_msg = "\n".join([f"{name}: {err}" for name, err in failed_extensions])
            pytest.fail(f"Failed to load the following extensions:\n{error_msg}")
