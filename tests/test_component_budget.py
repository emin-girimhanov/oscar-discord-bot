"""Discord allows one view forty components, and OSCAR has walked into that wall once.

`/start` drew one component per slash command. Every feature the bot gained pushed it
closer, and somewhere past eleven commands it went over:

    ValueError: maximum number of children exceeded (40)

The student saw "the application did not respond". Nothing on the screen said which
component was one too many, so the first command anybody runs was broken for a while
before it was noticed.

This file measures every view that can be built without a server, so the next one is
caught here and not by a student. A view over `WARN_AT` is not wrong yet, it is out of
room, and whoever adds the next button to it has to fold something into a block of
text first.

The filter mask walked into the same wall a second time, and so did the result list
it opens. The mask stood at 36 of 40 and one more filter group raised the same
`ValueError`. The result list stood at 37 and `per_page=7` raised it, with `per_page`
a constructor argument anybody may tune.

Counting a view once is not enough when its size depends on a number, because the
count only moves when somebody changes that number. So the two classes at the bottom
of this file change it themselves and check the view survives.
"""

from unittest.mock import patch

import discord
import pytest

from util.enums import LanguageCode


# The hard limit of the discord API, not a style rule.
MAX_CHILDREN = 40

# Where a view has to stop, so the next feature still fits.
WARN_AT = 36

USER = 4711


def build_views() -> dict[str, discord.ui.LayoutView]:
    """Every view that needs nothing but a user id and a language.

    Views that need a module, a challenge submission or a filled database are left
    out. They are small, and they are covered by their own tests.
    """
    # pylint: disable=import-outside-toplevel
    from oscar.cogs.help import HelpView
    from oscar.ui.challenge_view import ChallengeView
    from oscar.ui.contacts_view import ContactsView
    from oscar.ui.deadlines_view import DeadlinesView
    from oscar.ui.exam_archive_view import ExamArchiveView
    from oscar.ui.lms_view import LmsView
    from oscar.ui.progress_view import ProgressView
    from oscar.ui.select_view import SelectView
    from oscar.ui.start_view import StartView
    from oscar.ui.suggest_view import SuggestView
    from util.challenges import get_current_weekly_challenge

    german = LanguageCode.DE
    return {
        "StartView": StartView(USER, semester=3),
        "SelectView": SelectView(USER),
        "HelpView": HelpView(german),
        "ContactsView": ContactsView(default_language=german),
        "LmsView": LmsView(default_language=german),
        "DeadlinesView": DeadlinesView(default_language=german),
        "ProgressView": ProgressView(user_id=USER, default_language=german),
        "SuggestView": SuggestView(user_id=USER, default_language=german),
        "ExamArchiveView": ExamArchiveView(USER),
        "ChallengeView": ChallengeView(
            default_language=german,
            initial_challenge_id=get_current_weekly_challenge().id,
        ),
    }


@pytest.fixture(name="views")
def views_fixture():
    with patch("util.database.get_user_language", return_value=LanguageCode.DE):
        yield build_views()


def count(view: discord.ui.LayoutView) -> int:
    """How many components discord would count in this view."""
    return len(list(view.walk_children()))


class TestEveryViewFits:
    """The wall itself."""

    def test_they_all_build(self, views):
        """Building is where the limit is checked, so this is the whole test."""
        assert views, "no view was built, the test measures nothing"

    def test_none_is_over_the_limit(self, views):
        over = {name: count(view) for name, view in views.items() if count(view) > MAX_CHILDREN}
        assert not over, f"discord refuses these: {over}"

    def test_none_is_out_of_room(self, views):
        """A view at the limit breaks on the next button somebody adds to it."""
        tight = {
            name: count(view) for name, view in views.items() if count(view) > WARN_AT
        }
        assert not tight, (
            f"{tight} of {MAX_CHILDREN} components. Fold something into a block of "
            "text before adding anything else, this is how /start broke."
        )


class TestTheNumbersAreVisible:
    """A number nobody reads is a number nobody fixes."""

    def test_the_budget_is_reported(self, views, capsys):
        for name, view in sorted(views.items(), key=lambda pair: -count(pair[1])):
            print(f"{name:<18} {count(view):>2} / {MAX_CHILDREN}")
        printed = capsys.readouterr().out
        assert "StartView" in printed


class TestTheFilterMaskHasRoom:
    """The mask grows with the filter options, so it has to be measured while growing.

        Every group costs a heading, a row and one component per button. At five
        groups the mask stood at 36 of 40 and a sixth crashed it. Dropping the
        separators between the groups and merging the title with the hint brought it
        back to 30, which is room for two more groups.
    """

    # How many more filter groups the mask has to survive. Two is what the room bought
    # by the last cut is worth. A third needs another cut, not a bigger number here.
    SPARE_GROUPS = 2

    @staticmethod
    def _mask_size(extra_groups: int) -> int:
        """Builds the mask with invented filter groups and counts its components."""
        # pylint: disable=import-outside-toplevel
        import oscar.ui.select_view as select_view
        from util.filter_options import FILTER_GROUPS, FilterGroup

        grown = list(FILTER_GROUPS) + [
            FilterGroup(
                f"invented_{number}",
                "heading_cp",
                ("cp_lt_5", "cp_eq_5", "cp_gt_5"),
            )
            for number in range(extra_groups)
        ]
        with patch.object(select_view, "FILTER_GROUPS", tuple(grown)), \
             patch("util.database.get_user_language", return_value=LanguageCode.DE):
            return len(list(select_view.SelectView(USER).walk_children()))

    def test_it_fits_today(self):
        assert self._mask_size(0) <= WARN_AT

    def test_it_survives_the_next_filter_somebody_adds(self):
        """This is the test that would have caught the crash before it shipped."""
        try:
            size = self._mask_size(1)
        except ValueError as error:
            pytest.fail(
                f"one more filter group breaks /filter: {error}. Fold something into "
                "a block of text, the way the separators were folded into the headings."
            )
        assert size <= MAX_CHILDREN

    def test_the_room_that_was_bought_is_still_there(self):
        try:
            size = self._mask_size(self.SPARE_GROUPS)
        except ValueError as error:
            pytest.fail(f"the mask lost its spare room: {error}")
        assert size <= MAX_CHILDREN

    def test_a_group_is_told_apart_without_spending_a_component(self):
        """The blank line in the heading replaced a `Separator` each."""
        # pylint: disable=import-outside-toplevel
        import oscar.ui.select_view as select_view

        with patch("util.database.get_user_language", return_value=LanguageCode.DE):
            view = select_view.SelectView(USER)
        separators = [
            item for item in view.walk_children()
            if isinstance(item, discord.ui.Separator)
        ]
        assert len(separators) <= 1, (
            f"{len(separators)} separators. Each one is a component the next filter "
            "group needs."
        )


class TestTheResultListHasRoom:
    """The page `/filter` opens draws four components per result.

        Six results plus the sort row and the navigation row stood at 37 of 40, and
        `per_page` is an argument of `PaginatedModuleView`. Raising it to seven raised
        the limit error instead of showing a seventh module. The separators between
        the results are a blank line in the title now, which is 31 at six results and
        room up to nine.
    """

    # The page size the view has to survive. `per_page` defaults to 6.
    LARGEST_PAGE = 9

    @staticmethod
    def _page_size(per_page: int, results: int = 30) -> int:
        """Builds one page of a result list and counts its components."""
        # pylint: disable=import-outside-toplevel
        from oscar.ui.select_view import PaginatedModuleView
        from util.enums import ModuleLanguage
        from util.module import Module

        modules = [
            Module(
                id_=number,
                language=ModuleLanguage.DE,
                title=f"Modul {number}",
                credit_points="5",
            )
            for number in range(results)
        ]
        with patch("util.database.get_user_language", return_value=LanguageCode.DE):
            view = PaginatedModuleView(modules, user_id=USER, per_page=per_page)
        return len(list(view.walk_children()))

    def test_the_default_page_fits(self):
        assert self._page_size(6) <= WARN_AT

    def test_a_bigger_page_still_fits(self):
        """This is the test that would have caught it. `per_page=7` used to crash."""
        for per_page in range(1, self.LARGEST_PAGE + 1):
            try:
                size = self._page_size(per_page)
            except ValueError as error:
                pytest.fail(f"per_page={per_page} breaks the result list: {error}")
            assert size <= MAX_CHILDREN, f"per_page={per_page} is {size} of {MAX_CHILDREN}"

    def test_an_empty_result_list_is_small(self):
        assert self._page_size(6, results=0) <= WARN_AT

    def test_the_page_does_not_grow_with_the_number_of_results(self):
        """Ten thousand hits and six hits have to cost the same, that is the point."""
        assert self._page_size(6, results=6) == self._page_size(6, results=10000)

    def test_a_result_costs_no_separator(self):
        """One separator per result is what took the page to 37 of 40."""
        # pylint: disable=import-outside-toplevel
        from oscar.ui.select_view import PaginatedModuleView
        from util.enums import ModuleLanguage
        from util.module import Module

        modules = [
            Module(id_=n, language=ModuleLanguage.DE, title=f"Modul {n}", credit_points="5")
            for n in range(12)
        ]
        with patch("util.database.get_user_language", return_value=LanguageCode.DE):
            view = PaginatedModuleView(modules, user_id=USER, per_page=6)
        separators = [
            item for item in view.walk_children()
            if isinstance(item, discord.ui.Separator)
        ]
        assert len(separators) <= 1, (
            f"{len(separators)} separators on one page. Each result that carries one "
            "is a component the next page size needs."
        )
