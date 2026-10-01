""" This module contains various classes for the handling of structured data"""

from collections.abc import Mapping
from typing import Any, Self, override
from loguru import logger


from util.tables import get_rows, get_value_by_id
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.typed_dicts import ModuleDict, TablesModuleDict



def without_nulls(data: Mapping[str, Any]) -> dict[str, Any]:
    """ Drops the columns the Tables API sent as null.

        `dict.get(key, default)` only falls back when the **key** is missing. The
        Tables API sends the key with a null value instead, so `Fachsemester` arrived
        as `None` for 15 of the 410 rows and every field of `Module` typed `int` could
        hold `None`. `/suggest` then raised

            TypeError: '>' not supported between instances of 'NoneType' and 'int'

        on the first of those modules it scored. Dropping the nulls first makes every
        `data.get(key, default)` below behave the way its default promises.

        Parameters:
            data: One row as the Tables API or a saved json returns it.

        Returns:
            The same row without the keys whose value is `None`.
    """
    return {key: value for key, value in data.items() if value is not None}


# pylint: disable=R0902 # (too-many-instance-attributes)
# pylint: disable=R0904 # (too-many-public-methods)
class Module():
    """Class for storing modules in a structured way."""

    # pylint: disable=R0913 # (too-many-arguments)
    # pylint: disable=R0917 # (too-many-positional-arguments)
    # pylint: disable=R0914 # (too-many-locals)
    def __init__(
		self,
        id_: int,                  # Identifizierung
        language: ModuleLanguage,  # Modulsprache

        status: int = -1,                                     # Status
        title: str = "",                                      # Modultitel
        title_en: str = "",                                   # Modultitel (englisch)
        chair: int = -1,                                      # Lehrstuhl
        responsibility: str = "",                             # Modulverantwortung
        lecturer: str = "",                                   # Dozent:in
        abbreviation: str = "",                               # Modulkürzel
        credit_points: str = "",                              # Credit Points
        semester_position: int = -1,                          # Semesterlage
        academic_semester: int = -1,                          # Fachsemester
        duration: int = -1,                                   # Dauer
        level: list[int] | None = None,                       # Niveau
        learning_goals: str = "",                             # Angestrebte Lernergebnisse
        content: str = "",                                    # Inhalt
        workload: str = "",                                   # Arbeitsaufwand
        study_exam_type: str = "",                            # Studien-/Prüfungsleistung
        teaching_form_sws: str = "",                          # Lehrform / SWS
        requirements_by_exam_regulations: str = "",           # Voraussetzungen nach Prüfungsordnung
        recommended_prerequisites: str = "",                  # Empfohlene Voraussetzungen
        media_forms: str = "",                                # Medienformen
        literature: str = "",                                 # Literatur
        notes: str = "",                                      # Hinweise
        first_examiner: str = "",                             # Erstprüfer
        second_examiner: str = "",                            # Zweitprüfer
        substitute: str = "",                                 # Stellvertreter
        usability_bsc_inf: list[int] | None = None,           # Verwendbarkeit B.Sc. INF
        usability_bsc_cv: list[int] | None = None,            # Verwendbarkeit B.Sc. CV
        usability_bsc_inginf: list[int] | None = None,        # Verwendbarkeit B.Sc. INGINF
        usability_bsc_wif: list[int] | None = None,           # Verwendbarkeit B.Sc. WIF
        usability_bsc_inf_bilingual: list[int] | None = None, # Verwendbarkeit B.Sc. INF (bilingual
        usability_msc_inf: list[int] | None = None,           # Verwendbarkeit M.Sc. INF
        usability_msc_inginf: list[int] | None = None,        # Verwendbarkeit M.Sc. INGINF
        usability_msc_wif: list[int] | None = None,           # Verwendbarkeit M.Sc. WIF
        usability_msc_dke: list[int] | None = None,           # Verwendbarkeit M.Sc. DKE
        usability_msc_de: list[int] | None = None,            # Verwendbarkeit M.Sc. DE
        usability_msc_vc: list[int] | None = None,            # Verwendbarkeit M.Sc. VC
        subtitle: str = "",                                   # Moduluntertitel
        exported_to: list[int] | None = None,                 # Exportiert nach
        imported_from: str = "",                              # Importiert von
        released_on: str = "",                                # Freigabe am
        courses: str = "",                                    # Lehrveranstaltungen
        irregular: str = "",                                  # Unregelmäßig
        exam_prerequisite: str = "",                          # Prüfungsvorleistung
        translation: 'Module | None' = None
		) -> None:

        self.id_: int = id_
        self.language: ModuleLanguage = language

        self._status: int = status
        self._title: str = title
        self._title_en: str = title_en
        self._chair: int = chair
        self.responsibility: str = responsibility
        self.lecturer: str = lecturer
        self.abbreviation: str = abbreviation
        self.credit_points: str = credit_points
        self._semester_position: int = semester_position
        self._academic_semester: int = academic_semester
        self._duration: int = duration
        self._level: list[int] = [] if level is None else level
        self._learning_goals: str = learning_goals
        self._content: str = content
        self._workload: str = workload
        self._study_exam_type: str = study_exam_type
        self._teaching_form_sws: str = teaching_form_sws
        self._requirements_by_exam_regulations: str = requirements_by_exam_regulations
        self._recommended_prerequisites: str = recommended_prerequisites
        self._media_forms: str = media_forms
        self._literature: str = literature
        self._notes: str = notes
        self.first_examiner: str = first_examiner
        self.second_examiner: str = second_examiner
        self.substitute: str = substitute
        self._usability_bsc_inf: list[int] = [] if usability_bsc_inf is None else usability_bsc_inf
        self._usability_bsc_cv: list[int] = [] if usability_bsc_cv is None else usability_bsc_cv
        self._usability_bsc_inginf: list[int] = [] if usability_bsc_inginf is None \
            else usability_bsc_inginf
        self._usability_bsc_wif: list[int] = [] if usability_bsc_wif is None else usability_bsc_wif
        self._usability_bsc_inf_bilingual: list[int] = [] if usability_bsc_inf_bilingual is None \
            else usability_bsc_inf_bilingual
        self._usability_msc_inf: list[int] = [] if usability_msc_inf is None else usability_msc_inf
        self._usability_msc_inginf: list[int] = [] if usability_msc_inginf is None \
            else usability_msc_inginf
        self._usability_msc_wif: list[int] = [] if usability_msc_wif is None else usability_msc_wif
        self._usability_msc_dke: list[int] = [] if usability_msc_dke is None else usability_msc_dke
        self._usability_msc_de: list[int] = [] if usability_msc_de is None else usability_msc_de
        self._usability_msc_vc: list[int] = [] if usability_msc_vc is None else usability_msc_vc
        self._subtitle: str = subtitle
        self._exported_to: list[int] = [] if exported_to is None else exported_to
        self._imported_from: str = imported_from
        self.released_on: str = released_on
        self._courses: str = courses
        self._irregular: str = irregular
        self._exam_prerequisite: str = exam_prerequisite
        self.translation: Module | None = translation

    @override
    def __str__(self)-> str:
        trans_str: str ="\n+ translation"
        return f"""Module( id_ = {self.id_},
        language = '{self.language if isinstance(self.language, str) else self.language.name}',
        title = '{self._title}'{trans_str if self.translation else ''})"""


    @classmethod
    def from_id(cls, id_: int) -> Self:
        """ Creates a Module instance by searching for a module with the given id.

            Parameters:
                id: The module id to search for

            Returns:
                The matching Module instance

            Raises:
                IndexError: If no module with the given name is found
        """
        modules: list[TablesModuleDict] = get_rows(720)

        modules_filtered: list[TablesModuleDict] = [
            module for module in modules
            if module.get("Identifizierung", -1) == id_
        ]

        if not modules_filtered:
            raise IndexError(f"No module found with id: '{id_}'")

        base_module: TablesModuleDict | None = next(
            (m for m in modules_filtered if m.get("Translation", "").lower() != "true"),
            None
        )
        translated_module: TablesModuleDict | None = next(
            (m for m in modules_filtered if m.get("Translation", "").lower() == "true"),
            None
        )
        if base_module is None:
            if translated_module is not None:
                return cls.from_tables_dict(translated_module)
        else:
            if translated_module is None:
                return cls.from_tables_dict(base_module)
            return cls.from_tables_dict(base_module, translated_module)

        return cls.from_tables_dict(modules_filtered[0])


    @classmethod
    def from_name(cls, name: str, name_is_en:bool = False) -> Self:
        """Creates a Module instance by searching for a module with the given name.

            Parameters:
                name: The module title to search for
                name_is_en: If True, search in English titles, otherwise in German titles

            Returns:
                The first matching Module instance

            Raises:
                IndexError: If no module with the given name is found
        """
        modules: list[TablesModuleDict] = get_rows(720)
        search_field: str = "Modultitel (englisch)" if name_is_en else "Modultitel"

        filtered_module_ids: list[int] = [
            module["Identifizierung"] for module in modules
            if module.get(search_field, "") == name
        ]
        # dict.fromkeys drops duplicates but keeps the table order, so a title
        # shared by several modules always resolves to the same one
        filtered_module_ids = list(dict.fromkeys(filtered_module_ids))

        if not filtered_module_ids:
            raise IndexError(f"No module found with '{search_field}': '{name}'")
        if len(filtered_module_ids) > 1:
            # pylint: disable=C0301 (line-too-long)
            logger.warning(f"multiple modules modules found for with '{search_field}': '{name}' (selecting the module with id={filtered_module_ids[0]})")

        return cls.from_id(filtered_module_ids[0])


    @classmethod
    def from_tables_dict(
        cls,
        data: TablesModuleDict,
        trans_data: TablesModuleDict|None = None
    ) -> Self:
        """ Creates a Module instance from a dictionary as provided by the tables (nextcloud) api.

            Parameters:
                data: A dictionary with the module data.
                trans_data: An optional dictionary with the (translated) module data.

            for structure see <TablesModuleDict>

        """

        data = without_nulls(data)  # pyright: ignore[reportAssignmentType]
        if trans_data is not None:
            trans_data = without_nulls(trans_data)  # pyright: ignore[reportAssignmentType]

        id_: int | None = data.get("Identifizierung", None)
        module_language: int | None = data.get("Modulsprache", None)
        trans: Module | None = None

        assert id_ is not None, "An identification number is required."

        language: ModuleLanguage
        if module_language in ModuleLanguage.values():
            language = ModuleLanguage(module_language)
            if trans_data:
                trans = Module.from_tables_dict(trans_data)
        else:
            logger.warning(
                f"unknown language id: {module_language}, assuming english ({ModuleLanguage.EN})"
            )
            language = ModuleLanguage.EN

        return cls(
            id_      = id_,
            language = language,

            status                           = data.get("Status", -1),
            title                            = data.get("Modultitel", ""),
            title_en                         = data.get("Modultitel (englisch)", ""),
            chair                            = data.get("Lehrstuhl", -1),
            responsibility                   = data.get("Modulverantwortung", ""),
            lecturer                         = data.get("Dozent:in", ""),
            abbreviation                     = data.get("Modulkürzel", ""),
            credit_points                    = data.get("Credit Points", ""),
            semester_position                = data.get("Semesterlage", -1),
            academic_semester                = data.get("Fachsemester", -1),
            duration                         = data.get("Dauer", -1),
            level                            = data.get("Niveau", []),
            learning_goals                   = data.get("Angestrebte Lernergebnisse", ""),
            content                          = data.get("Inhalt", ""),
            workload                         = data.get("Arbeitsaufwand", ""),
            study_exam_type                  = data.get("Studien-/Prüfungsleistung", ""),
            teaching_form_sws                = data.get("Lehrform / SWS", ""),
            requirements_by_exam_regulations = data.get("Voraussetzungen nach Prüfungsordnung", ""),
            recommended_prerequisites        = data.get("Empfohlene Voraussetzungen", ""),
            media_forms                      = data.get("Medienformen", ""),
            literature                       = data.get("Literatur", ""),
            notes                            = data.get("Hinweise", ""),
            first_examiner                   = data.get("Erstprüfer", ""),
            second_examiner                  = data.get("Zweitprüfer", ""),
            substitute                       = data.get("Stellvertreter", ""),
            usability_bsc_inf                = data.get("Verwendbarkeit B.Sc. INF", []),
            usability_bsc_cv                 = data.get("Verwendbarkeit B.Sc. CV", []),
            usability_bsc_inginf             = data.get("Verwendbarkeit B.Sc. INGINF", []),
            usability_bsc_wif                = data.get("Verwendbarkeit B.Sc. WIF", []),
            usability_bsc_inf_bilingual      = data.get("Verwendbarkeit B.Sc. INF (bilingual)", []),
            usability_msc_inf                = data.get("Verwendbarkeit M.Sc. INF", []),
            usability_msc_inginf             = data.get("Verwendbarkeit M.Sc. INGINF", []),
            usability_msc_wif                = data.get("Verwendbarkeit M.Sc. WIF", []),
            usability_msc_dke                = data.get("Verwendbarkeit M.Sc. DKE", []),
            usability_msc_de                 = data.get("Verwendbarkeit M.Sc. DE", []),
            usability_msc_vc                 = data.get("Verwendbarkeit M.Sc. VC", []),
            subtitle                         = data.get("Moduluntertitel", ""),
            exported_to                      = data.get("Exportiert nach", []),
            imported_from                    = data.get("Importiert von", ""),
            released_on                      = data.get("Freigabe am", ""),
            courses                          = data.get("Lehrveranstaltungen", ""),
            irregular                        = data.get("Unregelmäßig", ""),
            exam_prerequisite                = data.get("Prüfungsvorleistung", ""),
            translation                      = trans,
        )

    @classmethod
    def from_dict(cls, data: ModuleDict, trans_data: ModuleDict|None = None) -> Self:
        """ Creates a Module instance from a dictionary.

            Parameters:
                data: A dictionary with the module data.
                trans_data: An optional dictionary with the (translated) module data.

            for structure see <ModuleDict>

        """
        data = without_nulls(data)  # pyright: ignore[reportAssignmentType]
        if trans_data is not None:
            trans_data = without_nulls(trans_data)  # pyright: ignore[reportAssignmentType]

        id_: int | None = data.get("id", None)
        language_input = data.get("language", "")
        # the language is stored as its id, but may arrive as the string of that id
        language: ModuleLanguage = ModuleLanguage(int(language_input))

        assert id_ is not None, "An identification number is required."

        trans: Module | None = None
        if trans_data:
            trans = Module.from_dict(trans_data)

        return cls(
            id_       = id_,
            language  = language,


            status                           = data.get("status", -1),
            title                            = data.get("title", ""),
            title_en                         = data.get("title_en", ""),
            chair                            = data.get("chair", -1),
            responsibility                   = data.get("responsibility", ""),
            lecturer                         = data.get("lecturer", ""),
            abbreviation                     = data.get("abbreviation", ""),
            credit_points                    = data.get("credit_points", ""),
            semester_position                = data.get("semester_position", -1),
            academic_semester                = data.get("academic_semester", -1),
            duration                         = data.get("duration", -1),
            level                            = data.get("level", []),
            learning_goals                   = data.get("learning_goals", ""),
            content                          = data.get("content", ""),
            workload                         = data.get("workload", ""),
            study_exam_type                  = data.get("study_exam_type", ""),
            teaching_form_sws                = data.get("teaching_form_sws", ""),
            requirements_by_exam_regulations = data.get("requirements_by_exam_regulations", ""),
            recommended_prerequisites        = data.get("recommended_prerequisites", ""),
            media_forms                      = data.get("media_forms", ""),
            literature                       = data.get("literature", ""),
            notes                            = data.get("notes", ""),
            first_examiner                   = data.get("first_examiner", ""),
            second_examiner                  = data.get("second_examiner", ""),
            substitute                       = data.get("substitute", ""),
            usability_bsc_inf                = data.get("usability_bsc_inf", []),
            usability_bsc_cv                 = data.get("usability_bsc_cv", []),
            usability_bsc_inginf             = data.get("usability_bsc_inginf", []),
            usability_bsc_wif                = data.get("usability_bsc_wif", []),
            usability_bsc_inf_bilingual      = data.get("usability_bsc_inf_bilingual", []),
            usability_msc_inf                = data.get("usability_msc_inf", []),
            usability_msc_inginf             = data.get("usability_msc_inginf", []),
            usability_msc_wif                = data.get("usability_msc_wif", []),
            usability_msc_dke                = data.get("usability_msc_dke", []),
            usability_msc_de                 = data.get("usability_msc_de", []),
            usability_msc_vc                 = data.get("usability_msc_vc", []),
            subtitle                         = data.get("subtitle", ""),
            exported_to                      = data.get("exported_to", []),
            imported_from                    = data.get("imported_from", ""),
            released_on                      = data.get("released_on", ""),
            courses                          = data.get("courses", ""),
            irregular                        = data.get("irregular", ""),
            exam_prerequisite                = data.get("exam_prerequisite", ""),
            translation                      = trans,
        )


    def get_status(self) -> str:
        """ Trys to convert the status id into a human-readable string."""
        return get_value_by_id(self._status, "status")


    def get_title(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules title in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                A tuple containing the string and a boolean indicating whether
                an automatic translation was needed
        """

        if lang == LanguageCode.DE:
            return self._title
        if lang == LanguageCode.EN:
            if self._title_en != "":
                return self._title_en

        return self._title


    def _get_translation(
        self,
        text: str,
        trans: str,
        to_language: LanguageCode = LanguageCode.DE
    ) -> str:
        """ Simple utility function for selection of the correct string."""
        if len(trans.strip())>0 and self.language!=to_language:
            return trans.strip()
        return text.strip()


    def get_chair(self) -> str:
        """ Trys to convert the chair id into a human-readable string."""
        return get_value_by_id(self._chair, "lehrstuhl")


    def get_semester_position(self) -> str:
        """ Trys to convert the semester position id into a human-readable string."""
        return get_value_by_id(self._semester_position, "semesterlage")


    def get_academic_semester(self) -> str:
        """ Trys to convert the academic semester id into a human-readable string."""
        return get_value_by_id(self._academic_semester, "fachsemester")


    def get_duration(self) -> str:
        """ Trys to convert the duration id into a human-readable string."""
        return get_value_by_id(self._duration, "dauer")


    def get_level(self) -> list[str]:
        """ Trys to convert the level ids into human-readable strings."""
        result: list[str] = []
        for _level in self._level:
            result.append(get_value_by_id(_level, "niveau"))
        return result


    def get_learning_goals(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules learning goals in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_learning_goals()
        return self._get_translation(
            self._learning_goals,
            trans,
            lang
        )


    def get_content(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules content in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_content()
        return self._get_translation(
            self._content,
            trans,
            lang
        )


    def get_workload(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules workload in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_workload()
        return self._get_translation(
            self._workload,
            trans,
            lang
        )


    def get_study_exam_type(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules study / exam performance in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_study_exam_type()
        return self._get_translation(
            self._study_exam_type,
            trans,
            lang
        )


    def get_teaching_form_sws(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules teching format in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_teaching_form_sws()
        return self._get_translation(
            self._teaching_form_sws,
            trans,
            lang
        )


    def get_requirements_by_exam_regulations(
        self,
        lang: LanguageCode = LanguageCode.DE
    ) -> str:
        """ Retrieves the modules requirements (by exam regulations) in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_requirements_by_exam_regulations()
        return self._get_translation(
            self._requirements_by_exam_regulations,
            trans,
            lang
        )


    def get_recommended_prerequisites(
        self,
        lang: LanguageCode = LanguageCode.DE
    ) -> str:
        """ Retrieves the modules prerequisites in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_recommended_prerequisites()
        return self._get_translation(
            self._recommended_prerequisites,
            trans,
            lang
        )


    def get_media_forms(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules media forms in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_media_forms()
        return self._get_translation(
            self._media_forms,
            trans,
            lang
        )


    def get_literature(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules literature in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_literature()
        return self._get_translation(
            self._literature,
            trans,
            lang
        )


    def get_notes(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules notes in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_notes()
        return self._get_translation(
            self._notes,
            trans,
            lang
        )


    def get_usability_bsc_inf(self) -> list[str]:
        """ Trys to convert the usability b.sc. inf ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_bsc_inf:
            result.append(get_value_by_id(usability, "verwendbarkeit b.sc. inf"))
        return result


    def get_usability_bsc_cv(self) -> list[str]:
        """ Trys to convert the usability b.sc. cv ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_bsc_cv:
            result.append(get_value_by_id(usability, "verwendbarkeit b.sc. cv"))
        return result


    def get_usability_bsc_inginf(self) -> list[str]:
        """ Trys to convert the usability b.sc. inginf ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_bsc_inginf:
            result.append(get_value_by_id(usability, "verwendbarkeit b.sc. inginf"))
        return result


    def get_usability_bsc_wif(self) -> list[str]:
        """ Trys to convert the usability b.sc. wif ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_bsc_wif:
            result.append(get_value_by_id(usability, "verwendbarkeit b.sc. wif"))
        return result


    def get_usability_bsc_inf_bilingual(self) -> list[str]:
        """ Trys to convert the usability b.sc. inf (bilingual) ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_bsc_inf_bilingual:
            result.append(get_value_by_id(usability, "verwendbarkeit b.sc. inf (bilingual)"))
        return result


    def get_usability_msc_inf(self) -> list[str]:
        """ Trys to convert the usability m.sc. inf ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_msc_inf:
            result.append(get_value_by_id(usability, "verwendbarkeit m.sc. inf"))
        return result


    def get_usability_msc_inginf(self) -> list[str]:
        """ Trys to convert the usability m.sc. inginf ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_msc_inginf:
            result.append(get_value_by_id(usability, "verwendbarkeit m.sc. inginf"))
        return result


    def get_usability_msc_wif(self) -> list[str]:
        """ Trys to convert the usability m.sc. wif ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_msc_wif:
            result.append(get_value_by_id(usability, "verwendbarkeit m.sc. wif"))
        return result


    def get_usability_msc_dke(self) -> list[str]:
        """ Trys to convert the usability m.sc. dke ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_msc_dke:
            result.append(get_value_by_id(usability, "verwendbarkeit m.sc. dke"))
        return result


    def get_usability_msc_de(self) -> list[str]:
        """ Trys to convert the usability m.sc. de ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_msc_de:
            result.append(get_value_by_id(usability, "verwendbarkeit m.sc. de"))
        return result


    def get_usability_msc_vc(self) -> list[str]:
        """ Trys to convert the usability m.sc. vc ids into human-readable strings."""
        result: list[str] = []
        for usability in self._usability_msc_vc:
            result.append(get_value_by_id(usability, "verwendbarkeit m.sc. vc"))
        return result


    def get_usability_ids(self, study_course: StudyCourse) -> list[int]:
        """ The raw usability ids of one study programme.

            The `get_usability_*` methods render the ids as names. Comparing a module
            against a semesterplan needs the ids themselves. The attribute name follows
            the enum member, so `MSC_VC` reads `_usability_msc_vc` and all eleven
            programmes are covered without eleven separate branches.

            Parameters:
                study_course: The programme to look at.

            Returns:
                The stored ids, or an empty list when the module has none.
        """
        return getattr(self, f"_usability_{study_course.name.lower()}", [])


    def get_subtitle(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules subtitle in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_subtitle()
        return self._get_translation(
            self._subtitle,
            trans,
            lang
        )


    def get_exported_to(self) -> list[str]:
        """ Trys to convert the exported to ids into human-readable strings."""
        result: list[str] = []
        for faculty in self._exported_to:
            result.append(get_value_by_id(faculty, "exportiert nach"))
        return result


    def get_imported_from(self) -> str:
        """ Trys to convert the imported from id into a human-readable string.

            Most modules leave the field empty, so an unparsable value yields an empty string
            instead of a `ValueError`.
        """
        if not str(self._imported_from).strip().isdigit():
            return ""
        return get_value_by_id(int(self._imported_from), "importiert von")



    def get_irregular(self) -> bool:
        """ Trys to convert the irregular id into a human-readable string.

            But currently it dosn't seem to have a mapping,
            and therefore just returns the raw value.
        """
        if self._irregular.lower()=="true":
            return True
        return False


    def get_exam_prerequisite(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules exam prerequisites in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_exam_prerequisite()
        return self._get_translation(
            self._exam_prerequisite,
            trans,
            lang
        )

    def get_courses(self, lang: LanguageCode = LanguageCode.DE) -> str:
        """ Retrieves the modules courses in the requested language.

            Parameters:
                lang: The desired language as a `LanguageCode` enum value.

            Returns:
                If possible the translated String
        """
        trans: str = ""
        if self.translation:
            trans = self.translation.get_courses()
        return self._get_translation(
            self._courses,
            trans,
            lang
        )





if __name__ == "__main__":
    # example import from "tables" dict
    module: Module = Module.from_tables_dict({
        "Modultitel": "Mathematik M1d",
        "Modultitel (englisch)": "Mathematics M1d",
        "Modulverantwortung": "Prof. Dr. Volker Kaibel",
        "Dozent:in": "Prof. Dr. Volker Kaibel",
        "Modulkürzel": "",
        "Credit Points": "5",
        "Angestrebte Lernergebnisse":
            """Die Studierenden erlangen auf Verständnis beruhende Vertrautheitmit den für
fachwissenschaftliche Module in den BereichenIngenieurwissenschaften und Informatik relevanten
mathematischen Konzepten und Methoden. Sie erwerben technische Fähigkeiten im Umgang mit diesen,
insbesondere unter Verwendung fachspezifischer Beispiele.Thematischer Schwerpunkt des Moduls ist
eine Einführung in dieLineare Algebra.""",
        "Inhalt": """- Komplexe Zahlen
- Reele und komplexe Vektoren
- Matrizen
- Determinanten
- Lineare Abbildungen
- Eigenwerte (Einführung)
- Lineare Gleichungssysteme""",
        "Arbeitsaufwand": """Präsenzzeit:

Vorlesung Mathematik M1d -- 3 SWS / 42 h

Globalübung Mathematik M1d -- 2 SWS / 28 h

Gruppenübung Mathematik M1d -- 1 SWS / 14 h

Selbststudium: Vor- und Nachbereitung der Lehrveranstaltungen, Prüfungsvorbereitung -- 66 h""",
        "Studien-/Prüfungsleistung":
            "Prüfungsvorleistung: Ankündigung zu Beginn des Semesters Prüfung: Klausur",
        "Lehrform / SWS": "Vorlesung (3 SWS)\n\nÜbung (3 SWS)",
        "Empfohlene Voraussetzungen": "",
        "Identifizierung": 501325,
        "Lehrstuhl": 23,
        "Semesterlage": 0,
        "Fachsemester": 1,
        "Dauer": 0,
        "Modulsprache": 1,
        "Niveau": [0]
    })

    print(module.get_title(LanguageCode.EN))
    print(module.credit_points)
    print(module.get_learning_goals(LanguageCode.EN))
    print(module.get_content(LanguageCode.EN))
    print(module.get_workload(LanguageCode.EN))

    print("\n")

    print(Module.from_name("Introduction to Digital Games", True))






def get_module_list(table_id: int = 720) -> list[Module]:
    """ Retruns a list of all available modules from the tables tatabase"""
    module_dicts: list[TablesModuleDict] = get_rows(table_id)
    base_modules: list[TablesModuleDict] = []
    trans_modules: list[TablesModuleDict] = []
    for data in module_dicts:
        if data.get("Translation", "").lower() == "true":
            trans_modules.append(data)
        else:
            base_modules.append(data)


    module_list: list[Module] = []

    for data in base_modules:
        trans_data: TablesModuleDict | None = next(
            (m for m in trans_modules if m["Identifizierung"]==data["Identifizierung"]),
            None
        )
        module_list.append(Module.from_tables_dict(data, trans_data))

        if trans_data:
            trans_modules.remove(trans_data)

    for data in trans_modules:
        module_list.append(Module.from_tables_dict(data))

    return module_list
