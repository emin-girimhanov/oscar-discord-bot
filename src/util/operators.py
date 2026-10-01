""" This module says who may use the commands that are not meant for students.

    The check used to be "an administrator of the server the command was typed in".
    That held while OSCAR lived on one server. It is a public bot with global commands
    now, so anybody can invite it to a server of their own, where they are the
    administrator. From there `/review_feedback` handed out every feedback text and the
    discord id next to it, and `!resync` let a stranger make the bot resync its
    commands until discord rate limited it.

    An operator is therefore one of three: a developer named here, the owner of the
    discord application, or an administrator of the **home server**, the one
    `DISCORD_SERVER_ID` names. Being an administrator anywhere else counts for nothing.
"""

import os


DEVELOPER_IDS: list[int] = [
    515896235081859091,     # @combifightet
    363003829912076289,     # @malt0se
    241687107049881602,     # @grosskahn
    1071428951844585482,    # @_polylux_
]


def home_server_id() -> int | None:
    """ The server OSCAR is operated from.

        Returns:
            The id from `DISCORD_SERVER_ID`, or `None` when it is missing or not a
            number. Nobody is an administrator of `None`, so a broken setting closes
            the commands instead of opening them.
    """
    raw: str = os.environ.get("DISCORD_SERVER_ID", "").strip()
    return int(raw) if raw.isdigit() else None


def is_operator(user_id: int, guild_id: int | None, is_administrator: bool) -> bool:
    """ Tells whether somebody may use an operator command.

        The owner of the application is an operator too. Asking discord who that is
        takes a request, so the callers check it themselves, after this said no.

        Parameters:
            user_id: The discord id of whoever asks.
            guild_id: The server the command was used in, `None` in a direct message.
            is_administrator: Whether they are an administrator of that server.

        Returns:
            `True` for a developer anywhere, and for an administrator of the home
            server on the home server.
    """
    if user_id in DEVELOPER_IDS:
        return True

    home: int | None = home_server_id()
    return home is not None and guild_id == home and is_administrator
