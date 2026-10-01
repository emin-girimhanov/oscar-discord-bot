""" This module holds the view for the standard study plan (Regelstudienplan)."""

from pathlib import Path

import discord
from discord.ui import Button, View

from oscar.ui.owner_only import OwnerOnly
from util.bookstack import book_url
from util.database import get_database, get_user_language
from util.enums import LanguageCode, PO, StudyCourse
from util.paths import assets_dir
from util.plan_image import render_semesterplan
from util.plan_progress import PlanProgress, load_saved_modules, match_plan
from util.semesterplans import Semesterplan, get_semesterplans_manager
from util.translations import PLAN_PROGRESS_TEXTS, STUDY_COURSES, t


# The two hand drawn images we have. Every other programme is rendered from its json.
# The picture of the official table, one per bachelor programme. The number is the
# one in the file name under `assets/images`, cut out of the Studien- und
# Prüfungsordnung by `tools/extract_semesterplan_images.py`.
#
# The picture beats anything OSCAR can render: it carries the exam rules, the
# weightings and the "mind. 10 CP benotet" bars, and none of that fits in a list of
# module titles. The master programmes have no picture, because their regulation
# prints credit point ranges per area rather than a table of modules.
STUDYCOURSE_TO_IMAGE_ID: dict[StudyCourse, str] = {
    StudyCourse.BSC_INF: "1",
    StudyCourse.BSC_CV: "2",
    StudyCourse.BSC_INGINF: "3",
    StudyCourse.BSC_WIF: "4",
}

# A discord embed field holds at most 1024 characters.
MAX_FIELD_LENGTH: int = 1024

# The name both the attachment and the embed refer to.
IMAGE_FILENAME: str = "studyplan.png"

# The marks in front of a module. A tick only ever means "this is in your plan",
# `PLAN_PROGRESS_TEXTS["no_grades"]` says so in the footer, because OSCAR stores no
# grades. An open box beats a cross, a wall of crosses reads as failure.
PLANNED_MARK: str = "✅"
OPEN_MARK: str = "⬜"


def _spo_year(spo: str | int) -> int:
    """ Converts a stored PO value like `'PO_2024'` (or `2024`) into the year."""
    if isinstance(spo, int):
        return spo
    return int(str(spo).rsplit("_", 1)[-1])


class SPlanView(OwnerOnly, View):
    """ View for the standard study plan (NO Components V2)."""

    def __init__(self, user_id: int):
        super().__init__(timeout=180)

        self.user_id: int = user_id
        self.language: LanguageCode = get_user_language(user_id)

        prefs = get_database().get_preferences(user_id)

        if not prefs or "spo" not in prefs or "major" not in prefs:
            raise ValueError("User has no complete study preferences")

        self.user_major: StudyCourse = prefs["major"]
        self.user_po: PO = PO[prefs["spo"]]
        self.winter: bool = prefs.get("winter_semester", True)

        self.plan: Semesterplan | None = get_semesterplans_manager().get_best_matching_plan(
            study_course=self.user_major,
            spo=_spo_year(self.user_po.name),
            winter_semester=self.winter,
        )

        # A student who saved nothing is shown the plain plan. Marking every box as
        # missing would be a wall of crosses that tells them nothing they can act on.
        self.progress: PlanProgress | None = None
        if self.plan is not None:
            saved = load_saved_modules(user_id)
            if saved:
                self.progress = match_plan(self.plan, saved, self.user_major)

        # The official handbook for this programme, a link button needs no callback.
        _ = self.add_item(
            Button(
                label=(
                    "zum Modulhandbuch" if self.language == LanguageCode.DE
                    else "to the handbook"
                ),
                style=discord.ButtonStyle.link,
                url=book_url(self.user_major),
            )
        )

    @property
    def major_name(self) -> str:
        """ The study programme in the users language."""
        return STUDY_COURSES.get(self.user_major, {}).get(
            self.language, self.user_major.name
        )

    def get_image_path(self) -> Path | None:
        """ Returns the hand drawn plan image for this programme, or `None`.

            Only two programmes ship one, every other plan is rendered instead.
        """
        image_id = STUDYCOURSE_TO_IMAGE_ID.get(self.user_major)
        if image_id is None:
            return None

        season = "WiSe" if self.winter else "SoSe"
        path = assets_dir() / "images" / f"{image_id}_SPO_{self.user_po.name[-4:]}_{season}.png"

        return path if path.is_file() else None

    def get_image_file(self) -> discord.File | None:
        """ The picture that belongs to this plan.

            A hand drawn image wins while there is nothing to mark. It is a flat png,
            so a tick cannot be drawn into it. As soon as the student has saved
            modules the plan is rendered instead, because a marked text next to an
            unmarked picture reads as two different plans.

            Returns:
                A `discord.File` named `studyplan.png`, or `None` when there is no plan.
        """
        path = self.get_image_path()
        if path is not None and self.progress is None:
            return discord.File(path, filename=IMAGE_FILENAME)

        if self.plan is None:
            return None

        covered = self.progress.covered if self.progress is not None else None
        return discord.File(
            render_semesterplan(self.plan, self.language, covered),
            filename=IMAGE_FILENAME,
        )

    def _semester_lines(self, semester_index: int) -> str:
        """ Renders one semester of the plan as a bullet list.

            Every module gets a mark once the student has saved something. The mark
            reports what is in their plan, never what they passed.
        """
        if self.plan is None:
            return ""

        marks: list[bool] = (
            self.progress.covered[semester_index] if self.progress is not None else []
        )

        lines: list[str] = []
        for position, module in enumerate(self.plan.semesters[semester_index]):
            prefix: str = ""
            if self.progress is not None:
                planned: bool = position < len(marks) and marks[position]
                prefix = f"{PLANNED_MARK if planned else OPEN_MARK} "
            lines.append(f"- {prefix}{module.title} ({module.credit_points} CP)")

        text = "\n".join(lines)
        if len(text) > MAX_FIELD_LENGTH:
            text = text[: MAX_FIELD_LENGTH - 1] + "…"
        return text

    def _semester_label(self, index: int) -> str:
        """ The heading of one semester field, with its credit points."""
        if self.plan is None:
            return ""

        total: int = sum(module.credit_points for module in self.plan.semesters[index])
        if self.progress is None:
            return t(self.language, "semester_plain", PLAN_PROGRESS_TEXTS).format(
                number=index + 1, total=total
            )

        planned, total = self.progress.semester_credits(index)
        return t(self.language, "semester_marked", PLAN_PROGRESS_TEXTS).format(
            number=index + 1, planned=planned, total=total
        )

    def _footer(self) -> str:
        """ The line under the plan: how to read the marks, or how to get them."""
        if self.progress is None:
            return t(self.language, "nothing_saved", PLAN_PROGRESS_TEXTS)

        planned, total = self.progress.credits
        summary: str = t(self.language, "summary", PLAN_PROGRESS_TEXTS).format(
            planned=planned, total=total
        )
        legend: str = t(self.language, "legend", PLAN_PROGRESS_TEXTS)
        no_grades: str = t(self.language, "no_grades", PLAN_PROGRESS_TEXTS)
        return f"{summary}\n{legend}\n{no_grades}"

    def create_embed(self) -> discord.Embed:
        """ Builds the embed for the standard study plan."""
        is_german = self.language == LanguageCode.DE

        title = "Regelstudienplan" if is_german else "Standard Study Plan"

        if self.plan is None:
            description = (
                f"Für **{self.major_name}** (PO {self.user_po.name[-4:]}) gibt es noch "
                "keinen hinterlegten Regelstudienplan."
                if is_german else
                f"There is no standard study plan for **{self.major_name}** "
                f"(PO {self.user_po.name[-4:]}) yet."
            )
            return discord.Embed(
                title=title, description=description, color=discord.Color.orange()
            )

        embed = discord.Embed(
            title=f"{title} – {self.plan.title}",
            description=(
                f"PO {self.plan.spo} · {len(self.plan.semesters)} "
                + ("Semester" if is_german else "semesters")
            ),
            color=discord.Color.blue(),
        )

        for index in range(len(self.plan.semesters)):
            embed.add_field(
                name=self._semester_label(index),
                value=self._semester_lines(index) or "—",
                inline=False,
            )

        # every plan has a picture now, either hand drawn or rendered
        embed.set_image(url=f"attachment://{IMAGE_FILENAME}")
        embed.set_footer(text=self._footer())

        return embed
