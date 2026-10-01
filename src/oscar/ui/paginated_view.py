""" Generic view able to perform pagination"""


from typing import Callable
import discord
from discord.interactions import Interaction
from discord.client import Client
from discord.ui import LayoutView, Button

class PaginatedView(discord.ui.View):
    """ Class holding a Paginated View"""
    def __init__(
            self,
            interaction: discord.Interaction,
            total_pages: int,
            get_page: Callable[[int], discord.Embed]
        ):
        self.interaction: Interaction[Client] = interaction
        self.total_pages: int = total_pages
        self.get_page: Callable[[int], discord.Embed] = get_page
        self.index:int = 0
        super().__init__(timeout=300)  # doesn't accept new interaction after <timeout> seconds

    async def check_user(self, interaction: discord.Interaction) -> bool:
        """ Chec weather the user has the right to perform the interaction"""
        if interaction.user == self.interaction.user:
            return True

        _ = await interaction.response.send_message(
            'Only the original auther can interact',
            ephemeral=True
        )
        return False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """ Runs `check_user` before any page button.

            `check_user` was written for this and then never called, so the page
            buttons stayed open to everyone in the channel. discord.py calls
            `interaction_check` by itself, which is the hook that actually runs.
        """
        return await self.check_user(interaction)

    async def setup(self):
        """ Setup the embed and button callbacks"""
        embed:discord.Embed = self.get_page(self.index)

        if self.total_pages <=1:
            _ = await self.interaction.response.send_message(embed=embed)
        else:
            self.__update_buttons()
            _ = await self.interaction.response.send_message(embed=embed, view=self)

    async def __update(self, interaction:discord.Interaction):
        embed:discord.Embed = self.get_page(self.index)
        self.__update_buttons()
        _ =await interaction.response.edit_message(embed=embed, view=self)

    #  ❮ ❯ > › ➧ ➤ ▶ ►   ℹ   ⏮ ◀ ▶ ⏭  » ≫ ⓘ
    #  ǀ❮   ❮   ❯   ❯ǀ
    #  ∣❮   ❮   ❯   ❯∣
    #  ⎪❮   ❮   ❯   ❯⎪
    #  ❘❮   ❮   ❯   ❯❘
    #  ❙❮   ❮   ❯   ❯❙        # This one looks the best imo
    #  ❚❮   ❮   ❯   ❯❚
    #  ┃❮   ❮   ❯   ❯┃
    #  │❮   ❮   ❯   ❯│
    #  ￨❮   ❮   ❯   ❯￨
    def __update_buttons(self):
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = False
        if self.index <= 1:
            if isinstance(self.children[0], Button):
                self.children[0].disabled = True
            if self.index <=0:
                if isinstance(self.children[1], Button):
                    self.children[1].disabled = True
        if self.index >= self.total_pages-2:
            if isinstance(self.children[3], Button):
                self.children[3].disabled = True
            if self.index >= self.total_pages-1:
                if isinstance(self.children[2], Button):
                    self.children[2].disabled = True

    @discord.ui.button(label='❙❮', style=discord.ButtonStyle.secondary)
    async def first(self, interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Callback for the skip to the first page button"""
        self.index = 0
        await self.__update(interaction=interaction)

    @discord.ui.button(label='❮', style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Callback for the previous page button"""
        self.index -= 1
        await self.__update(interaction=interaction)

    @discord.ui.button(label='❯', style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Callback for the next page button"""
        self.index += 1
        await self.__update(interaction=interaction)

    @discord.ui.button(label='❯❙', style=discord.ButtonStyle.secondary)
    async def last(self, interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Callback for the skip to the last page button"""
        self.index = self.total_pages-1
        await self.__update(interaction=interaction)
