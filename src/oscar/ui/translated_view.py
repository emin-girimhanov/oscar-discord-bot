""" This module contains an abstract view for handeling translation"""


import discord
from discord.ui import LayoutView
from loguru import logger

from oscar.ui.buttons import ToggleButton
from util.enums import LanguageCode
from util.translations import LANGUAGES


class TranslatedView(LayoutView):
    """Base class for views that support language switching with a toggle button."""

    def __init__(self, default_language: LanguageCode = LanguageCode.EN):
        super().__init__()
        self.language_code: LanguageCode = default_language
        # True = English, False = German
        self.toggle_state: bool = default_language == LanguageCode.EN
        self._build_view()

    def _build_view(self) -> None:
        """Build the view components. Must be implemented by subclasses."""
        _ = self.clear_items()
        self._build_content()

    def _build_content(self) -> None:
        """Override this method in subclasses to build the actual content."""
        raise NotImplementedError("Subclasses must implement _build_content()")

    def _create_language_toggle(self) -> ToggleButton:
        """Create a language toggle button with proper labels."""
        return ToggleButton(
            state=self.toggle_state,
            label_on=LANGUAGES[LanguageCode.DE][LanguageCode.DE],  # Show "switch to German"
            label_off=LANGUAGES[LanguageCode.EN][LanguageCode.EN],  # Show "switch to English"
            style_on=discord.ButtonStyle.secondary,
            style_off=discord.ButtonStyle.secondary,
            on_changed=self._on_language_change,
        )

    async def _on_language_change(self, interaction: discord.Interaction, state: bool) -> None:
        """Handle language change from toggle button."""
        logger.debug(
            f"Changed language toggle state to {state} ({'English' if state else 'German'})"
        )

        # Update both the toggle state and language code
        self.toggle_state = state
        self.language_code = LanguageCode.EN if state else LanguageCode.DE

        await self._update(interaction)


    async def _update(self, interaction: discord.Interaction):
        """Update the view to reflect the new language."""
        logger.debug("Updating translated view")
        _ = self.clear_items()
        self._build_view()

        # Update the message with the new view
        if interaction.response.is_done():
            _ = await interaction.edit_original_response(view=self)
        else:
            _ = await interaction.response.edit_message(view=self)
