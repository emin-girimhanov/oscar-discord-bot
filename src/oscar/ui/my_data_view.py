""" The views behind `/my_data`, where a student reads and deletes their own data.

    Two views live here. `MyDataView` lists what is stored and hands the same data
    out as a file. `DeleteConfirmView` is the question in front of the deletion,
    because the deletion cannot be undone and a semester plan is real work.
"""

import io
import json
from datetime import datetime, timezone

import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from oscar.ui.owner_only import OwnerOnly
from util.database import get_database
from util.enums import LanguageCode
from util.translations import MY_DATA_TEXTS, t
from util.typed_dicts import UserDataDict


# The overview is a summary. Listing a hundred modules would hit the component limit,
# and the file behind the download button holds every one of them anyway.
MAX_LISTED_MODULES: int = 15

# Same reasoning for the feedback, of which a student rarely has more than a handful.
MAX_LISTED_FEEDBACK: int = 5

EXPORT_FILENAME: str = "oscar_my_data.json"

TIMEOUT: int = 300

ACCENT_COLOR: int = 0x4378D5


def has_data(data: UserDataDict) -> bool:
    """ Tells whether the database holds anything at all about this student.

        A bare row in `users` counts. It is their discord id, and we stored it.

        Parameters:
            data: an export as `Database.export_user_data` returns it.

        Returns:
            `False` for somebody who never used the bot, `True` otherwise.
    """
    return bool(
        data["account"]
        or data["preferences"]
        or data["semester_plan"]
        or data["feedback"]
        or data.get("challenge_submissions")
    )


def _value_or_placeholder(value: object, language: LanguageCode) -> str:
    """ Renders a stored value, or says that the column is empty."""
    if value is None or value == "":
        return t(language, "not_stored", MY_DATA_TEXTS)
    return str(value)


def _feedback_date(timestamp: object) -> str:
    """ Turns the stored unix time into a date a student recognises."""
    if not isinstance(timestamp, int):
        return "?"
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")


def _account_lines(data: UserDataDict, language: LanguageCode) -> list[str]:
    """ The `users` row: the discord id, and a name column we never write."""
    account: dict[str, object] = data["account"] or {}
    return [
        t(language, "account_heading", MY_DATA_TEXTS),
        f"{t(language, 'discord_id', MY_DATA_TEXTS)}: "
        f"{_value_or_placeholder(account.get('id', data['user_id']), language)}",
        f"{t(language, 'stored_name', MY_DATA_TEXTS)}: "
        f"{_value_or_placeholder(account.get('name'), language)}",
    ]


def _preference_lines(data: UserDataDict, language: LanguageCode) -> list[str]:
    """ The `preferences` row, one label per column."""
    lines: list[str] = [t(language, "preferences_heading", MY_DATA_TEXTS)]

    preferences: dict[str, object] | None = data["preferences"]
    if not preferences:
        lines.append(t(language, "no_preferences", MY_DATA_TEXTS))
        return lines

    start: object = preferences.get("winter_semester")
    start_name: str = t(language, "not_stored", MY_DATA_TEXTS)
    if start is not None:
        start_name = t(
            language, "winter_start" if start else "summer_start", MY_DATA_TEXTS
        )

    for key, column in (
        ("preference_language", "language"),
        ("preference_semester", "semester"),
        ("preference_major", "major"),
        ("preference_spo", "spo"),
    ):
        lines.append(
            f"{t(language, key, MY_DATA_TEXTS)}: "
            f"{_value_or_placeholder(preferences.get(column), language)}"
        )

    lines.append(f"{t(language, 'preference_start', MY_DATA_TEXTS)}: {start_name}")
    return lines


def _plan_lines(data: UserDataDict, language: LanguageCode) -> list[str]:
    """ The saved modules, by title, because an id alone tells a student nothing."""
    plan: list[dict[str, object]] = data["semester_plan"]
    lines: list[str] = [
        t(language, "plan_heading", MY_DATA_TEXTS).format(count=len(plan))
    ]

    if not plan:
        lines.append(t(language, "no_plan", MY_DATA_TEXTS))
        return lines

    title_column: str = "title_en" if language == LanguageCode.EN else "title"
    for entry in plan[:MAX_LISTED_MODULES]:
        title: object = entry.get(title_column) or entry.get("title")
        if not title:
            title = t(language, "unknown_module", MY_DATA_TEXTS)
        lines.append(f"• {title} ({entry.get('module_id')})")

    hidden: int = len(plan) - MAX_LISTED_MODULES
    if hidden > 0:
        lines.append(t(language, "more_modules", MY_DATA_TEXTS).format(count=hidden))

    return lines


def _feedback_lines(data: UserDataDict, language: LanguageCode) -> list[str]:
    """ The feedback entries, by date and rating. The free text stays in the file."""
    feedback: list[dict[str, object]] = data["feedback"]
    lines: list[str] = [
        t(language, "feedback_heading", MY_DATA_TEXTS).format(count=len(feedback))
    ]

    if not feedback:
        lines.append(t(language, "no_feedback", MY_DATA_TEXTS))
        return lines

    for entry in feedback[:MAX_LISTED_FEEDBACK]:
        lines.append("• " + t(language, "feedback_entry", MY_DATA_TEXTS).format(
            date = _feedback_date(entry.get("time")),
            intuitiveness = entry.get("intuitiveness"),
            discoverability = entry.get("discoverability"),
            usefulness = entry.get("usefulness"),
        ))

    lines.append(t(language, "feedback_texts_note", MY_DATA_TEXTS))
    return lines


def summarise(data: UserDataDict, language: LanguageCode) -> str:
    """ Writes the export out as something a student can read at a glance.

        The download holds the same data verbatim. This is the friendlier half of
        the answer, for somebody who only wants to see what we know.

        Parameters:
            data:     an export as `Database.export_user_data` returns it.
            language: the language the student picked.

        Returns:
            One block of markdown, with a section per table.
    """
    blocks: list[list[str]] = [
        _account_lines(data, language),
        _preference_lines(data, language),
        _plan_lines(data, language),
        _feedback_lines(data, language),
    ]
    return "\n\n".join("\n".join(block) for block in blocks)


def export_file(data: UserDataDict) -> discord.File:
    """ Packs the export into the JSON file a student can keep.

        Parameters:
            data: an export as `Database.export_user_data` returns it.

        Returns:
            A `discord.File` named `oscar_my_data.json`.
    """
    payload: str = json.dumps(data, indent=4, ensure_ascii=False, default=str)
    return discord.File(
        io.BytesIO(payload.encode("utf-8")), filename=EXPORT_FILENAME
    )


# OwnerOnly first, or discord.py's own check wins and everybody may click
class MyDataView(OwnerOnly, LayoutView):
    """ Shows a student everything stored about them, and offers both exits.

        The data is read once, by the cog, and handed in. The view never guesses
        whose data it shows.
    """

    def __init__(self, user_id: int, data: UserDataDict, language: LanguageCode):
        """ Parameters:
                user_id:  the student who ran the command.
                data:     their export, as `Database.export_user_data` returns it.
                language: the language they picked.
        """
        super().__init__(timeout=TIMEOUT)
        self.user_id: int = user_id
        self.data: UserDataDict = data
        self.language: LanguageCode = language

        self.download_button: Button[LayoutView] = Button(
            label=t(self.language, "download_button", MY_DATA_TEXTS),
            style=discord.ButtonStyle.secondary,
        )
        self.download_button.callback = self._download

        self.delete_button: Button[LayoutView] = Button(
            label=t(self.language, "delete_button", MY_DATA_TEXTS),
            style=discord.ButtonStyle.danger,
        )
        self.delete_button.callback = self._ask_before_deleting

        self._build_view()

    def _build_view(self) -> None:
        """ Draws the summary and the two buttons below it."""
        _ = self.clear_items()
        _ = self.add_item(
            Container(
                TextDisplay(f"# {t(self.language, 'title', MY_DATA_TEXTS)}"),
                TextDisplay(t(self.language, "intro", MY_DATA_TEXTS)),
                Separator(),
                TextDisplay(summarise(self.data, self.language)),
                Separator(),
                ActionRow[LayoutView](self.download_button, self.delete_button),
                accent_color=ACCENT_COLOR,
            )
        )

    async def _download(self, interaction: discord.Interaction) -> None:
        """ Sends the same data as a file, in its own ephemeral message.

            A file cannot be attached to this view, because a components v2
            message only shows attachments a component points at. A separate
            message is the simpler answer, and `/review_feedback` sends its
            export the same way.
        """
        _ = await interaction.response.send_message(
            t(self.language, "download_ready", MY_DATA_TEXTS),
            file=export_file(self.data),
            ephemeral=True,
        )

    async def _ask_before_deleting(self, interaction: discord.Interaction) -> None:
        """ Opens the confirmation. Nothing is deleted here."""
        _ = await interaction.response.send_message(
            view=DeleteConfirmView(self.user_id, self.data, self.language),
            ephemeral=True,
        )


# OwnerOnly first, or discord.py's own check wins and everybody may click
class DeleteConfirmView(OwnerOnly, LayoutView):
    """ The question in front of the deletion.

        It names what disappears, with the counts of this student's own rows, so
        nobody loses a semester plan they spent an afternoon on to a stray click.
    """

    def __init__(self, user_id: int, data: UserDataDict, language: LanguageCode):
        """ Parameters:
                user_id:  the student whose data would be deleted.
                data:     their export, read for the counts shown in the question.
                language: the language they picked.
        """
        super().__init__(timeout=TIMEOUT)
        self.user_id: int = user_id
        self.data: UserDataDict = data
        self.language: LanguageCode = language

        self.confirm_button: Button[LayoutView] = Button(
            label=t(self.language, "confirm_yes", MY_DATA_TEXTS),
            style=discord.ButtonStyle.danger,
        )
        self.confirm_button.callback = self._delete

        self.cancel_button: Button[LayoutView] = Button(
            label=t(self.language, "confirm_no", MY_DATA_TEXTS),
            style=discord.ButtonStyle.secondary,
        )
        self.cancel_button.callback = self._cancel

        self._build_view()

    def question(self) -> str:
        """ The wording of the question, with this student's own counts in it.

            Returns:
                The list of what a confirmation removes.
        """
        return t(self.language, "confirm_text", MY_DATA_TEXTS).format(
            modules = len(self.data["semester_plan"]),
            feedback = len(self.data["feedback"]),
        )

    def _build_view(self) -> None:
        """ Draws the question and the two buttons under it."""
        _ = self.clear_items()
        _ = self.add_item(
            Container(
                TextDisplay(f"# {t(self.language, 'confirm_title', MY_DATA_TEXTS)}"),
                TextDisplay(self.question()),
                Separator(),
                ActionRow[LayoutView](self.confirm_button, self.cancel_button),
                accent_color=discord.Color.red().value,
            )
        )

    def _show_outcome(self, message: str) -> None:
        """ Replaces the question with its answer, buttons and all.

            Parameters:
                message: what happened, in the students language.
        """
        _ = self.clear_items()
        _ = self.add_item(
            Container(
                TextDisplay(message),
                accent_color=ACCENT_COLOR,
            )
        )
        self.stop()

    async def _delete(self, interaction: discord.Interaction) -> None:
        """ Removes everything, then says so in place of the question."""
        # `delete_user_data` logs how many rows went, without naming the student
        _ = get_database().delete_user_data(self.user_id)

        self._show_outcome(t(self.language, "deleted", MY_DATA_TEXTS))
        _ = await interaction.response.edit_message(view=self)

    async def _cancel(self, interaction: discord.Interaction) -> None:
        """ Keeps everything and says so."""
        self._show_outcome(t(self.language, "cancelled", MY_DATA_TEXTS))
        _ = await interaction.response.edit_message(view=self)
