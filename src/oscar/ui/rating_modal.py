""" This module provides the modal dialog for rating a module."""

import discord
from discord import ui
from discord.ui import TextInput

from util.database import get_database
from util.enums import LanguageCode
from util.module import Module
from util.translations import RATING_TEXTS, t


class ModuleRatingModal(ui.Modal):
    """ Modal dialog allowing students to evaluate a module."""

    def __init__(self, module: Module, language: LanguageCode):
        title = t(language, "rate_title", RATING_TEXTS)
        super().__init__(title=f"{title}: {module.abbreviation}"[:45])
        self.module: Module = module
        self.language: LanguageCode = language

        self.rating_input: TextInput[ui.Modal] = TextInput(
            label=t(language, "score_label", RATING_TEXTS),
            placeholder="1 - 5 (⭐)",
            min_length=1,
            max_length=1,
            required=True,
        )
        self.difficulty_input: TextInput[ui.Modal] = TextInput(
            label=t(language, "difficulty_label", RATING_TEXTS),
            placeholder="1 - 5 (1=leicht, 5=schwer)",
            min_length=1,
            max_length=1,
            required=True,
        )
        self.comment_input: TextInput[ui.Modal] = TextInput(
            label=t(language, "comment_label", RATING_TEXTS),
            style=discord.TextStyle.long,
            placeholder="Tipps für zukünftige Studierende...",
            required=False,
            max_length=500,
        )

        _ = self.add_item(self.rating_input)
        _ = self.add_item(self.difficulty_input)
        _ = self.add_item(self.comment_input)

    async def on_submit(self, interaction: discord.Interaction):  # pylint: disable=arguments-differ
        """ Handles submission of the rating form."""

        rating_raw = self.rating_input.value.strip()
        diff_raw = self.difficulty_input.value.strip()

        if not (rating_raw.isdigit() and diff_raw.isdigit()):
            await interaction.response.send_message(
                t(self.language, "invalid_input", RATING_TEXTS),
                ephemeral=True,
            )
            return

        rating = int(rating_raw)
        difficulty = int(diff_raw)

        if not (1 <= rating <= 5 and 1 <= difficulty <= 5):
            await interaction.response.send_message(
                t(self.language, "invalid_input", RATING_TEXTS),
                ephemeral=True,
            )
            return

        comment = self.comment_input.value.strip() or None

        db = get_database()
        db.rate_module(
            user_id=interaction.user.id,
            module_id=self.module.id_,
            rating=rating,
            difficulty=difficulty,
            comment=comment,
        )

        msg = t(self.language, "rate_success", RATING_TEXTS).format(
            title=self.module.get_title(self.language),
            rating=rating,
            difficulty=difficulty,
        )
        await interaction.response.send_message(msg, ephemeral=True)
