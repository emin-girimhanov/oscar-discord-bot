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
            intents=intents  # pyright: ignore[reportArgumentType]
        )
    # pylint: disable=W0718 # (broad-exception-caught)
    except Exception:
        sys.exit(1)

    oscar.setup_bot()
    oscar.run(oscar.bot_token)


if __name__ == "__main__":
    main()
