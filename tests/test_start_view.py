"""`/start` crashed, and it crashed in a way nothing on the screen explained.

Discord allows one view forty components in total. The welcome screen spends most of
them on buttons and selects, and it used to draw **one component per slash command**.
So every feature the bot gained pushed `/start` closer to the edge, and somewhere past
eleven commands it went over:

    ValueError: maximum number of children exceeded (40)

The student saw "the application did not respond". Nothing said which component was
the one too many, and `/start` is the first thing anybody runs.

The command list is one block now, so it costs one component whatever it grows to.
`test_the_command_list_costs_one_component` is the test that keeps it that way.
"""

from unittest.mock import patch

import discord
import pytest

from oscar.ui.start_view import StartView
from util.command_surface import CORE_ORDER
from util.enums import LanguageCode
from util.translations import COMMAND_TEXTS


# What discord.py raises at. It is a hard limit of the API, not a style rule.
MAX_CHILDREN = 40

# What we keep free, so the next feature does not break `/start` again.
HEADROOM = 8

USER = 4711


def children_of(view: discord.ui.LayoutView) -> int:
    """How many components discord would count in this view."""
    return len(list(view.walk_children()))


@pytest.fixture(name="german")
def german_fixture():
    with patch("oscar.ui.start_view.get_user_language", return_value=LanguageCode.DE):
        yield


class TestItBuildsAtAll:
    """The regression itself."""

    @pytest.mark.parametrize("language", [LanguageCode.DE, LanguageCode.EN])
    def test_the_welcome_screen_opens(self, language: LanguageCode):
        with patch("oscar.ui.start_view.get_user_language", return_value=language):
            view = StartView(USER, semester=3)
        assert children_of(view) > 0

    @pytest.mark.parametrize("semester", [-1, 1, 12])
    def test_any_semester_works(self, german, semester: int):
        assert children_of(StartView(USER, semester=semester)) > 0

    def test_it_keeps_room_for_the_next_feature(self, german):
        """Passing the limit is what broke it, so stop well before the limit."""
        count = children_of(StartView(USER, semester=3))
        assert count <= MAX_CHILDREN - HEADROOM, (
            f"/start uses {count} of {MAX_CHILDREN} components. Move something into "
            "a block of text before it goes over again."
        )


class TestTheCommandList:
    """Why it broke, and why it cannot break the same way twice."""

    def test_the_command_list_costs_one_component(self, german):
        """Ten times the commands must not cost ten times the components."""
        before = children_of(StartView(USER, semester=3))

        inflated = dict(COMMAND_TEXTS)
        for number in range(40):
            inflated[f"invented_{number}"] = {
                LanguageCode.DE: "erfunden",
                LanguageCode.EN: "invented",
            }
        with patch("oscar.ui.start_view.COMMAND_TEXTS", inflated):
            after = children_of(StartView(USER, semester=3))

        assert after == before, (
            "the welcome screen grows with the command list again, which is exactly "
            "how it hit the forty component limit"
        )

    def test_every_core_command_is_named(self, german):
        view = StartView(USER, semester=3)
        text = " ".join(
            item.content
            for item in view.walk_children()
            if isinstance(item, discord.ui.TextDisplay)
        )
        for command in CORE_ORDER:
            assert f"/{command}" in text, f"/start does not mention /{command}"

    def test_only_the_core_commands_get_a_line(self, german):
        """Every command works. The welcome screen explains eight of them.

        The line under the list may name a few of the others as examples, which is
        what sends a newcomer to `/help` in the first place. What it may not do is
        explain them, because that is the list that grew until `/start` broke.
        """
        view = StartView(USER, semester=3)
        block = next(
            item.content
            for item in view.walk_children()
            if isinstance(item, discord.ui.TextDisplay) and "/start" in item.content
        )
        explained = [line for line in block.splitlines() if line.startswith("`/")]
        assert len(explained) == len(CORE_ORDER)
        for line in explained:
            name = line.split("`")[1].lstrip("/")
            assert name in CORE_ORDER

    def test_it_says_where_the_other_commands_are(self, german):
        view = StartView(USER, semester=3)
        text = " ".join(
            item.content
            for item in view.walk_children()
            if isinstance(item, discord.ui.TextDisplay)
        )
        assert "/help" in text

    def test_the_order_is_the_one_a_student_meets(self, german):
        view = StartView(USER, semester=3)
        block = next(
            item.content
            for item in view.walk_children()
            if isinstance(item, discord.ui.TextDisplay) and "/start" in item.content
        )
        positions = [block.index(f"/{command}") for command in CORE_ORDER]
        assert positions == sorted(positions)
