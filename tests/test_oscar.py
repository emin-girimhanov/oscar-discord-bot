import unittest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
import os
import discord
from discord.ext import commands
from oscar.oscar import Oscar
import pkgutil

class TestOscar(unittest.IsolatedAsyncioTestCase):
    def test_init_success(self):
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=True):
            bot = Oscar(command_prefix="!", intents=discord.Intents.default())
            self.assertEqual(bot.server_id, "123")
            self.assertEqual(bot.bot_token, "abc")

    def test_init_no_server_id(self):
        with patch.dict(os.environ, {"BOT_TOKEN": "abc"}, clear=True), \
             patch("oscar.oscar.load_dotenv", return_value=True):
             if "DISCORD_SERVER_ID" in os.environ:
                 del os.environ["DISCORD_SERVER_ID"]

             with self.assertRaises(RuntimeError):
                 Oscar(command_prefix="!", intents=discord.Intents.default())

    def test_init_no_token(self):
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123"}, clear=True), \
             patch("oscar.oscar.load_dotenv", return_value=True):
             if "BOT_TOKEN" in os.environ:
                 del os.environ["BOT_TOKEN"]

             with self.assertRaises(RuntimeError):
                 Oscar(command_prefix="!", intents=discord.Intents.default())

    def test_init_no_dotenv(self):
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=False), \
             patch("oscar.oscar.logger") as mock_logger:
            _ = Oscar(command_prefix="!", intents=discord.Intents.default())
            mock_logger.warning.assert_called_once()

    async def test_setup_bot(self):
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=True):
            bot = Oscar(command_prefix="!", intents=discord.Intents.default())

        captured_events = {}
        def event_decorator(func):
            captured_events[func.__name__] = func
            return func

        bot.event = event_decorator
        bot.command = MagicMock()
        # Mock methods on the existing tree object
        bot.tree.clear_commands = MagicMock()
        bot.tree.copy_global_to = MagicMock()
        bot.tree.sync = AsyncMock(return_value=[])

        bot.load_extension = AsyncMock()

        with patch("pkgutil.walk_packages", return_value=[(None, "ext1", None), (None, "ext2", None)]), \
             patch("oscar.oscar.oscar_cogs") as mock_cogs:

             mock_cogs.__path__ = ["/fake/path"]
             mock_cogs.__name__ = "oscar.cogs"

             bot.setup_bot()
             self.assertTrue(bot.command.called)

             await captured_events["on_ready"]()
             self.assertEqual(bot.load_extension.call_count, 2)
             bot.load_extension.assert_any_call("ext1")
             bot.tree.sync.assert_called_with()

             # a reconnect must not reload cogs or sync again
             await captured_events["on_ready"]()
             self.assertEqual(bot.load_extension.call_count, 2)
             self.assertEqual(bot.tree.sync.call_count, 1)

    @staticmethod
    def _bot_with_two_guilds():
        """Builds a bot whose tree is mocked and that reports two guilds."""
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=True):
            bot = Oscar(command_prefix="!", intents=discord.Intents.default())

        bot.tree.clear_commands = MagicMock()
        bot.tree.copy_global_to = MagicMock()
        bot.tree.sync = AsyncMock(return_value=[])
        return bot, MagicMock(), MagicMock()

    async def test_sync_commands_global_scope_clears_the_guild_copies(self):
        """Discord lists both scopes, so the guild copies must go or every command doubles."""
        bot, guild_a, guild_b = self._bot_with_two_guilds()

        with patch.object(type(bot), "guilds", new_callable=unittest.mock.PropertyMock,
                          return_value=[guild_a, guild_b]), \
             patch.dict(os.environ, {"OSCAR_COMMAND_SCOPE": "global"}):
            await bot.sync_commands()

        bot.tree.clear_commands.assert_any_call(guild=guild_a)
        bot.tree.clear_commands.assert_any_call(guild=guild_b)
        # nothing may be copied into a guild in this scope
        bot.tree.copy_global_to.assert_not_called()
        # the last call is the global one
        bot.tree.sync.assert_called_with()

    async def test_sync_commands_defaults_to_global_scope(self):
        """Without the variable the safe scope is used."""
        bot, guild_a, _ = self._bot_with_two_guilds()

        env = {k: v for k, v in os.environ.items() if k != "OSCAR_COMMAND_SCOPE"}
        with patch.object(type(bot), "guilds", new_callable=unittest.mock.PropertyMock,
                          return_value=[guild_a]), \
             patch.dict(os.environ, env, clear=True):
            await bot.sync_commands()

        bot.tree.copy_global_to.assert_not_called()
        bot.tree.sync.assert_called_with()

    async def test_sync_commands_guild_scope_clears_the_global_set(self):
        """The guild scope is instant, so the global set must go or every command doubles."""
        bot, guild_a, guild_b = self._bot_with_two_guilds()

        with patch.object(type(bot), "guilds", new_callable=unittest.mock.PropertyMock,
                          return_value=[guild_a, guild_b]), \
             patch.dict(os.environ, {"OSCAR_COMMAND_SCOPE": "guild"}):
            await bot.sync_commands()

        bot.tree.copy_global_to.assert_any_call(guild=guild_a)
        bot.tree.copy_global_to.assert_any_call(guild=guild_b)
        bot.tree.sync.assert_any_call(guild=guild_a)
        bot.tree.sync.assert_any_call(guild=guild_b)
        # the global set is emptied last, after the guilds already have their copies
        bot.tree.clear_commands.assert_any_call(guild=None)
        bot.tree.sync.assert_called_with()

    async def test_setup_bot_load_extension_failure(self):
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=True):
            bot = Oscar(command_prefix="!", intents=discord.Intents.default())

        captured_events = {}
        def event_decorator(func):
            captured_events[func.__name__] = func
            return func
        bot.event = event_decorator
        bot.tree.clear_commands = MagicMock()
        bot.tree.copy_global_to = MagicMock()
        bot.tree.sync = AsyncMock(return_value=[])
        bot.load_extension = AsyncMock(side_effect=Exception("Failed"))

        with patch("pkgutil.walk_packages", return_value=[(None, "ext1", None)]), \
             patch("oscar.oscar.oscar_cogs") as mock_cogs, \
             patch("oscar.oscar.logger") as mock_logger:

             mock_cogs.__path__ = ["/fake/path"]
             mock_cogs.__name__ = "oscar.cogs"

             bot.setup_bot()
             await captured_events["on_ready"]()
             mock_logger.exception.assert_called()


    async def test_ping_command(self):
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=True):
            bot = Oscar(command_prefix="!", intents=discord.Intents.default())

        captured_commands = {}
        def command_decorator():
            def wrapper(func):
                captured_commands[func.__name__] = func
                return func
            return wrapper

        bot.command = command_decorator
        bot.setup_bot()

        ping_func = captured_commands.get("ping")
        self.assertIsNotNone(ping_func)

        ctx = MagicMock(spec=commands.Context)
        ctx.send = AsyncMock()

        # Mock latency property
        type(bot).latency = unittest.mock.PropertyMock(return_value=0.123)

        await ping_func(ctx)

        ctx.send.assert_called()

    async def test_resync_command(self):
        with patch.dict(os.environ, {"DISCORD_SERVER_ID": "123", "BOT_TOKEN": "abc"}), \
             patch("oscar.oscar.load_dotenv", return_value=True):
            bot = Oscar(command_prefix="!", intents=discord.Intents.default())

        captured_commands = {}
        def command_decorator():
            def wrapper(func):
                captured_commands[func.__name__] = func
                return func
            return wrapper

        bot.command = command_decorator
        bot.tree.clear_commands = MagicMock()
        bot.tree.copy_global_to = MagicMock()
        bot.tree.sync = AsyncMock()

        bot.setup_bot()

        resync_func = captured_commands.get("resync")

        ctx = MagicMock(spec=commands.Context)
        ctx.send = AsyncMock()

        cmd_mock = MagicMock()
        cmd_mock.name = "cmd1"
        bot.tree.sync.return_value = [cmd_mock]

        with patch.dict(os.environ, {"OSCAR_REVISION": "abc1234"}):
            await resync_func(ctx)

        bot.tree.sync.assert_called_with()
        ctx.send.assert_called_once()
        reply = ctx.send.call_args.args[0]
        self.assertIn("/cmd1", reply)
        # !resync is a prefix command, so its reply names the build even without a slash sync
        self.assertIn("abc1234", reply)
