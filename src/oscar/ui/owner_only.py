""" A view belongs to the student who opened it, and to nobody else.

    Every view in this package already carried the user id it was built for, but
    nothing ever checked who was pressing the buttons. `/start`, `/filter`,
    `/feedback` and `/semesterplan` answered in the channel, so their components were
    visible and clickable for everyone in it.

    That was not only untidy. `DeleteButton` writes to the id stored in the view, not
    to the id of whoever clicked, so a stranger pressing the red X in someone else's
    semester plan removed that person's module from the database. The buttons in
    `/start` overwrite the same person's programme and examination regulations.

    discord.py calls `interaction_check` before it runs any component callback, and a
    `False` stops the callback. One method therefore covers every button and select in
    a view, including ones added later.
"""


import discord

from util.enums import LanguageCode
from util.translations import VIEW_TEXTS, t


class OwnerOnly:
    """ Mixin that refuses component clicks from anyone but the view's owner.

        Mix it in **before** the discord.py base class, so this `interaction_check`
        is the one that runs:

        ```python
        class StartView(OwnerOnly, LayoutView):
            ...
        ```

        The class using it must set `self.user_id`. If it also has `self.language`,
        the refusal is written in that language.
    """

    user_id: int

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """ Lets the owner through and turns everyone else away politely.

            Parameters:
                interaction: the click discord.py is about to dispatch.

            Returns:
                `True` for the student the view was built for, `False` otherwise.
        """
        if interaction.user.id == self.user_id:
            return True

        language: LanguageCode = getattr(self, "language", LanguageCode.EN)
        _ = await interaction.response.send_message(
            t(language, "not_your_view", VIEW_TEXTS),
            ephemeral=True,
        )
        return False
