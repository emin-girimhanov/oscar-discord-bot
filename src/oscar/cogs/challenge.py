""" Code Golf and Weekly Programming Challenges cog for OSCAR."""

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from oscar.ui.challenge_view import ChallengeView
from util.challenges import get_challenge_by_number, get_current_weekly_challenge
from util.database import get_user_language
from util.enums import LanguageCode


class ChallengeCog(commands.Cog):
    """Cog providing weekly code golf challenges and leaderboards."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded ChallengeCog")

    async def _handle_challenge_command(
        self,
        interaction: discord.Interaction,
        challenge_nr: int | None = None,
        rangliste: bool = False,
    ) -> None:
        """Internal handler for challenge and codegolf slash commands."""
        _ = await interaction.response.defer(ephemeral=True)
        user_lang: LanguageCode = get_user_language(interaction.user.id)

        target_challenge_id: str | None = None
        if challenge_nr is not None:
            c = get_challenge_by_number(challenge_nr)
            if c is not None:
                target_challenge_id = c.id

        if target_challenge_id is None:
            target_challenge_id = get_current_weekly_challenge().id

        view = ChallengeView(
            default_language=user_lang,
            initial_challenge_id=target_challenge_id,
            initial_show_leaderboard=rangliste,
        )

        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(
        name="codegolf",
        description="Wöchentliche Code-Golf-Challenge & Bestenliste (Weekly Code Golf)",
    )
    @app_commands.describe(
        nummer="Optionale Nummer der Challenge (1-10)",
        rangliste="Direkt die Rangliste / Leaderboard anzeigen",
    )
    async def codegolf(
        self,
        interaction: discord.Interaction,
        nummer: int | None = None,
        rangliste: bool = False,
    ):
        """Opens the Code Golf interactive challenge view."""
        await self._handle_challenge_command(
            interaction, challenge_nr=nummer, rangliste=rangliste
        )

    @app_commands.command(
        name="challenge",
        description="Wöchentliche Programmier-Challenge & Rangliste (Weekly Code Golf)",
    )
    @app_commands.describe(
        nummer="Optionale Nummer der Challenge (1-10)",
        rangliste="Direkt die Rangliste / Leaderboard anzeigen",
    )
    async def challenge(
        self,
        interaction: discord.Interaction,
        nummer: int | None = None,
        rangliste: bool = False,
    ):
        """Alias for /codegolf to view weekly programming challenge."""
        await self._handle_challenge_command(
            interaction, challenge_nr=nummer, rangliste=rangliste
        )


async def setup(bot: commands.Bot):
    """Cog setup method"""
    await bot.add_cog(ChallengeCog(bot))
