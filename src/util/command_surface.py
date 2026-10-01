""" Which commands OSCAR puts in front of a new student first.

    Every command the cogs register is in the discord picker. `/ansprechpartner`,
    `/fristen`, `/klausuren`, `/badges` and the rest are all typeable, and their German
    and English names both work.

    What this module decides is something smaller: which handful `/start` names, and in
    which order. The welcome screen used to list every command it could find, one
    component each, which is what pushed it past the forty component limit of a discord
    view and made `/start` raise an exception instead of answering.

    A newcomer cannot learn twenty names at once anyway. So `/start` names these eight,
    and points at `/help` for everything else. Two rules decide what belongs in here:

    * it needs an argument, so it cannot be a button (`/module`, `/compare`), or
    * it is typed in the middle of a conversation (`/here`, `/semesterplan`).

    `/my_data` breaks both rules and is in anyway. A student who wants their data
    deleted should not have to read a list first.
"""


# The commands `/start` names, as a set for membership tests.
CORE: frozenset[str] = frozenset({
    "start",          # the setup wizard, the first thing anybody runs
    "help",           # the way to everything that is not in this list
    "module",         # takes a module name, so it cannot be a button
    "here",           # the module of the current channel, typed while reading
    "filter",         # the search mask
    "compare",        # takes two or three module names
    "semesterplan",   # the plan a student edits all term
    "my_data",        # deleting your own data must not need a menu
})


# Commands only an administrator sees. They carry `default_permissions`, so discord
# hides them from every other member of the server.
ADMIN: frozenset[str] = frozenset({
    "version",
    "review_feedback",
})


# The same eight, in the order a student meets them. `/start` and `/help` print the
# list, and a set has no order to print.
CORE_ORDER: tuple[str, ...] = (
    "start",
    "module",
    "here",
    "filter",
    "compare",
    "semesterplan",
    "my_data",
    "help",
)
