""" This module holds the view for the semesterplan"""

from typing import override
from discord.ui import ActionRow, Container, LayoutView, Separator, TextDisplay
from loguru import logger
from oscar.ui.custom_view import CustomView
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
        else:
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
                _ = plan.add_item(text_section)
                _ = plan.add_item(button_section)
                _ = plan.add_item(Separator())

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
                _ = plan.add_item(TextDisplay(f"{emoji} {rsp_title}"))

        _ = plan.add_item(Separator())
        _ = self.add_item(plan)
