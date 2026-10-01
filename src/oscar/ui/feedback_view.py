import discord
from discord import ui
from discord.ui import ActionRow, Container, LayoutView, Select, Separator, TextDisplay, TextInput
from discord.ui.button import Button

from oscar.ui.owner_only import OwnerOnly
from util.database import get_database, get_user_language

from util.enums import LanguageCode
from util.translations import t, FEEDBACK_TEXTS


class ImproveModal(ui.Modal):
    def __init__(self,parent: "FeedbackView", language: LanguageCode, title: str, number: int):
        super().__init__(title=title)
        self.parent: FeedbackView = parent
        self.number: int = number
        label: str = ""
        if number == 1:
            label = t(language, "improve", FEEDBACK_TEXTS)
        elif number == 2:
            label = t(language, "wish", FEEDBACK_TEXTS)
        elif number == 3:
            label = t(language, "bug", FEEDBACK_TEXTS)
        self.answer: TextInput[LayoutView] = ui.TextInput(
            label=label,
            style=discord.TextStyle.long,
            required=False
        )

        _ = self.add_item(self.answer)


    async def on_submit(  # pylint: disable=arguments-differ
        self, interaction: discord.Interaction
    ):
        text = self.answer.value

        if self.number == 1:
            self.parent.improvements = text
        elif self.number == 2:
            self.parent.wishes = text
        elif self.number == 3:
            self.parent.bugs = text

        _ = await interaction.response.defer(ephemeral=True)



class FeedbackView(OwnerOnly, LayoutView):  # pylint: disable=too-many-instance-attributes
    """ Class for giving feedback"""

    def __init__(self,user_id:int, semester: int):
        super().__init__(timeout=300)
        self.semester: int = semester
        self.user_id: int = user_id
        self.language: LanguageCode = get_user_language(user_id)
        self._build_view()
        self.intuitiveness: int | None = None
        self.discoverability: int | None = None
        self.usefulness: int | None = None

        self.improvements: str = ""
        self.wishes: str = ""
        self.bugs: str = ""


    def _build_view(self):  # pylint: disable=too-many-locals

        #---- 3 selecter-------
        options = [
            discord.SelectOption(
                label=t(self.language,"choose_1",FEEDBACK_TEXTS),value="1"
            ),
            discord.SelectOption(
                label=t(self.language,"choose_2",FEEDBACK_TEXTS),value="2"
            ),
            discord.SelectOption(
                label=t(self.language,"choose_3",FEEDBACK_TEXTS),value="3"
            ),
            discord.SelectOption(
                label=t(self.language,"choose_4",FEEDBACK_TEXTS),value="4"
            )
        ]

        intuative: Select[LayoutView] = Select(
            options=options,
            placeholder="The operation is intuitive" if self.language==LanguageCode.EN else
                        "Die Bedienung ist intuitiv.",
        )

        modules: Select[LayoutView] = Select(
            options=options,
            placeholder="Modules are easy to find an plan." if self.language==LanguageCode.EN else
                        "Module lassen sich gut finden und planen.",
        )

        info: Select[LayoutView] = Select(
            options=options,
            placeholder="The information displayed is useful" if self.language==LanguageCode.EN else
                        "Die zu sehenden Informationen sind sinnvoll.",
        )

        async def intuitiveness_callback(interaction: discord.Interaction):
            self.intuitiveness = int(intuative.values[0])
            _ = await interaction.response.defer()

        intuative.callback = intuitiveness_callback

        async def discoverability_callback(interaction: discord.Interaction):
            self.discoverability = int(modules.values[0])
            _ = await interaction.response.defer()

        modules.callback = discoverability_callback


        async def usefulness_callback(interaction: discord.Interaction):
            self.usefulness = int(info.values[0])
            _ = await interaction.response.defer()

        info.callback = usefulness_callback



        #------ buttons for modals-----
        improve_button: Button[LayoutView] = discord.ui.Button(
            label="What can be improved?" if self.language==LanguageCode.EN else
                  "Was kann verbessert werden?",
            style=discord.ButtonStyle.secondary
        )
        wish_button: Button[LayoutView] = discord.ui.Button(
            label="What is something you wish for?" if self.language==LanguageCode.EN else
                  "Was wünscht ihr euch noch?",
            style=discord.ButtonStyle.secondary
        )
        bug_button: Button[LayoutView] = discord.ui.Button(
            label="Have you found any busg?" if self.language==LanguageCode.EN else
                  "Hast du bugs gefunden?",
            style=discord.ButtonStyle.secondary
        )

        async def improve_callback(interaction: discord.Interaction):
            modal = ImproveModal(
                parent=self,
                language=self.language,
                title="Improvement" if self.language==LanguageCode.EN else "Verbesserung",
                number=1
            )

            _ = await interaction.response.send_modal(modal)

        improve_button.callback = improve_callback

        async def wish_callback(interaction: discord.Interaction):
            modal = ImproveModal(
            parent=self,
            language=self.language,
            title="wishes" if self.language==LanguageCode.EN else "Wünsche",
            number=2
        )
            _ = await interaction.response.send_modal(modal)

        wish_button.callback = wish_callback

        async def bug_callback(interaction: discord.Interaction):
            modal = ImproveModal(
            parent=self,
            language=self.language,
            title="bug",
            number=3
        )
            _ = await interaction.response.send_modal(modal)

        bug_button.callback = bug_callback

        #-----send button-----
        send_button: Button[LayoutView] = discord.ui.Button(
            label="Send" if self.language==LanguageCode.EN else "Senden",
            style=discord.ButtonStyle.success
        )
        async def send_callback(interaction: discord.Interaction):
            db = get_database()
            db.send_feedback(
                user_id=self.user_id,
                intuitiveness=5-(self.intuitiveness or 4),      # reverse scale beacause of dropdown
                discoverability=5-(self.discoverability or 4),  # option ordering
                usefulness=5-(self.usefulness or 4),
                improvements=self.improvements,
                wishes=self.wishes,
                bugs=self.bugs
            )

            _ = await interaction.response.send_message(
                "Danke für dein Feedback!",
                ephemeral=True)


        send_button.callback = send_callback

        _ = self.clear_items()
        #-----window-----
        _ = self.add_item(
            Container(
                TextDisplay("# Feedback"),
                TextDisplay(t(self.language,"welcome_text",FEEDBACK_TEXTS)),
                Separator(),
                ActionRow[LayoutView](intuative),
                ActionRow[LayoutView](modules),
                ActionRow[LayoutView](info),
                Separator(),
                ActionRow[LayoutView](improve_button),
                ActionRow[LayoutView](wish_button),
                ActionRow[LayoutView](bug_button),
                Separator(),
                ActionRow[LayoutView](send_button)
            )
        )
