"""Tests for UI components (Buttons, etc.)."""
# pylint: disable=protected-access, trailing-whitespace

from unittest.mock import MagicMock, AsyncMock
import discord

from oscar.ui.buttons import ToggleButton
from oscar.ui.select_button import (
    SelectButton,
    FilterButton,
    InfoButton,
    DeleteButton,
)

# --- ToggleButton tests ---

class TestToggleButton:
    def test_init_default_state_true(self):
        btn = ToggleButton(state=True, label_on="ON", label_off="OFF")
        assert btn.toggle_state is True
        assert btn.label == "ON"

    def test_init_default_state_false(self):
        btn = ToggleButton(state=False, label_on="ON", label_off="OFF")
        assert btn.toggle_state is False
        assert btn.label == "OFF"

    def test_init_custom_styles(self):
        btn = ToggleButton(
            state=True,
            style_on=discord.ButtonStyle.primary,
            style_off=discord.ButtonStyle.danger,
        )
        assert btn.style == discord.ButtonStyle.primary

    def test_init_with_on_changed(self):
        callback = AsyncMock()
        btn = ToggleButton(on_changed=callback)
        assert btn.on_changed is callback

    async def test_callback_toggles_state(self):
        btn = ToggleButton(state=True, label_on="ON", label_off="OFF")
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.is_done = MagicMock(return_value=True) # property mocked? No, is_done() method on some versions?
        # In discord.py 2.0+, interaction.response.is_done() checks if response sent.
        # But wait, interaction.response.is_done() is a method.
        # Let's mock it properly.
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = True

        interaction.edit_original_response = AsyncMock()
        btn._view = MagicMock()

        await btn.callback(interaction)
        assert btn.toggle_state is False
        assert btn.label == "OFF"

    async def test_callback_calls_on_changed(self):
        """
        Dieser Test prüft, ob eine Aktion (ein Callback) ausgelöst wird,
        wenn wir den Button "klicken".
        """
        # 1. Vorbereitung (Mocking)
        callback = AsyncMock() # Eine "falsche" Funktion, die aufzeichnet, ob sie gerufen wurde.
        btn = ToggleButton(state=False, on_changed=callback)

        interaction = MagicMock(spec=discord.Interaction) # Wir simulieren eine Discord-Interaktion.
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()
        btn._view = MagicMock()

        # 2. Aktion: Wir rufen den Callback manuell auf, als hätte ein User geklickt.
        await btn.callback(interaction)

        # 3. Überprüfung: Hat der Button unsere falsche Funktion aufgerufen?
        callback.assert_called_once_with(interaction, True)


# --- SelectButton / FilterButton / InfoButton / DeleteButton tests ---

class TestButtonClasses:
    async def test_select_button_init(self):
        btn = SelectButton(label="Test", group="mygroup")
        assert btn.label == "Test"
        assert btn.group == "mygroup"
        assert btn.selected is False
        assert btn.style == discord.ButtonStyle.secondary

    async def test_filter_button_init(self):
        btn = FilterButton(label="Filter", group="cat")
        assert btn.label == "Filter"
        assert btn.group == "cat"
        assert btn.selected is False

    async def test_info_button_init(self):
        btn = InfoButton(label="Info", module="Mathe I")
        assert btn.label == "Info"
        assert btn.module_name == "Mathe I"

    async def test_delete_button_init(self):
        mock_view = MagicMock()
        mock_module = MagicMock()
        btn = DeleteButton(view=mock_view, module=mock_module)
        assert btn.label == "X"
        assert btn.style == discord.ButtonStyle.danger
        assert btn.view_ref is mock_view
        assert btn.module is mock_module
