""" One spelling rule for every fuzzy search in OSCAR.

    Three places compare a piece of text against a module title: the autocomplete of
    `/module`, the channel name that `/here` reads, and `/compare`. They have to agree
    on what counts as the same word, and until now they did not.

    Two differences cost a student the right module:

    * **Case.** `process.extract` compares raw strings unless it is given a processor.
      `SOFTWARE ENGINEERING` typed in capitals scored below "Grundlagen der
      Theoretischen Informatik" and never found "Software Engineering &
      IT-Projektmanagement".
    * **Umlauts.** A discord channel is called `#schluesselkompetenzen` or
      `#schlusselkompetenzen`, the handbook writes "Schlüsselkompetenzen", and
      rapidfuzz sees three different words. `qualitaetsmanagement` put
      "Datenmanagement" above "Qualitätsmanagementsysteme".

    So both sides of every comparison go through `match_key`. It lowercases, drops the
    punctuation and folds the umlaut in two steps: the letter becomes its plain form,
    then the `ue`, `ae`, `oe` and `ss` pairs collapse onto a single letter. All three
    spellings end up identical.

    The folding is lossy on purpose. "Masse" and "Maße" become the same key, and so do
    "Ingenieure" and a misspelling of it. That is the point: a search may be generous,
    it is the caller that decides whether a score is good enough to act on.
"""

from rapidfuzz import utils


# The umlaut written as one letter, and what it folds to.
UMLAUTS: dict[str, str] = {"ä": "a", "ö": "o", "ü": "u", "ß": "ss"}

# The same sounds written as two letters. Folded after `UMLAUTS`, so `ß` and `ss`
# reach the same key.
DIGRAPHS: dict[str, str] = {"ue": "u", "ae": "a", "oe": "o", "ss": "s"}


def fold_umlauts(text: str) -> str:
    """ Writes every spelling of an umlaut the same way.

        Parameters:
            text: Any lowercase text, a channel name or a module title.

        Returns:
            The text with `ä`, `ö`, `ü`, `ß` and their `ae`, `oe`, `ue`, `ss`
            spellings folded onto one plain letter each.
    """
    for umlaut, plain in UMLAUTS.items():
        text = text.replace(umlaut, plain)
    for digraph, plain in DIGRAPHS.items():
        text = text.replace(digraph, plain)
    return text


def match_key(text: str) -> str:
    """ The form rapidfuzz compares. Lowercase, no punctuation, no umlaut.

        Pass this as the `processor` of every `process.extract` call, so the query
        and the titles are always folded the same way.

        Parameters:
            text: A search term, a channel name or a module title.

        Returns:
            The comparable form of the text.
    """
    return fold_umlauts(utils.default_process(text))
