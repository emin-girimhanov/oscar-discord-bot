""" Interactive view for displaying faculty and university contact persons.

    Presents the contact details from `util.contacts`: the Dean's Office, the
    Examination Office, FaRaFIN, the programme directors, scholarships, Erasmus and
    counselling. A field the official page does not state is left out, and every card
    has a button to that page. Supports language switching.
"""

from typing import override
import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Select, Separator, TextDisplay

from oscar.ui.translated_view import TranslatedView
from util.contacts import CONTACT_CATEGORIES, ContactCategory, ContactPerson, get_category_by_key
from util.enums import LanguageCode


class ContactsView(TranslatedView):
    """ View that allows browsing official FIN and OVGU contact persons."""

    def __init__(
        self,
        default_language: LanguageCode = LanguageCode.DE,
        initial_category_key: str = "dekanat_pa"
    ):
        self.selected_category_key: str = initial_category_key
        super().__init__(default_language=default_language)

    def _create_category_select(self, lang: LanguageCode) -> ActionRow[LayoutView]:
        """Creates the category selection dropdown."""
        options: list[discord.SelectOption] = []
        for c in CONTACT_CATEGORIES:
            title = c.title_de if lang == LanguageCode.DE else c.title_en
            desc = c.description_de if lang == LanguageCode.DE else c.description_en
            options.append(
                discord.SelectOption(
                    label=f"{c.emoji} {title}"[:100],
                    value=c.key,
                    description=desc[:100],
                    default=c.key == self.selected_category_key,
                )
            )

        placeholder = (
            "Kategorie wählen..." if lang == LanguageCode.DE
            else "Select category..."
        )
        select: Select[LayoutView] = Select(
            options=options,
            placeholder=placeholder,
        )

        async def on_select(interaction: discord.Interaction):
            self.selected_category_key = select.values[0]
            await self._update(interaction)

        select.callback = on_select
        return ActionRow[LayoutView](select)

    @staticmethod
    def _render_person(person: ContactPerson, lang: LanguageCode) -> TextDisplay:
        """Renders contact card markdown for one person or office."""
        title = person.title_de if lang == LanguageCode.DE else person.title_en
        details = person.details_de if lang == LanguageCode.DE else person.details_en
        german = lang == LanguageCode.DE
        lines = [f"### {title}"]
        # A field the official page does not state is empty, and is left out here.
        # The link button under the card leads to the page that has the rest.
        if person.office:
            lines.append(f"**{'Raum' if german else 'Office'}:** {person.office}")
        if person.email:
            lines.append(f"**E-Mail:** `{person.email}`")
        if person.phone:
            lines.append(f"**{'Telefon' if german else 'Phone'}:** {person.phone}")
        if details:
            lines.append(f"\n{details}")
        return TextDisplay("\n".join(lines))

    @override
    def _build_content(self) -> None:
        lang: LanguageCode = self.language_code
        cat: ContactCategory | None = get_category_by_key(self.selected_category_key)
        if cat is None:
            cat = CONTACT_CATEGORIES[0]
            self.selected_category_key = cat.key

        container = Container[LayoutView]()
        header = (
            "# Wichtige Ansprechpartner der FIN & OVGU"
            if lang == LanguageCode.DE else
            "# Key Contacts at FIN & OVGU"
        )
        _ = container.add_item(TextDisplay(header))
        _ = container.add_item(Separator())
        _ = container.add_item(self._create_category_select(lang))
        _ = container.add_item(Separator())

        cat_title = cat.title_de if lang == LanguageCode.DE else cat.title_en
        cat_desc = cat.description_de if lang == LanguageCode.DE else cat.description_en
        _ = container.add_item(TextDisplay(f"## {cat.emoji} {cat_title}\n*{cat_desc}*"))
        _ = container.add_item(Separator())

        link_buttons: list[Button[LayoutView]] = []
        for person in cat.contacts:
            _ = container.add_item(self._render_person(person, lang))
            if person.url:
                title = person.title_de if lang == LanguageCode.DE else person.title_en
                link_buttons.append(
                    Button(label=title[:80], style=discord.ButtonStyle.link, url=person.url)
                )
            _ = container.add_item(Separator())

        if link_buttons:
            _ = container.add_item(ActionRow[LayoutView](*link_buttons[:4]))

        _ = container.add_item(ActionRow[LayoutView](self._create_language_toggle()))
        _ = self.add_item(container)
