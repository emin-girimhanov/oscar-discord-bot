""" Interactive UI view for module suggestions and recommendations.

    Allows students to browse personalized module proposals, select focus clusters
    (e.g. AI, Systems Engineering, Games, Scientific Computing), view explanations,
    and save suggested modules directly to their semester plan.
"""

from typing import override
import discord
from discord.ui import ActionRow, Container, LayoutView, Select, Separator, TextDisplay
from loguru import logger

from oscar.ui.translated_view import TranslatedView
from util.database import get_database
from util.enums import LanguageCode
from util.suggestions import CATEGORY_NAMES, ModuleSuggestion, get_module_suggestions
from util.translations import MODULE_TEXTS, t


class SuggestView(TranslatedView):
    """View displaying module recommendations with category filtering and save actions."""

    def __init__(
        self,
        user_id: int,
        initial_category: str = "ALL",
        default_language: LanguageCode = LanguageCode.DE,
    ):
        self.user_id: int = user_id
        self.category_key: str = initial_category
        self.saved_feedback: str | None = None
        super().__init__(default_language=default_language)

    def _category_select(self) -> Select[LayoutView]:
        """Builds category dropdown."""
        options: list[discord.SelectOption] = []
        for key, labels in CATEGORY_NAMES.items():
            label = labels.get(self.language_code, key)
            options.append(
                discord.SelectOption(
                    label=label,
                    value=key,
                    default=(key == self.category_key),
                )
            )

        placeholder = (
            "Schwerpunkt / Kategorie wählen"
            if self.language_code == LanguageCode.DE
            else "Select focus / category"
        )
        select: Select[LayoutView] = Select(placeholder=placeholder, options=options)

        async def callback(interaction: discord.Interaction):
            self.category_key = select.values[0]
            self.saved_feedback = None
            await self._update(interaction)

        select.callback = callback
        return select

    def _save_select(self, suggestions: list[ModuleSuggestion]) -> Select[LayoutView]:
        """Builds dropdown to save a suggested module into semester plan."""
        options: list[discord.SelectOption] = []
        for sug in suggestions:
            title = sug.module.get_title(self.language_code)
            cp = sug.module.credit_points or "?"
            label = f"{title[:75]} ({cp} CP)"
            desc = f"ID: {sug.module.id_} • {sug.module.lecturer[:40]}"
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(sug.module.id_),
                    description=desc,
                )
            )

        placeholder = (
            "📥 Modul in Semesterplan speichern..."
            if self.language_code == LanguageCode.DE
            else "📥 Save module to semester plan..."
        )
        select: Select[LayoutView] = Select(placeholder=placeholder, options=options)

        async def callback(interaction: discord.Interaction):
            module_id = int(select.values[0])
            db = get_database()

            saved_mod = next((s.module for s in suggestions if s.module.id_ == module_id), None)
            name = (
                saved_mod.get_title(self.language_code)
                if saved_mod
                else str(module_id)
            )

            try:
                db.add_to_semesterplan(self.user_id, module_id, self.language_code)
            except (AssertionError, KeyError):
                # a select that raises shows "interaction failed" and nothing else
                logger.exception(f"Could not add module {module_id} to a plan")
                self.saved_feedback = t(
                    self.language_code, "plan_failed", MODULE_TEXTS
                ).format(title=name)
                await self._update(interaction)
                return

            if self.language_code == LanguageCode.DE:
                self.saved_feedback = f"✅ **'{name}'** wurde zu deinem Semesterplan hinzugefügt!"
            else:
                self.saved_feedback = f"✅ **'{name}'** has been added to your semester plan!"

            await self._update(interaction)

        select.callback = callback
        return select

    def _render_suggestion_card(
        self, sug: ModuleSuggestion, index: int
    ) -> TextDisplay:
        """Formats one module recommendation."""
        m = sug.module
        title = m.get_title(self.language_code)
        cp = m.credit_points or "-"
        sws = m.get_teaching_form_sws(self.language_code) or "-"
        lecturer = m.lecturer or "-"
        reason = sug.reason_de if self.language_code == LanguageCode.DE else sug.reason_en

        lines = [
            f"### {index}. {title} (`{m.id_}`)",
            f"💡 **Empfehlungsgrund:** *{reason}*",
            f"📊 **CP:** `{cp}` | **SWS / Form:** `{sws}` | **Dozent:** `{lecturer}`",
        ]
        return TextDisplay("\n".join(lines))

    @override
    def _build_content(self) -> None:
        """Constructs layout components."""
        suggestions = get_module_suggestions(
            user_id=self.user_id,
            category_key=self.category_key,
            limit=5,
        )

        header_title = (
            "## 🎓 Modul-Empfehlungen für dein Studium"
            if self.language_code == LanguageCode.DE
            else "## 🎓 Module Suggestions for Your Studies"
        )
        cat_name = CATEGORY_NAMES.get(self.category_key, {}).get(
            self.language_code, self.category_key
        )
        active_cat_line = (
            f"Aktueller Filter: **{cat_name}**"
            if self.language_code == LanguageCode.DE
            else f"Active filter: **{cat_name}**"
        )

        elements: list[LayoutView | ActionRow | TextDisplay | Separator] = [
            TextDisplay(f"{header_title}\n{active_cat_line}"),
        ]

        if self.saved_feedback:
            elements.append(TextDisplay(self.saved_feedback))

        elements.append(Separator())

        if not suggestions:
            empty_msg = (
                "🔍 *Keine weiteren Module gefunden, die deinen Kriterien entsprechen "
                "oder noch nicht geplant sind.*"
                if self.language_code == LanguageCode.DE
                else "🔍 *No further modules found matching your criteria or not yet planned.*"
            )
            elements.append(TextDisplay(empty_msg))
        else:
            for idx, sug in enumerate(suggestions, start=1):
                elements.append(self._render_suggestion_card(sug, idx))
                if idx < len(suggestions):
                    elements.append(Separator())

        self.add_item(Container(*elements))

        # Controls
        cat_row = ActionRow(self._category_select())
        self.add_item(cat_row)

        if suggestions:
            save_row = ActionRow(self._save_select(suggestions))
            self.add_item(save_row)

        toggle_row = ActionRow(self._create_language_toggle())
        self.add_item(toggle_row)
