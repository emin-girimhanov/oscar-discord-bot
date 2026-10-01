""" This module holds a variety of different button types"""


from collections.abc import Awaitable
from typing import Callable, override
import discord
from discord.ui import Button, LayoutView


# pylint: disable=R0902  # (too-many-instance-attributes)
class ToggleButton(Button[LayoutView]):
    """ Toggle button class that switches between two states"""

    toggle_state: bool
    label_on: str
    label_off: str
    style_on: discord.ButtonStyle
    style_off: discord.ButtonStyle
    on_changed: Callable[[discord.Interaction, bool], Awaitable[None]] | None

    # pylint: disable=R0913  # (too-many-arguments)
    # pylint: disable=R0917  # (too-many-positional-arguments)
    def __init__(
        self,
        state: bool = True,
        label_on: str = "✔",
        label_off: str = "✘",
        style_on: discord.ButtonStyle = discord.ButtonStyle.success,
        style_off: discord.ButtonStyle = discord.ButtonStyle.danger,
        on_changed: Callable[[discord.Interaction, bool], Awaitable[None]] | None = None,
    ):
        self.toggle_state = state
        self.label_on = label_on
        self.label_off = label_off
        self.style_on = style_on
        self.style_off = style_off
        self.on_changed = on_changed

        super().__init__(
            label=label_on if state else label_off,
            style=style_on if state else style_off,
        )


    @override
    async def callback(self, interaction: discord.Interaction):
        self.toggle_state = not self.toggle_state

        self.label: str = self.label_on if self.toggle_state else self.label_off
        self.style: discord.ButtonStyle = self.style_on if self.toggle_state else self.style_off

        if self.on_changed:
            await self.on_changed(interaction, self.toggle_state)

        # makes sure to always update the button state
        if interaction.response.is_done():
            _ = await interaction.edit_original_response(view=self.view)
        else:
            _ = await interaction.response.edit_message(view=self.view)
