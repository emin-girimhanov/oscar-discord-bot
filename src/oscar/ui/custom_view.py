""" This module holds an abstract clas for LayoutView's, that support custom build methods"""


from discord.ui import LayoutView

from oscar.ui.owner_only import OwnerOnly



class CustomView(OwnerOnly, LayoutView):
    """Base class for views that support a custom build funciton.

        `OwnerOnly` comes first on purpose. Its `interaction_check` has to win over
        the one discord.py provides, which lets everybody through.
    """

    user_id: int

    def __init__(self, user_id: int):
        """ Parameters:
                user_id: the user that created this view"""
        super().__init__()
        self.user_id = user_id
        self.build_view()

    def build_view(self) -> None:
        """Override this method in subclasses to build the actual content."""
        raise NotImplementedError("Subclasses must implement _build_view()")
