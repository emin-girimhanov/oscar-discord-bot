"""This module houses the base class for the oscar bot and its setup code"""

import asyncio
import importlib
import os
import pkgutil
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger

from oscar.localization import GermanNames
from util.bookstack import drop_missing_books, refresh_books
from util.command_surface import HIDDEN
from util.database import get_database
from util.operators import is_operator
from util.semesterplans import get_semesterplans_manager
from util.tables import refresh_interval, warm_cache

oscar_cogs = importlib.import_module("oscar.cogs")

# How often the handbook links are read again. The slugs have changed twice within a
# day, and the round costs seventeen small requests, so four times a day is cheap.
HANDBOOK_REFRESH_SECONDS: int = 6 * 60 * 60


class Oscar(commands.Bot):
    """Custom Bot class for abstraction"""

    def __init__(
        self,
        *args: tuple[Any],  # pyright: ignore[reportExplicitAny]
        **kwargs: dict[str, Any]  # pyright: ignore[reportExplicitAny]
    ):
        # Forward all arguments, and keyword-only arguments to commands.Bot
        self.server_id: str
        self.bot_token: str
        self._startup_done: bool = False
        super().__init__(*args, **kwargs)
        # self.db = None    # To Do: establish database connection (maybe somewhere else?)

        if not load_dotenv():
            logger.warning("No Environment Variables File found.")

        try:
            self.server_id = os.environ[
                "DISCORD_SERVER_ID"
            ]  # Hole dir die Server-ID aus der Umgebungsvariablen
        except KeyError as exc:
            logger.exception(
                "DISCORD_SERVER_ID Environment Variable not set, terminating."
            )
            raise RuntimeError("Constructor failed") from exc

        try:
            self.bot_token = os.environ["BOT_TOKEN"]
        except KeyError as exc:
            logger.exception("BOT_TOKEN Environment Variable not set, terminating.")
            raise RuntimeError("Constructor failed") from exc

        # ensure db is ready, and semesterplans are loaded:
        _ = get_database()
        _ = get_semesterplans_manager()

    async def sync_commands(self) -> list[discord.app_commands.AppCommand]:
        """Registers all app commands in exactly one scope.

        Discord keeps global and guild commands apart and lists **both**, so a command
        registered in both scopes shows up twice in the picker. Whichever scope is used
        here, the other one is emptied first.

        `OSCAR_COMMAND_SCOPE` picks the scope:

        * `global` (default) reaches every server the bot is in, including ones it joins
          later. A client can take up to an hour to notice a change.
        * `guild` registers only in the servers the bot is in right now. Those appear at
          once, which is what you want while developing.
        """
        scope: str = os.environ.get("OSCAR_COMMAND_SCOPE", "global").strip().lower()

        if scope == "guild":
            # copy first, clearing the global set below also empties the local tree
            for guild in self.guilds:
                self.tree.clear_commands(guild=guild)
                self.tree.copy_global_to(guild=guild)
                guild_synced = await self.tree.sync(guild=guild)
                logger.info(
                    f"Synced {len(guild_synced)} commands to '{guild.name}' ({guild.id})"
                )

            self.tree.clear_commands(guild=None)
            synced = await self.tree.sync()
            logger.info(f"Cleared the global commands, {len(synced)} left")
            return synced

        if scope != "global":
            logger.warning(f"Unknown OSCAR_COMMAND_SCOPE '{scope}', falling back to global")

        # drop any per guild copies, otherwise every command is listed twice
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
            _ = await self.tree.sync(guild=guild)
            logger.info(f"Cleared guild commands in '{guild.name}' ({guild.id})")

        synced = await self.tree.sync()
        logger.info(
            f"Synced {len(synced)} global application commands: "
            f"{[command.name for command in synced]}"
        )
        return synced

    def hide_commands(self) -> list[str]:
        """ Takes the commands that are switched off out of the tree before it syncs.

            The cogs still define them, so nothing else has to know. A command that is
            not in the tree is not sent to discord, and discord drops it from the
            picker on the next sync.

            Returns:
                The names that were taken out, for the log.
        """
        removed: list[str] = []
        for name in sorted(HIDDEN):
            if self.tree.remove_command(name) is not None:
                removed.append(name)
        return removed

    async def keep_tables_warm(self):
        """ Fills the module table cache before anybody asks for it, and keeps it full.

            Reading the table takes about a second and a half, and it is a blocking
            request made from inside a command handler. So the first command after a
            restart, and the first one after the ten minute cache expired, held up the
            whole bot for that long. Discord gives an interaction three seconds before
            it tells the student the application did not respond.

            Warming it here costs one request every nine minutes on a thread nobody
            waits for, and takes a cold `/module` from 1620 ms down to 5 ms.
        """
        while not self.is_closed():
            try:
                _ = await asyncio.to_thread(warm_cache)
            except Exception:  # pylint: disable=broad-exception-caught
                # the next round tries again, and a command still works, it just pays
                # for the cold cache itself
                logger.exception("Could not warm the module table")
            await asyncio.sleep(refresh_interval())

    async def keep_handbook_links_fresh(self):
        """ Finds the module handbooks again whenever BookStack renames them.

            The page map in the image is a snapshot. Two weeks after it was written
            eleven of its thirteen books answered 404, and every handbook button
            opened a search instead of the module. Reading the map again takes about
            five seconds on a thread nobody waits for.

            `refresh_books` finds a renamed book under its new slug. `drop_missing_books`
            runs after it and turns whatever is still dead into a search, so a student
            never lands on an error page.
        """
        while not self.is_closed():
            try:
                _ = await asyncio.to_thread(refresh_books)
                _ = await asyncio.to_thread(drop_missing_books)
            except Exception:  # pylint: disable=broad-exception-caught
                # the links of the last round keep working, the next round tries again
                logger.exception("Could not refresh the module handbook links")
            await asyncio.sleep(HANDBOOK_REFRESH_SECONDS)

    def setup_bot(self):
        """Sets up (automatically loads all available cogs) and runs the bot instance"""
        self._startup_done: bool = False

        @self.event
        async def on_ready():  # pyright: ignore[reportUnusedFunction]
            revision = os.environ.get("OSCAR_REVISION", "unknown (local run)")
            logger.info(f"Logged in as {self.user}, running build {revision}")

            # on_ready fires again after every reconnect
            if self._startup_done:
                return

            for _, name, _ in pkgutil.walk_packages(
                oscar_cogs.__path__, oscar_cogs.__name__ + "."
            ):
                try:
                    await self.load_extension(name)
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.exception(f"Couldn't load '{name}'")

            # without a translator discord.py sends the names in one language only
            await self.tree.set_translator(GermanNames())

            hidden = self.hide_commands()
            if hidden:
                logger.info(f"Switched off, see util.command_surface.HIDDEN: {hidden}")

            _ = await self.sync_commands()
            self._startup_done = True

            # The faculty renames a BookStack book whenever an edition rolls over, and
            # the module handbook button then opens a 404.
            _ = asyncio.create_task(self.keep_handbook_links_fresh())

            # Nobody should be the one who waits for the module table.
            _ = asyncio.create_task(self.keep_tables_warm())

        async def on_app_command_error(
            interaction: discord.Interaction, error: app_commands.AppCommandError
        ):
            # without this, any exception shows up as a silent "application did not respond"
            if isinstance(error, app_commands.CheckFailure):
                message = ("Du darfst diesen Befehl nicht nutzen. "
                           "/ You are not allowed to use this command.")
            else:
                name = interaction.command.name if interaction.command else "?"
                logger.opt(exception=error).error(f"Command '/{name}' failed")
                message = ("Da ist leider etwas schiefgelaufen, versuch es bitte später nochmal. "
                           "/ Something went wrong, please try again later.")
            try:
                if interaction.response.is_done():
                    _ = await interaction.followup.send(message, ephemeral=True)
                else:
                    _ = await interaction.response.send_message(message, ephemeral=True)
            except discord.HTTPException:
                logger.exception("Couldn't send the error message to the user")

        self.tree.on_error = on_app_command_error

        async def operator_only(ctx: commands.context.Context[commands.Bot]) -> bool:
            # `has_permissions(administrator=True)` let the administrator of any server
            # in, and anybody can invite a public bot to a server of their own
            permissions = getattr(ctx.author, "guild_permissions", None)
            if is_operator(
                user_id=ctx.author.id,
                guild_id=ctx.guild.id if ctx.guild else None,
                is_administrator=bool(permissions is not None and permissions.administrator),
            ):
                return True
            return await self.is_owner(ctx.author)

        # Ping command to test deployment latency
        @self.command()
        @commands.check(operator_only)
        async def ping(  # pyright: ignore[reportUnusedFunction]
            ctx: commands.context.Context[commands.Bot]
        ):
            latency = round(self.latency, 2)
            logger.info(f"Latency is `{latency}ms`")
            _ = await ctx.send(f"Latency is {latency}ms")

        @self.command()
        @commands.check(operator_only)
        async def resync(  # pyright: ignore[reportUnusedFunction]
            ctx: commands.context.Context[commands.Bot]
        ):
            synced = await self.sync_commands()
            names = ", ".join(f"/{cmd.name}" for cmd in synced)
            # a prefix command needs no slash sync, so this always names the running build
            revision = os.environ.get("OSCAR_REVISION", "unknown (local run)")
            _ = await ctx.send(
                f"🔄 Build `{revision}` synced {len(synced)} commands "
                f"to {len(self.guilds)} server(s): {names}"
            )
