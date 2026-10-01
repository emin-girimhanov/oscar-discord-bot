""" This module contains the AllInfoView class for displaying detailed module
    information in a Discord UI.
"""


from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay
from loguru import logger

from util.database import  get_user_language
from util.module import Module
from util.enums import LanguageCode
from util.translations import INFO_TEXTS, module_language_name




class AllInfoView(LayoutView):
    """ Class representing a detailed view of module information in a Discord UI."""

    def __init__(self,
        user_id:int,
        module: Module
        ):
        super().__init__()
        self.module: Module = module
        self.user_id: int = user_id
        self.language: LanguageCode = get_user_language(user_id)
        logger.debug(f"Language: '{self.language.name}'")
        self.build_view()


    def build_view(self):
        """ Builds the detailed module information view."""
        _ = self.clear_items()

        _ = self.add_item(
            Container[LayoutView](
                TextDisplay(f"# {self.module.get_title(self.language)}"),
                Separator(),
                TextDisplay(
                    f"_{INFO_TEXTS['module_number'][self.language]}: {self.module.id_}_"
                ),
                Separator(),
                TextDisplay(f"**{INFO_TEXTS['responsibility'][self.language]}**"),
                TextDisplay(f"{self.module.responsibility}"),
                Separator(),
                TextDisplay(f"**{INFO_TEXTS['lecturer'][self.language]}**"),
                TextDisplay(f"{self.module.lecturer}"),
                ActionRow[LayoutView](
                    Button(
                        label=f"{INFO_TEXTS['abbreviation'][self.language]}:  {
                            self.module.abbreviation}"
                    ),
                    Button(label=f"CP: {self.module.credit_points}"),
                    Button(label=f"Semester: {self.module.get_semester_position()}"),
                    Button(
                        label=f"{INFO_TEXTS['semester'][self.language]}: {
                            self.module.get_academic_semester()}"
                    ),
                ),
                ActionRow[LayoutView](
                    Button(
                        label=f"{INFO_TEXTS['duration'][self.language]}: {
                            self.module.get_duration()}"
                    ),
                    Button(
                        label=f"{INFO_TEXTS['language'][self.language]}:  {
                            module_language_name(self.module.language, self.language)}"
                    ),
                    Button(label=f"{INFO_TEXTS['level'][self.language]}: {
                        ', '.join(self.module.get_level())}"
                    ),
                ),
                Separator(),
                TextDisplay(f"**{INFO_TEXTS['ilo'][self.language]}**"),
                TextDisplay(f"{self.module.get_learning_goals(self.language)}"),
                Separator(),
                TextDisplay(f"**{INFO_TEXTS['content'][self.language]}**"),
                TextDisplay(f"{self.module.get_content(self.language)}"),
                Separator(),
                TextDisplay(f"**{INFO_TEXTS['effort'][self.language]}**"),
                TextDisplay(f"{self.module.get_workload(self.language)}"),
                Separator()
            )
        )
