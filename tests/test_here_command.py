"""`/here` answers with the module the current channel is named after.

The FinEmporium server keeps one channel per module, so the name of the channel
already says what the student is reading about. `/here` saves them typing the title
again, and it has to be honest about the three cases it can land in: it knows, it has
to ask, or it found nothing.

The matching itself is tested in `test_channel_module.py`. What is checked here is the
command around it: which channel name it reads, what it sends back, and that it never
opens a module it is not sure about.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from oscar.cogs.modul import ModulSearch, channel_name_of
from oscar.ui.channel_module_view import ChannelModuleView
from util.enums import LanguageCode
from util.tables import ModuleMatch


ROWS = [
    {"Identifizierung": 500100, "Modulsprache": 1, "Modultitel": "Datenbanken 1"},
    {"Identifizierung": 500200, "Modulsprache": 1, "Modultitel": "Datenbanken 2"},
    {"Identifizierung": 500300, "Modulsprache": 1, "Modultitel": "Logik"},
]

OWNER = 4711
STRANGER = 1337


def make_interaction(channel_name: str | None = "logik"):
    """An interaction that looks like `/here` typed in `#channel_name`."""
    interaction = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.user.id = OWNER
    if channel_name is None:
        # a direct message: discord hands over a channel without a name
        interaction.channel = MagicMock(spec=discord.DMChannel)
    else:
        channel = MagicMock(spec=discord.TextChannel)
        channel.name = channel_name
        interaction.channel = channel
    return interaction


def make_cog() -> ModulSearch:
    bot = MagicMock(spec=discord.ext.commands.Bot)
    return ModulSearch(bot)


class TestChannelNameOf:
    """Which name the command reads, before anything is searched."""

    def test_a_text_channel_gives_its_name(self):
        interaction = make_interaction("datenbanken")
        assert channel_name_of(interaction) == "datenbanken"

    def test_a_thread_gives_the_name_of_its_parent(self):
        """A thread is named after a question, the channel after the module."""
        parent = MagicMock(spec=discord.TextChannel)
        parent.name = "datenbanken"
        thread = MagicMock(spec=discord.Thread)
        thread.name = "wie war die klausur"
        thread.parent = parent
        interaction = MagicMock()
        interaction.channel = thread
        assert channel_name_of(interaction) == "datenbanken"

    def test_an_orphan_thread_falls_back_to_its_own_name(self):
        thread = MagicMock(spec=discord.Thread)
        thread.name = "datenbanken"
        thread.parent = None
        interaction = MagicMock()
        interaction.channel = thread
        assert channel_name_of(interaction) == "datenbanken"

    def test_a_direct_message_has_no_name(self):
        assert channel_name_of(make_interaction(None)) is None


class TestHereCommand:
    """The three answers the command may give."""

    @patch("oscar.cogs.modul.Catalogue")
    async def test_a_direct_message_is_told_to_use_module(self, _catalogue):
        """Without a channel name there is nothing to search for."""
        cog = make_cog()
        interaction = make_interaction(None)

        await cog.here_command.callback(cog, interaction)

        interaction.response.send_message.assert_awaited_once()
        message = interaction.response.send_message.call_args.args[0]
        assert "/module" in message
        interaction.followup.send.assert_not_awaited()

    @patch("oscar.cogs.modul.Catalogue")
    async def test_a_channel_about_no_module_says_so(self, catalogue_cls):
        """`#memes` gets an answer, not a wrong module."""
        catalogue = MagicMock()
        catalogue.get_modules.return_value = [
            ModuleMatch("Datenbanken 1", 500100, "Datenbanken 1"),
        ]
        catalogue_cls.return_value = catalogue

        cog = make_cog()
        interaction = make_interaction("memes")

        await cog.here_command.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        message = interaction.followup.send.call_args.args[0]
        assert "memes" in message
        assert "/module" in message

    @patch("oscar.cogs.modul.ModuleView")
    @patch("oscar.cogs.modul.Catalogue")
    @patch("util.module.get_rows")
    async def test_a_clear_channel_opens_the_module(
        self, mock_rows, catalogue_cls, view_cls
    ):
        mock_rows.return_value = ROWS
        catalogue = MagicMock()
        catalogue.get_modules.return_value = [
            ModuleMatch("Logik", 500300, "Logik"),
            ModuleMatch("Datenbanken 1", 500100, "Datenbanken 1"),
        ]
        catalogue_cls.return_value = catalogue

        cog = make_cog()
        interaction = make_interaction("logik")

        await cog.here_command.callback(cog, interaction)

        opened = view_cls.call_args.args[1]
        assert opened.id_ == 500300

    @patch("oscar.cogs.modul.ChannelModuleView")
    @patch("oscar.cogs.modul.ModuleView")
    @patch("oscar.cogs.modul.Catalogue")
    async def test_an_ambiguous_channel_asks_instead_of_guessing(
        self, catalogue_cls, module_view_cls, picker_cls
    ):
        """`#datenbanken` is either part 1 or part 2, and the bot may not decide."""
        catalogue = MagicMock()
        catalogue.get_modules.return_value = [
            ModuleMatch("Datenbanken 1", 500100, "Datenbanken 1"),
            ModuleMatch("Datenbanken 2", 500200, "Datenbanken 2"),
        ]
        catalogue_cls.return_value = catalogue

        cog = make_cog()
        interaction = make_interaction("datenbanken")

        await cog.here_command.callback(cog, interaction)

        module_view_cls.assert_not_called()
        picker_cls.assert_called_once()
        channel_name = picker_cls.call_args.args[1]
        candidates = picker_cls.call_args.args[2]
        assert channel_name == "datenbanken"
        assert len(candidates) == 2

    @patch("oscar.cogs.modul.Catalogue")
    async def test_the_answer_is_always_private(self, catalogue_cls):
        """A module card in the open channel would be noise for everybody else."""
        catalogue = MagicMock()
        catalogue.get_modules.return_value = []
        catalogue_cls.return_value = catalogue

        cog = make_cog()
        interaction = make_interaction("memes")

        await cog.here_command.callback(cog, interaction)

        assert interaction.response.defer.call_args.kwargs["ephemeral"] is True
        assert interaction.followup.send.call_args.kwargs["ephemeral"] is True


class TestChannelModuleView:
    """The picker the command falls back to."""

    @pytest.fixture(autouse=True)
    def no_catalogue_lookup(self):
        """The option descriptions read the catalogue, which the suite has no access to."""
        with patch("oscar.ui.channel_module_view.Module") as module_cls:
            module_cls.from_id.return_value = MagicMock(
                lecturer="Prof. Test", credit_points="6"
            )
            yield module_cls

    @pytest.fixture(name="candidates")
    def candidates_fixture(self) -> list[tuple[ModuleMatch, float]]:
        return [
            (ModuleMatch("Datenbanken 1", 500100, "Datenbanken 1"), 95.0),
            (ModuleMatch("Datenbanken 2", 500200, "Datenbanken 2"), 95.0),
        ]

    @patch("oscar.ui.channel_module_view.get_user_language")
    def test_every_candidate_becomes_an_option(self, language, candidates):
        language.return_value = LanguageCode.DE
        view = ChannelModuleView(OWNER, "datenbanken", candidates)
        labels = [
            option.label
            for item in view.walk_children()
            if isinstance(item, discord.ui.Select)
            for option in item.options
        ]
        assert labels == ["Datenbanken 1", "Datenbanken 2"]

    @patch("oscar.ui.channel_module_view.get_user_language")
    def test_an_option_carries_the_module_id(self, language, candidates):
        """Picking an entry has to open exactly the module that was shown."""
        language.return_value = LanguageCode.DE
        view = ChannelModuleView(OWNER, "datenbanken", candidates)
        values = [
            option.value
            for item in view.walk_children()
            if isinstance(item, discord.ui.Select)
            for option in item.options
        ]
        assert values == ["500100", "500200"]

    @patch("oscar.ui.channel_module_view.get_user_language")
    def test_the_channel_name_is_shown(self, language, candidates):
        language.return_value = LanguageCode.DE
        view = ChannelModuleView(OWNER, "datenbanken", candidates)
        texts = " ".join(
            item.content
            for item in view.walk_children()
            if isinstance(item, discord.ui.TextDisplay)
        )
        assert "datenbanken" in texts

    @patch("oscar.ui.channel_module_view.Module")
    @patch("oscar.ui.channel_module_view.get_user_language")
    def test_an_option_names_the_lecturer(self, language, module_cls, candidates):
        """Two entries with the same title are only tellable apart by the lecturer."""
        language.return_value = LanguageCode.DE
        module_cls.from_id.return_value = MagicMock(lecturer="Prof. Saake", credit_points="6")

        view = ChannelModuleView(OWNER, "datenbanken", candidates)
        descriptions = [
            option.description
            for item in view.walk_children()
            if isinstance(item, discord.ui.Select)
            for option in item.options
        ]
        assert all("Prof. Saake" in text for text in descriptions)

    @patch("oscar.ui.channel_module_view.Module")
    @patch("oscar.ui.channel_module_view.get_user_language")
    def test_an_unreadable_module_leaves_the_picker_standing(
        self, language, module_cls, candidates
    ):
        """A missing description is cosmetic, an exception would break the command."""
        language.return_value = LanguageCode.DE
        module_cls.from_id.side_effect = IndexError

        view = ChannelModuleView(OWNER, "datenbanken", candidates)
        options = [
            option
            for item in view.walk_children()
            if isinstance(item, discord.ui.Select)
            for option in item.options
        ]
        assert len(options) == 2
        assert all(option.description is None for option in options)

    @patch("oscar.ui.channel_module_view.get_user_language")
    async def test_a_stranger_cannot_use_the_picker(self, language, candidates):
        """The picker belongs to whoever typed `/here`."""
        language.return_value = LanguageCode.DE
        view = ChannelModuleView(OWNER, "datenbanken", candidates)

        click = MagicMock(spec=discord.Interaction)
        click.user = MagicMock()
        click.user.id = STRANGER
        click.response = MagicMock()
        click.response.send_message = AsyncMock()

        assert await view.interaction_check(click) is False
        click.response.send_message.assert_awaited_once()

    @patch("oscar.ui.channel_module_view.get_user_language")
    async def test_the_owner_may_use_the_picker(self, language, candidates):
        language.return_value = LanguageCode.DE
        view = ChannelModuleView(OWNER, "datenbanken", candidates)

        click = MagicMock(spec=discord.Interaction)
        click.user = MagicMock()
        click.user.id = OWNER

        assert await view.interaction_check(click) is True
