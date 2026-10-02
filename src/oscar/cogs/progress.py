""" Progress and Achievements cog for OSCAR."""

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from oscar.ui.help_launcher import open_progress
from oscar.ui.progress_view import ProgressView
from util.database import get_user_language


class Progress(commands.Cog):
    """Cog for personal study progress and gamification badges."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded Progress cog")

    @app_commands.command(
        name="badges",
        description="Deine Badges und Meilensteine (your badges and milestones)"
    )
    async def badges(self, interaction: discord.Interaction):
        """Command to display user achievements and gamification badges."""
        await open_progress(interaction)

    @app_commands.command(
        name="progress",
        description="Dein Studienfortschritt und deine Credit Points (your progress)"
    )
    async def progress(self, interaction: discord.Interaction):
        """Command to display user personal study progress and planned credit points."""
        await open_progress(interaction)

    @app_commands.command(
        name="cohort",
        description="Anonymisierte Kohorten-Statistiken (Anonymous cohort statistics)",
    )
    @app_commands.describe(
        studiengang="Optionaler Studiengang-Filter (e.g. BSC_INF)",
        semester="Optionaler Semester-Filter (1-12)",
    )
    async def cohort(
        self,
        interaction: discord.Interaction,
        studiengang: str | None = None,
        semester: int | None = None,
    ):
        """Command to display privacy-preserving cohort study progress metrics."""
        _ = await interaction.response.defer(ephemeral=True)
        user_lang = get_user_language(interaction.user.id)
        await interaction.followup.send(
            view=ProgressView(
                user_id=interaction.user.id,
                default_language=user_lang,
                initial_mode="cohort",
                target_major=studiengang,
                target_semester=semester,
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="statistik",
        description="Fakultätsweite und Kohorten-Statistiken (Faculty & cohort analytics)",
    )
    async def statistik(self, interaction: discord.Interaction):
        """Alias command for cohort and faculty statistics."""
        await self.cohort.callback(self, interaction)


async def setup(bot: commands.Bot):
    """Setup the Progress cog."""
    await bot.add_cog(Progress(bot))
