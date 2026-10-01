""" Unit tests for FIN Learning Management Systems (LMS) guide (Issue #51)."""
# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import AsyncMock, MagicMock
import pytest
import discord

from oscar.cogs.help import Help
from oscar.ui.lms_view import LmsView
from util.enums import LanguageCode
from util.lms import (
    FIN_PLATFORMS,
    FIN_PLATFORMS,
    get_default_platform,
    get_platform_by_key,
)
from util.translations import FAQ_ANSWERS, FAQ_QUESTIONS


# The hosts that answered when the list was last checked by hand, and the ones that
# answered NXDOMAIN. The dead ones were in the guide for months.
LIVE_HOSTS = {
    "elearning.ovgu.de",
    "lsf.ovgu.de",
    "bookstack.cs.ovgu.de",
    "isggit3.cs.ovgu.de",
}

DEAD_HOSTS = {
    "moodle2.cs.ovgu.de",
    "webwork.cs.ovgu.de",
    "gitlab.cs.ovgu.de",
    "handbook.cs.ovgu.de",
}


class TestLmsDirectory:
    """Tests covering the data integrity of FIN_PLATFORMS."""

    def test_platforms_collection_not_empty(self):
        platforms = FIN_PLATFORMS
        assert len(platforms) >= 4

    def test_essential_platforms_present(self):
        keys = {p.key for p in FIN_PLATFORMS}
        assert "elearning" in keys
        assert "gitlab" in keys
        assert "lsf" in keys
        assert "handbook" in keys

    def test_no_platform_points_at_a_host_that_does_not_exist(self):
        """Four of these were in the guide, and all four answer NXDOMAIN.

        A student followed `/lms` into a browser error and had no way to tell that
        the bot was wrong rather than their network.
        """
        for platform in FIN_PLATFORMS:
            for dead in DEAD_HOSTS:
                assert dead not in platform.url, (
                    f"{platform.key} points at {dead}, which does not resolve"
                )

    @pytest.mark.parametrize("platform", FIN_PLATFORMS, ids=lambda p: p.key)
    def test_every_url_is_a_host_somebody_opened(self, platform):
        """The suite has no network, so this checks the list, not the host.

        Adding a portal means opening it first and putting its host in `LIVE_HOSTS`.
        """
        host = platform.url.removeprefix("https://").split("/")[0]
        assert host in LIVE_HOSTS, (
            f"{platform.key} uses {host}, which nobody has opened. Resolve it and "
            "add it to LIVE_HOSTS, or take the entry out."
        )

    def test_the_default_is_the_moodle(self):
        """A student opening the guide wants their course material."""
        assert get_default_platform().key == "elearning"
        assert get_default_platform().url == "https://elearning.ovgu.de"

    @pytest.mark.parametrize("platform", FIN_PLATFORMS)
    def test_platform_attributes_populated(self, platform):
        assert platform.key
        assert platform.name
        assert platform.emoji
        assert platform.url.startswith("https://")
        assert len(platform.login_type_de) > 0
        assert len(platform.login_type_en) > 0
        assert len(platform.scope_de) > 0
        assert len(platform.scope_en) > 0
        assert len(platform.description_de) > 0
        assert len(platform.description_en) > 0
        assert len(platform.tips_de) > 0
        assert len(platform.tips_en) > 0

    def test_get_platform_by_key_found_and_not_found(self):
        found = get_platform_by_key("elearning")
        assert found is not None
        assert found.key == "elearning"

        missing = get_platform_by_key("non_existent_portal")
        assert missing is None


class TestLmsView:
    """Tests covering the interactive LmsView UI component."""

    def test_initialization_de(self):
        view = LmsView(default_language=LanguageCode.DE)
        assert view.language_code == LanguageCode.DE
        assert view.selected_platform_key == "elearning"
        assert len(view.children) > 0

    def test_initialization_en(self):
        view = LmsView(default_language=LanguageCode.EN, initial_platform_key="lsf")
        assert view.language_code == LanguageCode.EN
        assert view.selected_platform_key == "lsf"
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_language_toggle(self):
        view = LmsView(default_language=LanguageCode.DE)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()

        toggle = view._create_language_toggle()
        await toggle.callback(interaction)

        assert view.language_code == LanguageCode.EN
        assert interaction.response.edit_message.await_count >= 1

    @pytest.mark.asyncio
    async def test_select_dropdown_switches_platform(self):
        view = LmsView(default_language=LanguageCode.DE)
        container = view.children[0]
        # Dropdown action row is at child index 2
        select_row = container.children[2]
        select_comp = select_row.children[0]

        select_comp._values = ["gitlab"]
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.edit_message = AsyncMock()

        await select_comp.callback(interaction)
        assert view.selected_platform_key == "gitlab"


class TestLmsCommands:
    """Tests for /lms and /elearning slash commands."""

    @pytest.mark.asyncio
    async def test_lms_command_invokes_view(self):
        bot = MagicMock()
        cog = Help(bot)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 777
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        await cog.lms.callback(cog, interaction)
        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once()
        _, kwargs = interaction.followup.send.call_args
        assert isinstance(kwargs.get("view"), LmsView)
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_elearning_alias_invokes_lms(self):
        bot = MagicMock()
        cog = Help(bot)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 777
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        await cog.elearning.callback(cog, interaction)
        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once()


class TestLmsFaqIntegration:
    """Check that LMS FAQ question and answer exist and match."""

    def test_which_lms_in_faq(self):
        assert "which_lms" in FAQ_QUESTIONS
        assert "which_lms" in FAQ_ANSWERS
        assert LanguageCode.DE in FAQ_QUESTIONS["which_lms"]
        assert LanguageCode.EN in FAQ_QUESTIONS["which_lms"]
        for language in (LanguageCode.DE, LanguageCode.EN):
            answer = FAQ_ANSWERS["which_lms"][language]
            assert "elearning.ovgu.de" in answer
            assert "lsf.ovgu.de" in answer
            for dead in DEAD_HOSTS:
                assert dead not in answer, f"the FAQ still names {dead}"


class TestModuleCardLearningPlatform:
    """The module card carries one platform button, and it has to be the right one.

    It first pointed at the FIN Moodle (`moodle2.cs.ovgu.de`). That is not where
    students look for their course, and the host does not answer from outside the
    university network either. The button opens the central eLearning instead.
    """

    @pytest.fixture(name="card")
    def card_fixture(self):
        # pylint: disable=import-outside-toplevel
        from unittest.mock import patch

        from oscar.ui.module_view import ModuleView

        module = MagicMock()
        module.id_ = 500100
        module.get_title.return_value = "Datenbanken 1"
        module.get_content.return_value = "Inhalt"
        module.get_teaching_form_sws.return_value = "2V"
        module.abbreviation = "DB1"
        module.lecturer = "Gunter Saake"
        module.credit_points = "5"
        module.language = MagicMock()

        with patch("oscar.ui.module_view.get_user_language", return_value=LanguageCode.DE), \
             patch("oscar.ui.module_view.get_database") as database, \
             patch("oscar.ui.module_view.module_url", return_value="https://example.invalid"), \
             patch("oscar.ui.module_view.lsf_search_url", return_value="https://example.invalid"):
            database.return_value.get_preferences.return_value = None
            database.return_value.get_module_ratings.return_value = {"count": 0}
            yield ModuleView(4711, module)

    def _urls(self, card) -> list[str]:
        return [
            item.url
            for item in card.walk_children()
            if isinstance(item, discord.ui.Button) and item.url
        ]

    def test_it_links_to_the_central_elearning(self, card):
        assert any("elearning.ovgu.de" in url for url in self._urls(card))

    def test_it_does_not_link_to_the_fin_moodle(self, card):
        """`moodle2.cs.ovgu.de` does not answer from outside the university network."""
        assert not any("moodle2.cs.ovgu.de" in url for url in self._urls(card))

    def test_the_card_and_the_guide_agree(self):
        """Both open the same portal, so a student is never sent two ways."""
        assert get_default_platform().url == "https://elearning.ovgu.de"
