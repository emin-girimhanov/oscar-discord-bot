"""`/here` reads the channel name and has to land on the right module.

The FinEmporium server keeps one channel per module. The names are shortened
(`mathe-1`), abbreviated (`grundlagen-der-theo-informatik`) and written in arabic
numbers where the module handbook writes roman ones. The table in
`test_channel_matching` is the real channel list of that server, checked against the
real module titles of the FIN handbook.

Two failures matter, and they are not equally bad. Finding nothing is a nuisance, the
student types `/module` instead. Opening the wrong module without asking is worse,
because nothing on the screen says it is wrong. So a hit is only opened straight away
when the title survives the comparison unchanged and leads the next one clearly.
"""

from collections import Counter

import pytest

from util.channel_module import (
    CERTAIN_THRESHOLD,
    MATCH_THRESHOLD,
    MAX_CANDIDATES,
    covers_the_title,
    find_candidates,
    is_certain,
    query_variants,
    to_query,
)
from util.tables import ModuleMatch, _build_label


# A slice of the real handbook, picked so that every ambiguity of the real data is in
# it: two "Datenbanken", three "Grundlagen der Theoretischen Informatik", a title that
# contains another title, and modules nobody keeps a channel for.
TITLES: tuple[str, ...] = (
    "Algorithmen und Datenstrukturen",
    "Algorithmen und Programmierung",
    "Einführung in die Informatik - Algorithmen und Datenstrukturen I",
    "Database Concepts",
    "Datenbanken 1",
    "Datenbanken 2",
    "Einführung in die Informatik",
    "Einführung in die Informatik II",
    "Einführung in die Betriebswirtschaftslehre",
    "Grundlagen der Theoretischen Informatik",
    "Grundlagen der Theoretischen Informatik II",
    "Grundlagen der Theoretischen Informatik III",
    "Logik",
    "Logic",
    "Mathematik II",
    "Mathematik III",
    "Mathematik M1d",
    "Mathematik M2d",
    "Mathematik M3d",
    "Mathematik M5d",
    "Modellierung",
    "Modellierung und Simulation von Computernetzen",
    "Software Development Project",
    "Software-Development for Industrial Robotics",
    "Software Engineering & IT-Projektmanagement",
    "Software Engineering for technical applications",
    "Softwareprojekt (dual)",
    "Softwareprojekt RIOT OS",
    "Wissenschaftliches Seminar",
    "Wissenschaftliches Seminar (dual)",
    "Selected Chapters of IT Security 1",
)


class FakeCatalogue:
    """A catalogue that answers from `TITLES` and never touches the network."""

    def __init__(self, titles: tuple[str, ...] = TITLES):
        counts: Counter[str] = Counter(titles)
        self._modules: list[ModuleMatch] = [
            ModuleMatch(title, index + 1, _build_label(title, index + 1, counts[title] > 1))
            for index, title in enumerate(titles)
        ]

    def get_modules(self) -> list[ModuleMatch]:
        return list(self._modules)


@pytest.fixture(name="catalogue")
def catalogue_fixture() -> FakeCatalogue:
    return FakeCatalogue()


class TestToQuery:
    """The channel name has to become plain words before anything can match it."""

    @pytest.mark.parametrize(
        ("channel", "expected"),
        [
            ("datenbanken", "datenbanken"),
            ("algorithmen-und-datenstrukturen", "algorithmen und datenstrukturen"),
            ("software_engineering", "software engineering"),
            ("Datenbanken", "datenbanken"),
            ("einführung-in-die-informatik", "einführung in die informatik"),
        ],
    )
    def test_separators_and_case(self, channel: str, expected: str):
        assert to_query(channel) == expected

    def test_emoji_prefix_is_dropped(self):
        """Channel names often carry an emoji that no module title has."""
        assert to_query("📚-datenbanken") == "datenbanken"

    def test_number_glued_to_a_word_is_split(self):
        """`schlüko1-2` has to become words, not one unsearchable blob."""
        assert to_query("schlüko1-2") == "schlüsselkompetenzen 1 2"

    def test_abbreviation_is_expanded(self):
        assert to_query("mathe-1") == "mathematik 1"
        assert to_query("grundlagen-der-theo-informatik") == (
            "grundlagen der theoretische informatik"
        )

    def test_a_name_without_words_is_empty(self):
        assert to_query("🎉") == ""
        assert to_query("---") == ""


class TestQueryVariants:
    """One channel name is offered in the spellings a title might use."""

    def test_arabic_number_is_offered_as_roman(self):
        variants = query_variants("mathe-2")
        assert "mathematik 2" in variants
        assert "mathematik ii" in variants

    def test_the_plain_query_comes_first(self):
        assert query_variants("mathe-2")[0] == "mathematik 2"

    def test_a_long_name_may_drop_its_last_word(self):
        variants = query_variants("algorithmen-und-datenstrukturen")
        assert "algorithmen und" in variants

    def test_no_duplicates(self):
        variants = query_variants("logik")
        assert len(variants) == len(set(variants))

    def test_an_empty_name_yields_nothing(self):
        assert query_variants("🎉") == []


class TestChannelMatching:
    """The real channel list of the FinEmporium server against the real titles."""

    @pytest.mark.parametrize(
        ("channel", "expected_title"),
        [
            ("algorithmen-und-datenstrukturen", "Algorithmen und Datenstrukturen"),
            ("database-concepts", "Database Concepts"),
            ("einführung-in-die-informatik", "Einführung in die Informatik"),
            ("logik", "Logik"),
            ("modellierung", "Modellierung"),
            ("software-development-project", "Software Development Project"),
            ("wiss-seminar", "Wissenschaftliches Seminar"),
            ("grundlagen-der-theo-informatik", "Grundlagen der Theoretischen Informatik"),
            ("it-projektmanagement", "Software Engineering & IT-Projektmanagement"),
        ],
    )
    def test_best_candidate_is_the_right_module(
        self, catalogue: FakeCatalogue, channel: str, expected_title: str
    ):
        candidates = find_candidates(catalogue, channel)
        assert candidates, f"#{channel} found nothing"
        assert candidates[0][0].title == expected_title

    @pytest.mark.parametrize("channel", ["allgemein", "memes", "trainingsmodul-smk"])
    def test_a_channel_about_no_module_finds_nothing(
        self, catalogue: FakeCatalogue, channel: str
    ):
        """Better an honest miss than a module nobody asked for."""
        assert find_candidates(catalogue, channel) == []

    def test_an_emoji_prefix_does_not_break_the_match(self, catalogue: FakeCatalogue):
        with_emoji = find_candidates(catalogue, "📚-datenbanken")
        without = find_candidates(catalogue, "datenbanken")
        assert [m.id_ for m, _ in with_emoji] == [m.id_ for m, _ in without]

    def test_every_candidate_clears_the_threshold(self, catalogue: FakeCatalogue):
        for _module, score in find_candidates(catalogue, "datenbanken"):
            assert score >= MATCH_THRESHOLD

    def test_the_list_stays_short(self, catalogue: FakeCatalogue):
        assert len(find_candidates(catalogue, "mathe-1")) <= MAX_CANDIDATES

    def test_candidates_are_sorted_by_score(self, catalogue: FakeCatalogue):
        scores = [score for _module, score in find_candidates(catalogue, "mathe-2")]
        assert scores == sorted(scores, reverse=True)

    def test_a_module_appears_once_even_when_several_spellings_find_it(
        self, catalogue: FakeCatalogue
    ):
        """`mathe-2` searches as `mathematik 2` and as `mathematik ii`."""
        ids = [module.id_ for module, _score in find_candidates(catalogue, "mathe-2")]
        assert len(ids) == len(set(ids))


class TestIsCertain:
    """Opening the wrong module without asking is the failure to avoid."""

    def test_nothing_is_never_certain(self):
        assert is_certain([]) is False

    def test_a_single_candidate_is_certain(self, catalogue: FakeCatalogue):
        candidates = find_candidates(catalogue, "database-concepts")
        assert len(candidates) == 1
        assert is_certain(candidates) is True

    @pytest.mark.parametrize(
        "channel",
        ["algorithmen-und-datenstrukturen", "logik", "wiss-seminar"],
    )
    def test_a_clear_winner_opens_at_once(self, catalogue: FakeCatalogue, channel: str):
        assert is_certain(find_candidates(catalogue, channel)) is True

    @pytest.mark.parametrize("channel", ["datenbanken", "mathe-1", "software-engineering"])
    def test_an_ambiguous_channel_asks(self, catalogue: FakeCatalogue, channel: str):
        """`#datenbanken` is either Datenbanken 1 or 2, and `#mathe-1` scores 96
        against the wrong module. Both have to reach the picker."""
        candidates = find_candidates(catalogue, channel)
        assert len(candidates) > 1
        assert is_certain(candidates) is False

    def test_a_tie_at_the_top_is_never_certain(self):
        module_a = ModuleMatch("Datenbanken 1", 1, "Datenbanken 1")
        module_b = ModuleMatch("Datenbanken 2", 2, "Datenbanken 2")
        tie = [(module_a, CERTAIN_THRESHOLD), (module_b, CERTAIN_THRESHOLD)]
        assert is_certain(tie) is False


class TestUmlautChannels:
    """The three spellings of one channel name have to behave identically."""

    UMLAUT_TITLES = (
        "Einführung in die Betriebswirtschaftslehre",
        "Einführung in die Informatik",
    )

    @pytest.mark.parametrize(
        "channel",
        [
            "einführung-in-die-betriebswirtschaftslehre",
            "einfuehrung-in-die-betriebswirtschaftslehre",
            "einfuhrung-in-die-betriebswirtschaftslehre",
        ],
    )
    def test_all_three_spellings_find_the_module(
        self, catalogue: FakeCatalogue, channel: str
    ):
        candidates = find_candidates(catalogue, channel)
        assert candidates
        assert candidates[0][0].title == "Einführung in die Betriebswirtschaftslehre"

    def test_the_spelling_does_not_change_the_score(self, catalogue: FakeCatalogue):
        """Before the folding, `fuer` cost points and turned an open into a question."""
        scores = {
            find_candidates(catalogue, channel)[0][1]
            for channel in (
                "einführung-in-die-betriebswirtschaftslehre",
                "einfuehrung-in-die-betriebswirtschaftslehre",
                "einfuhrung-in-die-betriebswirtschaftslehre",
            )
        }
        assert len(scores) == 1

    def test_a_folded_channel_still_opens_at_once(self, catalogue: FakeCatalogue):
        assert is_certain(
            find_candidates(catalogue, "einfuehrung-in-die-betriebswirtschaftslehre")
        ) is True

    def test_folding_does_not_invent_a_match(self, catalogue: FakeCatalogue):
        """Noise must stay noise. `ue` inside a word is not a licence to match."""
        assert find_candidates(catalogue, "memes") == []
        assert find_candidates(catalogue, "allgemein") == []


class TestCoverage:
    """A short chat channel must not open a long module title without asking.

        `fuzz.WRatio` scores a short word sitting inside a long title at exactly 90,
        and that was the only candidate, so `#dev` opened "Clean Code Development"
        and `#code` opened it too. Both are ordinary chat channels.
    """

    SHORT_TITLES = (
        "Clean Code Development",
        "Software Testing",
        "Grundlagen des Maschinellen Lernens",
        "Datenbanken 1",
        "Compilerbau",
    )

    @pytest.fixture(name="short_catalogue")
    def short_catalogue_fixture(self) -> FakeCatalogue:
        return FakeCatalogue(self.SHORT_TITLES)

    @pytest.mark.parametrize("channel", ["dev", "code", "test", "lernen"])
    def test_a_chat_channel_never_opens_a_module(
        self, short_catalogue: FakeCatalogue, channel: str
    ):
        candidates = find_candidates(short_catalogue, channel)
        assert is_certain(candidates, channel) is False

    @pytest.mark.parametrize("channel", ["compilerbau", "datenbanken-1"])
    def test_a_channel_named_after_the_module_still_opens(
        self, short_catalogue: FakeCatalogue, channel: str
    ):
        assert is_certain(find_candidates(short_catalogue, channel), channel) is True

    def test_the_coverage_is_measured_on_the_expanded_name(self):
        """`#db` becomes `datenbanken`, and that is what has to cover the title."""
        assert covers_the_title("db-1", "Datenbanken 1") is True
        assert covers_the_title("dev", "Clean Code Development") is False

    def test_an_empty_title_is_never_covered(self):
        assert covers_the_title("datenbanken", "") is False

    def test_without_a_channel_name_only_the_scores_decide(self):
        """The old signature still works, for a caller that has no channel."""
        module = ModuleMatch("Clean Code Development", 1, "Clean Code Development")
        assert is_certain([(module, 90.0)]) is True
