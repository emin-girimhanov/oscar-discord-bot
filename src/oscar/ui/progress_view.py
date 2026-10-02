""" Interactive UI view for personal study progress and achievement badges.

    Displays a student's personal study progress, credit point load, visual progress bar,
    and gamification badges (Issue #11 / #48). Supports language toggling.
"""

from typing import override
import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from oscar.ui.translated_view import TranslatedView
from util.badges import Badge, UserProgress, compute_user_progress
from util.command_surface import HIDDEN
from util.database import get_database
from util.enums import LanguageCode, StudyCourse
from util.translations import COHORT_TEXTS, t


class ProgressView(TranslatedView):
    """View displaying personal achievements, study workload, and cohort analytics."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        user_id: int,
        default_language: LanguageCode = LanguageCode.DE,
        initial_mode: str = "progress",
        target_major: StudyCourse | str | None = None,
        target_semester: int | None = None,
    ):
        self.user_id: int = user_id
        self.view_mode: str = initial_mode
        self.target_major: StudyCourse | str | None = target_major
        self.target_semester: int | None = target_semester
        super().__init__(default_language=default_language)

    @staticmethod
    def _render_badge_line(badge: Badge, lang: LanguageCode) -> str:
        """Formats a single badge line with status indicator."""
        name = badge.name_de if lang == LanguageCode.DE else badge.name_en
        desc = badge.desc_de if lang == LanguageCode.DE else badge.desc_en
        status = badge.status_text(lang)

        if badge.unlocked:
            return f"**{badge.emoji} {name}** — *{status}*\n> {desc}"
        return f"🔒 **{name}** ({status})\n> {desc}"

    @classmethod
    def _render_stats_section(cls, progress: UserProgress, lang: LanguageCode) -> TextDisplay:
        """Renders profile and credit points summary."""
        if progress.has_profile and progress.major:
            sem = (
                f"{progress.semester}. Semester"
                if lang == LanguageCode.DE else
                f"Semester {progress.semester}"
            )
            profile_line = f"🎓 **Studiengang:** {progress.major.name} ({sem})"
        else:
            profile_line = (
                "⚠️ *Noch kein Profil gespeichert. Nutze `/start` zum Einrichten.*"
                if lang == LanguageCode.DE else
                "⚠️ *No profile saved yet. Use `/start` to set up.*"
            )

        cp_label = "Geplante Leistung" if lang == LanguageCode.DE else "Planned workload"
        mod_label = "Module" if lang == LanguageCode.DE else "Modules"
        badg_label = "Erfolge" if lang == LanguageCode.DE else "Achievements"
        status_suffix = "freigeschaltet" if lang == LanguageCode.DE else "unlocked"

        stats_lines = [
            profile_line,
            f"📚 **{cp_label}:** {progress.planned_cp} / {progress.target_cp} CP "
            f"({progress.planned_modules_count} {mod_label})",
            f"📊 `{progress.progress_bar(12)}`",
        ]
        if "badges" not in HIDDEN:
            stats_lines.append(
                f"🎖️ **{badg_label}:** {progress.unlocked_badges_count} / "
                f"{progress.total_badges_count} {status_suffix}"
            )
        return TextDisplay("\n".join(stats_lines))

    def _render_badges_list(
        self, badges: list[Badge], title: str, empty_msg: str, lang: LanguageCode
    ) -> list[TextDisplay]:
        """Renders a section of badges."""
        items: list[TextDisplay] = [TextDisplay(title)]
        if badges:
            lines = [self._render_badge_line(b, lang) for b in badges]
            items.append(TextDisplay("\n\n".join(lines)))
        else:
            items.append(TextDisplay(empty_msg))
        return items

    # pylint: disable=too-many-locals
    def _render_cohort_content(
        self, progress: UserProgress, lang: LanguageCode, container: Container[LayoutView]
    ) -> None:
        """Renders the cohort statistics screen."""
        db = get_database()
        major = self.target_major if self.target_major is not None else progress.major
        semester = self.target_semester if self.target_semester is not None else progress.semester

        major_display = major.name if hasattr(major, "name") else (str(major) if major else "FIN")
        sem_str = str(semester) if semester else "?"

        stats = db.get_cohort_statistics(major=major, semester=semester)

        _ = container.add_item(TextDisplay(t(lang, "cohort_title", COHORT_TEXTS)))
        _ = container.add_item(Separator())
        _ = container.add_item(TextDisplay(t(lang, "cohort_desc", COHORT_TEXTS)))
        _ = container.add_item(Separator())

        if not stats["has_sufficient_data"]:
            notice = t(lang, "insufficient_data", COHORT_TEXTS).format(
                major=major_display,
                semester=sem_str,
                count=stats["cohort_size"],
                min_size=stats["min_cohort_size"],
            )
            _ = container.add_item(TextDisplay(notice))
        else:
            metrics_head = t(lang, "metrics_header", COHORT_TEXTS).format(
                count=stats["cohort_size"]
            )
            avg_mod_label = t(lang, "avg_modules", COHORT_TEXTS)
            avg_cp_label = t(lang, "avg_cp", COHORT_TEXTS)
            metrics_text = (
                f"{metrics_head}\n"
                f"• 📚 **{avg_mod_label}:** {stats['avg_modules_planned']} Module\n"
                f"• 🎯 **{avg_cp_label}:** {stats['avg_cp_planned']} CP"
            )
            _ = container.add_item(TextDisplay(metrics_text))
            _ = container.add_item(Separator())

            top_head = t(lang, "top_modules_header", COHORT_TEXTS)
            _ = container.add_item(TextDisplay(top_head))
            if stats["top_modules"]:
                mod_lines: list[str] = []
                for idx, tm in enumerate(stats["top_modules"], start=1):
                    title = tm["title"] if lang == LanguageCode.DE else tm["title_en"]
                    filled_blocks = min(10, tm["percentage"] // 10)
                    pct_bar = f"`[{'█' * filled_blocks}{'░' * (10 - filled_blocks)}]`"
                    mod_lines.append(
                        f"**{idx}. {title}**\n"
                        f"> {pct_bar} {tm['percentage']}% ({tm['count']} Studierende)"
                    )
                _ = container.add_item(TextDisplay("\n\n".join(mod_lines)))
            else:
                _ = container.add_item(TextDisplay(t(lang, "no_modules_planned", COHORT_TEXTS)))

        if stats["major_distribution"]:
            _ = container.add_item(Separator())
            fac_head = t(lang, "faculty_header", COHORT_TEXTS).format(
                total=stats["total_registered_students"]
            )
            dist_lines = [fac_head]
            for md in stats["major_distribution"][:6]:
                dist_lines.append(
                    f"• **{md['major']}:** {md['percentage']}% ({md['count']} Studierende)"
                )
            _ = container.add_item(TextDisplay("\n".join(dist_lines)))

    @override
    def _build_content(self) -> None:
        lang: LanguageCode = self.language_code
        progress: UserProgress = compute_user_progress(self.user_id)
        container = Container[LayoutView]()

        show_badges = "badges" not in HIDDEN
        show_cohort = "cohort" not in HIDDEN

        if self.view_mode == "cohort" and show_cohort:
            self._render_cohort_content(progress, lang, container)
        elif not show_badges:
            header = (
                "# Dein Studienfortschritt" if lang == LanguageCode.DE
                else "# Your Study Progress"
            )
            _ = container.add_item(TextDisplay(header))
            _ = container.add_item(Separator())
            _ = container.add_item(self._render_stats_section(progress, lang))
            _ = container.add_item(Separator())
        else:
            header = (
                "# 🏆 Deine Erfolge & Studienfortschritt"
                if lang == LanguageCode.DE else
                "# 🏆 Your Achievements & Study Progress"
            )
            _ = container.add_item(TextDisplay(header))
            _ = container.add_item(Separator())
            _ = container.add_item(self._render_stats_section(progress, lang))
            _ = container.add_item(Separator())

            unlocked = [b for b in progress.badges if b.unlocked]
            locked = [b for b in progress.badges if not b.unlocked]

            unlocked_title = (
                f"### ✨ Freigeschaltet ({len(unlocked)})"
                if lang == LanguageCode.DE else
                f"### ✨ Unlocked ({len(unlocked)})"
            )
            empty_unlocked = (
                "*Noch keine Badges freigeschaltet. Speicher dein erstes Modul "
                "oder richte dein Profil mit `/start` ein!*"
                if lang == LanguageCode.DE else
                "*No badges unlocked yet. Save your first module or "
                "set up your profile with `/start`!*"
            )
            for item in self._render_badges_list(unlocked, unlocked_title, empty_unlocked, lang):
                _ = container.add_item(item)

            _ = container.add_item(Separator())

            if locked:
                locked_title = (
                    f"### 🎯 Nächste Meilensteine ({len(locked)})"
                    if lang == LanguageCode.DE else
                    f"### 🎯 Next Milestones ({len(locked)})"
                )
                for item in self._render_badges_list(locked, locked_title, "", lang):
                    _ = container.add_item(item)
                _ = container.add_item(Separator())

        cohort_toggle_btn = Button[LayoutView](
            label=t(
                lang,
                "btn_cohort" if self.view_mode == "progress" else "btn_progress",
                COHORT_TEXTS,
            ),
            style=discord.ButtonStyle.primary,
        )

        async def cohort_toggle_callback(interaction: discord.Interaction):
            self.view_mode = "cohort" if self.view_mode == "progress" else "progress"
            await self._update(interaction)

        cohort_toggle_btn.callback = cohort_toggle_callback

        buttons: list[Button[LayoutView]] = [self._create_language_toggle()]
        if show_cohort:
            buttons.append(cohort_toggle_btn)
        _ = container.add_item(ActionRow[LayoutView](*buttons))
        _ = self.add_item(container)
