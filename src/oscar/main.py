"""This module starts the bot setup"""

import sys

import discord

from oscar.oscar import Oscar


def main():
    """Main method"""
    intents = discord.Intents.default()
    intents.message_content = True

    try:
        oscar: Oscar = Oscar(
            command_prefix="!",  # pyright: ignore[reportArgumentType]
            intents=intents,  # pyright: ignore[reportArgumentType]
            # OSCAR prints text students typed. Nothing it says pings anybody unless
            # the message asks for it, the study group thread is the one that does.
            allowed_mentions=discord.AllowedMentions.none(),  # pyright: ignore[reportArgumentType]
        )
    except Exception:  # pylint: disable=broad-exception-caught
        sys.exit(1)

    oscar.setup_bot()
    oscar.run(oscar.bot_token)


if __name__ == "__main__":
    main()
