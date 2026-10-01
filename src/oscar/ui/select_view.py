""" This module holds the view for the module filter mask and for its result list."""


from collections.abc import Callable, Iterator

import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from oscar.ui.owner_only import OwnerOnly
from oscar.ui.select_button import FilterButton, InfoButton
from util.database import get_user_language
from util.enums import LanguageCode
from util.filter_options import FILTER_GROUPS, apply_selection
from util.module import Module
from util.modules_filter import ModulesFilter, SortKey, sort_modules
from util.translations import FILTER_TEXTS, t


ACCENT_COLOR: int = 0x4378d5

# A discord view holds forty components and no more. The mask spends one on every
# heading, one on every row and one on every button, so it grows with the options.
# At five groups it stood at 36 of 40, and a sixth group raised
# `ValueError: maximum number of children exceeded (40)`, the same crash that took
# `/start` down. Two things bought the room back: the title and the hint share one
# block of text, and the groups are told apart by a blank line inside their heading
# rather than by a `Separator` component. See `tests/test_component_budget.py`.
GROUP_SPACING: str = "\n"

# The orders offered above the result list, as (label key, sort key, descending).
SORT_OPTIONS: tuple[tuple[str, SortKey, bool], ...] = (
    ("sort_cp_asc", SortKey.CREDIT_POINTS, False),
    ("sort_cp_desc", SortKey.CREDIT_POINTS, True),
    ("sort_title_asc", SortKey.TITLE, False),
    ("sort_title_desc", SortKey.TITLE, True),
)


def filter_buttons(items: list) -> Iterator[FilterButton]:
    """ Finds every filter button of a view, however deeply it is nested.

        Parameters:
            items: The children of a view or of one of its containers.

        Yields:
            Each `FilterButton` below `items`.
    """
    for item in items:
        if isinstance(item, FilterButton):
            yield item
        elif hasattr(item, "children"):
            yield from filter_buttons(item.children)


class SelectView(OwnerOnly, LayoutView):
    """ Class for filtering a list of modules"""
    def __init__(self,user_id:int):
        super().__init__()
        # kept so `OwnerOnly` can tell whose filter mask this is
        self.user_id: int = user_id
        self.language: LanguageCode = get_user_language(user_id)
        self._build_view()

    def _text(self, key: str) -> str:
        """ Reads one string of the mask in the language of its owner.

            Parameters:
                key: The key in `translations.FILTER_TEXTS`.

            Returns:
                The translated string.
        """
        return t(self.language, key, FILTER_TEXTS)

    def selected_values(self) -> dict[str, list[str]]:
        """ Reads which options the student pressed.

            The buttons are read by value, not by label, so the answer is the same in
            every language. Several pressed buttons of one row all end up in the list
            of that row, which is what makes them an or.

            Returns:
                Group key to the values selected in that group, empty groups left out.
        """
        selection: dict[str, list[str]] = {}
        for button in filter_buttons(self.children):
            if button.selected:
                selection.setdefault(button.group, []).append(button.value)
        return selection

    async def _search(self, interaction: discord.Interaction):
        """ Runs the search and answers with the result list.

            Parameters:
                interaction: The click on the search button.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        module_filter = ModulesFilter(remove_invalid=True)
        result: list[Module] = apply_selection(self.selected_values(), module_filter)

        _ = await interaction.followup.send(
            view=PaginatedModuleView(result, user_id=interaction.user.id)
        )

    def _option_rows(self) -> list:
        """ Builds one heading and one button row per filter group.

            Returns:
                The items of the mask, in the order of `FILTER_GROUPS`.
        """
        items: list = []
        for index, group in enumerate(FILTER_GROUPS):
            spacing: str = GROUP_SPACING if index else ""
            items.append(TextDisplay(f"{spacing}**{self._text(group.heading_key)}**"))
            items.append(
                ActionRow[LayoutView](*[
                    FilterButton(self._text(value), group=group.key, value=value)
                    for value in group.values
                ])
            )
        return items

    def _build_view(self):
        """ Draws the whole mask."""
        search_button: Button[LayoutView] = discord.ui.Button(
            label=self._text("search"), style=discord.ButtonStyle.primary
        )
        search_button.callback = self._search

        _ = self.clear_items()
        _ = self.add_item(
            Container(
                TextDisplay(
                    f"# {self._text('title')}\n{self._text('hint')}"
                ),
                Separator(),
                *self._option_rows(),
                ActionRow(search_button),
                accent_color=ACCENT_COLOR,
            )
        )


class PaginatedModuleView(OwnerOnly, LayoutView):  # pylint: disable=too-many-instance-attributes
    """ Class for showing a filtered module list page by page, in a chosen order."""

    def __init__(self, modules: list, user_id, per_page: int = 6 ):
        super().__init__()
        # the order the filter produced, kept so the sorting can be taken back
        self.modules: list[Module] = list(modules)
        self.per_page = per_page
        self.index = 0
        self.total_pages = max(1, (len(self.modules) + per_page - 1) // per_page)
        self.user_id = user_id
        self.language: LanguageCode = get_user_language(user_id)
        self.sort_key: SortKey | None = None
        self.sort_descending: bool = False
        # what the pages are cut out of, so the order holds across every page
        self.ordered_modules: list[Module] = list(self.modules)

        self._build_page()

    def _text(self, key: str) -> str:
        """ Reads one string of the result list in the language of its owner.

            Parameters:
                key: The key in `translations.FILTER_TEXTS`.

            Returns:
                The translated string.
        """
        return t(self.language, key, FILTER_TEXTS)

    def _get_page_modules(self):
        start = self.index * self.per_page
        end = start + self.per_page
        return self.ordered_modules[start:end]

    def _apply_sort(self):
        """ Puts the whole list into the chosen order, not only the shown page."""
        if self.sort_key is None:
            self.ordered_modules = list(self.modules)
        else:
            self.ordered_modules = sort_modules(
                self.modules,
                self.sort_key,
                descending=self.sort_descending,
                language=self.language,
            )

    def _sort_callback(self, key: SortKey, descending: bool) -> Callable:
        """ Builds the callback of one sort button.

            Pressing the order that is already active takes the sorting back, so the
            order the filter produced can be reached again.

            Parameters:
                key: The order the button stands for.
                descending: The direction the button stands for.

            Returns:
                The callback for that button.
        """
        async def callback(interaction: discord.Interaction):
            if self.sort_key == key and self.sort_descending == descending:
                self.sort_key = None
                self.sort_descending = False
            else:
                self.sort_key = key
                self.sort_descending = descending
            self.index = 0
            self._apply_sort()
            self._build_page()
            _ = await interaction.response.edit_message(view=self)

        return callback

    def _sort_row(self) -> ActionRow:
        """ Builds the row of sort buttons, the active order marked green.

            Returns:
                The row, ready to be added to the view.
        """
        buttons: list[Button] = []
        for label_key, key, descending in SORT_OPTIONS:
            active: bool = self.sort_key == key and self.sort_descending == descending
            button = Button(
                label=self._text(label_key),
                style=discord.ButtonStyle.success if active else discord.ButtonStyle.secondary,
            )
            button.callback = self._sort_callback(key, descending)
            buttons.append(button)
        return ActionRow(*buttons)

    def _nav_row(self) -> ActionRow:
        """ Builds the row of page buttons.

            Returns:
                The row, ready to be added to the view.
        """
        first_btn = Button(label="⏮", style=discord.ButtonStyle.secondary, disabled=self.index == 0)
        first_btn.callback = self._first

        prev_btn = Button(label="◀", style=discord.ButtonStyle.primary, disabled=self.index == 0)
        prev_btn.callback = self._prev

        next_btn = Button(
            label="▶",
            style=discord.ButtonStyle.primary,
            disabled=self.index >= self.total_pages - 1,
        )
        next_btn.callback = self._next

        last_btn = Button(
            label="⏭",
            style=discord.ButtonStyle.secondary,
            disabled=self.index >= self.total_pages - 1,
        )
        last_btn.callback = self._last

        return ActionRow(first_btn, prev_btn, next_btn, last_btn)

    def _build_page(self):
        _ = self.clear_items()

        header: str = self._text("page_header").format(
            page=self.index + 1, pages=self.total_pages
        )
        page_container = Container(
            TextDisplay(f"# {header}"),
            Separator(),
            accent_color=ACCENT_COLOR,
        )

        if not self.modules:
            _ = page_container.add_item(TextDisplay(self._text("no_results")))
            _ = self.add_item(page_container)
            return

        for position, module in enumerate(self._get_page_modules()):
            # A `Separator` between the results cost one component each, and six of
            # them put the page at 37 of 40. `per_page=7` then raised
            # `ValueError: maximum number of children exceeded (40)`, and `per_page`
            # is a constructor argument anybody may tune. The blank line does the
            # same job for free.
            spacing: str = GROUP_SPACING if position else ""
            _ = page_container.add_item(
                TextDisplay(f"{spacing}**{module.get_title(self.language)}**")
            )
            _ = page_container.add_item(
                ActionRow(
                    InfoButton(
                        label=self._text("more_info"),
                        # InfoButton looks the module up by name and has no language
                        # flag, so it always gets the German title.
                        module=module.get_title(LanguageCode.DE),
                    )
                )
            )

        _ = self.add_item(page_container)
        _ = self.add_item(self._sort_row())
        _ = self.add_item(self._nav_row())

    # --- Pagination Callbacks ---
    async def _first(self, interaction: discord.Interaction):
        self.index = 0
        self._build_page()
        _ = await interaction.response.edit_message(view=self)

    async def _prev(self, interaction: discord.Interaction):
        self.index -= 1
        self._build_page()
        _ = await interaction.response.edit_message(view=self)

    async def _next(self, interaction: discord.Interaction):
        self.index += 1
        self._build_page()
        _ = await interaction.response.edit_message(view=self)

    async def _last(self, interaction: discord.Interaction):
        self.index = self.total_pages - 1
        self._build_page()
        _ = await interaction.response.edit_message(view=self)
