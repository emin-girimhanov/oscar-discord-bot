"""`/compare` puts two or three modules side by side.

Picking one elective out of three meant opening three cards and remembering the first
one. Everything the comparison needs was already on `Module`, so the risk here is not
the data, it is the discord limits: an embed renders three inline fields in a row, a
field name holds 256 characters and a field value 1024. Going over any of those makes
the whole message fail rather than look untidy.
"""

from unittest.mock import MagicMock, patch

import pytest

from oscar.ui.compare_view import (
    MAX_FIELD_NAME,
    MAX_FIELD_VALUE,
    MAX_MODULES,
    ROW_KEYS,
    UNKNOWN,
    CompareView,
    differing_rows,
    module_rows,
)
from util.enums import LanguageCode
from util.translations import COMPARE_TEXTS


def make_module(
    id_: int = 1,
    title: str = "Datenbanken",
    credit_points: str = "5",
    sws: str = "2V + 1Ü",
    lecturer: str = "Prof. Saake",
    exam: str = "Klausur",
    language: int = 1,
):
    """A module stub carrying only what the comparison reads."""
    module = MagicMock()
    module.id_ = id_
    module.credit_points = credit_points
    module.lecturer = lecturer
    module.language = language
    module.get_title.return_value = title
    module.get_teaching_form_sws.return_value = sws
    module.get_study_exam_type.return_value = exam
    return module


class TestOneModulesRow:
    def test_every_row_key_is_filled(self):
        row = module_rows(make_module(), LanguageCode.DE)
        assert set(row) == set(ROW_KEYS)

    def test_a_multi_line_value_becomes_one_line(self):
        """The table separates teaching forms with newlines, which wrecks a column."""
        module = make_module(sws="Vorlesung 2 SWS\nÜbung 1 SWS")
        assert "\n" not in module_rows(module, LanguageCode.DE)["sws"]

    @pytest.mark.parametrize("empty", ["", "   ", "\n"])
    def test_an_empty_value_becomes_a_dash(self, empty):
        """A blank column reads as a rendering fault. A dash reads as no data."""
        module = make_module(credit_points=empty)
        assert module_rows(module, LanguageCode.DE)["credit_points"] == UNKNOWN

    def test_every_row_has_a_heading_in_both_languages(self):
        for key in ROW_KEYS:
            assert COMPARE_TEXTS[key][LanguageCode.DE].strip()
            assert COMPARE_TEXTS[key][LanguageCode.EN].strip()


class TestWhatDiffers:
    def test_identical_modules_differ_in_nothing(self):
        rows = [module_rows(make_module(), LanguageCode.DE)] * 2
        assert differing_rows(rows) == []

    def test_one_changed_value_is_reported(self):
        rows = [
            module_rows(make_module(credit_points="5"), LanguageCode.DE),
            module_rows(make_module(credit_points="6"), LanguageCode.DE),
        ]
        assert differing_rows(rows) == ["credit_points"]

    def test_the_order_follows_the_table(self):
        rows = [
            module_rows(make_module(exam="Klausur", credit_points="5"), LanguageCode.DE),
            module_rows(make_module(exam="mündlich", credit_points="6"), LanguageCode.DE),
        ]
        assert differing_rows(rows) == ["credit_points", "exam"]


@patch("oscar.ui.compare_view.module_url", return_value="https://example.org/page")
@patch("oscar.ui.compare_view.get_database")
@patch("oscar.ui.compare_view.get_user_language", return_value=LanguageCode.DE)
class TestTheEmbed:
    @staticmethod
    def _view(modules):
        return CompareView(user_id=4711, modules=modules)

    def test_one_field_per_module(self, _lang, mock_db, _url):
        mock_db.return_value.get_preferences.return_value = None
        embed = self._view([make_module(1, "A"), make_module(2, "B")]).create_embed()

        assert len(embed.fields) == 2
        assert [field.name for field in embed.fields] == ["A", "B"]

    def test_the_fields_sit_next_to_each_other(self, _lang, mock_db, _url):
        mock_db.return_value.get_preferences.return_value = None
        embed = self._view([make_module(1, "A"), make_module(2, "B")]).create_embed()

        assert all(field.inline for field in embed.fields)

    def test_a_fourth_module_is_dropped(self, _lang, mock_db, _url):
        """Four fields wrap onto a second row and stop being a comparison."""
        mock_db.return_value.get_preferences.return_value = None
        modules = [make_module(i, f"M{i}") for i in range(1, 5)]

        assert len(self._view(modules).create_embed().fields) == MAX_MODULES

    def test_the_footer_names_the_difference(self, _lang, mock_db, _url):
        mock_db.return_value.get_preferences.return_value = None
        embed = self._view([
            make_module(1, "A", credit_points="5"),
            make_module(2, "B", credit_points="6"),
        ]).create_embed()

        assert COMPARE_TEXTS["credit_points"][LanguageCode.DE] in embed.footer.text

    def test_the_footer_says_so_when_nothing_differs(self, _lang, mock_db, _url):
        mock_db.return_value.get_preferences.return_value = None
        embed = self._view([make_module(1, "A"), make_module(2, "A")]).create_embed()

        assert embed.footer.text == COMPARE_TEXTS["identical"][LanguageCode.DE]

    def test_a_long_title_cannot_break_the_message(self, _lang, mock_db, _url):
        mock_db.return_value.get_preferences.return_value = None
        embed = self._view([
            make_module(1, "Modul " * 200),
            make_module(2, "B"),
        ]).create_embed()

        assert len(embed.fields[0].name) <= MAX_FIELD_NAME

    def test_a_long_value_cannot_break_the_message(self, _lang, mock_db, _url):
        mock_db.return_value.get_preferences.return_value = None
        embed = self._view([
            make_module(1, "A", lecturer="Prof. " * 400),
            make_module(2, "B"),
        ]).create_embed()

        assert len(embed.fields[0].value) <= MAX_FIELD_VALUE

    def test_each_module_gets_a_handbook_button(self, _lang, mock_db, _url):
        mock_db.return_value.get_preferences.return_value = None
        view = self._view([make_module(1, "A"), make_module(2, "B")])

        assert len(view.children) == 2
        assert all(button.url for button in view.children)


class TestTheCommand:
    @staticmethod
    def _cog():
        import discord  # noqa: PLC0415
        from oscar.cogs.modul import ModulSearch  # noqa: PLC0415

        with patch("oscar.cogs.modul.Catalogue"):
            return ModulSearch(MagicMock(spec=discord.ext.commands.Bot))

    @staticmethod
    def _interaction():
        from unittest.mock import AsyncMock  # noqa: PLC0415

        interaction = MagicMock()
        interaction.user.id = 4711
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        return interaction

    @patch("oscar.cogs.modul.get_user_language", return_value=LanguageCode.DE)
    @patch("oscar.cogs.modul.CompareView")
    @patch("oscar.cogs.modul.resolve_module")
    async def test_two_modules_are_compared(self, resolve, _view, _lang):
        resolve.side_effect = [make_module(1, "A"), make_module(2, "B")]
        interaction = self._interaction()
        cog = self._cog()

        await cog.compare.callback(cog, interaction, "1", "2")

        _, kwargs = interaction.followup.send.call_args
        assert "embed" in kwargs
        assert kwargs["ephemeral"] is True

    @patch("oscar.cogs.modul.get_user_language", return_value=LanguageCode.DE)
    @patch("oscar.cogs.modul.resolve_module")
    async def test_the_same_module_twice_is_refused(self, resolve, _lang):
        """Comparing a module with itself renders a table that says nothing."""
        resolve.side_effect = [make_module(7, "A"), make_module(7, "A")]
        interaction = self._interaction()
        cog = self._cog()

        await cog.compare.callback(cog, interaction, "7", "7")

        args, _ = interaction.followup.send.call_args
        assert args[0] == COMPARE_TEXTS["too_few"][LanguageCode.DE]

    @patch("oscar.cogs.modul.get_user_language", return_value=LanguageCode.EN)
    @patch("oscar.cogs.modul.resolve_module", side_effect=IndexError)
    async def test_an_unknown_module_is_named_in_the_answer(self, _resolve, _lang):
        interaction = self._interaction()
        cog = self._cog()

        await cog.compare.callback(cog, interaction, "Kein solches Modul", "2")

        args, _ = interaction.followup.send.call_args
        assert "Kein solches Modul" in args[0]

    @patch("oscar.cogs.modul.get_user_language", return_value=LanguageCode.EN)
    @patch("oscar.cogs.modul.CompareView")
    @patch("oscar.cogs.modul.resolve_module")
    async def test_the_third_module_is_optional(self, resolve, _view, _lang):
        resolve.side_effect = [make_module(1, "A"), make_module(2, "B")]
        interaction = self._interaction()
        cog = self._cog()

        await cog.compare.callback(cog, interaction, "1", "2", None)

        assert resolve.call_count == 2
