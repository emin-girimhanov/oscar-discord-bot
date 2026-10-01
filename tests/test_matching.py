"""One spelling rule, used by every fuzzy search in OSCAR.

Two differences used to cost a student the right module. Capital letters, because
`process.extract` compares raw strings unless it is given a processor, so
`SOFTWARE ENGINEERING` found "Grundlagen der Theoretischen Informatik". And umlauts,
because a discord channel is called `#schluesselkompetenzen` while the handbook writes
"Schlüsselkompetenzen".

`match_key` folds both sides of every comparison the same way. These tests pin down
what it folds, and what it must leave alone.
"""

import pytest

from util.matching import fold_umlauts, match_key


class TestFoldUmlauts:
    """Every spelling of one word has to end up as one key."""

    @pytest.mark.parametrize(
        ("written", "folded"),
        [
            ("schlüsselkompetenzen", "schluselkompetenzen"),
            ("schluesselkompetenzen", "schluselkompetenzen"),
            ("schlusselkompetenzen", "schluselkompetenzen"),
            ("für", "fur"),
            ("fuer", "fur"),
            ("ausgewählte", "ausgewahlte"),
            ("ausgewaehlte", "ausgewahlte"),
            ("größe", "grose"),
            ("groesse", "grose"),
            ("einführung", "einfuhrung"),
            ("einfuehrung", "einfuhrung"),
        ],
    )
    def test_every_spelling_folds_onto_the_same_word(self, written: str, folded: str):
        assert fold_umlauts(written) == folded

    def test_a_word_without_an_umlaut_is_untouched(self):
        assert fold_umlauts("datenbanken") == "datenbanken"

    def test_an_empty_text_stays_empty(self):
        assert fold_umlauts("") == ""

    def test_the_sharp_s_reaches_the_same_key_as_a_double_s(self):
        assert fold_umlauts("maße") == fold_umlauts("masse")


class TestMatchKey:
    """What rapidfuzz actually compares."""

    def test_capitals_do_not_matter(self):
        """`SOFTWARE ENGINEERING` used to find the wrong module."""
        assert match_key("SOFTWARE ENGINEERING") == match_key("software engineering")

    def test_punctuation_does_not_matter(self):
        assert match_key("Einführung in die Informatik!") == match_key("einfuehrung in die informatik")

    def test_it_is_the_same_on_both_sides(self):
        """The query and the module title go through one function, not two."""
        assert match_key("Schlüsselkompetenzen") == match_key("schluesselkompetenzen")

    def test_two_different_modules_keep_different_keys(self):
        """Folding is generous, not blind."""
        assert match_key("Datenbanken 1") != match_key("Datenbanken 2")
        assert match_key("Logik") != match_key("Logistik")

    def test_a_hyphen_is_not_a_letter(self):
        assert match_key("In-Memory") == match_key("in memory")
