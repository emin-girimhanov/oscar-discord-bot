""" Builds every view of the bot against the live catalogue and reports what breaks.

    The unit tests build views from modules written by hand, and a module written by
    hand is always well formed. The real table is not. Two crashes got past the whole
    suite and were found by this script instead:

    * `/suggest` died on `TypeError: '>' not supported between instances of 'NoneType'
      and 'int'`, because 15 of the 410 rows send `Fachsemester` as null and
      `dict.get(key, default)` only falls back when the key is missing.
    * The result list of `/filter` stood at 37 of the 40 components a discord view
      holds, so `per_page=7` raised `ValueError: maximum number of children exceeded`.

    Nothing here asserts. It builds, counts and prints, and the exit code is the number
    of views that raised. Run it after a change to a view, and after the module table
    changes:

        python tools/smoke_views.py

    It needs the Nextcloud Tables API, so it is not part of the pipeline. `.env` has to
    be filled in the way `docs/developer/setup.md` describes.

    A view that raises on purpose is listed as expected. `SPlanView` raises
    `ValueError` for a student who has not run `/start` yet, and its caller catches
    that and says so.
"""

import asyncio
import sys
import traceback
from collections.abc import Callable
from unittest.mock import patch

from util.enums import LanguageCode


# Any user id that is not in the database, so the views fall back to their defaults.
USER: int = 4711

# The modules to build a card for. The first is whatever the catalogue lists first,
# the rest are picked because they broke something: a row with null columns, a title
# with an umlaut, a module whose handbook page is only in the catalogue book.
SAMPLE_IDS: tuple[int, ...] = (120282, 110360, 102625, 100391)

# Views that raise by design, with the reason. They are not failures.
EXPECTED: dict[str, str] = {
    "SPlanView": "ValueError when the student has not run /start yet, the caller says so",
}

# A view above this many of the 40 components a discord view holds is out of room.
WARN_AT: int = 36


class Report:
    """ Collects one line per view and decides the exit code."""

    def __init__(self) -> None:
        self.lines: list[tuple[str, str, bool]] = []

    def note(self, name: str, ok: bool, outcome: str) -> None:
        """ Adds a line that did not come from building a view.

            Parameters:
                name: What to call it in the report.
                ok: Whether it passed.
                outcome: What to print behind the name.
        """
        self.lines.append((name, outcome, ok))

    def record(self, name: str, build: Callable[[], object]) -> None:
        """ Builds one view and notes what happened.

            Parameters:
                name: What to call it in the report.
                build: Builds the view. Anything it raises is caught.
        """
        try:
            view = build()
            count = len(list(view.walk_children()))  # pyright: ignore[reportAttributeAccessIssue]
            room = "" if count <= WARN_AT else "  OUT OF ROOM"
            self.lines.append((name, f"{count:>2} / 40{room}", not room))
        except Exception as error:  # pylint: disable=broad-except
            reason = EXPECTED.get(name)
            if reason is not None:
                self.lines.append((name, f"expected: {reason}", True))
                return
            self.lines.append((name, f"{type(error).__name__}: {error}", False))
            print(f"\n--- {name} ---", file=sys.stderr)
            traceback.print_exc()

    def print(self) -> int:
        """ Writes the report and returns how many views failed."""
        print("\n=== views ===")
        failed = 0
        for name, outcome, ok in self.lines:
            if not ok:
                failed += 1
            print(f"{'  ' if ok else '!!'} {name:<40} {outcome}")
        print(f"\n{len(self.lines)} views built, {failed} failed")
        return failed


async def main() -> int:
    """ Builds everything and prints the report."""
    # pylint: disable=import-outside-toplevel, too-many-locals
    from oscar.ui.all_info_view import AllInfoView
    from oscar.ui.channel_module_view import ChannelModuleView
    from oscar.ui.compare_view import CompareView
    from oscar.ui.feedback_view import FeedbackView
    from oscar.ui.module_reviews_view import ModuleReviewsView
    from oscar.ui.module_view import ModuleView
    from oscar.ui.my_data_view import MyDataView
    from oscar.ui.select_view import PaginatedModuleView, SelectView
    from oscar.ui.semesterplan_view import SemesterplanView
    from oscar.ui.splan_view import SPlanView
    from oscar.ui.study_buddy_view import StudyBuddyView
    from oscar.ui.suggest_view import SuggestView
    from util.channel_module import find_candidates
    from util.database import get_database
    from util.module import Module, get_module_list
    from util.tables import Catalogue

    report = Report()
    catalogue = Catalogue(720)
    entries = catalogue.get_modules()
    print(f"catalogue: {len(entries)} modules")
    if not entries:
        print("the Tables API answered nothing, check .env", file=sys.stderr)
        return 1

    wanted = (entries[0].id_, *SAMPLE_IDS)
    modules: list[Module] = []
    for module_id in wanted:
        try:
            modules.append(Module.from_id(module_id))
        except Exception as error:  # pylint: disable=broad-except
            report.lines.append((f"Module.from_id({module_id})", str(error), False))

    german = LanguageCode.DE
    with patch("util.database.get_user_language", return_value=german):
        for module in modules:
            report.record(f"ModuleView({module.id_})", lambda m=module: ModuleView(USER, m))
            report.record(
                f"ModuleReviewsView({module.id_})",
                lambda m=module: ModuleReviewsView(USER, m),
            )
            report.record(
                f"AllInfoView({module.id_})", lambda m=module: AllInfoView(USER, m)
            )

        if len(modules) >= 3:
            report.record("CompareView", lambda: CompareView(USER, modules[:3]))

        candidates = find_candidates(catalogue, "datenbanken")
        report.record(
            "ChannelModuleView",
            lambda: ChannelModuleView(USER, "datenbanken", candidates),
        )

        every = get_module_list()
        print(f"built {len(every)} modules from the whole table")
        report.record("SelectView", lambda: SelectView(USER))
        report.record(
            "PaginatedModuleView (every module)",
            lambda: PaginatedModuleView(every, user_id=USER),
        )
        export = get_database().export_user_data(USER)
        report.record("MyDataView", lambda: MyDataView(USER, export, german))
        report.record("SPlanView", lambda: SPlanView(USER))
        report.record("SemesterplanView", lambda: SemesterplanView(USER))
        report.record("StudyBuddyView", lambda: StudyBuddyView(USER))
        report.record("FeedbackView", lambda: FeedbackView(USER, semester=3))
        report.record(
            "SuggestView", lambda: SuggestView(user_id=USER, default_language=german)
        )

    _score_everything(report, every)
    return report.print()


def _score_everything(report: Report, modules: list) -> None:
    """ Scores every module for a student who has a semester set.

        `SuggestView` alone does not reach the crash this script was written for. A
        user without preferences has no semester, and the comparison that raised sits
        behind `if ctx.semester is not None`. So the scoring is run here with a
        context that has one, against every module of the real table.

        Parameters:
            report: Where to note the outcome.
            modules: Every module, as `get_module_list` returns it.
    """
    # pylint: disable=import-outside-toplevel
    from util.enums import StudyCourse
    from util.suggestions import UserContext, _score_single_module

    context = UserContext(saved_ids=set(), major=StudyCourse.BSC_WIF, semester=5)
    name = f"/suggest scoring all {len(modules)} modules"
    try:
        scored = sum(
            _score_single_module(module, "ALL", context) is not None
            for module in modules
        )
        report.note(name, True, f"{scored} suggested, none raised")
    except Exception as error:  # pylint: disable=broad-except
        report.note(name, False, f"{type(error).__name__}: {error}")
        traceback.print_exc()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
