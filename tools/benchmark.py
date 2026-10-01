""" Measures what a student waits for, against the live data.

    A discord interaction has **three seconds** before the student is told the
    application did not respond. This script says how much of that budget each step
    spends. It found the one that mattered:

        /module datenbanken, cold cache    1620 ms
        /module datenbanken, warm cache       5 ms

    Reading the module table is a blocking request made from inside a command handler,
    so a cold cache stopped the whole bot, not only that one command. `warm_cache` in
    `util.tables` fills it before anybody asks. Everything else is under ten
    milliseconds and needs no attention.

    Run it from the repository root, inside the university network:

        python tools/benchmark.py

    It needs the Nextcloud Tables API, so it is not part of the pipeline. Numbers move
    with the network, so read the shape rather than the exact figure: the cold column
    is a network request, the warm column is a dict lookup, and nothing in between
    should be slow.
"""

import asyncio
import time
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from util.enums import LanguageCode


# Anything slower than this in the warm column is worth looking at.
SLOW_MS: float = 50.0

# How often to run each step. The fastest round is the honest one, because the slow
# rounds are the garbage collector and the other programs on the machine.
ROUNDS: int = 3

USER: int = 4711


def measure(label: str, work: Callable[[], Any], rounds: int = ROUNDS) -> Any:
    """ Runs one step and prints how long its fastest round took.

        Parameters:
            label: What to call the step in the report.
            work: The step. Its return value is handed back.
            rounds: How often to run it.

        Returns:
            Whatever `work` returned on the last round.
    """
    best: float | None = None
    result: Any = None
    for _ in range(rounds):
        started = time.perf_counter()
        result = work()
        taken = time.perf_counter() - started
        best = taken if best is None else min(best, taken)

    milliseconds = (best or 0) * 1000
    mark = "  <-- slow" if milliseconds > SLOW_MS else ""
    print(f"  {label:<44} {milliseconds:>9.1f} ms{mark}")
    return result


async def main() -> int:
    """ Prints the report. Returns 0, the numbers are for a human to read."""
    # pylint: disable=import-outside-toplevel, too-many-locals
    from oscar.ui.module_view import ModuleView
    from oscar.ui.select_view import PaginatedModuleView, SelectView
    from oscar.ui.suggest_view import SuggestView
    from util.filter_options import apply_selection
    from util.module import Module, get_module_list
    from util.modules_filter import ModulesFilter
    from util.suggestions import get_module_suggestions
    from util import tables
    from util.tables import Catalogue, clear_tables_cache, get_rows, warm_cache

    print("=== cold, what a command paid before the cache was warmed ===")
    clear_tables_cache()
    tables.last_dict_update = -1
    measure("warm_cache()  the whole cold path", warm_cache, rounds=1)

    print("\n=== warm, what a command pays now ===")
    measure("get_rows(720)", lambda: get_rows(720))
    catalogue = measure("Catalogue(720)", lambda: Catalogue(720))
    measure("find_match('datenbanken')", lambda: catalogue.find_match("datenbanken"))

    matches = catalogue.find_match("datenbanken")
    if not matches:
        print("the catalogue is empty, check .env")
        return 1
    module_id = matches[0].id_
    module = measure(f"Module.from_id({module_id})", lambda: Module.from_id(module_id))
    modules = measure("get_module_list()", get_module_list)
    print(f"       {len(modules)} modules")

    with patch("util.database.get_user_language", return_value=LanguageCode.DE):
        measure("ModuleView       the module card", lambda: ModuleView(USER, module))
        measure("SelectView       the filter mask", lambda: SelectView(USER))
        measure(
            "PaginatedModuleView  the result list",
            lambda: PaginatedModuleView(modules, user_id=USER),
        )
        measure(
            "SuggestView",
            lambda: SuggestView(user_id=USER, default_language=LanguageCode.DE),
        )

    measure(
        "get_module_suggestions('ALL')",
        lambda: get_module_suggestions(user_id=USER, category_key="ALL"),
    )
    selection = {"cp": ["cp_eq_5"], "sws": ["sws_gt_3"]}
    hits = measure(
        "apply_selection  /filter end to end",
        lambda: apply_selection(selection, ModulesFilter(remove_invalid=True)),
    )
    print(f"       {len(hits)} modules matched")

    print(f"\nA discord interaction has 3000 ms. Anything over {SLOW_MS:.0f} ms is marked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
