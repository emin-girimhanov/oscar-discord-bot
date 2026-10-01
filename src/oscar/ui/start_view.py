""" This module contains the class for the initial bot view"""


import discord
from discord.ui import ActionRow, Container, LayoutView, Select, Separator, TextDisplay
from discord.ui.button import Button

from oscar.ui.owner_only import OwnerOnly
from oscar.ui.select_button import SelectButton
from util.database import get_database, get_user_language
from util.enums import LanguageCode, StudyCourse,PO
from util.command_surface import CORE_ORDER
from util.translations import (
    COMMAND_TEXTS,
    LANGUAGES,
    PO_REGULATIONS,
    START_TEXTS,
    STUDY_COURSES,
    t,
)



class StartView(OwnerOnly, LayoutView):
    """ Class for the initial start view for the discord bot"""

    def __init__(self,user_id:int, semester: int):
        super().__init__(timeout=300)
        self.semester: int = semester
        self.user_id: int = user_id
        self.language: LanguageCode = get_user_language(user_id)
        self._build_view()

    def _command_overview(self) -> str:
        """ The commands a student can type, as one piece of text.

            This used to be one `TextDisplay` per command. Discord allows a view forty
            components in total, and the welcome screen already spends most of them on
            buttons and selects, so `/start` started raising
            `maximum number of children exceeded (40)` as soon as the bot passed
            eleven commands. It stayed broken for a while, because nothing on the
            screen says which component was one too many.

            One block is one component, whatever the list does next.

            The bot has around thirty commands. Nobody learns thirty names on their
            first day, so this names the eight of `CORE_ORDER` and points at `/help`
            for the rest.

            Returns:
                One line per command, plus one saying where the others are.
        """
        lines: list[str] = [
            f"`/{command}` {COMMAND_TEXTS[command][self.language]}"
            for command in CORE_ORDER
            if command in COMMAND_TEXTS
        ]
        lines.append(t(self.language, "more_commands", START_TEXTS))
        return "\n".join(lines)

    def _build_view(self):  # pylint: disable=too-many-locals,too-many-statements

        _ = self.clear_items()

        options: list[discord.SelectOption] = []
        for course in StudyCourse.values():
            options.append(
                discord.SelectOption(
                    label = STUDY_COURSES[StudyCourse(course)][self.language],
                    value = StudyCourse(course).name
                )
            )

        study_course: Select[LayoutView] = Select(
            options=options,
            placeholder="Make a selection" if self.language==LanguageCode.EN else
                        "Triff eine Auswahl",
        )

        async def callback(interaction: discord.Interaction):
            user_id= interaction.user.id
            major = study_course.values[0]
            db = get_database()
            db.set_preferences(user_id = user_id, major = major)
            if self.language == LanguageCode.DE:
                message = f"✅ Studiengang **{major}** wurde gespeichert."
            else:
                message = f"✅ Course of study **{major}** was saved."
            _ = await interaction.response.send_message(message,ephemeral=True)

        study_course.callback = callback
        # hier für die PO
        options_po: list[discord.SelectOption] = []
        for po in PO.values():
            options_po.append(
                discord.SelectOption(
                    label=PO_REGULATIONS[PO(po)][self.language],
                    value=PO(po).name
                )
            )

        po_select: Select[LayoutView] = Select(
            options=options_po,
            placeholder="Choose examination regulations" if self.language == LanguageCode.EN else
                        "Wähle Prüfungsordnung",
        )

        async def po_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            po = po_select.values[0]
            db = get_database()
            db.set_preferences(user_id=user_id, spo=po)
            if self.language == LanguageCode.DE:
                message = f"✅ Prüfungsordnung **{po}** wurde gespeichert."
            else:
                message = f"✅ Examination regulations **{po}** were saved."
            _ = await interaction.response.send_message(message, ephemeral=True)

        po_select.callback = po_callback

        yes_button: Button[LayoutView] = discord.ui.Button(
            label="Yes" if self.language==LanguageCode.EN else "Ja",
            style=discord.ButtonStyle.success
        )
        no_button: Button[LayoutView] = discord.ui.Button(
            label="No"if self.language==LanguageCode.EN else "Nein",
            style=discord.ButtonStyle.danger
        )
        en_button: Button[LayoutView] = discord.ui.Button(
            label = LANGUAGES[LanguageCode.EN][LanguageCode.EN],
            style=discord.ButtonStyle.secondary
        )
        de_button: Button[LayoutView] = discord.ui.Button(
            label = LANGUAGES[LanguageCode.DE][LanguageCode.DE],
            style=discord.ButtonStyle.secondary
        )

        async def yes_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            semester = self.semester
            if semester < 1:
                # no "Semester N" role found, saving -1 would break /semesterplan later
                if self.language == LanguageCode.DE:
                    message = "❌ Ich habe keine Semester-Rolle bei dir gefunden. " \
                              "Hol dir bitte zuerst eine."
                else:
                    message = "❌ I couldn't find a semester role on your profile. " \
                              "Please pick one first."
                _ = await interaction.response.send_message(message, ephemeral=True)
                return
            db = get_database()
            db.set_preferences(user_id=user_id,semester=semester)
            if self.language == LanguageCode.DE:
                message = f"✅ Semester **{self.semester}** wurde gespeichert."
            else:
                message = f"✅ Semester **{self.semester}** was saved."
            _ = await interaction.response.send_message(message,ephemeral=True)


        async def no_callback(interaction: discord.Interaction):
            _ = self.clear_items()
            _ = self.add_item(
            Container(
                TextDisplay(t(
                    self.language,
                    "welcome_title",
                    START_TEXTS
                )),
                TextDisplay("\u200b"),
                TextDisplay(t(
                    self.language,
                    "welcome_text",
                    START_TEXTS
                )),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "before_info",
                    START_TEXTS
                )),
                TextDisplay("\u200b"),
                TextDisplay(t(
                    self.language,
                    "language_question",
                    START_TEXTS
                )),
                ActionRow[LayoutView](en_button, de_button),
                TextDisplay("\u200b"),
                TextDisplay("**What Semester are you currently in ?**" \
                     if self.language==LanguageCode.EN else "In welchem Semester bist du gerade?"),
                ActionRow(
                    SelectButton("1",group="Semester"),
                    SelectButton("2",group="Semester"),
                    SelectButton("3",group="Semester"),
                    SelectButton("4",group="Semester")
                ),
                ActionRow(
                    SelectButton("5",group="Semester"),
                    SelectButton("6",group="Semester"),
                    SelectButton("7",group="Semester"),
                    SelectButton("8+",group="Semester")
                ),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "subject",
                    START_TEXTS
                )),
                ActionRow[LayoutView](study_course),
                ActionRow[LayoutView](po_select),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "commands_info",
                    START_TEXTS
                )),
                TextDisplay(self._command_overview()),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "thank_you",
                    START_TEXTS
                )),
                TextDisplay("\u200b"),
                accent_color=0x4378d5)
            )
            _ = await interaction.response.edit_message(view =self)

        async def en_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            db = get_database()
            db.set_preferences(user_id=user_id, language=LanguageCode.EN)
            self.language = LanguageCode.EN
            self._build_view()
            _ = await interaction.response.edit_message(view=self)

        async def de_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            db = get_database()
            db.set_preferences(user_id=user_id, language=LanguageCode.DE)
            self.language = LanguageCode.DE
            self._build_view()
            _ = await interaction.response.edit_message(view=self)

        yes_button.callback = yes_callback
        no_button.callback = no_callback
        en_button.callback = en_callback
        de_button.callback = de_callback

        # Fester Anfang
        #self.add_item(

        _ = self.clear_items()

        _ = self.add_item(
            Container[LayoutView](
                TextDisplay(t(
                    self.language,
                    "welcome_title",
                    START_TEXTS
                )),
                TextDisplay("\u200b"),
                TextDisplay(t(
                    self.language,
                    "welcome_text",
                    START_TEXTS
                )),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "before_info",
                    START_TEXTS
                )),
                TextDisplay("\u200b"),
                TextDisplay(t(
                    self.language,
                    "language_question",
                    START_TEXTS
                )),
                ActionRow[LayoutView](en_button, de_button),
                TextDisplay("\u200b"),
                TextDisplay(t(
                    self.language,
                    "semester_question",
                    START_TEXTS
                ).format(semester=self.semester)),
                ActionRow[LayoutView](yes_button, no_button),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "subject",
                    START_TEXTS
                )),
                ActionRow[LayoutView](study_course),
                ActionRow[LayoutView](po_select),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "commands_info",
                    START_TEXTS
                )),
                TextDisplay(self._command_overview()),
                Separator(),
                TextDisplay(t(
                    self.language,
                    "thank_you",
                    START_TEXTS
                )),
                TextDisplay("\u200b"),
                accent_color=0x4378d5

            )
        )
