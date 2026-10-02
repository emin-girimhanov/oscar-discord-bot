""" Cog providing the /suggest and /recommend slash commands.

    Proposes tailored modules based on the student's study course, semester,
    open credit slots, and curated topic clusters (e.g. AI, Games, Systems).
"""

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from loguru import logger

from oscar.ui.suggest_view import SuggestView
from util.database import get_user_language


class ModuleSuggestions(commands.Cog):
    """Cog handling module recommendation and suggestion interactions."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded ModuleSuggestions cog")

    # one command, a German client sees it as `/empfehlung`, see `oscar.localization`
    @app_commands.command(
        name=locale_str("suggest", de="empfehlung"),
        description=locale_str(
            "Modules that fit your programme and your focus area",
            de="Module, die zu deinem Studiengang und Schwerpunkt passen",
        ),
    )
    @app_commands.describe(
        category=locale_str(
            "Choose a focus area (e.g. AI, Games, Systems, Scientific Computing)",
            de="Wähle einen Schwerpunkt (z.B. KI, Games, Systems, Scientific Computing)",
        ),
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(
                name=locale_str("Fitting my study programme", de="Passend zum Studiengang"),
                value="ALL",
            ),
            app_commands.Choice(
                name=locale_str("Artificial Intelligence (AI)", de="Künstliche Intelligenz (KI)"),
                value="AI",
            ),
            app_commands.Choice(
                name=locale_str(
                    "Computer Graphics & Games", de="Computergrafik & Digitale Spiele"
                ),
                value="ComputerGame",
            ),
            app_commands.Choice(
                name=locale_str("Software & Systems Engineering"),
                value="SystemsEngineering",
            ),
            app_commands.Choice(
                name=locale_str(
                    "Scientific Computing & Simulation",
                    de="Wissenschaftliches Rechnen & Simulation",
                ),
                value="ScientificComputing",
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


async def setup(bot: commands.Bot):
    """Sets up the ModuleSuggestions cog."""
    await bot.add_cog(ModuleSuggestions(bot))
