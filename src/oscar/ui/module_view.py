""" This module holds the view for a single module"""

import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from oscar.ui.all_info_view import AllInfoView
from util.bookstack import has_page, module_url
from util.database import get_database, get_user_language
from util.enums import LanguageCode, StudyCourse
from util.exams import primary_archive
from util.lms import get_default_platform
from util.lsf import lsf_search_url
from util.module import Module
from util.translations import (
    module_language_name,
    ratings_label,
    t,
    EXAM_TEXTS,
    MODULE_TEXTS,
    RATING_TEXTS,
)


# How many reviews the card asks for. It shows the newest and counts the rest, so it
# only needs to know whether there is more than one.
REVIEW_PEEK: int = 5

# The newest review is cut here. The card is a summary, the full text is one click away.
MAX_PEEK_LENGTH: int = 140


class ModuleView(LayoutView):
    """ Class for displaying module related information"""
    def __init__(
        self,
        user_id: int,
        module: Module):
        super().__init__()
        self.module: Module = module
        self.language: LanguageCode = get_user_language(user_id)

        # The handbook link points into the users own programme when we know it.
        preferences = get_database().get_preferences(user_id)
        self.study_course: StudyCourse | None = (
            preferences.get("major") if preferences else None
        )

        self._build_view()

    def _get_rating_text(self) -> str:
        rating_info = get_database().get_module_ratings(self.module.id_)
        count = rating_info.get("count", 0) if isinstance(rating_info, dict) else 0
        if isinstance(count, (int, float)) and count > 0:
            count_label = ratings_label(self.language, int(count))
            diff_label = t(self.language, "difficulty", RATING_TEXTS)
            avg_rating = rating_info.get("avg_rating") or 0.0
            avg_diff = rating_info.get("avg_difficulty") or 0.0
            return (
                f"\n⭐ {avg_rating:.1f}/5 ({int(count)} {count_label}) | "
                f"🏋️ {diff_label}: {avg_diff:.1f}/5"
            )
        no_ratings_label = t(self.language, "no_ratings", RATING_TEXTS)
        return f"\n⭐ {no_ratings_label}"

    def _get_review_text(self) -> str:
        """ The newest written review, so the card shows one without a click.

            The comments were stored from the first day and displayed nowhere, so a
            student wrote a tip that nobody could read. The averages alone never say
            *why* a module is rated the way it is.

            Returns:
                One quoted line plus a count of the rest, or the empty string when
                nobody has written anything yet.
        """
        comments = get_database().get_module_comments(self.module.id_, limit=REVIEW_PEEK)
        if not comments:
            return ""

        newest = str(comments[0].get("comment", "")).strip().replace("\n", " ")
        if not newest:
            return ""
        if len(newest) > MAX_PEEK_LENGTH:
            newest = newest[: MAX_PEEK_LENGTH - 1].rstrip() + "…"

        line = "\n" + t(self.language, "latest_review", RATING_TEXTS).format(comment=newest)
        if len(comments) > 1:
            line += " " + t(self.language, "more_reviews", RATING_TEXTS).format(
                count=len(comments) - 1
            )
        return line

    # pylint: disable=too-many-locals
    def _build_view(self):
        _ = self.clear_items()

        plan_label = (
            "zu Semesterübersicht hinzufügen"
            if self.language == LanguageCode.DE
            else "add to semester overview"
        )
        semester_plan_button: Button[LayoutView] = Button(
            label=plan_label,
            style=discord.ButtonStyle.primary,
        )
        # A link button opens the public LSF course search, it takes no callback.
        lsf_button: Button[LayoutView] = Button(
            label="zum LSF-Modul" if self.language == LanguageCode.DE else "to LSF",
            style=discord.ButtonStyle.link,
            url=lsf_search_url(self.module.get_title(self.language)),
        )
        # The faculty module handbook. Only about two thirds of the modules in the
        # catalogue have a page in it, and the rest fall back to the BookStack search.
        # The label says which of the two it is, so nobody expects the module and gets
        # a result list.
        exact_page: bool = has_page(self.module.id_, self.study_course)
        if exact_page:
            handbook_label = (
                "zum Modulhandbuch" if self.language == LanguageCode.DE else "to the handbook"
            )
        else:
            handbook_label = (
                "im Handbuch suchen"
                if self.language == LanguageCode.DE
                else "search the handbook"
            )
        bookstack_button: Button[LayoutView] = Button(
            label=handbook_label,
            style=discord.ButtonStyle.link,
            url=module_url(
                self.module.id_,
                self.module.get_title(self.language),
                self.study_course,
            ),
        )
        info_button: Button[LayoutView] = Button(
            label="mehr Infos" if self.language == LanguageCode.DE else "more info",
            style=discord.ButtonStyle.primary,
        )
        study_buddy_button: Button[LayoutView] = Button(
            label="👥 Lerngruppe" if self.language == LanguageCode.DE else "👥 Study Group",
            style=discord.ButtonStyle.secondary,
        )

        async def study_buddy_callback(interaction: discord.Interaction):
            # pylint: disable=import-outside-toplevel
            from oscar.ui.study_buddy_view import StudyBuddyView
            await interaction.response.send_message(
                view=StudyBuddyView(user_id=interaction.user.id, module_id=self.module.id_),
                ephemeral=True,
            )

        study_buddy_button.callback = study_buddy_callback

        rate_button: Button[LayoutView] = Button(
            label="⭐ Bewerten" if self.language == LanguageCode.DE else "⭐ Rate",
            style=discord.ButtonStyle.success,
        )
        # `klausuren.farafin.de` used to sit here. That host no longer resolves,
        # so the archive is named in one place now, `util.exams`.
        exam_button: Button[LayoutView] = Button(
            label=t(self.language, "exam_button", EXAM_TEXTS),
            style=discord.ButtonStyle.link,
            url=primary_archive().url(self.language),
        )
        # A course has no stable address, so the button opens the platform itself.
        # `util.lms` names which one, and it is checked there that the host answers.
        elearning = get_default_platform()
        moodle_button: Button[LayoutView] = Button(
            label=f"{elearning.emoji} eLearning",
            style=discord.ButtonStyle.link,
            url=elearning.url,
        )

        reviews_button: Button[LayoutView] = Button(
            label=t(self.language, "reviews_button", RATING_TEXTS),
            style=discord.ButtonStyle.secondary,
        )

        async def reviews_button_callback(interaction: discord.Interaction):
            # pylint: disable=import-outside-toplevel
            from oscar.ui.module_reviews_view import ModuleReviewsView

            await interaction.response.send_message(
                view=ModuleReviewsView(interaction.user.id, self.module),
                ephemeral=True,
            )

        reviews_button.callback = reviews_button_callback

        async def rate_button_callback(interaction: discord.Interaction):
            # pylint: disable=import-outside-toplevel
            from oscar.ui.rating_modal import ModuleRatingModal
            await interaction.response.send_modal(
                ModuleRatingModal(module=self.module, language=self.language)
            )

        rate_button.callback = rate_button_callback

        async def semester_plan_button_callback(interaction: discord.Interaction):
            db = get_database()
            user_id = interaction.user.id
            db.add_to_semesterplan(user_id=user_id, module_id=self.module.id_)

            # the confirmation used to be german for everyone, including english users
            _ = await interaction.response.send_message(
                t(self.language, "added_to_plan", MODULE_TEXTS).format(
                    title=self.module.get_title(self.language)
                ),
                ephemeral=True,
            )

        # pylint: disable=broad-exception-caught
        async def info_button_callback(interaction: discord.Interaction):
            # Send initial (loading) response
            _ = await interaction.response.send_message(
                "Lade Modulinformationen...", ephemeral=True
            )
            user_id = interaction.user.id

            try:
                module = self.module
            except Exception as exc:
                err_msg = f"Fehler beim Laden des Moduls: {exc}"
                try:
                    _ = await interaction.edit_original_response(content=err_msg)
                except Exception:
                    await interaction.followup.send(err_msg, ephemeral=True)
                return

            try:
                _ = await interaction.edit_original_response(
                    content=None, view=AllInfoView(module=module, user_id=user_id)
                )
            except Exception:
                await interaction.followup.send(
                    view=AllInfoView(module=module, user_id=user_id), ephemeral=True
                )

        semester_plan_button.callback = semester_plan_button_callback
        info_button.callback = info_button_callback
        label1 = t(self.language, "kuerzel", MODULE_TEXTS)
        label2 = t(self.language, "sprache", MODULE_TEXTS)
        label3 = t(self.language, "dozent", MODULE_TEXTS)

        rating_text = self._get_rating_text() + self._get_review_text()

        _ = self.add_item(
            Container(
                TextDisplay(f"# {self.module.get_title(self.language)}"),
                Separator(),
                TextDisplay("\u200b"),
                TextDisplay(
                    f"{label1}"
                    + f"{self.module.abbreviation}\n"
                    + "SWS: "
                    + f"{self.module.get_teaching_form_sws(self.language).replace('\n',' ')}\n"
                    + f"{label2}"
                    + f"{module_language_name(self.module.language, self.language)}\n"
                    + f"{label3}"
                    + f"{self.module.lecturer}\n"
                    + "Creditpoints: "
                    + f"{self.module.credit_points}"
                    + rating_text
                ),
                TextDisplay("\u200b"),
                TextDisplay(f"{self.module.get_content(self.language)}"),
                TextDisplay("\u200b"),
                Separator(),
                ActionRow(
                    semester_plan_button,
                    lsf_button,
                    bookstack_button,
                    study_buddy_button,
                    info_button,
                ),
                ActionRow(
                    rate_button,
                    reviews_button,
                    moodle_button,
                    exam_button,
                ),
                accent_color=discord.Color.dark_blue(),
            )
        )
