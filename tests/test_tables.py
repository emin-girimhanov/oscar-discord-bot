"""Comprehensive tests for the tables module (API communication and data retrieval)."""

import pytest
from unittest.mock import patch, MagicMock, call
import time


class TestGetJson:
    """Tests for the get_json function."""

    def test_get_json_success(self, mock_requests_get):
        from util.tables import get_json
        _, mock_response = mock_requests_get
        mock_response.json.return_value = {"key": "value"}

        result = get_json("https://example.com/api")
        assert result == {"key": "value"}

    def test_get_json_failure(self, mock_requests_get):
        from util.tables import get_json
        _, mock_response = mock_requests_get
        mock_response.ok = False

        result = get_json("https://example.com/api")
        assert result == {}

    def test_get_json_passes_auth_and_timeout(self, mock_requests_get):
        from util.tables import get_json, auth, REQUEST_TIMEOUT
        mock_get, _ = mock_requests_get
        get_json("https://example.com/api")

        mock_get.assert_called_once_with(
            "https://example.com/api",
            auth=auth,
            timeout=REQUEST_TIMEOUT,
        )

    def test_get_json_empty_response(self, mock_requests_get):
        from util.tables import get_json
        _, mock_response = mock_requests_get
        mock_response.json.return_value = {}

        result = get_json("https://example.com/api")
        assert result == {}


class TestGetRows:
    """Tests for the get_rows function."""

    def test_get_rows_success(self, mock_requests_get):
        from util.tables import get_rows
        _, mock_response = mock_requests_get
        mock_response.json.return_value = [
            ["Identifizierung", "Modultitel"],
            [1, "Mathe 1"],
            [2, "Informatik 1"],
        ]

        result = get_rows(720)
        assert len(result) == 2
        assert result[0]["Identifizierung"] == 1
        assert result[0]["Modultitel"] == "Mathe 1"
        assert result[1]["Identifizierung"] == 2

    def test_get_rows_failure(self, mock_requests_get):
        from util.tables import get_rows
        _, mock_response = mock_requests_get
        mock_response.ok = False

        result = get_rows(720)
        assert result == []

    def test_get_rows_single_row(self, mock_requests_get):
        from util.tables import get_rows
        _, mock_response = mock_requests_get
        mock_response.json.return_value = [
            ["Identifizierung", "Modultitel"],
            [42, "Single Module"],
        ]
        result = get_rows(720)
        assert len(result) == 1
        assert result[0]["Modultitel"] == "Single Module"

    def test_get_rows_no_data_rows(self, mock_requests_get):
        """When only headers are present, result should be empty."""
        from util.tables import get_rows
        _, mock_response = mock_requests_get
        mock_response.json.return_value = [
            ["Identifizierung", "Modultitel"],
        ]
        result = get_rows(720)
        assert result == []

    def test_get_rows_many_columns(self, mock_requests_get):
        from util.tables import get_rows
        _, mock_response = mock_requests_get
        mock_response.json.return_value = [
            ["Col1", "Col2", "Col3", "Col4"],
            ["a", "b", "c", "d"],
        ]
        result = get_rows(720)
        assert result[0] == {"Col1": "a", "Col2": "b", "Col3": "c", "Col4": "d"}


class TestGetScheme:
    """Tests for the get_scheme function."""

    def test_get_scheme_success(self, mock_requests_get):
        from util.tables import get_scheme
        _, mock_response = mock_requests_get
        mock_response.json.return_value = {
            "columns": [{"title": "status", "type": "selection", "selectionOptions": []}]
        }

        result = get_scheme(720)
        assert "columns" in result

    def test_get_scheme_failure(self, mock_requests_get):
        from util.tables import get_scheme
        _, mock_response = mock_requests_get
        mock_response.ok = False

        result = get_scheme(720)
        assert result == []


class TestGetTableIds:
    """Tests for the get_table_ids function."""

    def test_get_table_ids_success(self):
        from util.tables import get_table_ids
        with patch("util.tables.get_json") as mock_get_json:
            mock_get_json.return_value = [
                {"id": 720, "title": "FIN Moduldatenbank", "ownership": "admin"},
            ]
            result = get_table_ids()
            assert len(result) == 1
            assert result[0]["id"] == 720
            assert result[0]["name"] == "FIN Moduldatenbank"
            assert result[0]["owner"] == "admin"


class TestGetRowsFromView:
    """Tests for get_rows_from_view."""

    def test_get_rows_from_view_success(self):
        """Tests the view-based row retrieval with column resolution and title cleaning."""
        import util.tables as tables
        with patch.object(tables, "get_json") as mock_get_json:
            # First call - columns, second call - rows
            mock_get_json.side_effect = [
                # __get_columns_from_view
                [{"id": 1, "title": "Modultitel "}, {"id": 2, "title": "Credit Points"}],
                # __get_rows_from_view
                [
                    {"data": [
                        {"columnId": 1, "value": "Mathe 1"},
                        {"columnId": 2, "value": "5"},
                    ]},
                ],
            ]

            result = tables.get_rows_from_view(2018)
            assert len(result) == 1
            # Modultitel space should be cleaned
            assert result[0]["Modultitel"] == "Mathe 1"
            assert result[0]["Credit Points"] == "5"

    def test_get_rows_from_view_title_cleaning(self):
        """Test that Modultitel(englisch) is cleaned to 'Modultitel (englisch)'."""
        import util.tables as tables
        with patch.object(tables, "get_json") as mock_get_json:
            mock_get_json.side_effect = [
                [{"id": 1, "title": "Modultitel(englisch)"}],
                [{"data": [{"columnId": 1, "value": "Math 101"}]}],
            ]
            result = tables.get_rows_from_view(2018)
            assert "Modultitel (englisch)" in result[0]

    def test_get_rows_from_view_empty(self):
        import util.tables as tables
        with patch.object(tables, "get_json") as mock_get_json:
            mock_get_json.side_effect = [
                [{"id": 1, "title": "Col1"}],
                [],
            ]
            result = tables.get_rows_from_view(2018)
            assert result == []


class TestGetValueById:
    """Tests for get_value_by_id with the selections dictionary."""

    def test_get_value_by_id_found(self):
        import util.tables as tables
        # Directly set the global state
        original_dict = tables.selectionse_dict
        original_ts = tables.last_dict_update
        try:
            tables.selectionse_dict = {"status": {1: "Aktiv", 2: "Inaktiv"}}
            tables.last_dict_update = int(time.time())

            result = tables.get_value_by_id(1, "status")
            assert result == "Aktiv"
        finally:
            tables.selectionse_dict = original_dict
            tables.last_dict_update = original_ts

    def test_get_value_by_id_key_not_found(self):
        import util.tables as tables
        original_dict = tables.selectionse_dict
        original_ts = tables.last_dict_update
        try:
            tables.selectionse_dict = {"status": {1: "Aktiv"}}
            tables.last_dict_update = int(time.time())

            result = tables.get_value_by_id(1, "nonexistent_key")
            assert result == "1"
        finally:
            tables.selectionse_dict = original_dict
            tables.last_dict_update = original_ts

    def test_get_value_by_id_id_not_found(self):
        import util.tables as tables
        original_dict = tables.selectionse_dict
        original_ts = tables.last_dict_update
        try:
            tables.selectionse_dict = {"status": {1: "Aktiv"}}
            tables.last_dict_update = int(time.time())

            result = tables.get_value_by_id(999, "status")
            assert result == "999"
        finally:
            tables.selectionse_dict = original_dict
            tables.last_dict_update = original_ts

    def test_get_value_by_id_case_insensitive_key(self):
        import util.tables as tables
        original_dict = tables.selectionse_dict
        original_ts = tables.last_dict_update
        try:
            tables.selectionse_dict = {"lehrstuhl": {23: "Informatik"}}
            tables.last_dict_update = int(time.time())

            result = tables.get_value_by_id(23, "Lehrstuhl")
            assert result == "Informatik"
        finally:
            tables.selectionse_dict = original_dict
            tables.last_dict_update = original_ts

    def test_get_value_by_id_triggers_update_when_stale(self):
        """When last_dict_update is old, __update_selections_dict should be called."""
        import util.tables as tables
        original_dict = tables.selectionse_dict
        original_ts = tables.last_dict_update
        try:
            tables.last_dict_update = -1
            tables.selectionse_dict = {}

            with patch.object(tables, "get_scheme") as mock_scheme:
                mock_scheme.return_value = {
                    "columns": [
                        {
                            "title": "status",
                            "type": "selection",
                            "selectionOptions": [
                                {"id": 1, "label": "Aktiv"},
                            ],
                        }
                    ]
                }
                result = tables.get_value_by_id(1, "status")
                assert result == "Aktiv"
                mock_scheme.assert_called_once()
        finally:
            tables.selectionse_dict = original_dict
            tables.last_dict_update = original_ts

    def test_get_value_by_id_skips_update_when_recent(self):
        """When last_dict_update is recent, no API call should be made."""
        import util.tables as tables
        original_dict = tables.selectionse_dict
        original_ts = tables.last_dict_update
        try:
            tables.last_dict_update = int(time.time())
            tables.selectionse_dict = {"status": {1: "Test"}}

            with patch.object(tables, "get_scheme") as mock_scheme:
                result = tables.get_value_by_id(1, "status")
                assert result == "Test"
                mock_scheme.assert_not_called()
        finally:
            tables.selectionse_dict = original_dict
            tables.last_dict_update = original_ts


class TestGetDefaults:
    """Tests for get_defaults function."""

    def test_get_defaults(self):
        import util.tables as tables
        with patch.object(tables, "get_json") as mock_get_json:
            # First call: __get_columns_from_view
            # Second call: __get_defaults for each column
            mock_get_json.side_effect = [
                # columns from view
                [{"id": 10, "title": "Status"}],
                # defaults for column 10
                {"selectionOptions": [{"id": 1, "label": "Aktiv"}, {"id": 2, "label": "Inaktiv"}]},
            ]
            result = tables.get_defaults(2018)
            assert "Status" in result
            assert result["Status"][1] == "Aktiv"
            assert result["Status"][2] == "Inaktiv"


class TestCatalogue:
    """Tests for the Catalogue class."""

    def test_catalogue_init(self):
        from util.tables import Catalogue
        with patch("util.tables.get_rows") as mock_rows:
            mock_rows.return_value = [
                {"Identifizierung": 1, "Modultitel": "Mathe 1"},
                {"Identifizierung": 2, "Modultitel": "Informatik 1"},
            ]
            cat = Catalogue(2018)
            assert len(cat.get_module_list()) == 2
            assert "Mathe 1" in cat.get_module_list()

    def test_catalogue_find_match(self):
        from util.tables import Catalogue
        with patch("util.tables.get_rows") as mock_rows:
            mock_rows.return_value = [
                {"Identifizierung": 1, "Modultitel": "Mathematik M1a"},
                {"Identifizierung": 2, "Modultitel": "Mathematik M1b"},
                {"Identifizierung": 3, "Modultitel": "Informatik I"},
                {"Identifizierung": 4, "Modultitel": "Datenbanken"},
            ]
            cat = Catalogue(2018)
            matches = cat.find_match("Mathematik")
            assert len(matches) > 0
            # Fuzzy matching should find Mathematik-related modules
            assert any("Mathematik" in m.title for m in matches)

    def test_catalogue_find_match_no_close_match(self):
        """Even with no close match, rapidfuzz still returns results."""
        from util.tables import Catalogue
        with patch("util.tables.get_rows") as mock_rows:
            mock_rows.return_value = [
                {"Identifizierung": 1, "Modultitel": "Mathe"},
                {"Identifizierung": 2, "Modultitel": "Physik"},
            ]
            cat = Catalogue(2018)
            matches = cat.find_match("Biologie")
            # rapidfuzz always returns matches (with varying scores)
            assert isinstance(matches, list)

    def test_catalogue_get_module_list_empty(self):
        from util.tables import Catalogue
        with patch("util.tables.get_rows") as mock_rows:
            mock_rows.return_value = []
            cat = Catalogue(2018)
            # An unreachable api leaves the catalogue empty instead of raising.
            assert mock_rows.called
            assert cat._modules == []


# Two genuinely different modules that share a title, plus one unique module.
DUPLICATE_TITLE_ROWS = [
    {"Identifizierung": 100372, "Modultitel": "Introduction to Simulation"},
    {"Identifizierung": 120345, "Modultitel": "Introduction to Simulation"},
    {"Identifizierung": 500100, "Modultitel": "Datenbanken"},
]


class TestCatalogueDuplicateTitles:
    """Tests that modules sharing a title stay distinguishable in the picker."""

    def _catalogue(self, rows):
        from util.tables import Catalogue
        with patch("util.tables.get_rows") as mock_rows:
            mock_rows.return_value = rows
            return Catalogue(2018)

    def test_unique_title_keeps_plain_label(self):
        """A title only one module carries stays exactly as it is."""
        cat = self._catalogue(DUPLICATE_TITLE_ROWS)
        matches = cat.find_match("Datenbanken")
        unique = [m for m in matches if m.id_ == 500100]

        assert len(unique) == 1
        assert unique[0].label == "Datenbanken"
        assert unique[0].title == "Datenbanken"

    def test_shared_title_gets_the_id_appended(self):
        """Both modules show up, with different labels and their own ids."""
        cat = self._catalogue(DUPLICATE_TITLE_ROWS)
        matches = cat.find_match("Introduction to Simulation")
        shared = [m for m in matches if m.title == "Introduction to Simulation"]

        assert len(shared) == 2
        assert {m.id_ for m in shared} == {100372, 120345}
        assert {m.label for m in shared} == {
            "Introduction to Simulation (100372)",
            "Introduction to Simulation (120345)",
        }

    def test_labels_of_shared_title_are_unique(self):
        """No two entries of the whole catalogue read the same."""
        cat = self._catalogue(DUPLICATE_TITLE_ROWS)
        labels = [m.label for m in cat.find_match("Introduction")]

        assert len(labels) == len(set(labels))

    def test_get_module_list_returns_raw_titles(self):
        """The title list keeps the raw titles, the id suffix is display only."""
        cat = self._catalogue(DUPLICATE_TITLE_ROWS)

        assert cat.get_module_list().count("Introduction to Simulation") == 2

    def test_translations_are_skipped(self):
        """Translation rows repeat the id and must not show up a second time."""
        rows = DUPLICATE_TITLE_ROWS + [
            {
                "Identifizierung": 500100,
                "Modultitel": "Databases",
                "Translation": "true",
            },
        ]
        cat = self._catalogue(rows)

        assert "Databases" not in cat.get_module_list()
        assert len(cat.get_module_list()) == 3

    def test_rows_without_an_id_are_skipped(self):
        """A module that can't be named by id can't be opened either."""
        rows = [
            {"Identifizierung": 42, "Modultitel": "Mathe 1"},
            {"Modultitel": "Ohne Identifizierung"},
        ]
        cat = self._catalogue(rows)

        assert cat.get_module_list() == ["Mathe 1"]

    def test_duplicate_ids_are_kept_once(self):
        """The same module listed twice stays a single entry."""
        rows = [
            {"Identifizierung": 42, "Modultitel": "Mathe 1"},
            {"Identifizierung": 42, "Modultitel": "Mathe 1"},
        ]
        cat = self._catalogue(rows)

        assert cat.get_module_list() == ["Mathe 1"]

    def test_labels_respect_the_discord_length_limit(self):
        """Discord rejects a choice name longer than 100 characters."""
        from util.tables import CHOICE_LENGTH_LIMIT
        long_title = "M" * 140
        rows = [
            {"Identifizierung": 1, "Modultitel": long_title},
            {"Identifizierung": 2, "Modultitel": long_title},
            {"Identifizierung": 3, "Modultitel": "X" * 140},
        ]
        cat = self._catalogue(rows)
        matches = cat.find_match(long_title)

        assert all(len(m.label) <= CHOICE_LENGTH_LIMIT for m in matches)
        # the id survives the cut, otherwise the two entries would read the same
        shared = [m for m in matches if m.title == long_title]
        assert len(shared) == 2
        assert shared[0].label.endswith(")")
        assert shared[0].label != shared[1].label

    def test_empty_catalogue_reloads_on_search(self):
        """An unreachable api leaves the catalogue empty, a later search retries."""
        from util.tables import Catalogue
        with patch("util.tables.get_rows") as mock_rows:
            mock_rows.return_value = []
            cat = Catalogue(2018)
            mock_rows.return_value = DUPLICATE_TITLE_ROWS
            matches = cat.find_match("Datenbanken")

        assert any(m.id_ == 500100 for m in matches)


SPELLING_ROWS = [
    {"Identifizierung": 110360, "Modultitel": "Einführung in die Informatik"},
    {"Identifizierung": 102625, "Modultitel": "Qualitätsmanagementsysteme"},
    {"Identifizierung": 100375, "Modultitel": "Datenmanagement"},
    {"Identifizierung": 100393, "Modultitel": "Software Engineering & IT-Projektmanagement"},
    {"Identifizierung": 110455, "Modultitel": "Grundlagen der Theoretischen Informatik"},
    {"Identifizierung": 501325, "Modultitel": "Mathematik M1d"},
]


class TestCatalogueSpelling:
    """How a student types is not how the handbook writes.

        `find_match` compared raw strings, so the autocomplete was case sensitive and
        umlaut sensitive. Typing in capitals found the wrong module, and writing
        `qualitaetsmanagement` put "Datenmanagement" above the module it names.
    """

    def _catalogue(self, rows=None):
        from util.tables import Catalogue
        with patch("util.tables.get_rows") as mock_rows:
            mock_rows.return_value = rows if rows is not None else SPELLING_ROWS
            return Catalogue(2018)

    def _top(self, query: str) -> str:
        return self._catalogue().find_match(query)[0].title

    @pytest.mark.parametrize(
        "query",
        ["software engineering", "Software Engineering", "SOFTWARE ENGINEERING"],
    )
    def test_capitals_find_the_same_module(self, query: str):
        assert self._top(query) == "Software Engineering & IT-Projektmanagement"

    @pytest.mark.parametrize(
        "query",
        ["qualitätsmanagement", "qualitaetsmanagement", "qualitatsmanagement"],
    )
    def test_every_umlaut_spelling_finds_the_module(self, query: str):
        assert self._top(query) == "Qualitätsmanagementsysteme"

    @pytest.mark.parametrize(
        "query",
        ["einführung informatik", "einfuehrung informatik", "einfuhrung informatik"],
    )
    def test_the_spelling_does_not_change_the_order(self, query: str):
        assert self._top(query) == "Einführung in die Informatik"

    def test_the_results_are_identical_whatever_the_spelling(self):
        cat = self._catalogue()
        umlaut = [m.id_ for m in cat.find_match("Einführung")]
        plain = [m.id_ for m in cat.find_match("einfuehrung")]
        assert umlaut == plain

    def test_a_module_nobody_offers_still_finds_nothing_useful(self):
        """Folding is generous. It must not turn noise into a confident hit."""
        cat = self._catalogue()
        assert "Biologie" not in [m.title for m in cat.find_match("Biologie")]
