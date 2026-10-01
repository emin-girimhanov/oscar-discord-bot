"""Comprehensive tests for the Module class and all its methods."""

import pytest
from unittest.mock import MagicMock, patch
from util.module import Module
from util.enums import LanguageCode


# --- TestModule: core construction and lookup methods ---

class TestModule:
    """Tests for Module construction from various sources."""

    def test_init_from_dict(self, sample_module_dict):
        module = Module.from_tables_dict(sample_module_dict)
        assert module.id_ == 123
        assert module.language == LanguageCode.DE
        assert module._title == "Test Modul"
        assert module._title_en == "Test Module"

    def test_get_title_de(self, sample_module_dict):
        module = Module.from_tables_dict(sample_module_dict)
        assert module.get_title(LanguageCode.DE) == "Test Modul"

    def test_get_title_en_existing(self, sample_module_dict):
        module = Module.from_tables_dict(sample_module_dict)
        assert module.get_title(LanguageCode.EN) == "Test Module"

    def test_get_title_en_falls_back_to_german(self, sample_module_dict):
        """Without an english title the german one is returned."""
        sample_module_dict["Modultitel (englisch)"] = ""
        module = Module.from_tables_dict(sample_module_dict)

        assert module.get_title(LanguageCode.EN) == "Test Modul"

    @patch("util.module.get_rows")
    def test_from_id_found(self, mock_get_rows, sample_module_dict):
        mock_get_rows.return_value = [sample_module_dict]
        module = Module.from_id(123)
        assert module.id_ == 123
        assert module._title == "Test Modul"
        mock_get_rows.assert_called()

    @patch("util.module.get_rows")
    def test_from_id_not_found(self, mock_get_rows):
        mock_get_rows.return_value = []
        with pytest.raises(IndexError):
            Module.from_id(999)

    @patch("util.module.get_rows")
    def test_from_id_multiple_matches_returns_first(self, mock_get_rows, sample_module_dict):
        """When multiple modules share the same ID, the first match is returned."""
        dict2 = dict(sample_module_dict)
        dict2["Modultitel"] = "Second Module"
        mock_get_rows.return_value = [sample_module_dict, dict2]
        module = Module.from_id(123)
        assert module._title == "Test Modul"

    @patch("util.module.get_rows")
    def test_from_name_found(self, mock_get_rows, sample_module_dict):
        mock_get_rows.return_value = [sample_module_dict]
        module = Module.from_name("Test Modul")
        assert module.id_ == 123

        module_en = Module.from_name("Test Module", name_is_en=True)
        assert module_en.id_ == 123

    @patch("util.module.get_rows")
    def test_from_name_not_found(self, mock_get_rows):
        mock_get_rows.return_value = []
        with pytest.raises(IndexError):
            Module.from_name("Nonexistent Module")

    @patch("util.module.get_rows")
    def test_from_name_multiple_results_logs_warning(self, mock_get_rows, sample_module_dict):
        """When multiple modules match the name, the first one should be returned."""
        dict2 = dict(sample_module_dict)
        mock_get_rows.return_value = [sample_module_dict, dict2]
        module = Module.from_name("Test Modul")
        assert module.id_ == 123


class TestModuleStr:
    """Tests for Module.__str__."""

    def test_str_representation(self, sample_module_dict):
        module = Module.from_tables_dict(sample_module_dict)
        result = str(module)
        assert "123" in result
        assert "Test Modul" in result

    def test_str_contains_language(self, sample_module_dict):
        module = Module.from_tables_dict(sample_module_dict)
        result = str(module)
        assert "de" in result

    def test_str_contains_german_title(self, sample_module_dict):
        """__str__ prints the german title, not the english one."""
        module = Module.from_tables_dict(sample_module_dict)
        result = str(module)
        assert "Test Modul" in result

    def test_str_empty_titles(self):
        module = Module(id_=1, language=LanguageCode.DE)
        result = str(module)
        assert "1" in result


class TestFromDict:
    """Tests for Module.from_dict with various data shapes."""

    def test_from_dict_valid(self):
        data = {
            "id": 101,
            "language": 1,
            "title": "Dict Data Module",
            "title_en": "Dict Data Module EN",
            "credit_points": "5",
        }
        module = Module.from_dict(data)
        assert module.id_ == 101
        assert module.language == LanguageCode.DE
        assert module._title == "Dict Data Module"
        assert module.credit_points == "5"

    def test_from_dict_language_string(self):
        data = {"id": 102, "language": "1", "title": "String Lang Module"}
        module = Module.from_dict(data)
        assert module.id_ == 102
        assert module.language == LanguageCode.DE

    def test_from_dict_language_en(self):
        data = {"id": 103, "language": 0, "title": "English Module"}
        module = Module.from_dict(data)
        assert module.language == LanguageCode.EN

    def test_from_dict_minimal_fields(self):
        data = {"id": 200, "language": 0}
        module = Module.from_dict(data)
        assert module.id_ == 200
        assert module._title == ""
        assert module.credit_points == ""

    def test_from_dict_all_fields(self):
        data = {
            "id": 300, "language": 1,
            "status": 1, "title": "T", "title_en": "Te",
            "chair": 2, "responsibility": "R", "lecturer": "L",
            "abbreviation": "A", "credit_points": "10",
            "semester_position": 1, "academic_semester": 2,
            "duration": 1, "level": [1, 2],
            "learning_goals": "LG", "content": "C",
            "workload": "W", "study_exam_type": "SE",
            "teaching_form_sws": "TFS",
            "requirements_by_exam_regulations": "REQ",
            "recommended_prerequisites": "RP",
            "media_forms": "MF", "literature": "LIT",
            "notes": "N", "first_examiner": "FE",
            "second_examiner": "SE2", "substitute": "S",
            "usability_bsc_inf": [1], "usability_bsc_cv": [2],
            "usability_bsc_inginf": [3], "usability_bsc_wif": [4],
            "usability_bsc_inf_bilingual": [5],
            "usability_msc_inf": [6], "usability_msc_inginf": [7],
            "usability_msc_wif": [8], "usability_msc_dke": [9],
            "usability_msc_de": [10], "usability_msc_vc": [11],
            "subtitle": "Sub", "exported_to": [1, 2],
            "imported_from": "IF", "released_on": "2024-01-01",
            "courses": "Kurse", "irregular": "Ja",
            "exam_prerequisite": "EP",
        }
        module = Module.from_dict(data)
        assert module.id_ == 300
        assert module._title == "T"
        assert module._usability_bsc_inf == [1]
        assert module._usability_msc_vc == [11]
        assert module._exported_to == [1, 2]
        assert module._courses == "Kurse"

    def test_from_dict_missing_id_raises(self):
        """Module.from_dict without 'id' key should raise AssertionError."""
        data = {"language": 1, "title": "No ID"}
        with pytest.raises((AssertionError, TypeError)):
            Module.from_dict(data)


class TestFromTablesDictEdgeCases:
    """Tests for from_tables_dict edge cases."""

    def test_unknown_language_falls_back_to_en(self, sample_module_dict):
        """An unknown language id is treated as english, see from_tables_dict."""
        sample_module_dict["Modulsprache"] = 999
        module = Module.from_tables_dict(sample_module_dict)
        assert module.language == LanguageCode.EN

    def test_none_language_falls_back_to_en(self, sample_module_dict):
        sample_module_dict["Modulsprache"] = None
        module = Module.from_tables_dict(sample_module_dict)
        assert module.language == LanguageCode.EN

    def test_missing_optional_fields_default(self, sample_module_dict):
        """Only required fields are provided; optional fields should default."""
        minimal = {"Identifizierung": 999, "Modulsprache": 1}
        module = Module.from_tables_dict(minimal)
        assert module.id_ == 999
        assert module._title == ""
        assert module._title_en == ""
        assert module.credit_points == ""
        assert module._usability_bsc_inf == []

    def test_missing_id_raises_assertion(self):
        """from_tables_dict without Identifizierung should raise AssertionError."""
        data = {"Modulsprache": 1, "Modultitel": "No ID"}
        with pytest.raises(AssertionError):
            Module.from_tables_dict(data)

    def test_all_fields_populated(self, sample_module_dict):
        """Test that all fields from the tables dict are mapped correctly."""
        sample_module_dict["Modulkürzel"] = "TM"
        sample_module_dict["Dauer"] = 2
        sample_module_dict["Niveau"] = [0, 1]
        sample_module_dict["Arbeitsaufwand"] = "150h"
        sample_module_dict["Studien-/Prüfungsleistung"] = "Klausur"
        sample_module_dict["Lehrform / SWS"] = "VL 3 SWS"
        sample_module_dict["Medienformen"] = "Tafel"
        sample_module_dict["Literatur"] = "Buch"
        sample_module_dict["Hinweise"] = "Note"
        sample_module_dict["Erstprüfer"] = "EP"
        sample_module_dict["Zweitprüfer"] = "ZP"
        sample_module_dict["Stellvertreter"] = "SV"
        sample_module_dict["Verwendbarkeit B.Sc. CV"] = [1, 2]
        sample_module_dict["Exportiert nach"] = [3]
        sample_module_dict["Moduluntertitel"] = "Untertitel"
        sample_module_dict["Prüfungsvorleistung"] = "PVL"

        module = Module.from_tables_dict(sample_module_dict)
        assert module.abbreviation == "TM"
        assert module._duration == 2
        assert module._level == [0, 1]
        assert module._workload == "150h"
        assert module._study_exam_type == "Klausur"
        assert module._teaching_form_sws == "VL 3 SWS"
        assert module._media_forms == "Tafel"
        assert module._literature == "Buch"
        assert module._notes == "Note"
        assert module.first_examiner == "EP"
        assert module.second_examiner == "ZP"
        assert module.substitute == "SV"
        assert module._usability_bsc_cv == [1, 2]
        assert module._exported_to == [3]
        assert module._subtitle == "Untertitel"
        assert module._exam_prerequisite == "PVL"


class TestModuleProperties:
    """Tests for properties that use get_value_by_id."""

    @pytest.mark.parametrize("method_name, return_value, expected_value, lookup_key, dict_update", [
        ("get_status", "Aktiv", "Aktiv", "status", None),
        ("get_chair", "Informatik", "Informatik", "lehrstuhl", None),
        ("get_semester_position", "Wintersemester", "Wintersemester", "semesterlage", None),
        ("get_academic_semester", "1. Semester", "1. Semester", "fachsemester", None),
        ("get_duration", "1 Semester", "1 Semester", "dauer", {"Dauer": 1}),
    ])
    def test_simple_properties(self, method_name, return_value, expected_value, lookup_key, dict_update, sample_module_dict):
        if dict_update:
            sample_module_dict.update(dict_update)
        module = Module.from_tables_dict(sample_module_dict)

        with patch("util.module.get_value_by_id") as mock_get_value:
            mock_get_value.return_value = return_value
            result = getattr(module, method_name)()
            assert result == expected_value
            if lookup_key:
                mock_get_value.assert_called_with(1, lookup_key)

    @patch("util.module.get_value_by_id")
    def test_get_level_multiple(self, mock_get_value, sample_module_dict):
        mock_get_value.return_value = "Bachelor"
        sample_module_dict["Niveau"] = [1, 2]
        module = Module.from_tables_dict(sample_module_dict)
        result = module.get_level()
        assert len(result) == 2
        assert all(r == "Bachelor" for r in result)

    @patch("util.module.get_value_by_id")
    def test_get_level_empty(self, mock_get_value, sample_module_dict):
        """Empty level list should return empty result."""
        module = Module.from_tables_dict(sample_module_dict)
        module._level = []
        result = module.get_level()
        assert result == []
        mock_get_value.assert_not_called()

    @patch("util.module.get_value_by_id")
    def test_get_level_single(self, mock_get_value, sample_module_dict):
        mock_get_value.return_value = "Master"
        sample_module_dict["Niveau"] = [5]
        module = Module.from_tables_dict(sample_module_dict)
        result = module.get_level()
        assert result == ["Master"]

    @patch("util.module.get_value_by_id")
    def test_get_imported_from(self, mock_get_value, sample_module_dict):
        """get_imported_from resolves the numeric id of the exporting faculty."""
        mock_get_value.return_value = "FMA"
        sample_module_dict["Importiert von"] = "1"
        module = Module.from_tables_dict(sample_module_dict)
        assert module.get_imported_from() == "FMA"

    def test_get_imported_from_empty(self, sample_module_dict):
        """An empty field must not raise, most modules leave it blank."""
        module = Module.from_tables_dict(sample_module_dict)
        assert module.get_imported_from() == ""

    def test_get_irregular_true(self, sample_module_dict):
        """get_irregular returns a bool, the tables store the string 'true'."""
        sample_module_dict["Unregelmäßig"] = "true"
        module = Module.from_tables_dict(sample_module_dict)
        assert module.get_irregular() is True

    def test_get_irregular_false(self, sample_module_dict):
        module = Module.from_tables_dict(sample_module_dict)
        assert module.get_irregular() is False


class TestUsabilityGetters:
    """Tests for ALL usability getter methods (bsc_inf, bsc_cv, ..., msc_vc)."""

    @pytest.mark.parametrize("getter_method, attr_name, key_suffix", [
        ("get_usability_bsc_inf", "usability_bsc_inf", "verwendbarkeit b.sc. inf"),
        ("get_usability_bsc_cv", "usability_bsc_cv", "verwendbarkeit b.sc. cv"),
        ("get_usability_bsc_inginf", "usability_bsc_inginf", "verwendbarkeit b.sc. inginf"),
        ("get_usability_bsc_wif", "usability_bsc_wif", "verwendbarkeit b.sc. wif"),
        ("get_usability_bsc_inf_bilingual", "usability_bsc_inf_bilingual", "verwendbarkeit b.sc. inf (bilingual)"),
        ("get_usability_msc_inf", "usability_msc_inf", "verwendbarkeit m.sc. inf"),
        ("get_usability_msc_inginf", "usability_msc_inginf", "verwendbarkeit m.sc. inginf"),
        ("get_usability_msc_wif", "usability_msc_wif", "verwendbarkeit m.sc. wif"),
        ("get_usability_msc_dke", "usability_msc_dke", "verwendbarkeit m.sc. dke"),
        ("get_usability_msc_de", "usability_msc_de", "verwendbarkeit m.sc. de"),
        ("get_usability_msc_vc", "usability_msc_vc", "verwendbarkeit m.sc. vc"),
    ])
    @patch("util.module.get_value_by_id")
    def test_usability_with_values(self, mock_get_value, getter_method, attr_name, key_suffix):
        mock_get_value.return_value = "Pflicht"
        module = Module(id_=1, language=LanguageCode.DE)
        # the getters read the private attribute, the constructor argument is the public name
        setattr(module, f"_{attr_name}", [1, 2, 3])
        result = getattr(module, getter_method)()
        assert len(result) == 3
        assert all(r == "Pflicht" for r in result)

    @pytest.mark.parametrize("getter_method, attr_name", [
        ("get_usability_bsc_inf", "usability_bsc_inf"),
        ("get_usability_bsc_cv", "usability_bsc_cv"),
        ("get_usability_bsc_inginf", "usability_bsc_inginf"),
        ("get_usability_bsc_wif", "usability_bsc_wif"),
        ("get_usability_bsc_inf_bilingual", "usability_bsc_inf_bilingual"),
        ("get_usability_msc_inf", "usability_msc_inf"),
        ("get_usability_msc_inginf", "usability_msc_inginf"),
        ("get_usability_msc_wif", "usability_msc_wif"),
        ("get_usability_msc_dke", "usability_msc_dke"),
        ("get_usability_msc_de", "usability_msc_de"),
        ("get_usability_msc_vc", "usability_msc_vc"),
    ])
    def test_usability_empty_list(self, getter_method, attr_name):
        """Empty usability list should return empty result without calling get_value_by_id."""
        module = Module(id_=1, language=LanguageCode.DE)
        setattr(module, f"_{attr_name}", [])
        with patch("util.module.get_value_by_id") as mock_gv:
            result = getattr(module, getter_method)()
            assert result == []
            mock_gv.assert_not_called()

    @patch("util.module.get_value_by_id")
    def test_get_exported_to_with_values(self, mock_get_value):
        mock_get_value.return_value = "FMB"
        module = Module(id_=1, language=LanguageCode.DE)
        module._exported_to = [1, 2]
        result = module.get_exported_to()
        assert result == ["FMB", "FMB"]

    def test_get_exported_to_empty(self):
        module = Module(id_=1, language=LanguageCode.DE)
        module._exported_to = []
        with patch("util.module.get_value_by_id") as mock_gv:
            result = module.get_exported_to()
            assert result == []
            mock_gv.assert_not_called()


class TestModuleTranslationGetters:
    """Tests for all getters that support translation via _get_translation."""

    @pytest.mark.parametrize("method_name, dict_key, dict_value", [
        ("get_learning_goals", "Angestrebte Lernergebnisse", "Lernen"),
        ("get_content", "Inhalt", "Inhalt"),
        ("get_workload", "Arbeitsaufwand", "150 Stunden"),
        ("get_study_exam_type", "Studien-/Prüfungsleistung", "Klausur"),
        ("get_teaching_form_sws", "Lehrform / SWS", "Vorlesung (3 SWS)"),
        ("get_requirements_by_exam_regulations", "Voraussetzungen nach Prüfungsordnung", "Keine"),
        ("get_recommended_prerequisites", "Empfohlene Voraussetzungen", "Mathe I"),
        ("get_media_forms", "Medienformen", "Tafel, Beamer"),
        ("get_literature", "Literatur", "Tanenbaum 2024"),
        ("get_notes", "Hinweise", "Bitte anmelden"),
        ("get_subtitle", "Moduluntertitel", "Grundlagen"),
        ("get_exam_prerequisite", "Prüfungsvorleistung", "Übungsschein"),
    ])
    def test_getters_same_language_no_translation(self, method_name, dict_key, dict_value, sample_module_dict):
        sample_module_dict[dict_key] = dict_value
        module = Module.from_tables_dict(sample_module_dict)
        assert getattr(module, method_name)(LanguageCode.DE) == dict_value

    @pytest.mark.parametrize("method_name, dict_key, dict_value", [
        ("get_learning_goals", "Angestrebte Lernergebnisse", "Lernen"),
        ("get_content", "Inhalt", "Inhalt"),
        ("get_workload", "Arbeitsaufwand", "150h"),
        ("get_study_exam_type", "Studien-/Prüfungsleistung", "Klausur"),
        ("get_teaching_form_sws", "Lehrform / SWS", "VL"),
        ("get_requirements_by_exam_regulations", "Voraussetzungen nach Prüfungsordnung", "Keine"),
        ("get_recommended_prerequisites", "Empfohlene Voraussetzungen", "Mathe"),
        ("get_media_forms", "Medienformen", "Tafel"),
        ("get_literature", "Literatur", "Buch"),
        ("get_notes", "Hinweise", "Hinweis"),
        ("get_subtitle", "Moduluntertitel", "Sub"),
        ("get_exam_prerequisite", "Prüfungsvorleistung", "PVL"),
    ])
    def test_getters_translation_needed(self, method_name, dict_key, dict_value, sample_module_dict):
        """When requesting EN for a DE module, the attached translation row is used."""
        sample_module_dict[dict_key] = dict_value

        translated_dict = dict(sample_module_dict)
        translated_dict["Modulsprache"] = LanguageCode.EN.value
        translated_dict[dict_key] = f"Translated_{dict_value}"

        module = Module.from_tables_dict(sample_module_dict, translated_dict)

        assert getattr(module, method_name)(LanguageCode.EN) == f"Translated_{dict_value}"

    @pytest.mark.parametrize("method_name", [
        "get_learning_goals", "get_content", "get_workload",
        "get_study_exam_type", "get_teaching_form_sws",
        "get_requirements_by_exam_regulations",
        "get_recommended_prerequisites", "get_media_forms",
        "get_literature", "get_notes", "get_subtitle",
        "get_exam_prerequisite",
    ])
    def test_getters_empty_string_same_language(self, method_name):
        """Empty string fields should return an empty string."""
        module = Module(id_=1, language=LanguageCode.DE)
        assert getattr(module, method_name)(LanguageCode.DE) == ""

    def test_get_translation_same_language_returns_text(self):
        """_get_translation returns the original text when the languages match."""
        module = Module(id_=1, language=LanguageCode.DE)
        assert module._get_translation("Hallo", "Hello", LanguageCode.DE) == "Hallo"

    def test_get_translation_other_language_returns_translation(self):
        """_get_translation returns the translation when another language is requested."""
        module = Module(id_=1, language=LanguageCode.DE)
        assert module._get_translation("Hallo", "Hello", LanguageCode.EN) == "Hello"

    def test_get_translation_falls_back_to_text(self):
        """Without a translation the original text is returned."""
        module = Module(id_=1, language=LanguageCode.DE)
        assert module._get_translation("Hallo", "  ", LanguageCode.EN) == "Hallo"


class TestModuleInit:
    """Tests for direct Module initialization edge cases."""

    def test_default_values(self):
        module = Module(id_=1, language=LanguageCode.DE)
        assert module.id_ == 1
        assert module.credit_points == ""
        assert module._title == ""
        assert module._title_en == ""
        assert module._usability_bsc_inf == []
        assert module._usability_bsc_cv == []
        assert module._usability_msc_vc == []
        assert module._exported_to == []
        assert module._level == []
        assert module._status == -1
        assert module._chair == -1
        assert module._semester_position == -1
        assert module._academic_semester == -1
        assert module._duration == -1

    def test_custom_values(self):
        module = Module(
            id_=42,
            language=LanguageCode.EN,
            credit_points="10",
            title="Advanced AI",
            title_en="Advanced AI",
            responsibility="Prof. Z",
        )
        assert module.id_ == 42
        assert module.language == LanguageCode.EN
        assert module.credit_points == "10"
        assert module._title == "Advanced AI"
        assert module.responsibility == "Prof. Z"

    def test_none_list_defaults_to_empty(self):
        """Passing None for list parameters should result in empty lists."""
        module = Module(
            id_=1, language=LanguageCode.DE,
            level=None,
            usability_bsc_inf=None,
            usability_bsc_cv=None,
            usability_bsc_inginf=None,
            usability_bsc_wif=None,
            usability_bsc_inf_bilingual=None,
            usability_msc_inf=None,
            usability_msc_inginf=None,
            usability_msc_wif=None,
            usability_msc_dke=None,
            usability_msc_de=None,
            usability_msc_vc=None,
            exported_to=None,
        )
        assert module._level == []
        assert module._usability_bsc_inf == []
        assert module._usability_bsc_cv == []
        assert module._usability_bsc_inginf == []
        assert module._usability_bsc_wif == []
        assert module._usability_bsc_inf_bilingual == []
        assert module._usability_msc_inf == []
        assert module._usability_msc_inginf == []
        assert module._usability_msc_wif == []
        assert module._usability_msc_dke == []
        assert module._usability_msc_de == []
        assert module._usability_msc_vc == []
        assert module._exported_to == []

    def test_list_parameters_are_used_when_provided(self):
        """Providing list values should use them directly."""
        module = Module(
            id_=1, language=LanguageCode.DE,
            level=[1, 2, 3],
            usability_bsc_inf=[10, 20],
            exported_to=[5],
        )
        assert module._level == [1, 2, 3]
        assert module._usability_bsc_inf == [10, 20]
        assert module._exported_to == [5]

    def test_all_string_fields(self):
        """Test setting all string fields."""
        module = Module(
            id_=1, language=LanguageCode.DE,
            title="T", title_en="Te",
            responsibility="R", lecturer="L",
            abbreviation="A", credit_points="CP",
            learning_goals="LG", content="Con",
            workload="W", study_exam_type="SE",
            teaching_form_sws="TF",
            requirements_by_exam_regulations="R1",
            recommended_prerequisites="R2",
            media_forms="MF", literature="Lit",
            notes="N", first_examiner="FE",
            second_examiner="SE2", substitute="S",
            subtitle="Sub", imported_from="IF",
            released_on="2024", courses="K",
            irregular="I", exam_prerequisite="EP",
        )
        assert module._title == "T"
        assert module._title_en == "Te"
        assert module.responsibility == "R"
        assert module.lecturer == "L"
        assert module.abbreviation == "A"
        assert module._learning_goals == "LG"
        assert module._content == "Con"
        assert module._workload == "W"
        assert module._study_exam_type == "SE"
        assert module._teaching_form_sws == "TF"
        assert module._requirements_by_exam_regulations == "R1"
        assert module._recommended_prerequisites == "R2"
        assert module._media_forms == "MF"
        assert module._literature == "Lit"
        assert module._notes == "N"
        assert module.first_examiner == "FE"
        assert module.second_examiner == "SE2"
        assert module.substitute == "S"
        assert module._subtitle == "Sub"
        assert module._imported_from == "IF"
        assert module.released_on == "2024"
        assert module._courses == "K"
        assert module._irregular == "I"
        assert module._exam_prerequisite == "EP"
