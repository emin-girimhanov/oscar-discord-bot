""" This module contains various custom buttons"""


import io
from typing import override
import discord
from discord.ui import Button, LayoutView

from oscar.ui.custom_view import CustomView
from oscar.ui.module_view import ModuleView
from util.calendar_export import generate_semester_calendar
from util.database import get_database, get_user_language
from util.enums import LanguageCode
from util.module import Module

class SelectButton(Button[LayoutView]):
    """ Class for a select button"""

    def __init__(self, label: str, group:str ="default"):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.selected: bool = False
        self.group: str = group


    @override
    async def callback(self, interaction: discord.Interaction):


        def iter_buttons(components):
            for child in components:
                if isinstance(child, SelectButton):
                    yield child
                elif hasattr(child, "children"):
                    yield from iter_buttons(child.children)

        for button in iter_buttons(self.view.children):
            if button.group == self.group:
                button.selected = False
                button.style = discord.ButtonStyle.secondary

        self.selected = True
        self.style = discord.ButtonStyle.success

        semester_int = None
        message = None

        if self.group == "Semester":
            semester_value = self.label or ""
            if semester_value.endswith("+"):
                semester_value = semester_value[:-1]

            try:
                semester_int = int(semester_value)
            except ValueError:
                pass

            if semester_int is not None:
                db = get_database()
                db.set_preferences(
                    user_id=interaction.user.id,
                    semester=semester_int
                )

                language = get_user_language(interaction.user.id)

                if language == LanguageCode.EN:
                    message = f"✅ Semester **{semester_int}** was saved."
                else:
                    message = f"✅ Semester **{semester_int}** wurde gespeichert."

        await interaction.response.edit_message(view=self.view)

        if message:
            await interaction.followup.send(
                message,
                ephemeral=True
            )



class FilterButton(discord.ui.Button[LayoutView]):
    """ Class for a filter button.

        The label is what the student reads and therefore changes with the language.
        The value is what the search reads and stays the same in every language. It
        falls back to the label, so an older button without a value still works.
    """
    def __init__(self, label: str, group:str ="default", value: str | None = None):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.selected: bool = False
        self.group:str = group
        self.value: str = label if value is None else value



    @override
    async def callback(self, interaction: discord.Interaction):
        self.selected = not self.selected
        if self.selected:
            self.style = discord.ButtonStyle.success
        else:
            self.style = discord.ButtonStyle.secondary
        _ = await interaction.response.edit_message(view=self.view)

class InfoButton(discord.ui.Button[LayoutView]):
    """ Class for an info button"""

    def __init__(self,label:str,module:str):
        super().__init__(label=label,style=discord.ButtonStyle.secondary)
        self.module_name = module

    @override
    async def callback(self, interaction: discord.Interaction):
        module = Module.from_name(name=self.module_name)
        user_id = interaction.user.id
        # the card is opened from a private list, so it stays private too
        _ = await interaction.response.send_message(
            view=ModuleView(
                user_id= user_id,
                module=module,
            ),
            ephemeral=True,
        )

class InfoButton2(discord.ui.Button):
    """ Class for an info button"""

    def __init__(self,label:str,module:str):
        super().__init__(label=label,style=discord.ButtonStyle.secondary)
        self.module_name = module

    @override
    async def callback(self, interaction: discord.Interaction):
        module = Module.from_name(name=self.module_name)
        await interaction.response.send_message(view=ModuleView(module=module), ephemeral=True)


class DeleteButton(discord.ui.Button[LayoutView]):
    """ Class for a delete button"""

    def __init__(self, view: CustomView, module):
        super().__init__(label="X", style=discord.ButtonStyle.danger)
        self.view_ref = view  # Referenz auf das View
        self.module = module  # Das zugehörige Modulobjekt

    @override
    async def callback(self, interaction: discord.Interaction):

        db = get_database()
        db.remove_from_semesterplan(user_id=self.view_ref.user_id, module_id=self.module.id_)


        self.view_ref.build_view()  # ruft deine eigene Logik auf, die alle Module aus DB neu lädt


        _ = await interaction.response.edit_message(view=self.view_ref)


class ExportCalendarButton(discord.ui.Button[LayoutView]):
    """ Button that generates and exports the user's semester plan as an .ics file."""

    def __init__(self, user_id: int, language: LanguageCode = LanguageCode.DE):
        label = (
            "📅 Kalender (.ics, ohne Zeiten)"
            if language == LanguageCode.DE
            else "📅 Calendar (.ics, no times)"
        )
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.user_id: int = user_id
        self.language: LanguageCode = language

    @override
    async def callback(self, interaction: discord.Interaction):
        db = get_database()
        stored_modules = db.get_semesterplan(self.user_id)
        if not stored_modules:
            msg = (
                "Dein Semesterplan enthält noch keine Module zum Exportieren."
                if self.language == LanguageCode.DE
                else "Your semester plan does not contain any modules to export yet."
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        full_modules: list[Module] = []
        for m in stored_modules:
            try:
                full_modules.append(Module.from_id(m.id_))
            except IndexError:
                continue

        prefs = db.get_preferences(self.user_id)
        ics_text = generate_semester_calendar(
            modules=full_modules,
            preferences=prefs,
            language=self.language,
        )

        file = discord.File(
            fp=io.BytesIO(ics_text.encode("utf-8")),
            filename="semesterplan.ics",
        )

        message = (
            "📅 **Hier ist dein Semesterplan als iCalendar-Datei (`.ics`).**\n\n"
            "Du kannst die Datei direkt in Google Calendar, Apple Kalender, Outlook "
            "oder dein Smartphone importieren.\n\n"
            "ℹ️ *Hinweis: Da die Moduldatenbank keine genauen Vorlesungszeiten und Räume enthält, "
            "sind deine Module als ganztägige Semestereinträge mit BookStack-Links und "
            "wichtigen FIN-Prüfungsfristen angelegt.*"
            if self.language == LanguageCode.DE else
            "📅 **Here is your semester plan as an iCalendar file (`.ics`).**\n\n"
            "You can import this file directly into Google Calendar, Apple Calendar, "
            "Outlook, or your smartphone.\n\n"
            "ℹ️ *Note: Because the module database does not contain exact lecture times and rooms, "
            "modules are exported as all-day entries with BookStack links and "
            "essential FIN examination deadlines.*"
        )

        await interaction.response.send_message(message, file=file, ephemeral=True)
