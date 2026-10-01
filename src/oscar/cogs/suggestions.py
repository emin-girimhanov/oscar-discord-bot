""" Cog providing the /suggest and /recommend slash commands.

    Proposes tailored modules based on the student's study course, semester,
    open credit slots, and curated topic clusters (e.g. AI, Games, Systems).
"""

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from oscar.ui.suggest_view import SuggestView
from util.database import get_user_language


class ModuleSuggestions(commands.Cog):
    """Cog handling module recommendation and suggestion interactions."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded ModuleSuggestions cog")

    @app_commands.command(
        name="suggest",
        description="Erhalte passende Modul-Empfehlungen für dein Studium & Schwerpunkte",
    )
    @app_commands.describe(
        category="Wähle einen Schwerpunkt (z.B. KI, Games, Systems, Scientific Computing)",
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="🎯 Passend zum Studiengang", value="ALL"),
            app_commands.Choice(name="🤖 Künstliche Intelligenz (KI / AI)", value="AI"),
            app_commands.Choice(name="🎮 Computergrafik & Digitale Spiele", value="ComputerGame"),
            app_commands.Choice(
                name="💻 Software & Systems Engineering", value="SystemsEngineering"
            ),
            app_commands.Choice(
                name="🔬 Wissenschaftliches Rechnen & Simulation", value="ScientificComputing"
            ),
        ]
    )
    async def suggest(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str] | None = None,
    ):
        """Displays module recommendations based on course, semester, or topic."""
        _ = await interaction.response.defer(ephemeral=True)
        user_lang = get_user_language(interaction.user.id)
        cat_key = category.value if category else "ALL"
        await interaction.followup.send(
            view=SuggestView(
                user_id=interaction.user.id,
                initial_category=cat_key,
                default_language=user_lang,
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="recommend",
        description="Get tailored module proposals for your study programme & focus area",
    )
    @app_commands.describe(
        category="Choose a focus area (e.g. AI, Games, Systems, Scientific Computing)",
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="🎯 Fitting my study programme", value="ALL"),
            app_commands.Choice(name="🤖 Artificial Intelligence (AI)", value="AI"),
            app_commands.Choice(name="🎮 Computer Graphics & Games", value="ComputerGame"),
            app_commands.Choice(
                name="💻 Software & Systems Engineering", value="SystemsEngineering"
            ),
            app_commands.Choice(
                name="🔬 Scientific Computing & Simulation", value="ScientificComputing"
            ),
        ]
    )
    async def recommend(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str] | None = None,
    ):
        """English alias for module suggestions."""
        await self.suggest(interaction, category)


async def setup(bot: commands.Bot):
    """Sets up the ModuleSuggestions cog."""
    await bot.add_cog(ModuleSuggestions(bot))
