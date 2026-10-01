""" Deadlines and Examination milestones cog for OSCAR."""

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from oscar.ui.help_launcher import open_deadlines


class Deadlines(commands.Cog):
    """Cog for semester milestones, exam registration windows, and academic deadlines."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded Deadlines cog")

    @app_commands.command(
        name="fristen",
        description="Zeigt wichtige Prüfungs- und Semesterfristen der FIN & OVGU"
    )
    async def fristen(self, interaction: discord.Interaction):
        """Command to display exam registration periods and semester milestones."""
        await open_deadlines(interaction)

    @app_commands.command(
        name="deadlines",
        description="Show examination deadlines and semester milestones"
    )
    async def deadlines(self, interaction: discord.Interaction):
        """English alias command to display examination deadlines and milestones."""
        await open_deadlines(interaction)


async def setup(bot: commands.Bot):
    """Setup the Deadlines cog."""
    await bot.add_cog(Deadlines(bot))
