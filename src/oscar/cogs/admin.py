""" Administrative cog for a discord bot."""

import io
from io import BytesIO
import json
import os
from typing import override
import time
import discord
from discord import Client, File, Interaction, MediaGalleryItem, app_commands
from discord.ext import commands
from discord.ui import ActionRow, Button, Container, LayoutView, MediaGallery, Section, Separator
from discord.ui import TextDisplay
from loguru import logger

from oscar.ui.translated_view import TranslatedView
from util.database import Database, get_database
from util.enums import LanguageCode
from util.plots import create_feedback_boxplot, create_feedback_timeline
from util.translations import FEEDBACK_REVIEW, format_duration
from util.typed_dicts import FeedbackReviewDict



DEVELOPER_IDS: list[int] = [
    515896235081859091,     # @combifightet
    363003829912076289,     # @malt0se
    241687107049881602,     # @grosskahn
    1071428951844585482,    # @_polylux_
]



def is_admin_or_developer(interaction: discord.Interaction) -> bool:
    """Check if user is an admin or developer."""
    # pylint: disable=C0301 # (line-too-long)
    return interaction.user.id in DEVELOPER_IDS or (interaction.user.guild_permissions.administrator) # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportAttributeAccessIssue]


class Administration(commands.Cog):
    """ Class for the administration cog."""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded Administration cog")

    # discord hides a command with this from anybody without the permission, so the
    # two admin commands never appear in a student's picker
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(description="Check which build of OSCAR is currently running")
    async def version(self, interaction: discord.Interaction):
        """ Diagnostic command to confirm a new deploy actually went live."""
        revision = os.environ.get("OSCAR_REVISION", "unknown (local run)")
        await interaction.response.send_message(
            f"OSCAR build `{revision}`",
            ephemeral=True,
        )

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(description="Review the given feedback")
    @app_commands.check(is_admin_or_developer)
    async def review_feedback(self, interaction: discord.Interaction):
        """ Command to review feedback given by users."""
        # \/ important (makes the bot say it"s thinking)
        _ = await interaction.response.defer()
        db: Database = get_database()
        feedback: list[FeedbackReviewDict] = db.get_feedback()

        boxplot_file: File = await create_feedback_boxplot(feedback)
        timeline_file: File = await create_feedback_timeline(feedback)

        await interaction.followup.send(
            view=ReviewFeedbackView(
                interaction=interaction,
                feedback=feedback,
                images=[boxplot_file, timeline_file],
            ),
            files=[boxplot_file, timeline_file],
        )


async def setup(bot: commands.Bot):
    """ Setup the Administration cog."""
    await bot.add_cog(Administration(bot))






class ReviewFeedbackView(TranslatedView):
    """ Feedback (review) view that extends TranslatedView for language switching."""

    # as unix time (eg. seconds)
    periods: list[int|None] = [
        3600,       # 1 Hour
        43200,      # 12 Hours
        86400,      # 1 Day
        604800,     # 1 Week
        2629743,    # 1 Month
        15778458,   # 6 Months
        31556926,   # 1 Year
        31556926,   # 2 Year
        31556926,   # 4 Year
        None        # All Time
    ]

    feedback: list[FeedbackReviewDict] = []
    feedback_filtered: list[FeedbackReviewDict] = []

    selected_zoom: int|None = None

    files: list[discord.File] = []

    def __init__(
            self,
            interaction: discord.Interaction,
            feedback: list[FeedbackReviewDict],
            images: list[discord.File],
            default_language: LanguageCode = LanguageCode.EN
        ):
        self.interaction: Interaction[Client] = interaction
        self.feedback = feedback
        self.files = images


        # make periods unique and sorted with None at the end
        self.periods = list(set(self.periods))
        self.periods.remove(None)
        self.periods.sort()  # pyright: ignore[reportCallIssue]
        # TODO: add code to only select valid (sensible) time spans
        self.periods.append(None)

        # limit time spans to a max of 5 options
        if len(self.periods) == 0:
            self.periods = [None]
        elif len(self.periods) > 5:
            step_size: float = (len(self.periods) - 1) / 4
            indices_to_keep: list[int] = [0]
            for i in range(1, 4):
                indices_to_keep.append(int(round(i * step_size)))
            self.periods = [self.periods[i] for i in indices_to_keep]
            self.periods.append(None)

        self.__filter_feedback()

        super().__init__(default_language)


    async def check_user(self, interaction: discord.Interaction) -> bool:
        """ Chec weather the user has the right to perform the interaction"""
        if interaction.user == self.interaction.user:
            return True

        _ = await interaction.response.send_message(
            "Only the original auther can interact",
            ephemeral=True
        )
        return False


    async def _create_boxplot_image(self) -> discord.File:
        """Generate boxplot image from filtered feedback data."""
        return await create_feedback_boxplot(
            self.feedback_filtered,
            self.language_code
        )

    async def _create_timeline_image(self) -> discord.File:
        """Generate timeline image from filtered feedback data."""
        return await create_feedback_timeline(
            self.feedback,
            self.selected_zoom,
            self.language_code
        )


    @override
    def _build_content(self):
        """ Build the feedback (review) view content with current language."""

        # time_span_buttons: list[Button[LayoutView]] = []
        time_span_buttons: ActionRow[LayoutView] = ActionRow()
        for duration in self.periods:
            button: Button[LayoutView] = Button(
                id = duration,
                label=format_duration(duration, self.language_code),
                disabled=self.selected_zoom == duration,
                style=discord.ButtonStyle.primary if self.selected_zoom == duration else
                      discord.ButtonStyle.secondary
            )

            async def time_span_callback(
                interaction: discord.Interaction,
                duration: int|None = duration
            ):
                if not await self.check_user(interaction):
                    return
                if duration == self.selected_zoom:
                    return

                self.selected_zoom = duration
                self.__filter_feedback()
                await self._update(interaction)

            button.callback = time_span_callback
            _ = time_span_buttons.add_item(button)


        download_button: Button[LayoutView] = Button(
            label="⤓",
            disabled=len(self.feedback)==0,
            style=discord.ButtonStyle.secondary,
        )

        async def download_callback(interaction: discord.Interaction):
            if not await self.check_user(interaction):
                return

            json_data: str = json.dumps(self.feedback, indent=4)
            json_bytes: BytesIO = io.BytesIO(json_data.encode('utf-8'))

            file: File = File(json_bytes, filename="feedback_data.json")

            _ = await interaction.response.send_message(
                FEEDBACK_REVIEW["finished_download"][self.language_code],
                file=file,
                ephemeral=True
            )

        download_button.callback = download_callback


        _ = self.add_item(
            Container(
                Section[LayoutView](
                    TextDisplay(f"# {FEEDBACK_REVIEW['review_feedback'][self.language_code]}"),
                    accessory=self._create_language_toggle(),
                ),
                Separator(),

                # TextDisplay(f"## {FEEDBACK_REVIEW["intuitiveness"][self.language_code]}"),
                TextDisplay(f"-# {FEEDBACK_REVIEW['zoom'][self.language_code]}"),
                time_span_buttons,
                Separator(),
                Separator(),

                MediaGallery(
                    MediaGalleryItem(self.files[0]), # boxplot image
                ),
                Separator(),
                MediaGallery(
                    MediaGalleryItem(self.files[1]), # timeline image
                ),
                Separator(),
                Separator(),

                # section for sending complete feedback data as a `.json` to one"s own dms
                Section[LayoutView](
                    TextDisplay(
                        f"-# {FEEDBACK_REVIEW['data_download'][self.language_code]} _(`.json`)_"
                    ),
                    accessory=download_button,
                ),
            )
        )


    @override
    async def _update(self, interaction: discord.Interaction):
        _ = self.clear_items()
        self._build_content()

        boxplot_file = await self._create_boxplot_image()
        timeline_file = await self._create_timeline_image()

        _ = await interaction.response.defer()
        _ = await interaction.edit_original_response(
            view=self,
            attachments=[boxplot_file, timeline_file]
        )


    def __filter_feedback(self):
        """ Filter the feedback based on the selected zoom (time span)."""
        if self.selected_zoom is None:
            self.feedback_filtered = self.feedback
            return

        current_time: int = int(time.time())
        filtered: list[FeedbackReviewDict] = [
            fb for fb in self.feedback
            if (current_time - fb["timestamp"]) <= self.selected_zoom
        ]

        self.feedback_filtered = filtered
