""" What `/help` can start, for somebody who does not know the command name yet.

    Every one of these also has its own slash command. `/fristen` and this menu open
    the same view, and the command is the faster way once you know it exists. The menu
    is for the first weeks, when you do not.

    Each entry answers in a new private message, so the help itself stays on screen and
    a student can open the next thing without typing anything again.

    The handlers are public, because the cogs call them too. A command that is
    still registered is a thin wrapper around the same function, so a fix lands
    in one place instead of in two.

    Imports sit inside the handlers on purpose. Pulling every view into this module at
    import time would make it the hub of the whole package, and `module_view` already
    imports back into the ui package.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import discord

from util.command_surface import HIDDEN
from util.database import get_user_language
from util.enums import LanguageCode


# A role called "Semester 3" is how the server records what term somebody is in.
SEMESTER_ROLE = re.compile(r"Semester\s+(\d+)")

# What `semester_of` answers when no role says otherwise.
UNKNOWN_SEMESTER: int = -1


@dataclass(frozen=True)
class HelpEntry:
    """ One line of the `/help` menu, and what pressing it opens."""
    key: str
    emoji: str
    label_de: str
    label_en: str
    open: Callable[[discord.Interaction], Awaitable[None]]

    def label(self, language: LanguageCode) -> str:
        """ The text of this entry in the language of the reader."""
        text = self.label_en if language == LanguageCode.EN else self.label_de
        return f"{self.emoji} {text}"


def semester_of(interaction: discord.Interaction) -> int:
    """ Reads the term a student is in from their server roles.

        Parameters:
            interaction: The click discord.py handed over.

        Returns:
            The number behind a role called "Semester N", or `UNKNOWN_SEMESTER` when
            no such role is set. A direct message has no roles at all.
    """
    for role in getattr(interaction.user, "roles", []):
        found = SEMESTER_ROLE.match(role.name)
        if found:
            return int(found.group(1))
    return UNKNOWN_SEMESTER


async def open_standard_plan(interaction: discord.Interaction) -> None:
    """ The official study plan of the student's own programme, drawn as an image."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.splan_view import SPlanView

    user_id = interaction.user.id
    language = get_user_language(user_id)
    try:
        view = SPlanView(user_id=user_id)
    except ValueError:
        await interaction.response.send_message(
            "Bitte nutze zuerst /start und wähle deinen Studiengang und deine "
            "Prüfungsordnung aus."
            if language == LanguageCode.DE
            else "Run /start first and pick your programme and examination regulations.",
            ephemeral=True,
        )
        return

    # drawing takes a moment, answer before the three second limit
    _ = await interaction.response.defer(ephemeral=True)
    embed = view.create_embed()
    image_file = await asyncio.to_thread(view.get_image_file)
    if image_file is None:
        _ = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        return
    _ = await interaction.followup.send(
        embed=embed, view=view, file=image_file, ephemeral=True
    )


async def open_progress(interaction: discord.Interaction) -> None:
    """ Personal progress, badges and the cohort comparison, all in one view."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.progress_view import ProgressView

    _ = await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    await interaction.followup.send(
        view=ProgressView(user_id=user_id, default_language=get_user_language(user_id)),
        ephemeral=True,
    )


async def open_suggestions(interaction: discord.Interaction) -> None:
    """ Modules that fit the student's programme and open credit points."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.suggest_view import SuggestView

    _ = await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    await interaction.followup.send(
        view=SuggestView(user_id=user_id, default_language=get_user_language(user_id)),
        ephemeral=True,
    )


async def open_exams(interaction: discord.Interaction) -> None:
    """ The past exam archives of the student councils."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.exam_archive_view import ExamArchiveView

    await interaction.response.send_message(
        view=ExamArchiveView(interaction.user.id), ephemeral=True
    )


async def open_deadlines(interaction: discord.Interaction) -> None:
    """ Examination registration windows and the other dates of the term."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.deadlines_view import DeadlinesView

    _ = await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(
        view=DeadlinesView(default_language=get_user_language(interaction.user.id)),
        ephemeral=True,
    )


async def open_platforms(interaction: discord.Interaction) -> None:
    """ Which Moodle, which GitLab, which portal, and what to log in with."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.lms_view import LmsView

    _ = await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(
        view=LmsView(default_language=get_user_language(interaction.user.id)),
        ephemeral=True,
    )


async def open_contacts(interaction: discord.Interaction) -> None:
    """ The people to ask: dean's office, examination office, student council."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.contacts_view import ContactsView

    _ = await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(
        view=ContactsView(default_language=get_user_language(interaction.user.id)),
        ephemeral=True,
    )


async def open_code_golf(interaction: discord.Interaction) -> None:
    """ The weekly programming puzzle and its leaderboard."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.challenge_view import ChallengeView
    from util.challenges import get_current_weekly_challenge

    _ = await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(
        view=ChallengeView(
            default_language=get_user_language(interaction.user.id),
            initial_challenge_id=get_current_weekly_challenge().id,
        ),
        ephemeral=True,
    )


async def open_feedback(interaction: discord.Interaction) -> None:
    """ What the student thinks of the bot itself."""
    # pylint: disable=import-outside-toplevel
    from oscar.ui.feedback_view import FeedbackView

    await interaction.response.send_message(
        view=FeedbackView(user_id=interaction.user.id, semester=semester_of(interaction)),
        ephemeral=True,
    )


# The order is the order a student reads them in: studying first, then the campus,
# then the things that are nice rather than necessary.
ALL_ENTRIES: tuple[HelpEntry, ...] = (
    HelpEntry(
        "standard_plan", "🗺️", "Regelstudienplan", "Official study plan",
        open_standard_plan,
    ),
    HelpEntry(
        "progress", "📊", "Studienfortschritt", "Study progress", open_progress,
    ),
    HelpEntry(
        "suggest", "💡", "Modul-Empfehlungen", "Module suggestions", open_suggestions,
    ),
    HelpEntry("exams", "📚", "Altklausuren", "Past exams", open_exams),
    HelpEntry("deadlines", "📅", "Fristen & Termine", "Deadlines", open_deadlines),
    HelpEntry("platforms", "🎓", "Lernplattformen", "Learning platforms", open_platforms),
    HelpEntry("contacts", "📞", "Ansprechpartner", "Contacts", open_contacts),
    HelpEntry("codegolf", "🏌️", "Code Golf", "Code golf", open_code_golf),
    HelpEntry("feedback", "✉️", "Feedback zum Bot", "Feedback on the bot", open_feedback),
)


# What the menu shows: everything that is not switched off.
HELP_ENTRIES: tuple[HelpEntry, ...] = tuple(
    entry for entry in ALL_ENTRIES if entry.key not in HIDDEN
)


def get_entry(key: str) -> HelpEntry | None:
    """ Looks up one menu entry.

        Parameters:
            key: The value discord sends back when a line was picked.

        Returns:
            The entry, or `None` when no entry carries that key.
    """
    for entry in HELP_ENTRIES:
        if entry.key == key:
            return entry
    return None
