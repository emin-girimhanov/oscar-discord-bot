""" Unit tests for weekly Code Golf challenges catalog."""

import datetime
from util.challenges import (
    Challenge,
    CHALLENGES,
    get_challenge_by_id,
    get_challenge_by_number,
    get_current_weekly_challenge,
)
from util.enums import LanguageCode


class TestChallengesCatalog:
    """Tests covering the challenge catalog structure and lookups."""

    def test_the_challenges_are_unique_and_numbered(self):
        challenges = CHALLENGES
        assert len(challenges) == 10

        ids = [c.id for c in challenges]
        assert len(ids) == len(set(ids))

        numbers = [c.number for c in challenges]
        assert numbers == list(range(1, 11))

    def test_get_challenge_by_id_found(self):
        c = get_challenge_by_id("fizzbuzz")
        assert c is not None
        assert c.number == 1
        assert "FizzBuzz" in c.title_de

    def test_get_challenge_by_id_not_found(self):
        assert get_challenge_by_id("non_existent_id") is None

    def test_get_challenge_by_number_found(self):
        c = get_challenge_by_number(2)
        assert c is not None
        assert c.id == "palindrome"

    def test_get_challenge_by_number_not_found(self):
        assert get_challenge_by_number(999) is None

    def test_localization_helpers(self):
        c = get_challenge_by_id("fizzbuzz")
        assert c is not None

        assert c.title(LanguageCode.DE) == c.title_de
        assert c.title(LanguageCode.EN) == c.title_en

        assert c.description(LanguageCode.DE) == c.description_de
        assert c.description(LanguageCode.EN) == c.description_en

        assert c.input_format(LanguageCode.DE) == c.input_format_de
        assert c.input_format(LanguageCode.EN) == c.input_format_en

        assert c.output_format(LanguageCode.DE) == c.output_format_de
        assert c.output_format(LanguageCode.EN) == c.output_format_en

    def test_weekly_rotation_predictable(self):
        # 2026-01-05 is in ISO week 2 of 2026
        d1 = datetime.date(2026, 1, 5)
        c1 = get_current_weekly_challenge(d1)
        # (2 - 1) % 10 = index 1 -> palindrome (number 2)
        assert c1.id == "palindrome"

        # 2026-01-12 is in ISO week 3 of 2026
        d2 = datetime.date(2026, 1, 12)
        c2 = get_current_weekly_challenge(d2)
        # (3 - 1) % 10 = index 2 -> fibonacci (number 3)
        assert c2.id == "fibonacci"

        # Calling without ref_date returns a valid Challenge
        current = get_current_weekly_challenge()
        assert isinstance(current, Challenge)
