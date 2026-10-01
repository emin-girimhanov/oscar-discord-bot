""" This module makes text a student typed safe to show to other students.

    A review and the language of a code golf entry are free text, and OSCAR prints
    them into its own messages. Discord renders markdown in those, so `[Altklausur]
    (https://evil.example)` became a link that looked as if OSCAR had written it, and
    a `# Ankündigung` on a new line became a heading in the bot's voice.

    The text stays readable. Only what Discord would turn into formatting, a hidden
    link or a ping is taken out.
"""

import re


# Every character Discord reads as markup. A backslash in front makes it print as
# itself. `<` and `>` are in here because `<@id>` is a ping and `<https://…>` a link.
_MARKUP: re.Pattern[str] = re.compile(r"([\\*_~|`\[\]<>#])")

# Goes after every `@`, so `@everyone` and `@here` are words and not pings.
_ZERO_WIDTH_SPACE: str = chr(0x200B)


def plain(text: str) -> str:
    """ Turns typed text into one line that Discord shows exactly as it was typed.

        Parameters:
            text: What the student wrote.

        Returns:
            The same words on a single line, without working markdown, masked links
            or mentions. A bare address stays visible, so the reader sees where it
            goes. An underscore in it is escaped like any other, which is the price
            for not having to guess where an address ends.
    """
    one_line: str = " ".join(text.split())
    return _MARKUP.sub(r"\\\1", one_line).replace("@", f"@{_ZERO_WIDTH_SPACE}")
