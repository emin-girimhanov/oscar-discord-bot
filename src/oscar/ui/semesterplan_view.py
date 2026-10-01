""" This module holds the view for the semesterplan

    **A plan with six modules used to crash this view.** Discord allows one view forty
    components. Every module cost five of them, a text, a row, two buttons and a
    separator, and every line of the standard study plan one more. Six modules are a
    normal semester of 30 CP, and the student who had planned exactly that got

        ValueError: maximum number of children exceeded (40)

    and "the application did not respond". `tests/test_component_budget.py` could not
    see it, because the size of this view depends on the database.

    So the view counts now. Up to `ROWS_MAX` modules keep their own two buttons. A
    longer plan is written as one list with two menus under it, which costs the same
    five components for seven modules as for twenty five. The standard study plan is
    one block of text in both cases.
"""

from typing import override
import discord
from discord.ui import ActionRow, Container, LayoutView, Select, Separator, TextDisplay
from loguru import logger
from oscar.ui.custom_view import CustomView
from oscar.ui.module_view import ModuleView
from oscar.ui.select_button import DeleteButton, ExportCalendarButton, InfoButton
from util.credit_calc import get_modules_for_semester
from util.database import get_database
from util.enums import LanguageCode, StudyCourse
from util.module import Module
from util.typed_dicts import PrefsDict


def get_usability_for_major(module: Module, major: StudyCourse) -> list[int]:
    """ Die Usability-Liste des Moduls für diesen Studiengang.

        Deckt alle elf Studiengänge ab. Vorher standen hier nur vier, alle anderen
        bekamen stillschweigend eine leere Liste und damit lauter fehlende Module.
    """
    return module.get_usability_ids(major)




# How many modules are drawn with their own "more info" and delete button. Each costs
# four components and everything around them eleven, so six modules end at 35 of 40.
ROWS_MAX: int = 6

# Discord caps a select menu at 25 options. A plan beyond that is 125 CP in one
# semester, the menus then hold the first 25 and the text says how many are left.
SELECT_MAX: int = 25


class RemoveSelect(Select[LayoutView]):
    """ The menu that removes one module from a long plan."""

    def __init__(self, view: CustomView, modules: list[Module], language: LanguageCode):
        super().__init__(
            placeholder="Modul entfernen …" if language == LanguageCode.DE
            else "Remove a module …",
            options=[
                discord.SelectOption(label=m.get_title(language)[:100], value=str(m.id_))
                for m in modules[:SELECT_MAX]
            ],
        )
        self.view_ref: CustomView = view

    @override
    async def callback(self, interaction: discord.Interaction):
        get_database().remove_from_semesterplan(
            user_id=self.view_ref.user_id, module_id=int(self.values[0])
        )
        self.view_ref.build_view()
        _ = await interaction.response.edit_message(view=self.view_ref)


class InfoSelect(Select[LayoutView]):
    """ The menu that opens the card of one module of a long plan."""

    def __init__(self, modules: list[Module], language: LanguageCode):
        super().__init__(
            placeholder="Mehr Infos zu …" if language == LanguageCode.DE
            else "More info about …",
            options=[
                discord.SelectOption(label=m.get_title(language)[:100], value=str(m.id_))
                for m in modules[:SELECT_MAX]
            ],
        )

    @override
    async def callback(self, interaction: discord.Interaction):
        # the card is opened from a private list, so it stays private too
        _ = await interaction.response.send_message(
            view=ModuleView(
                user_id=interaction.user.id,
                module=Module.from_id(int(self.values[0])),
            ),
            ephemeral=True,
        )


class SemesterplanView(CustomView):
    """Custom class to hold a semester plan (view)"""

    def __init__(self, user_id: int):
        super().__init__(user_id=user_id)

    @override
    def build_view(self):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        _ = self.clear_items()
        db = get_database()
        module_list: list[Module] = db.get_semesterplan(self.user_id)
        preferences: PrefsDict | None = db.get_preferences(self.user_id)

        semester = preferences.get("semester") if preferences else None
        major: StudyCourse | None = preferences.get("major") if preferences else None
        spo = preferences.get("spo") if preferences else None
        winter = preferences.get("winter_semester") if preferences else None

        logger.debug(
            f"Building semesterplan view: spo={spo!r}, winter={winter!r}, "
            f"major={major!r}, semester={semester!r}"
        )

        language: LanguageCode = LanguageCode.DE
        if preferences is not None:
            language = preferences["language"]

        plan: Container[LayoutView] = Container[LayoutView](
            TextDisplay("# Deine Semesterübersicht" if language == LanguageCode.DE
                        else "# Your Semester Overview"),
            Separator()
        )


        full_module_list: list[Module] = []
        for m in module_list:
            try:
                full_module_list.append(Module.from_id(m.id_))
            except IndexError:
                continue

        acquired_cp = 0
        for m in full_module_list:
            acquired_cp += int(m.credit_points) if m.credit_points.strip() else 0
        _ = plan.add_item(TextDisplay(
            "## Deine eingetragenen Module" if language == LanguageCode.DE
            else "## Your Enrolled Modules"
        ))

        if not full_module_list:
            _ = plan.add_item(TextDisplay(
                "Noch keine Module eingetragen." if language == LanguageCode.DE
                else "No modules added yet."
            ))
        elif len(full_module_list) <= ROWS_MAX:
            for m in full_module_list:
                cp_str = m.credit_points.strip() if m.credit_points.strip() else "?"
                text_section = TextDisplay(f"{m.get_title(language)} – {cp_str} CP")
                original = next((orig for orig in module_list if orig.id_ == m.id_), m)
                button_section: ActionRow[LayoutView] = ActionRow[LayoutView](
                    InfoButton(
                        label="mehr Infos" if language == LanguageCode.DE else "more info",
                        module=f"{m.get_title(language)}"
                    ),
                    DeleteButton(view=self, module=original)
                )
                # no separator in between, it is the fifth component of a module and
                # the one that pushed a plan of six over the limit
                _ = plan.add_item(text_section)
                _ = plan.add_item(button_section)
            _ = plan.add_item(Separator())
        else:
            self._add_long_plan(plan, full_module_list, language)

        cp_label = (f"**Gesamt CP: {acquired_cp}**" if language == LanguageCode.DE
                    else f"**Total CP: {acquired_cp}**")
        _ = plan.add_item(TextDisplay(cp_label))
        _ = plan.add_item(
            ActionRow[LayoutView](
                ExportCalendarButton(user_id=self.user_id, language=language)
            )
        )
        _ = plan.add_item(Separator())


        if major is None or spo is None or semester is None:
            missing = (
                " Bitte nutze zuerst /start und wähle Studiengang, Prüfungsordnung "
                "und Semester aus."
                if language == LanguageCode.DE else
                " Please run /start first and pick your programme, examination "
                "regulations and semester."
            )
            _ = plan.add_item(TextDisplay(missing))
            _ = self.add_item(plan)
            return

        # Every plan we ship is offered. The manager falls back to the closest SPO,
        # so a hardcoded list of supported programmes would only hide our own data.
        try:
            rsp_modules: list[dict] = get_modules_for_semester(
                spo=spo,
                major=major,
                winter=winter is not False,
                semester=semester,
                study_course=major,
            )
        except FileNotFoundError:
            warning = (
                " Für deine SPO, deinen Studiengang oder dein Startsemester "
                "existiert noch kein Regelstudienplan."
                if language == LanguageCode.DE else
                " No study progression plan available for your SPO, major, or start semester yet."
            )
            _ = plan.add_item(TextDisplay(warning))
            _ = self.add_item(plan)
            return
        _ = plan.add_item(TextDisplay(
            f"## Regelstudienplan – {semester}. Semester" if language == LanguageCode.DE
            else f"## Study Progression Plan – Semester {semester}"
        ))

        if not rsp_modules:
            _ = plan.add_item(TextDisplay(
                "Keine Module für dieses Semester gefunden." if language == LanguageCode.DE
                else "No modules found for this semester."
            ))
        else:
            # one block of text, a component per line is what the limit is spent on
            rsp_lines: list[str] = []
            for rsp_module in rsp_modules:
                rsp_id = rsp_module.get("identification")
                rsp_title = rsp_module.get("title", "?")

                if rsp_id is None:

                    rsp_usability: list[int] = rsp_module.get("usability", [])
                    covered = any(
                        any(uid in rsp_usability for uid in get_usability_for_major(full_m, major))
                        for full_m in full_module_list
                    )
                else:

                    covered = any(full_m.id_ == rsp_id for full_m in full_module_list)

                emoji = "✅" if covered else "❌"
                rsp_lines.append(f"{emoji} {rsp_title}")
            _ = plan.add_item(TextDisplay("\n".join(rsp_lines)))

        _ = plan.add_item(Separator())
        _ = self.add_item(plan)

    def _add_long_plan(
        self,
        plan: Container[LayoutView],
        modules: list[Module],
        language: LanguageCode,
    ) -> None:
        """ Draws a plan that has more modules than there is room for buttons.

            The modules become one numbered list, and two menus under it remove a
            module or open its card. That is five components however long the plan is.

            Parameters:
                plan: The container the plan is drawn into.
                modules: The modules of the plan, as the catalogue knows them.
                language: The language of the student.
        """
        lines: list[str] = []
        for number, m in enumerate(modules[:SELECT_MAX], start=1):
            cp_str = m.credit_points.strip() if m.credit_points.strip() else "?"
            lines.append(f"{number}. {m.get_title(language)} – {cp_str} CP")

        hidden = len(modules) - SELECT_MAX
        if hidden > 0:
            lines.append(
                f"… und {hidden} weitere. Entferne Module, um sie hier zu sehen."
                if language == LanguageCode.DE else
                f"… and {hidden} more. Remove modules to see them here."
            )

        _ = plan.add_item(TextDisplay("\n".join(lines)))
        _ = plan.add_item(ActionRow[LayoutView](InfoSelect(modules, language)))
        _ = plan.add_item(ActionRow[LayoutView](RemoveSelect(self, modules, language)))
        _ = plan.add_item(Separator())
