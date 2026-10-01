""" This module contains the communication logic with the modules database, via
    the tables (nextcloud) api.

    It's used for retrieving the latest module specific information.
"""

# import json
import os
import threading
import time
import traceback
from collections import Counter
from typing import Any, NamedTuple

import requests
import requests.auth
from dotenv import load_dotenv
from loguru import logger
from rapidfuzz import fuzz, process
from requests.models import HTTPBasicAuth

from util.enums import StudyCourse
from util.matching import match_key
from util.typed_dicts import TablesModuleDict

load_dotenv()



REQUEST_TIMEOUT: int = 30 # in seconds

tablesURL: str
tablesUsername: str
tablesPassword: str
auth: HTTPBasicAuth

try:
    tablesURL = os.environ["TABLES_URL"]
    tablesUsername = os.environ["TABLES_USERNAME"]
    tablesPassword = os.environ["TABLES_PASSWORD"]
except KeyError as exc:
    raise KeyError(traceback.format_exc()) from exc

auth = requests.auth.HTTPBasicAuth(tablesUsername, tablesPassword)

# works with and without a trailing slash in TABLES_URL
_API_BASE: str = f"{tablesURL.rstrip('/')}/api/1"

_CACHE_LOCK: threading.Lock = threading.Lock()
_CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL: int = int(os.environ.get("TABLES_CACHE_TTL", "600"))


# The table the bot reads for every module. Warmed at startup and kept warm, so a
# command never waits for the network.
MODULE_TABLE_ID: int = 720

# How long before the cache expires to fetch it again. A minute is plenty for a
# request that takes about one second, and it keeps the two from racing.
REFRESH_MARGIN: int = 60


def refresh_interval() -> int:
    """ How often the cache should be filled again.

        Returns:
            Seconds. Always at least a minute, so a small `TABLES_CACHE_TTL` cannot
            turn the warming into a flood of requests.
    """
    return max(60, CACHE_TTL - REFRESH_MARGIN)


def warm_cache() -> bool:
    """ Fetches everything a command needs, so it is in the cache before anybody asks.

        Reading the module table takes about a second, and reading the selection
        labels behind it another half. Both are plain blocking requests, so the first
        command after a restart, and the first one after the cache expires, held up
        the whole bot for **1.6 seconds**. Discord gives an interaction three seconds
        before it shows "the application did not respond".

        Call this from a background thread at startup and every `refresh_interval`
        seconds. It is safe to call at any time and never raises.

        Returns:
            `True` when the module table has rows afterwards.
    """
    started = time.time()
    rows = get_rows(MODULE_TABLE_ID)
    # fills `selectionse_dict`, which is what turns an id into a readable label
    _ = get_value_by_id(-1, "fachsemester")
    took = time.time() - started

    if not rows:
        logger.warning(f"Could not warm the module table, it came back empty ({took:.1f}s)")
        return False
    logger.info(f"Module table warm: {len(rows)} rows in {took:.1f}s")
    return True


def clear_tables_cache() -> None:
    """ Clears the in-memory cache for Tables API calls and resets selection dictionary."""
    # pylint: disable=W0603 # (global-statement)
    global last_dict_update, selectionse_dict
    with _CACHE_LOCK:
        _CACHE.clear()
        last_dict_update = -1
        selectionse_dict = {}


def _get_from_cache(key: str) -> Any | None:
    """ Retrieves an item from the in-memory cache if not expired.

        Parameters:
            key: Unique key for cached item.

        Returns:
            Cached data or None if missing or expired.
    """
    with _CACHE_LOCK:
        if key in _CACHE:
            ts, data = _CACHE[key]
            if time.time() - ts < CACHE_TTL:
                return data
            del _CACHE[key]
    return None


def _set_in_cache(key: str, data: Any) -> None:
    """ Stores an item in the in-memory cache.

        Parameters:
            key: Unique key for cached item.
            data: Data to store.
    """
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), data)


def get_json(url: str) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
    """ Sends a GET request to the specified URL and returns the JSON response.

        Parameters:
            url: The URL to send the GET request to.

        Returns:
            The JSON response if the request is successful, otherwise an empty dictionary.
            Never raises, so an unreachable Tables API can't take a whole cog down.
    """
    try:
        response = requests.get(
            url,
            auth=auth,
            timeout=REQUEST_TIMEOUT
        )
        if response.ok:
            return response.json()  # pyright: ignore[reportAny]
        logger.warning(f"Tables API request to '{url}' failed with status {response.status_code}")
    except (requests.RequestException, ValueError):
        logger.exception(f"Tables API request to '{url}' failed")
    return {}


def __get_columns_from_view(view_id: int) -> dict[Any, Any]:  # pyright: ignore[reportExplicitAny]
    """ Retrieves the columns from a specific view.

        Parameters:
            view_id: The ID of the view to retrieve columns from.

        Returns:
            A dictionary mapping column IDs to column titles.
    """

    data = get_json(f"{_API_BASE}/views/{view_id}/columns")    # pyright: ignore[reportAny]
    return {col["id"]: col["title"] for col in data}  # pyright: ignore[reportAny]


def __get_rows_from_view(view_id: int) -> list[Any]:  # pyright: ignore[reportExplicitAny]
    """ Retrieves the rows from a specific view.

        Parameters:
            view_id: The ID of the view to retrieve rows from.

        Returns:
            A list of rows from the view.
    """
    data = get_json(f"{_API_BASE}/views/{view_id}/rows")  # pyright: ignore[reportAny]
    return [row["data"] for row in data]  # pyright: ignore[reportAny]


def get_rows_from_view(view_id: int) -> list[dict[str, Any]]:  # pyright: ignore[reportExplicitAny]
    """ Retrieves the rows from a specific view and formats them.

        Parameters:
            view_id: The ID of the view to retrieve rows from.

        Returns:
            A list of dictionaries representing the formatted rows.
    """
    cache_key = f"view_rows:{view_id}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return [row.copy() for row in cached]

    columns = __get_columns_from_view(view_id)
    rows_data = __get_rows_from_view(view_id)

    result_rows = []
    for row in rows_data:  # pyright: ignore[reportAny]
        result: dict[str, Any] = {}  # pyright: ignore[reportExplicitAny]
        for cell in row:  # pyright: ignore[reportAny]
            title = (  # pyright: ignore[reportAny]
                columns[cell["columnId"]]  # pyright: ignore[reportAny]
                .replace("Modultitel ", "Modultitel")
                .replace("Modultitel(englisch)", "Modultitel (englisch)")
            )
            result[title] = cell["value"]
        result_rows.append(result)  # pyright: ignore[reportUnknownMemberType]
    if result_rows:
        _set_in_cache(cache_key, result_rows)
    return result_rows  # pyright: ignore[reportUnknownVariableType]


def get_table_ids() -> list[dict[str, Any]]:  # pyright: ignore[reportExplicitAny]
    """ Retrieves the IDs and names of all tables.

        Returns:
            A list of dictionaries containing table IDs, names, and ownership information.
    """
    data = get_json(f"{_API_BASE}/tables")  # pyright: ignore[reportAny]
    # pylint: disable=C0301 # (line-too-long)
    return [{"id": t["id"], "name": t["title"], "owner": t["ownership"]} for t in data]  # pyright: ignore[reportAny]


def get_rows(table_id: int) -> list[TablesModuleDict]:
    """ Retrieves the rows from a specific table.

        Parameters:
            table_id: The ID of the table to retrieve rows from.

        Returns:
            A list of dictionaries representing the rows of the table.
    """
    cache_key = f"rows:{table_id}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return [row.copy() for row in cached]  # pyright: ignore[reportReturnType]

    data: list[list[Any]] = get_json(  # pyright: ignore[reportExplicitAny, reportAny]
        f"{_API_BASE}/tables/{table_id}/rows/simple"
    )
    if not data:
        return []

    keys: list[str] = data[0]

    rows: list[TablesModuleDict] = [  # pyright: ignore[reportReturnType]
        dict(zip(keys, row)) for row in data[1:]
    ]
    if rows:
        _set_in_cache(cache_key, rows)
    return rows


def __get_defaults(col_id: int) -> dict[Any, Any]:  # pyright: ignore[reportExplicitAny]
    """ Retrieves the default options for a specific column.

        Parameters:
            col_id: The ID of the column to retrieve defaults from.

        Returns:
            A dictionary mapping option IDs to their labels.
    """
    data = get_json(f"{_API_BASE}/columns/{col_id}")  # pyright: ignore[reportAny]
    # pylint: disable=C0301 # (line-too-long)
    return {opt["id"]: opt["label"] for opt in data.get("selectionOptions", [])}  # pyright: ignore[reportAny]


def get_defaults(view_id: int) -> dict[Any, Any]:  # pyright: ignore[reportExplicitAny]
    """ Retrieves the default options for columns in a specific view.

        Parameters:
            view_id: The ID of the view to retrieve defaults from.

        Returns:
            A dictionary mapping column titles to their default options.
    """
    cols = __get_columns_from_view(view_id)
    return {cols[key]: __get_defaults(key) for key in cols.keys()}  # pyright: ignore[reportAny]


def get_scheme(table_id: int) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
    """ Retrieves the scheme for a specific table.

        Parameters:
            table_id: The ID of the table to retrieve scheme from.

        Returns:
            An object representing the json data.
    """
    cache_key = f"scheme:{table_id}"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached

    data = get_json(f"{_API_BASE}/tables/{table_id}/scheme")  # pyright: ignore[reportAny]
    result = data if data else []  # pyright: ignore[reportAny]
    if result:
        _set_in_cache(cache_key, result)
    return result



selectionse_dict: dict[str, dict[int, str]] = {}
last_dict_update: int = -1  # pylint: disable=C0103

def __update_selections_dict(table_id: int = 720):
    """ Updates the global selections dictionary for a specific view,
        if the `LAST_DICT_UPDATE` has been longer than one day.

        Parameters:
            view_id: The ID of the view to update selections from.
    """
    # pylint: disable=W0603 # (global-statement)
    global last_dict_update, selectionse_dict
    if time.time() - last_dict_update < 86400:  # 86400 seconds = 1 day
        return
    table_scheme = get_scheme(table_id)  # pyright: ignore[reportAny]
    if not isinstance(table_scheme, dict) or "columns" not in table_scheme:
        # keep the old values and retry on the next call
        return
    last_dict_update = int(time.time())
    selectionse_dict = {}
    for column in table_scheme["columns"]:  # pyright: ignore[reportAny]
        if column["type"] == "selection":
            selectionse_dict[str(column["title"]).lower()] = {  # pyright: ignore[reportAny]
                # pylint: disable=C0301 # (line-too-long)
                int(opt["id"]): str(opt["label"]) for opt in column["selectionOptions"]  # pyright: ignore[reportAny]
            }



def get_value_by_id(id_: int, key: str) -> str:
    """ Retrieves the value of a specific key for a module identified by its ID.

        Parameters:
            id_: The id value for the dictionary.
            key: The key whose dictionary is to be retrieved.

        Returns:
            The value associated with the specified key for the module with the given ID.
            or: the id as a string, if the key (or id) is not found.
    """
    __update_selections_dict()

    if selectionse_dict.keys().__contains__(key.lower()):
        if id_ in selectionse_dict[key.lower()].keys():
            return selectionse_dict[key.lower()][id_]
    return str(id_)


def get_usability_name(study_course: StudyCourse, id_: int) -> str:
    """ Retrieves the name for a specific usability category byb its ID
        Parameters:
            study_course: The current study course
            id:           The id of the usability category 
    """
    # 'verwendbarkeit b.sc. inf (bilingual)
    # BSC_INF_BILINGUAL
    segments: list[str] = str(study_course.name).lower().split("_")
    key: str = "verwendbarkeit"
    if len(segments) >= 1:
        # convert bsc or msc to b.sc. or m.sc.
        res: str = ""
        if len(segments[0]) >= 1:
            res += f"{segments[0][0]}."
            if len(segments[0]) >= 2:
                res += f"{segments[0][1:]}."
        key += f" {res}"
    if len(segments) >= 2:
        key += f" {segments[1]}"
    if len(segments) >= 3:
        key += f" ({' '.join(segments[2:])})"
    return get_value_by_id(id_, key)



CHOICE_LENGTH_LIMIT: int = 100  # discord caps a choice name and value at 100 characters


class ModuleMatch(NamedTuple):
    """ One candidate of a module search.

        `title` is the raw module title and is what the fuzzy search works on.
        `label` is what the user reads. It carries the id as a suffix when other
        modules share the same title, and equals `title` otherwise.
        `id_` names the module without ambiguity, so a picked entry always opens
        the module the user saw.
    """
    title: str
    id_: int
    label: str


def _build_label(title: str, id_: int, ambiguous: bool) -> str:
    """ Builds the text shown for one module in the picker.

        Parameters:
            title: The raw module title.
            id_: The identification number of the module.
            ambiguous: Whether another module carries the same title.

        Returns:
            The title on its own, or the title plus the id, cut to discords limit.
    """
    if not ambiguous:
        return title[:CHOICE_LENGTH_LIMIT]
    suffix: str = f" ({id_})"
    return f"{title[:CHOICE_LENGTH_LIMIT - len(suffix)]}{suffix}"


class Catalogue:
    """ Class for creation of a Module Catalog and searching for specific module names"""
    _module_catalogue: list[TablesModuleDict]
    _modules: list[ModuleMatch]

    def __init__(self, view: int):
        """ Initializes the Catalogue with modules from a specific view.

            Parameters:
                view: The ID of the view to initialize the catalogue from.
        """
        self._view: int = view
        self._module_catalogue = []
        self._modules = []
        self._load()

    def _load(self):
        """ (Re)loads the titles. Stays empty if the Tables API is unreachable.

            Rows without an id are skipped, because a module that can't be named by
            id can't be opened either. Titles shared by several modules get the id
            appended, so the picker stays readable for the unique majority.
        """
        self._module_catalogue = get_rows(self._view)

        entries: list[tuple[str, int]] = []
        seen_ids: set[int] = set()
        for data in self._module_catalogue:
            title: str = str(data.get("Modultitel", ""))
            id_: int | None = data.get("Identifizierung", None)
            if not title or id_ is None:
                continue
            if str(data.get("Translation", "")).lower() == "true":
                continue
            if id_ in seen_ids:
                continue
            seen_ids.add(id_)
            entries.append((title, id_))

        title_counts: Counter[str] = Counter(title for title, _ in entries)
        self._modules = [
            ModuleMatch(title, id_, _build_label(title, id_, title_counts[title] > 1))
            for title, id_ in entries
        ]

    def find_match(self, module_name: str) -> list[ModuleMatch]:
        """ Finds matches for a given module name in the catalogue.

            Parameters:
                module_name: The name of the module to find matches for.

            Returns:
                A list of matches, each with the label to show and the id to open.
        """
        if not self._modules:
            self._load()
        titles: list[str] = [entry.title for entry in self._modules]
        # Without `match_key` the comparison is case sensitive and umlaut sensitive.
        # `SOFTWARE ENGINEERING` found "Grundlagen der Theoretischen Informatik", and
        # `qualitaetsmanagement` put "Datenmanagement" above the module it names.
        matches = process.extract(
            module_name,
            titles,
            scorer=fuzz.WRatio,
            processor=match_key,
        )
        return [self._modules[match[2]] for match in matches]

    def get_module_list(self) -> list[str]:
        """ Returns a list of all module titles"""
        if not self._modules:
            self._load()
        return [entry.title for entry in self._modules]

    def get_modules(self) -> list[ModuleMatch]:
        """ Every module of the catalogue.

            `find_match` throws the scores away, which is right for the autocomplete
            of `/module`. `/here` has to know how close a hit is before it opens
            anything, so it needs the entries themselves.

            Returns:
                A copy of the catalogue, so a caller cannot reorder the cache.
        """
        if not self._modules:
            self._load()
        return list(self._modules)









if __name__ == "__main__":

    print("\nTable ids:")
    print(get_table_ids())
    # 'id': 1430, 'name': 'Willkommen zu OVGU-Cloud-Tabellen!',
    # 'id': 720,  'name': 'FIN Moduldatenbank',

    print()
    # print(get_rows(1430))
    print(get_rows(720)[:1])

    # view = get_rows_from_view(2018)
    # print(view)

    # Identifizierung + Modulsprache ist primary key

    print()
    print(get_scheme(720)["columns"][27+1]) # index 27 == 'Verwendbarkeit B.Sc. INF'
    # 27  ==  "Verwendbarkeit B.Sc. INF": list[int],
    # 28  ==  "Verwendbarkeit B.Sc. CV": list[int],
    # 29  ==  "Verwendbarkeit B.Sc. INGINF": list[int],
    # 30  ==  "Verwendbarkeit B.Sc. WIF": list[int],
    # 31  ==  "Verwendbarkeit B.Sc. INF (bilingual)": list[int],
    # 32  ==  "Verwendbarkeit M.Sc. INF": list[int],
    # 33  ==  "Verwendbarkeit M.Sc. INGINF": list[int],
    # 34  ==  "Verwendbarkeit M.Sc. WIF": list[int],
    # 35  ==  "Verwendbarkeit M.Sc. DKE": list[int],
    # 36  ==  "Verwendbarkeit M.Sc. DE": list[int],
    # 37  ==  "Verwendbarkeit M.Sc. VC": list[int],

    # save databse data to file for easy access
    # with open("module_database_rows.json", "w", encoding="utf8") as file:
    #     json.dump(get_rows(720), file)
    # with open("module_database_scheme.json", "w", encoding="utf8") as file:
    #     json.dump(get_scheme(720), file)

    print()
    print(get_usability_name(StudyCourse.BSC_CV, 4))
