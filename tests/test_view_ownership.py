"""A view belongs to the student who opened it, and nobody else may press its buttons.

`/start`, `/filter`, `/feedback` and `/semesterplan` used to answer in the channel, so
their components were visible and clickable for everyone. Nothing checked who clicked.

The worst case was not cosmetic. `DeleteButton` removes a module from the plan of the
user the **view** was built for, not from the plan of whoever clicked, so any member of
the channel could delete another student's saved modules. The buttons in `/start`
overwrite that same person's programme, regulations and language.

Two things stop it now, and both are checked here: the commands answer ephemerally, and
`OwnerOnly.interaction_check` refuses a foreign click even if a view is ever posted
publicly again.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from oscar.ui.custom_view import CustomView
from oscar.ui.feedback_view import FeedbackView
from oscar.ui.owner_only import OwnerOnly
from oscar.ui.paginated_view import PaginatedView
from oscar.ui.select_view import PaginatedModuleView, SelectView
from oscar.ui.semesterplan_view import SemesterplanView
from oscar.ui.splan_view import SPlanView
from oscar.ui.start_view import StartView
from util.enums import LanguageCode


OWNER = 4711
STRANGER = 1337


def _click_by(user_id: int):
    """An interaction that looks like `user_id` pressing a component."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


class _Owned(OwnerOnly):
    """The smallest thing that can own a view, so the mixin is tested on its own."""

    def __init__(self, user_id: int, language: LanguageCode = LanguageCode.EN):
        self.user_id = user_id
        self.language = language


class TestOwnerOnly:
    async def test_the_owner_may_click(self):
        view = _Owned(OWNER)
        interaction = _click_by(OWNER)

        assert await view.interaction_check(interaction) is True
        interaction.response.send_message.assert_not_called()

    async def test_a_stranger_may_not_click(self):
        view = _Owned(OWNER)
        interaction = _click_by(STRANGER)

        assert await view.interaction_check(interaction) is False

    async def test_the_stranger_is_told_why_and_only_they_see_it(self):
        view = _Owned(OWNER)
        interaction = _click_by(STRANGER)

        _ = await view.interaction_check(interaction)

        interaction.response.send_message.assert_called_once()
        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    @pytest.mark.parametrize("language, expected", [
        (LanguageCode.DE, "gehört jemand anderem"),
        (LanguageCode.EN, "belongs to somebody else"),
    ])
    async def test_the_refusal_speaks_the_users_language(self, language, expected):
        view = _Owned(OWNER, language)
        interaction = _click_by(STRANGER)

        _ = await view.interaction_check(interaction)

        args, _ = interaction.response.send_message.call_args
        assert expected in args[0]

    async def test_a_view_without_a_language_still_answers(self):
        """`CustomView` has no `language` attribute. The check must not crash on it."""
        class Bare(OwnerOnly):
            def __init__(self):
                self.user_id = OWNER

        interaction = _click_by(STRANGER)
        assert await Bare().interaction_check(interaction) is False
        interaction.response.send_message.assert_called_once()


# Every view that acts on behalf of one student, with the argument name for its owner.
PERSONAL_VIEWS = [
    CustomView,
    SemesterplanView,
    StartView,
    FeedbackView,
    SelectView,
    PaginatedModuleView,
    SPlanView,
]


class TestEveryPersonalViewIsOwned:
    @pytest.mark.parametrize("view_class", PERSONAL_VIEWS, ids=lambda c: c.__name__)
    def test_it_mixes_in_the_check(self, view_class):
        assert issubclass(view_class, OwnerOnly), (
            f"{view_class.__name__} acts on one student's data but does not check who "
            "is clicking. Mix in OwnerOnly."
        )

    @pytest.mark.parametrize("view_class", PERSONAL_VIEWS, ids=lambda c: c.__name__)
    def test_the_check_actually_wins(self, view_class):
        """`OwnerOnly` must come before the discord.py base, or its check is shadowed.

        discord.py's own `interaction_check` returns `True` for everybody. Writing
        `class X(LayoutView, OwnerOnly)` compiles and silently lets strangers in.
        """
        assert view_class.interaction_check is OwnerOnly.interaction_check, (
            f"{view_class.__name__} resolves interaction_check to "
            f"{view_class.interaction_check.__qualname__}. Put OwnerOnly first in the "
            "base class list."
        )

    def test_a_view_in_the_wrong_order_is_detected(self):
        """Proves the check above can fail."""
        class WrongOrder(discord.ui.LayoutView, OwnerOnly):
            pass

        assert WrongOrder.interaction_check is not OwnerOnly.interaction_check


class TestPaginatedViewGuardIsWiredUp:
    """`check_user` existed from the start, but nothing ever called it."""

    async def test_the_page_buttons_run_the_check(self):
        opener = MagicMock(spec=discord.Interaction)
        opener.user = MagicMock()
        opener.user.id = OWNER

        view = PaginatedView(interaction=opener, total_pages=5, get_page=lambda i: None)

        stranger = _click_by(STRANGER)
        assert await view.interaction_check(stranger) is False

        owner = _click_by(OWNER)
        owner.user = opener.user
        assert await view.interaction_check(owner) is True


class TestPersonalCommandsAnswerPrivately:
    """An ephemeral message cannot be clicked by anyone else at all."""

    @staticmethod
    def _cog():
        from oscar.cogs.modul import ModulSearch  # noqa: PLC0415

        with patch("oscar.cogs.modul.Catalogue"):
            return ModulSearch(MagicMock(spec=discord.ext.commands.Bot))

    @staticmethod
    def _interaction():
        interaction = MagicMock()
        interaction.user.id = OWNER
        interaction.user.roles = []
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        return interaction

    async def test_filter_is_private(self):
        interaction = self._interaction()
        with patch("oscar.cogs.modul.SelectView"):
            await self._cog().filter.callback(self._cog(), interaction)

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    async def test_start_is_private(self):
        interaction = self._interaction()
        with patch("oscar.cogs.modul.StartView"):
            await self._cog().start.callback(self._cog(), interaction)

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    async def test_feedback_is_private(self):
        interaction = self._interaction()
        with patch("oscar.ui.feedback_view.FeedbackView"):
            await self._cog().feedback.callback(self._cog(), interaction)

        _, kwargs = interaction.response.send_message.call_args
        assert kwargs["ephemeral"] is True

    async def test_semesterplan_is_private(self):
        interaction = self._interaction()
        with patch("oscar.cogs.modul.SemesterplanView"):
            await self._cog().plan.callback(self._cog(), interaction)

        _, defer_kwargs = interaction.response.defer.call_args
        assert defer_kwargs["ephemeral"] is True

        _, send_kwargs = interaction.followup.send.call_args
        assert send_kwargs["ephemeral"] is True

    async def test_standard_plan_is_private(self):
        interaction = self._interaction()
        with patch("oscar.ui.splan_view.SPlanView"):
            await self._cog().s_plan.callback(self._cog(), interaction)

        _, defer_kwargs = interaction.response.defer.call_args
        assert defer_kwargs["ephemeral"] is True

        _, send_kwargs = interaction.followup.send.call_args
        assert send_kwargs["ephemeral"] is True


