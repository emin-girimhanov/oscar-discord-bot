""" The cog behind `/my_data`, the students own copy of their data and its delete key.

    The privacy policy promises two things this command has to deliver: a student
    may see everything we hold about them, and may have it removed. Until now the
    policy pointed at an email address, and section 6.5 already spoke of deleting
    your data "via bot command".
"""

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from oscar.ui.my_data_view import MyDataView, has_data
from util.database import get_database, get_user_language
from util.enums import LanguageCode
from util.translations import MY_DATA_TEXTS, t
from util.typed_dicts import UserDataDict


class MyData(commands.Cog):
    """ Class for the command that shows and deletes one students own data."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded MyData cog")

    @app_commands.command(
        name="my_data",
        description="Deine gespeicherten Daten ansehen und löschen (see and delete your data)",
    )
    async def my_data(self, interaction: discord.Interaction):
        """ Shows the caller their stored data and offers to delete it.

            The answer is ephemeral, and stays ephemeral. This is the one command
            whose message holds a students discord id, their programme and their
            free text feedback all at once.

            Parameters:
                interaction: automatically provided interaction object.
        """
        user_id: int = interaction.user.id
        language: LanguageCode = get_user_language(user_id)
        data: UserDataDict = get_database().export_user_data(user_id)

        if not has_data(data):
            # an empty file would look like a fault, or worse, like a loss
            _ = await interaction.response.send_message(
                t(language, "nothing_stored", MY_DATA_TEXTS),
                ephemeral=True,
            )
            return

        _ = await interaction.response.send_message(
            view=MyDataView(user_id, data, language),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    """ Setup the MyData cog."""
    await bot.add_cog(MyData(bot))
