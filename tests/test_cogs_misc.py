"""Tests for Helper and Examples Cogs."""

import pytest
from unittest.mock import MagicMock, AsyncMock
import discord

from oscar.cogs.examples import Examples, get_pagination_embed, ButtonsView
from oscar.cogs.help import Help as HelpCog

# --- Examples Cog Tests ---

class TestExamplesCog:
    async def test_init_generates_sample_data(self):
        bot = MagicMock(spec=discord.ext.commands.Bot)
        cog = Examples(bot)
        assert cog.bot is bot
        assert len(cog.sample_data) == 64
        assert cog.sample_data[0]["id"] == 1
        assert cog.sample_data[0]["name"] == "Example 1"

    async def test_sample_data_statuses_cycle(self):
        bot = MagicMock(spec=discord.ext.commands.Bot)
        cog = Examples(bot)
        statuses = ["Active", "Inactive", "Pending", "Error"]
        for i, item in enumerate(cog.sample_data):
            assert item["status"] == statuses[i % 4]

# --- Helper Function Tests ---

class TestGetPaginationEmbed:
    def test_default_creates_embed(self):
        embed = get_pagination_embed()
        assert isinstance(embed, discord.Embed)
        assert embed.title == 'Pagination - Example'

    def test_with_existing_embed(self):
        base = discord.Embed(title="Custom", color=0xFF0000)
        embed = get_pagination_embed(index=1, embed=base)
        assert embed.title == "Custom"
        assert len(embed.fields) == 1

    def test_index_clamped_to_valid_range(self):
        embed = get_pagination_embed(index=-5)
        assert "1/" in embed.fields[0].name

        embed2 = get_pagination_embed(index=999)
        assert "4/" in embed2.fields[0].name


# --- ButtonsView Tests (Examples) ---

class TestButtonsView:
    async def test_init(self):
        interaction = MagicMock(spec=discord.Interaction)
        view = ButtonsView(interaction=interaction, enabled=True)
        assert view.enabled is True

    async def test_init_disabled(self):
        interaction = MagicMock(spec=discord.Interaction)
        view = ButtonsView(interaction=interaction, enabled=False)
        assert view.enabled is False

    async def test_setup_sends_embed(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()
        view = ButtonsView(interaction=interaction, enabled=True)
        await view.setup()
        interaction.response.send_message.assert_called_once()


# --- Help Cog Tests ---

class TestHelpCog:
    def test_init(self):
        bot = MagicMock(spec=discord.ext.commands.Bot)
        cog = HelpCog(bot)
        assert cog.bot is bot

    async def test_setup(self):
        from oscar.cogs.help import setup
        bot = MagicMock(spec=discord.ext.commands.Bot)
        bot.add_cog = AsyncMock()
        await setup(bot)
        bot.add_cog.assert_called_once()
