""" Interactive view for displaying FIN & OVGU Learning Management Systems (LMS).

    Guides students through the four portals that exist (eLearning, LSF, the
    BookStack module handbook and the FIN GitLab), clarifying login types,
    usage scopes, and common pitfalls (Issue #51).
"""

from typing import override
import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Select, Separator, TextDisplay

from oscar.ui.translated_view import TranslatedView
from util.enums import LanguageCode
from util.lms import (
    DEFAULT_PLATFORM_KEY,
    FIN_PLATFORMS,
    LearningPlatform,
    get_platform_by_key,
)


class LmsView(TranslatedView):
    """ View that allows navigating FIN and university learning management platforms."""

    def __init__(
        self,
        default_language: LanguageCode = LanguageCode.DE,
        initial_platform_key: str = DEFAULT_PLATFORM_KEY,
    ):
        self.selected_platform_key: str = initial_platform_key
        super().__init__(default_language=default_language)

    def _create_platform_select(self, lang: LanguageCode) -> ActionRow[LayoutView]:
        """Creates the platform selection dropdown."""
        options: list[discord.SelectOption] = []
        for p in FIN_PLATFORMS:
            scope = p.scope_de if lang == LanguageCode.DE else p.scope_en
            options.append(
                discord.SelectOption(
                    label=f"{p.emoji} {p.name}"[:100],
                    value=p.key,
                    description=scope[:100],
                    default=p.key == self.selected_platform_key,
                )
            )

        placeholder = (
            "Plattform wählen..." if lang == LanguageCode.DE
            else "Select platform..."
        )
        select: Select[LayoutView] = Select(
            options=options,
            placeholder=placeholder,
        )

        async def on_select(interaction: discord.Interaction):
            self.selected_platform_key = select.values[0]
            await self._update(interaction)

        select.callback = on_select
        return ActionRow[LayoutView](select)

    @staticmethod
    def _render_platform_details(
        platform: LearningPlatform, lang: LanguageCode
    ) -> list[TextDisplay]:
        """Formats the selected platform specifications into Markdown cards."""
        scope = platform.scope_de if lang == LanguageCode.DE else platform.scope_en
        login = platform.login_type_de if lang == LanguageCode.DE else platform.login_type_en
        desc = platform.description_de if lang == LanguageCode.DE else platform.description_en
        tips = platform.tips_de if lang == LanguageCode.DE else platform.tips_en

        scope_label = "Einsatzbereich" if lang == LanguageCode.DE else "Scope"
        login_label = "Login / Zugang" if lang == LanguageCode.DE else "Login / Access"
        desc_label = "Beschreibung" if lang == LanguageCode.DE else "Description"

        return [
            TextDisplay(f"## {platform.emoji} {platform.name}\n🔗 **URL:** <{platform.url}>"),
            TextDisplay(f"🎯 **{scope_label}:** {scope}\n🔑 **{login_label}:** {login}"),
            TextDisplay(f"📝 **{desc_label}:**\n{desc}\n\n{tips}"),
        ]

    @override
    def _build_content(self) -> None:
        lang: LanguageCode = self.language_code
        platform: LearningPlatform | None = get_platform_by_key(self.selected_platform_key)
        if platform is None:
            platform = FIN_PLATFORMS[0]
            self.selected_platform_key = platform.key

        container = Container[LayoutView]()
        header = (
            "# 🖥️ Lernplattformen & E-Learning an der FIN & OVGU"
            if lang == LanguageCode.DE else
            "# 🖥️ Learning Platforms & E-Learning at FIN & OVGU"
        )
        _ = container.add_item(TextDisplay(header))
        _ = container.add_item(Separator())
        _ = container.add_item(self._create_platform_select(lang))
        _ = container.add_item(Separator())

        for item in self._render_platform_details(platform, lang):
            _ = container.add_item(item)
            _ = container.add_item(Separator())

        btn_label = (
            f"🌐 {platform.name} öffnen" if lang == LanguageCode.DE
            else f"🌐 Open {platform.name}"
        )
        portal_button = Button[LayoutView](
            label=btn_label,
            style=discord.ButtonStyle.link,
            url=platform.url,
        )

        _ = container.add_item(
            ActionRow[LayoutView](
                portal_button,
                self._create_language_toggle(),
            )
        )
        _ = self.add_item(container)
