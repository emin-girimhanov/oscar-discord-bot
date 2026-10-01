""" Curated catalog of weekly Code Golf challenges for OSCAR.

    Provides programming puzzles that rotate on a weekly schedule (ISO calendar week),
    supporting both German and English descriptions, input/output specifications,
    and archive lookup.
"""

from dataclasses import dataclass
import datetime

from util.enums import LanguageCode


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class Challenge:
    """Represents a weekly code golf challenge."""
    id: str
    number: int
    title_de: str
    title_en: str
    description_de: str
    description_en: str
    input_format_de: str
    input_format_en: str
    output_format_de: str
    output_format_en: str
    example_input: str
    example_output: str

    def title(self, lang: LanguageCode) -> str:
        """Returns the localized challenge title."""
        return self.title_de if lang == LanguageCode.DE else self.title_en

    def description(self, lang: LanguageCode) -> str:
        """Returns the localized challenge description."""
        return self.description_de if lang == LanguageCode.DE else self.description_en

    def input_format(self, lang: LanguageCode) -> str:
        """Returns the localized input format."""
        return self.input_format_de if lang == LanguageCode.DE else self.input_format_en

    def output_format(self, lang: LanguageCode) -> str:
        """Returns the localized output format."""
        return self.output_format_de if lang == LanguageCode.DE else self.output_format_en


CHALLENGES: tuple[Challenge, ...] = (
    Challenge(
        id="fizzbuzz",
        number=1,
        title_de="FizzBuzz Klassiker",
        title_en="Classic FizzBuzz",
        description_de=(
            "Gib die Zahlen von 1 bis 100 zeilenweise aus. Für Vielfache von 3 gib 'Fizz' "
            "aus, für Vielfache von 5 'Buzz' und für Vielfache von beiden 'FizzBuzz'."
        ),
        description_en=(
            "Print numbers 1 to 100 on separate lines. For multiples of 3 print 'Fizz', "
            "for multiples of 5 print 'Buzz', and for multiples of both print 'FizzBuzz'."
        ),
        input_format_de="Keine Eingabe erforderlich.",
        input_format_en="No input required.",
        output_format_de="Zahlen bzw. Wörter von 1 bis 100, jeweils getrennt durch Zeilenumbruch.",
        output_format_en="Numbers or words from 1 to 100, separated by newline.",
        example_input="-",
        example_output="1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n...",
    ),
    Challenge(
        id="palindrome",
        number=2,
        title_de="Palindrom-Prüfung",
        title_en="Palindrome Checker",
        description_de=(
            "Prüfe, ob ein gegebener String vorwärts und rückwärts gelesen identisch ist. "
            "Groß-/Kleinschreibung und Leerzeichen sollen ignoriert werden. "
            "Gib 'true' oder 'false' aus."
        ),
        description_en=(
            "Check if a given string reads the same forwards and backwards. "
            "Case and whitespace should be ignored. Print 'true' or 'false'."
        ),
        input_format_de="Ein String via stdin.",
        input_format_en="A single string via stdin.",
        output_format_de="'true' wenn Palindrom, andernfalls 'false'.",
        output_format_en="'true' if palindrome, otherwise 'false'.",
        example_input="A man a plan a canal Panama",
        example_output="true",
    ),
    Challenge(
        id="fibonacci",
        number=3,
        title_de="N-te Fibonacci-Zahl",
        title_en="N-th Fibonacci Number",
        description_de=(
            "Berechne für eine nicht-negative Ganzzahl N die N-te Fibonacci-Zahl. "
            "Es gilt F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)."
        ),
        description_en=(
            "Compute the N-th Fibonacci number for a non-negative integer N. "
            "Definitions: F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)."
        ),
        input_format_de="Eine Ganzzahl N via stdin.",
        input_format_en="An integer N via stdin.",
        output_format_de="Der Wert F(N).",
        output_format_en="The value of F(N).",
        example_input="10",
        example_output="55",
    ),
    Challenge(
        id="primes",
        number=4,
        title_de="Primzahlen bis N",
        title_en="Primes up to N",
        description_de=(
            "Gib alle Primzahlen bis einschließlich N aufsteigend aus, getrennt durch Leerzeichen."
        ),
        description_en=(
            "Print all prime numbers up to and including N in ascending order, "
            "separated by spaces."
        ),
        input_format_de="Eine positive Ganzzahl N (N >= 2) via stdin.",
        input_format_en="A positive integer N (N >= 2) via stdin.",
        output_format_de="Primzahlen getrennt durch ein Leerzeichen.",
        output_format_en="Prime numbers separated by a space.",
        example_input="20",
        example_output="2 3 5 7 11 13 17 19",
    ),
    Challenge(
        id="caesar",
        number=5,
        title_de="Cäsar-Chiffre (ROT13)",
        title_en="Caesar Cipher (ROT13)",
        description_de=(
            "Verschlüssele einen Text mit ROT13. Jeder Buchstabe (A-Z, a-z) wird um 13 Positionen "
            "im Alphabet verschoben. Alle anderen Zeichen bleiben unverändert."
        ),
        description_en=(
            "Encrypt a text using ROT13. Each letter (A-Z, a-z) is shifted by 13 positions "
            "in the alphabet. Non-letter characters remain unchanged."
        ),
        input_format_de="Ein Text via stdin.",
        input_format_en="A text string via stdin.",
        output_format_de="Der mit ROT13 verschlüsselte Text.",
        output_format_en="The ROT13 encrypted text.",
        example_input="Hello World!",
        example_output="Uryyb Jbeyq!",
    ),
    Challenge(
        id="vowels",
        number=6,
        title_de="Vokale zählen",
        title_en="Count Vowels",
        description_de=(
            "Zähle die Gesamtanzahl aller Vokale (a, e, i, o, u; case-insensitive) in einem Text."
        ),
        description_en=(
            "Count the total number of vowels (a, e, i, o, u; case-insensitive) in a text."
        ),
        input_format_de="Eine Zeichenkette via stdin.",
        input_format_en="A string via stdin.",
        output_format_de="Die Anzahl der Vokale als Ganzzahl.",
        output_format_en="The count of vowels as an integer.",
        example_input="Otto-von-Guericke-Universitaet",
        example_output="14",
    ),
    Challenge(
        id="collatz",
        number=7,
        title_de="Collatz-Folge",
        title_en="Collatz Sequence Steps",
        description_de=(
            "Berechne die Anzahl der Schritte, bis die Zahl 1 erreicht wird (3n+1 Problem). "
            "Wenn n gerade: n = n / 2. Wenn n ungerade: n = 3n + 1."
        ),
        description_en=(
            "Calculate how many steps it takes to reach 1 in the 3n+1 Collatz problem. "
            "If n is even: n = n / 2. If n is odd: n = 3n + 1."
        ),
        input_format_de="Eine positive Ganzzahl n via stdin.",
        input_format_en="A positive integer n via stdin.",
        output_format_de="Anzahl der Schritte als Ganzzahl (für 1 ist es 0 Schritte).",
        output_format_en="Number of steps as integer (for 1 it is 0 steps).",
        example_input="6",
        example_output="8",
    ),
    Challenge(
        id="anagram",
        number=8,
        title_de="Anagramm-Prüfer",
        title_en="Anagram Checker",
        description_de=(
            "Prüfe, ob zwei durch ein Komma getrennte Wörter Anagramme voneinander sind "
            "(gleiche Buchstaben mit gleicher Häufigkeit, case-insensitive). "
            "Ausgabe 'true' oder 'false'."
        ),
        description_en=(
            "Determine whether two comma-separated words are anagrams of each other "
            "(identical characters with identical counts, case-insensitive). "
            "Print 'true' or 'false'."
        ),
        input_format_de="Zwei Wörter getrennt durch ein Komma via stdin (z.B. 'listen,silent').",
        input_format_en="Two words separated by a comma via stdin (e.g. 'listen,silent').",
        output_format_de="'true' wenn Anagramm, andernfalls 'false'.",
        output_format_en="'true' if anagram, otherwise 'false'.",
        example_input="listen,silent",
        example_output="true",
    ),
    Challenge(
        id="rpn",
        number=9,
        title_de="Reverse Polish Notation (RPN)",
        title_en="Reverse Polish Notation (RPN)",
        description_de=(
            "Werte einen Postfix-Rechenausdruck (Reverse Polish Notation) mit Ganzzahlen und den "
            "Operatoren +, -, *, / (Ganzzahldivision) aus. Tokens sind durch Leerzeichen getrennt."
        ),
        description_en=(
            "Evaluate a postfix arithmetic expression (RPN) with integers and operators "
            "+, -, *, / (integer division). Tokens are space-separated."
        ),
        input_format_de="Ein Postfix-Ausdruck via stdin.",
        input_format_en="A postfix expression string via stdin.",
        output_format_de="Das Ergebnis als Ganzzahl.",
        output_format_en="The computed integer result.",
        example_input="3 4 + 2 *",
        example_output="14",
    ),
    Challenge(
        id="roman",
        number=10,
        title_de="Römische Zahlen",
        title_en="Roman Numerals",
        description_de=(
            "Konvertiere eine ganze Zahl zwischen 1 und 3999 in eine römische Zahl "
            "(I, V, X, L, C, D, M) in Standardnotation."
        ),
        description_en=(
            "Convert an integer between 1 and 3999 into a Roman numeral string "
            "(I, V, X, L, C, D, M) in standard notation."
        ),
        input_format_de="Eine Ganzzahl von 1 bis 3999 via stdin.",
        input_format_en="An integer from 1 to 3999 via stdin.",
        output_format_de="Die römische Zahl als String.",
        output_format_en="The Roman numeral string.",
        example_input="2026",
        example_output="MMXXVI",
    ),
)


def get_challenge_by_id(challenge_id: str) -> Challenge | None:
    """Looks up a challenge by its unique identifier."""
    for c in CHALLENGES:
        if c.id == challenge_id:
            return c
    return None


def get_challenge_by_number(number: int) -> Challenge | None:
    """Looks up a challenge by its number."""
    for c in CHALLENGES:
        if c.number == number:
            return c
    return None


def get_current_weekly_challenge(ref_date: datetime.date | None = None) -> Challenge:
    """Determines the active challenge for the current calendar week.

    Uses ISO calendar week to rotate predictably through all challenges.
    """
    today = ref_date or datetime.date.today()
    _, iso_week, _ = today.isocalendar()
    idx = (iso_week - 1) % len(CHALLENGES)
    return CHALLENGES[idx]
