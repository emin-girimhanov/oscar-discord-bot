"""Every command stays typeable. `/start` only names the eight you need on day one.

An earlier version of this file guarded the opposite: the picker was cut to eight
commands and `/help` opened the rest. That was the wrong trade. `/ansprechpartner`,
`/fristen`, `/klausuren` and the others are quicker to type than to find in a menu, so
they are all registered again.

What stayed is the reason the cut was tried at all. The welcome screen listed every
command it could find, one component each, which pushed it past the forty component
limit of a discord view and made `/start` raise instead of answer. So `/start` names
the eight in `CORE`, and `/help` explains all of them.
"""

import importlib
import pkgutil

import pytest

import oscar.cogs as cogs
from oscar.cogs.help import command_order
from oscar.ui.help_launcher import HELP_ENTRIES
from util.command_surface import ADMIN, CORE, CORE_ORDER
from util.translations import COMMAND_TEXTS, HELP_ANSWERS


# Commands `/help` does not explain, and why that is fine.
UNDOCUMENTED: dict[str, str] = {
    # the German or English twin of a command that is documented
    "hier": "the same command as /here",
    "contacts": "the English name of /ansprechpartner",
    "elearning": "the English name of /lms",
    "deadlines": "the English name of /fristen",
    "challenge": "the German name of /codegolf",
    "recommend": "the English name of /suggest",
    "statistik": "the German name of /cohort",
    "semesterplan": "documented",
    # administrators only, hidden from students by discord itself
    "version": "admin only",
    "review_feedback": "admin only",
    # demonstrations of the ui toolkit, never meant for students
    "buttons": "a developer demo",
    "colors": "a developer demo",
    "pagination": "a developer demo",
}


def all_commands() -> list[str]:
    """Every slash command the cogs register."""
    names: list[str] = []
    for module in pkgutil.iter_modules(cogs.__path__):
        imported = importlib.import_module(f"oscar.cogs.{module.name}")
        for value in vars(imported).values():
            if isinstance(value, type) and hasattr(value, "__cog_app_commands__"):
                names.extend(command.name for command in value.__cog_app_commands__)
    return sorted(set(names))


class TestTheCoreSet:
    """What `/start` puts in front of a newcomer."""

    def test_it_stays_small(self):
        """Eight is what somebody reads on their first day."""
        assert len(CORE) == 8

    @pytest.mark.parametrize(
        "name",
        ["start", "help", "module", "here", "filter", "compare", "semesterplan", "my_data"],
    )
    def test_the_commands_worth_typing_are_in_it(self, name: str):
        assert name in CORE

    def test_my_data_is_in_it(self):
        """Deleting your own data must not need a list first."""
        assert "my_data" in CORE

    def test_the_order_holds_the_same_names(self):
        assert set(CORE_ORDER) == CORE
        assert len(CORE_ORDER) == len(CORE)

    def test_core_and_admin_do_not_overlap(self):
        assert not CORE & ADMIN

    def test_something_outside_it_is_still_a_command(self):
        """`/klausuren` is not on the welcome screen and works all the same."""
        assert not "klausuren" in CORE
        assert "klausuren" in all_commands()


class TestNothingIsHidden:
    """The regression the earlier reduction caused."""

    @pytest.mark.parametrize(
        "name",
        ["ansprechpartner", "fristen", "klausuren", "badges", "progress", "lms",
         "codegolf", "suggest", "standard_plan", "feedback", "rate", "studybuddy"],
    )
    def test_the_features_are_typeable_commands(self, name: str):
        """They were taken out of the picker once. They are back."""
        assert name in all_commands()

    def test_every_command_is_explained_or_excused(self):
        """A command `/help` cannot explain is one nobody can look up."""
        unexplained = [
            name
            for name in all_commands()
            if name not in COMMAND_TEXTS and name not in UNDOCUMENTED
        ]
        assert not unexplained, (
            f"{unexplained} have no entry in COMMAND_TEXTS. Write one, or say in "
            "UNDOCUMENTED why it needs none."
        )

    def test_every_documented_command_has_an_answer(self):
        """The dropdown promises an explanation, so there has to be one."""
        for name in COMMAND_TEXTS:
            assert name in HELP_ANSWERS, f"/{name} is listed but has no answer"

    def test_help_lists_the_core_ones_first(self):
        listed = command_order()
        assert listed[: len(CORE_ORDER)] == list(CORE_ORDER)

    def test_help_lists_every_documented_command(self):
        assert set(command_order()) == set(COMMAND_TEXTS)

    def test_the_menu_fits_a_discord_select(self):
        """Discord shows twenty five options and silently drops the rest."""
        assert len(command_order()) <= 25


class TestTheHelpMenuStillOpensThings:
    """`/help` gained a menu that starts a feature. It stays, commands or not."""

    def test_the_menu_is_not_empty(self):
        assert HELP_ENTRIES

    def test_no_entry_duplicates_a_core_command(self):
        """The eight are typed. The menu is for the rest."""
        for entry in HELP_ENTRIES:
            assert entry.key not in CORE
