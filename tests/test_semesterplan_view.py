""" The semester plan has to open for a plan of any size.

    Discord allows one view forty components. This view spent five per module and one
    per line of the standard study plan, so it raised

        ValueError: maximum number of children exceeded (40)

    as soon as a student had saved six modules. Six modules of 5 CP are a normal
    semester. `test_component_budget` counts the views that need no database, and this
    one does, so nothing ever built it with a real plan.

    The tests below build it with every plan size from nothing to far too much.
"""
# pylint: disable=redefined-outer-name, protected-access

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from oscar.ui.semesterplan_view import (
    ROWS_MAX,
    SELECT_MAX,
    InfoSelect,
    RemoveSelect,
    SemesterplanView,
)
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.module import Module


MAX_CHILDREN = 40
WARN_AT = 36
USER = 4711

PREFERENCES = {
    "user_id": USER,
    "language": LanguageCode.DE,
    "major": StudyCourse.BSC_INF,
    "semester": 1,
    "spo": "PO_2024",
    "winter_semester": True,
}

# A first semester of the standard study plan, eight lines is the longest we ship.
STANDARD_PLAN = [
    {"title": f"Pflichtmodul {n}", "credit_points": 5, "usability": [], "identification": 100 + n}
    for n in range(8)
]


def module(number: int) -> Module:
    return Module(
        id_=100 + number,
        language=ModuleLanguage.DE,
        title=f"Ein Modul mit einem recht langen Titel Nummer {number}",
        title_en=f"A module {number}",
        credit_points="5",
    )


def build(size: int, preferences: dict | None = None) -> SemesterplanView:
    """The view of a student who saved `size` modules."""
    modules = [module(n) for n in range(size)]
    by_id = {m.id_: m for m in modules}
    with patch("oscar.ui.semesterplan_view.get_database") as database, \
         patch("oscar.ui.semesterplan_view.Module.from_id", side_effect=by_id.__getitem__), \
         patch("oscar.ui.semesterplan_view.get_modules_for_semester",
               return_value=STANDARD_PLAN):
        database.return_value.get_semesterplan.return_value = modules
        database.return_value.get_preferences.return_value = preferences
        return SemesterplanView(USER)


def count(view: discord.ui.LayoutView) -> int:
    return len(list(view.walk_children()))


def texts_of(view: discord.ui.LayoutView) -> str:
    return "\n".join(
        item.content for item in view.walk_children()
        if isinstance(item, discord.ui.TextDisplay)
    )


def of_type(view: discord.ui.LayoutView, kind: type) -> list:
    return [item for item in view.walk_children() if isinstance(item, kind)]


class TestItOpensForEveryPlan:
    """The wall itself: building is where discord.py checks the limit."""

    @pytest.mark.parametrize("size", list(range(0, 31)) + [60, 274])
    @pytest.mark.parametrize("preferences", [None, PREFERENCES])
    def test_it_builds_and_stays_under_the_limit(self, size: int, preferences):
        view = build(size, preferences)
        assert count(view) <= MAX_CHILDREN

    @pytest.mark.parametrize("size", range(0, 31))
    def test_it_keeps_room_for_the_next_button(self, size: int):
        view = build(size, PREFERENCES)
        assert count(view) <= WARN_AT, (
            f"{count(view)} of {MAX_CHILDREN} components with {size} modules. "
            "Fold something into a block of text before adding anything."
        )

    def test_six_modules_are_the_plan_that_used_to_crash(self):
        """30 CP, the semester the standard study plan asks for."""
        view = build(6, PREFERENCES)
        assert "Nummer 5" in texts_of(view)

    def test_the_text_stays_under_what_discord_accepts(self):
        """All text of one message may hold 4000 characters."""
        assert len(texts_of(build(274, PREFERENCES))) < 4000


class TestAShortPlanKeepsItsButtons:
    """Up to `ROWS_MAX` modules nothing changes for the student."""

    def test_every_module_has_an_info_and_a_delete_button(self):
        view = build(ROWS_MAX, PREFERENCES)
        labels = [button.label for button in of_type(view, discord.ui.Button)]
        assert labels.count("X") == ROWS_MAX
        assert labels.count("mehr Infos") == ROWS_MAX
        assert not of_type(view, discord.ui.Select)


class TestALongPlanBecomesAList:
    """More modules than there is room for buttons."""

    def test_every_module_is_listed(self):
        text = texts_of(build(ROWS_MAX + 1, PREFERENCES))
        for number in range(ROWS_MAX + 1):
            assert f"Nummer {number} – 5 CP" in text

    def test_two_menus_replace_the_buttons(self):
        view = build(ROWS_MAX + 1, PREFERENCES)
        assert len(of_type(view, RemoveSelect)) == 1
        assert len(of_type(view, InfoSelect)) == 1
        assert "X" not in [button.label for button in of_type(view, discord.ui.Button)]

    def test_a_menu_never_holds_more_than_discord_allows(self):
        view = build(60, PREFERENCES)
        for menu in of_type(view, discord.ui.Select):
            assert len(menu.options) == SELECT_MAX
        assert f"und {60 - SELECT_MAX} weitere" in texts_of(view)

    def test_the_total_still_counts_every_module(self):
        assert "Gesamt CP: 60" in texts_of(build(12, PREFERENCES))

    async def test_removing_through_the_menu_deletes_that_module(self):
        view = build(ROWS_MAX + 1, PREFERENCES)
        menu = of_type(view, RemoveSelect)[0]
        menu._values = ["103"]
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.edit_message = AsyncMock()

        with patch("oscar.ui.semesterplan_view.get_database") as database:
            database.return_value.get_semesterplan.return_value = []
            database.return_value.get_preferences.return_value = PREFERENCES
            await menu.callback(interaction)

        database.return_value.remove_from_semesterplan.assert_called_once_with(
            user_id=USER, module_id=103
        )
        interaction.response.edit_message.assert_awaited_once()

    async def test_the_info_menu_opens_the_card_privately(self):
        view = build(ROWS_MAX + 1, PREFERENCES)
        menu = of_type(view, InfoSelect)[0]
        menu._values = ["103"]
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = USER
        interaction.response.send_message = AsyncMock()

        with patch("oscar.ui.semesterplan_view.Module.from_id", return_value=module(3)), \
             patch("oscar.ui.semesterplan_view.ModuleView") as card:
            await menu.callback(interaction)

        card.assert_called_once()
        assert interaction.response.send_message.call_args.kwargs["ephemeral"] is True


class TestTheStandardPlanIsOneBlock:
    """Eight lines used to be eight components."""

    def test_every_line_is_still_shown(self):
        text = texts_of(build(2, PREFERENCES))
        for line in STANDARD_PLAN:
            assert line["title"] in text

    def test_a_saved_module_is_ticked(self):
        text = texts_of(build(2, PREFERENCES))
        assert "✅ Pflichtmodul 0" in text
        assert "❌ Pflichtmodul 7" in text
