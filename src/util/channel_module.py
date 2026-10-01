""" Turns the name of a discord channel into a module search.

    The FinEmporium server keeps one channel per module, named after the module in
    the way discord wants it: lowercase, words joined by a hyphen, sometimes an
    emoji in front. `#algorithmen-und-datenstrukturen` is the module "Algorithmen
    und Datenstrukturen", and `/here` should say so without anybody typing a name.

    Umlauts are the reason a channel finds nothing at all. A server writes
    `#schluesselkompetenzen`, the handbook writes "Schlüsselkompetenzen", and the
    two only meet because `util.matching` folds both onto the same key.

    A channel name is not a module title though. It is shortened (`mathe-1`), it
    abbreviates (`grundlagen-der-theo-informatik`) and it drops the roman numerals
    the module handbook uses. So the name is cleaned up, widened into a few
    spellings, and then handed to the fuzzy search that `/module` already uses.

    Nothing here promises a hit. When no title comes close the caller says so and
    points at `/module`, which is better than opening the wrong module.
"""

import re

from rapidfuzz import fuzz, process

from util.matching import match_key
from util.tables import Catalogue, ModuleMatch


# Below this score a title is not a match, it is noise. Measured against the real
# channel names of the FinEmporium server: every correct pair reached 88 or more,
# while `#allgemein`, `#memes` and `#trainingsmodul-smk` found nothing at all.
MATCH_THRESHOLD: float = 80.0

# Only a title that survives the comparison unchanged is opened without asking.
# Anything below that is a guess, and `#mathe-1` showed what a guess costs: it
# scores 96 against "Mathematik II", which is the wrong module.
CERTAIN_THRESHOLD: float = 100.0

# Even a perfect score is only certain when the next title is clearly behind.
# "Einführung in die Informatik" beats its part II by exactly this much.
CERTAIN_GAP: float = 5.0

# How many candidates a picker may offer. Discord allows 25, five is enough to read.
MAX_CANDIDATES: int = 5

# How much of the module title the channel name has to cover before a single hit is
# opened without asking. `fuzz.WRatio` scores a short word that sits inside a long
# title at exactly 90, so `#dev` reached "Clean Code Development" and `#code` reached
# it too. Both are ordinary chat channels on any server. Below this share the hit goes
# to the picker, where the student can see what OSCAR guessed.
MIN_COVERAGE: float = 0.5

# Short forms that appear in channel names but never in a module title. Keep this
# list to real abbreviations. A channel that needs its own entry here belongs in
# the channel topic instead, where a human can write the module name in full.
ABBREVIATIONS: dict[str, str] = {
    "mathe": "mathematik",
    "theo": "theoretische",
    "theoinf": "theoretische informatik",
    "wiss": "wissenschaftliches",
    "prog": "programmierung",
    "db": "datenbanken",
    "se": "software engineering",
    "swp": "softwareprojekt",
    "schlüko": "schlüsselkompetenzen",
    "schlueko": "schlüsselkompetenzen",
}

# The module handbook numbers a series in roman, a channel name in arabic.
ROMAN_NUMERALS: dict[str, str] = {
    "1": "i",
    "2": "ii",
    "3": "iii",
    "4": "iv",
    "5": "v",
    "6": "vi",
}


def to_query(channel_name: str) -> str:
    """ Cleans a discord channel name into plain words.

        Parameters:
            channel_name: The name as discord reports it, without the leading `#`.

        Returns:
            The words of the name, lowercase and separated by single spaces.
            The empty string when the name holds no word at all.
    """
    lowered: str = channel_name.casefold()
    # a trailing number may sit tight against the word, as in `schlüko1-2`
    spaced: str = re.sub(r"(?<=[^\W\d_])(?=\d)", " ", lowered)
    words: list[str] = re.findall(r"[^\W_]+", spaced, flags=re.UNICODE)
    expanded: list[str] = [ABBREVIATIONS.get(word, word) for word in words]
    return " ".join(expanded).strip()


def query_variants(channel_name: str) -> list[str]:
    """ Widens a channel name into the spellings a module title might use.

        A channel called `mathe-2` should find "Mathematik II" as well as
        "Mathematik M2d", so the arabic number is offered as a roman one too.

        Parameters:
            channel_name: The name as discord reports it.

        Returns:
            The spellings to search for, best guess first, without duplicates.
            An empty list when the name holds no word.
    """
    query: str = to_query(channel_name)
    if not query:
        return []

    variants: list[str] = [query]
    roman: str = " ".join(ROMAN_NUMERALS.get(word, word) for word in query.split())
    if roman != query:
        variants.append(roman)

    # `wiss-seminar` and the like carry a word that no title spells out. Dropping the
    # last word is a cheap way to still find the head of the title.
    words: list[str] = query.split()
    if len(words) > 2:
        variants.append(" ".join(words[:-1]))

    seen: set[str] = set()
    unique: list[str] = []
    for variant in variants:
        if variant not in seen:
            seen.add(variant)
            unique.append(variant)
    return unique


def find_candidates(
    catalogue: Catalogue, channel_name: str
) -> list[tuple[ModuleMatch, float]]:
    """ Looks for the modules a channel could be about.

        Parameters:
            catalogue: The module catalogue to search in.
            channel_name: The name of the channel, without the leading `#`.

        Returns:
            Up to `MAX_CANDIDATES` pairs of module and score, best first. Only
            modules scoring at least `MATCH_THRESHOLD` are in it, so an empty list
            means the channel is about no module OSCAR knows.
    """
    variants: list[str] = query_variants(channel_name)
    if not variants:
        return []

    modules: list[ModuleMatch] = catalogue.get_modules()
    titles: list[str] = [module.title for module in modules]

    # One module may win under several spellings. Keep its best score.
    best: dict[int, tuple[ModuleMatch, float]] = {}
    for variant in variants:
        # `match_key` lowercases, drops the punctuation and folds the umlauts.
        # Without the lowercasing "software engineering" never finds
        # "Software Engineering & ...", and without the folding
        # "#schluesselkompetenzen" never finds "Schlüsselkompetenzen".
        extracted = process.extract(
            variant,
            titles,
            scorer=fuzz.WRatio,
            processor=match_key,
            limit=MAX_CANDIDATES,
            score_cutoff=MATCH_THRESHOLD,
        )
        for _title, score, index in extracted:
            module = modules[index]
            previous = best.get(module.id_)
            if previous is None or score > previous[1]:
                best[module.id_] = (module, float(score))

    ranked: list[tuple[ModuleMatch, float]] = sorted(
        best.values(), key=lambda pair: (-pair[1], pair[0].label)
    )
    return ranked[:MAX_CANDIDATES]


def covers_the_title(channel_name: str, title: str) -> bool:
    """ Says whether the channel name is long enough to mean this title.

        Parameters:
            channel_name: The name of the channel, without the leading `#`.
            title: The module title of the candidate.

        Returns:
            `False` when the name covers less than `MIN_COVERAGE` of the title, as
            `#dev` does of "Clean Code Development". An empty title is never covered.
    """
    name_length: int = len(match_key(to_query(channel_name)))
    title_length: int = len(match_key(title))
    if title_length == 0:
        return False
    return name_length / title_length >= MIN_COVERAGE


def is_certain(
    candidates: list[tuple[ModuleMatch, float]], channel_name: str = ""
) -> bool:
    """ Says whether the best candidate may be opened without asking.

        Parameters:
            candidates: The result of `find_candidates`.
            channel_name: The channel the candidates came from. Without it the
                coverage cannot be judged and only the scores decide.

        Returns:
            `True` when the best hit covers enough of the title and is either the
            only one left, or matches the channel exactly and leads the next one by
            `CERTAIN_GAP`.
    """
    if not candidates:
        return False
    if channel_name and not covers_the_title(channel_name, candidates[0][0].title):
        return False
    if len(candidates) == 1:
        return True
    best_score: float = candidates[0][1]
    runner_up: float = candidates[1][1]
    return best_score >= CERTAIN_THRESHOLD and best_score - runner_up >= CERTAIN_GAP
