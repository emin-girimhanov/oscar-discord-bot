""" Deadlines and Examination milestones cog for OSCAR."""

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from loguru import logger

from oscar.ui.help_launcher import open_deadlines


class Deadlines(commands.Cog):
    """Cog for semester milestones, exam registration windows, and academic deadlines."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded Deadlines cog")

    # one command, a German client sees it as `/fristen`, see `oscar.localization`
    @app_commands.command(
        name=locale_str("deadlines", de="fristen"),
        description=locale_str(
            "Roughly what is due when in the semester",
            de="Was im Semester ungefähr wann ansteht",
        ),
    )
    async def deadlines(self, interaction: discord.Interaction):
        """Command to display exam registration periods and semester milestones."""
        await open_deadlines(interaction)


async def setup(bot: commands.Bot):
    """Setup the Deadlines cog."""
    await bot.add_cog(Deadlines(bot))
