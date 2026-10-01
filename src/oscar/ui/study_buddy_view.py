""" This module provides the view and interactive components for study buddy matching.

    Allows students to opt in per module to form study groups and connect with others
    who plan the same module, completely opt-in, revocable, and privacy preserving.
"""

from typing import override
import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Select, Separator, TextDisplay
from loguru import logger

from oscar.ui.custom_view import CustomView
from util.database import get_database, get_user_language
from util.enums import LanguageCode
from util.module import Module


class JoinStudyBuddyButton(Button[LayoutView]):
    """ Button that opts the user in for study buddy matching on the selected module."""

    def __init__(self, view: "StudyBuddyView", module_id: int, language: LanguageCode):
        label = (
            "✅ Als Lernpartner:in eintragen"
            if language == LanguageCode.DE
            else "✅ Opt in as Study Buddy"
        )
        super().__init__(label=label, style=discord.ButtonStyle.success)
        self.view_ref: StudyBuddyView = view
        self.module_id: int = module_id
        self.language: LanguageCode = language

    @override
    async def callback(self, interaction: discord.Interaction):
        db = get_database()
        db.join_study_buddy(user_id=self.view_ref.user_id, module_id=self.module_id)
        self.view_ref.build_view()
        _ = await interaction.response.edit_message(view=self.view_ref)


class LeaveStudyBuddyButton(Button[LayoutView]):
    """ Button that opts the user out from study buddy matching on the selected module."""

    def __init__(self, view: "StudyBuddyView", module_id: int, language: LanguageCode):
        label = (
            "❌ Austragen"
            if language == LanguageCode.DE
            else "❌ Opt out"
        )
        super().__init__(label=label, style=discord.ButtonStyle.danger)
        self.view_ref: StudyBuddyView = view
        self.module_id: int = module_id
        self.language: LanguageCode = language

    @override
    async def callback(self, interaction: discord.Interaction):
        db = get_database()
        db.leave_study_buddy(user_id=self.view_ref.user_id, module_id=self.module_id)
        self.view_ref.build_view()
        _ = await interaction.response.edit_message(view=self.view_ref)


class CreateThreadButton(Button[LayoutView]):
    """ Button that creates a study group thread in the current channel."""

    def __init__(self, module: Module, buddies: list[int], language: LanguageCode):
        label = "🧵 Thread erstellen" if language == LanguageCode.DE else "🧵 Create Thread"
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.module: Module = module
        self.buddies: list[int] = buddies
        self.language: LanguageCode = language

    @override
    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not hasattr(channel, "create_thread"):
            msg = (
                "Threads können nur in Textkanälen eines Discord-Servers erstellt werden."
                if self.language == LanguageCode.DE else
                "Threads can only be created in server text channels."
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        title_short = (
            self.module.abbreviation
            or self.module.get_title(self.language)
        )[:30]
        thread_name = f"👥 Lerngruppe {title_short}"

        try:
            thread = await channel.create_thread(
                name=thread_name,
                auto_archive_duration=1440,
            )
            mentions = " ".join(f"<@{uid}>" for uid in self.buddies)
            welcome_msg = (
                f"👋 **Lerngruppe für {self.module.get_title(self.language)}**\n\n"
                f"Teilnehmende: {mentions}\n\n"
                f"Hier könnt ihr euch zu Übungen, Aufgaben und Prüfungsvorbereitung austauschen!"
                if self.language == LanguageCode.DE else
                f"👋 **Study Group for {self.module.get_title(self.language)}**\n\n"
                f"Participants: {mentions}\n\n"
                f"Use this thread to collaborate on assignments and exam preparation!"
            )
            # the bot pings nobody by default, here the ping is the point: it is what
            # brings the students who opted in into the thread
            await thread.send(
                welcome_msg,
                allowed_mentions=discord.AllowedMentions(users=True),
            )

            success_msg = (
                f"✅ Lerngruppen-Thread {thread.mention} wurde erfolgreich erstellt!"
                if self.language == LanguageCode.DE else
                f"✅ Study group thread {thread.mention} created successfully!"
            )
            await interaction.response.send_message(success_msg, ephemeral=True)
        except (discord.DiscordException, AttributeError) as err:
            logger.warning(f"Could not create study thread: {err}")
            fail_msg = (
                "Konnte keinen Thread erstellen (fehlende Bot-Berechtigung). "
                "Ihr könnt euch direkt per Discord-Direktnachricht (DM) austauschen!"
                if self.language == LanguageCode.DE else
                "Could not create a thread (missing bot permissions). "
                "Feel free to connect directly via Discord Direct Message (DM)!"
            )
            await interaction.response.send_message(fail_msg, ephemeral=True)


class StudyBuddyView(CustomView):
    """ View that displays study buddy information and opt-in status for modules."""

    def __init__(self, user_id: int, module_id: int | None = None):
        self.module_id: int | None = module_id
        super().__init__(user_id=user_id)

    @override
    # pylint: disable=too-many-locals,too-many-statements
    def build_view(self) -> None:
        _ = self.clear_items()
        db = get_database()
        language = get_user_language(self.user_id)

        # Retrieve enrolled modules from user's plan
        plan_modules = db.get_semesterplan(self.user_id)
        if self.module_id is None and plan_modules:
            self.module_id = plan_modules[0].id_

        module: Module | None = None
        if self.module_id is not None:
            try:
                module = Module.from_id(self.module_id)
            except IndexError:
                module = None

        container = Container[LayoutView]()
        header_text = (
            "# 👥 Study Buddies & Lerngruppen"
            if language == LanguageCode.DE
            else "# 👥 Study Buddies & Groups"
        )
        _ = container.add_item(TextDisplay(header_text))
        _ = container.add_item(Separator())

        if module is None:
            no_mod_text = (
                "Du hast noch kein Modul ausgewählt und dein Semesterplan ist leer.\n\n"
                "💡 **Tipp:** Nutze `/studybuddy module:<name>` um nach einem Modul zu suchen, "
                "oder füge Module mit `/module` zu deinem `/semesterplan` hinzu."
                if language == LanguageCode.DE else
                "No module selected and your semester plan is empty.\n\n"
                "💡 **Tip:** Use `/studybuddy module:<name>` to find a specific module, "
                "or add modules to your `/semesterplan` via `/module`."
            )
            _ = container.add_item(TextDisplay(no_mod_text))
            _ = self.add_item(container)
            return

        # Module Details & Statistics
        mod_title = module.get_title(language)
        cp_str = f" ({module.credit_points.strip()} CP)" if module.credit_points else ""
        _ = container.add_item(TextDisplay(f"### {mod_title}{cp_str}"))

        planner_count = db.get_module_planner_count(module.id_)
        buddy_count = db.get_study_buddy_count(module.id_)
        is_opted_in = db.is_study_buddy(self.user_id, module.id_)

        stats_text = (
            f"📊 **{planner_count}** Studierende haben dieses Modul im Semesterplan.\n"
            f"👥 **{buddy_count}** Studierende suchen aktiv nach einer Lerngruppe."
            if language == LanguageCode.DE else
            f"📊 **{planner_count}** students plan this module in their schedule.\n"
            f"👥 **{buddy_count}** students are actively looking for study buddies."
        )
        _ = container.add_item(TextDisplay(stats_text))
        _ = container.add_item(Separator())

        # Status & Action Section
        if is_opted_in:
            opt_status = (
                "✅ **Du bist als Lernpartner:in eingetragen!**\n"
                "Andere eingetragene Studierende können deinen Discord-Namen sehen. "
                "Du kannst dich jederzeit mit einem Klick wieder austragen."
                if language == LanguageCode.DE else
                "✅ **You are registered as a study buddy!**\n"
                "Other registered students can see your Discord handle. "
                "You can opt out at any time with one click."
            )
            _ = container.add_item(TextDisplay(opt_status))

            all_buddies = db.get_study_buddies(module.id_)
            other_buddies = [uid for uid in all_buddies if uid != self.user_id]

            action_row = ActionRow[LayoutView](
                LeaveStudyBuddyButton(view=self, module_id=module.id_, language=language)
            )

            if other_buddies:
                buddies_str = "\n".join(f"• <@{uid}>" for uid in other_buddies)
                list_title = (
                    f"**Andere Lernpartner:innen ({len(other_buddies)}):**\n{buddies_str}\n\n"
                    "*Tipp: Tauscht euch per DM aus oder erstellt einen Lerngruppen-Thread!*"
                    if language == LanguageCode.DE else
                    f"**Other Study Buddies ({len(other_buddies)}):**\n{buddies_str}\n\n"
                    "*Tip: Connect via DM or create a study thread below!*"
                )
                _ = container.add_item(TextDisplay(list_title))
                _ = action_row.add_item(
                    CreateThreadButton(module=module, buddies=all_buddies, language=language)
                )
            else:
                empty_buddies = (
                    "ℹ️ *Noch keine weiteren Studierenden für dieses Modul eingetragen. "
                    "Sobald jemand beitritt, siehst du sie hier!*"
                    if language == LanguageCode.DE else
                    "ℹ️ *No other students registered for this module yet. "
                    "As soon as someone joins, they will appear here!*"
                )
                _ = container.add_item(TextDisplay(empty_buddies))

            _ = container.add_item(action_row)

        else:
            opt_info = (
                "Möchtest du gemeinsam mit anderen lernen oder Übungsaufgaben bearbeiten?\n"
                "Trage dich ein, um andere eingetragene Studierende zu sehen und dich zu vernetzen."
                if language == LanguageCode.DE else
                "Want to study together or work on exercises with others?\n"
                "Opt in to view other registered students and connect with them."
            )
            _ = container.add_item(TextDisplay(opt_info))
            _ = container.add_item(
                ActionRow[LayoutView](
                    JoinStudyBuddyButton(view=self, module_id=module.id_, language=language)
                )
            )

        # Plan Module Switcher (Select Menu)
        if len(plan_modules) > 1:
            _ = container.add_item(Separator())
            select_options: list[discord.SelectOption] = []
            for m in plan_modules[:25]:
                try:
                    full_m = Module.from_id(m.id_)
                    title = full_m.get_title(language)
                except IndexError:
                    title = m.get_title(language)
                is_selected = m.id_ == module.id_
                select_options.append(
                    discord.SelectOption(
                        label=title[:100],
                        value=str(m.id_),
                        default=is_selected,
                    )
                )

            module_select: Select[LayoutView] = Select(
                options=select_options,
                placeholder=(
                    "Anderes Modul aus Semesterplan wählen"
                    if language == LanguageCode.DE else
                    "Select another module from semester plan"
                ),
            )

            async def on_module_select(interaction: discord.Interaction):
                self.module_id = int(module_select.values[0])
                self.build_view()
                _ = await interaction.response.edit_message(view=self)

            module_select.callback = on_module_select
            _ = container.add_item(ActionRow[LayoutView](module_select))

        _ = self.add_item(container)
