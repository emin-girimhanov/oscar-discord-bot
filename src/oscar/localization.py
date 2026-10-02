""" One command, two names: discord shows the one that fits the language of the client.

    Four features were registered twice, once under a German and once under an English
    name: `/fristen` and `/deadlines`, `/ansprechpartner` and `/contacts`, `/lms` and
    `/elearning`, `/suggest` and `/recommend`. Every student saw both in the picker and
    had to work out that they were the same thing.

    Discord can carry translations of a command name. A client set to German then
    shows `/fristen`, every other client shows `/deadlines`, and it is one command.
    `discord.py` asks a `Translator` for those translations while it syncs.

    The German text travels with the string itself:

    ```python
    @app_commands.command(
        name=locale_str("deadlines", de="fristen"),
        description=locale_str("Roughly what is due when", de="Was ungefähr wann ansteht"),
    )
    ```

    **Which name a student sees follows the language of their discord app**, not the
    language they picked in `/start`. Discord decides that before OSCAR is asked
    anything, and it is the same for every bot.

    `util.command_surface.TWO_NAMES` lists the pairs for `/help`, which has to print a
    name without knowing the client.
"""

import discord
from discord import app_commands
from discord.app_commands import TranslationContextTypes, locale_str


class GermanNames(app_commands.Translator):
    """ Hands discord the German text of a string that carries one."""

    async def translate(
        self,
        string: locale_str,
        locale: discord.Locale,
        context: TranslationContextTypes,
    ) -> str | None:
        """ Returns the German text for a German client, and nothing for anybody else.

            Parameters:
                string: The text discord.py is about to send, with its extras.
                locale: The language discord asks a translation for.
                context: Where the string is used, not needed here.

            Returns:
                The `de` extra of the string for `discord.Locale.german`. `None` for
                every other language and for a string without that extra, which makes
                discord fall back to the text itself.
        """
        if locale is discord.Locale.german:
            german = string.extras.get("de")
            return str(german) if german else None
        return None
