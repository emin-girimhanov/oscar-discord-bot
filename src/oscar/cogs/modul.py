""" This module holds a class for module related commands"""


import asyncio
import re
import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from oscar.ui.channel_module_view import ChannelModuleView
from oscar.ui.compare_view import CompareView
from oscar.ui.help_launcher import open_exams, open_feedback, open_standard_plan
from oscar.ui.module_view import ModuleView
from oscar.ui.semesterplan_view import SemesterplanView
from oscar.ui.select_view import SelectView
from oscar.ui.start_view import StartView
from oscar.ui.study_buddy_view import StudyBuddyView
from util.channel_module import find_candidates, is_certain
from util.database import get_database, get_user_language
from util.module import Module
from util.tables import Catalogue, ModuleMatch
from util.translations import COMPARE_TEXTS, HERE_TEXTS, MODULE_TEXTS, RATING_TEXTS, t




def resolve_module(value: str) -> Module:
    """ Resolves the argument of the /module command into a single module.

        The suggestion list hands over the module id, which is unique even when two
        modules share a title. A user may also type a title by hand instead of
        picking a suggestion, which is then looked up by title as before.

        Parameters:
            value: The id of a picked suggestion, or a title typed by hand.

        Returns:
            The matching Module instance.

        Raises:
            IndexError: If no module matches the value.
    """
    reference: str = value.strip()
    if reference.isdigit():
        return Module.from_id(int(reference))
    return Module.from_name(name=reference)



def channel_name_of(interaction: discord.Interaction) -> str | None:
    """ Reads the name of the channel a command was typed in.

        A thread is named after the topic somebody opened, not after the module, so
        the parent channel is asked instead. A direct message has no name at all.

        Parameters:
            interaction: The interaction discord.py handed to the command.

        Returns:
            The channel name without the leading `#`, or `None` in a direct message.
    """
    channel = interaction.channel
    if isinstance(channel, discord.Thread) and channel.parent is not None:
        return channel.parent.name
    return getattr(channel, "name", None)


class ModulSearch(commands.Cog):
    """ Class for module related commands"""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.module_catalogue: Catalogue = Catalogue(720)
        logger.info("Loaded ModulSearch cog")


    # @app_commands.command(
    #     name="search", description="suche module nach einem bestimmten Kriterium"
    # )
    # async def search(self, interaction: discord.Interaction, filter_str: str):
    #     """ Command for searching modules by a filter string

    #         Parameters:
    #             interaction: automatically provided interaction object.
    #             filter_str: The filter string to search modules.
    #     """
    #     _ = await interaction.response.send_message(filter_str)



    async def module_autocomplete(
        self, _interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """ Autocomplete function for module names

            Parameters:
                interaction: automatically provided interaction object.
                current: The current input of the user.

            Returns:
                A list of up to 5 module choices matching the current input.
                The value of a choice is the module id, so picking an entry opens
                exactly the module that was shown.
        """
        result = [
            app_commands.Choice(name=match.label, value=str(match.id_))
            for match in self.module_catalogue.find_match(current)
        ]
        return result[:5]

    @app_commands.command(name="module", description="search for a modul")
    @app_commands.autocomplete(modul=module_autocomplete)
    async def search_module(self, interaction: discord.Interaction, modul: str):
        """ Command for searching a single module by name

            Parameters:
                interaction: automatically provided interaction object.
                modul: The id of a picked suggestion, or a module title typed by hand.
        """
        _ = await interaction.response.defer(ephemeral=True)

        language = get_user_language(interaction.user.id)

        try:
            module = resolve_module(modul)
        except IndexError:
            await interaction.followup.send(
                t(language, "not_found", MODULE_TEXTS).format(name=modul),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            view=ModuleView(
                interaction.user.id,
                module
            ),
            ephemeral=True,
        )


    @app_commands.command(
        name="compare",
        description="put two or three modules side by side",
    )
    @app_commands.autocomplete(
        first=module_autocomplete,
        second=module_autocomplete,
        third=module_autocomplete,
    )
    async def compare(
        self,
        interaction: discord.Interaction,
        first: str,
        second: str,
        third: str | None = None,
    ):
        """ Command for comparing two or three modules at a glance.

            Parameters:
                interaction: automatically provided interaction object.
                first: The id of a picked suggestion, or a title typed by hand.
                second: The second module, same as `first`.
                third: An optional third module. Three fit in one embed row.
        """
        _ = await interaction.response.defer(ephemeral=True)

        language = get_user_language(interaction.user.id)
        modules: list[Module] = []

        for reference in (first, second, third):
            if reference is None:
                continue
            try:
                modules.append(resolve_module(reference))
            except IndexError:
                await interaction.followup.send(
                    t(language, "not_found", MODULE_TEXTS).format(name=reference),
                    ephemeral=True,
                )
                return

        # naming the same module twice compares it with itself, which says nothing
        unique: list[Module] = []
        for module in modules:
            if all(module.id_ != seen.id_ for seen in unique):
                unique.append(module)

        if len(unique) < 2:
            await interaction.followup.send(
                t(language, "too_few", COMPARE_TEXTS),
                ephemeral=True,
            )
            return

        view = CompareView(user_id=interaction.user.id, modules=unique)
        await interaction.followup.send(
            embed=view.create_embed(),
            view=view,
            ephemeral=True,
        )


    @app_commands.command(name="filter", description="suchmaske für module")
    async def filter(self, interaction: discord.Interaction):
        """ Command to open the filter dialog for module filtering by different criteria

            Parameters:
                interaction: automatically provided interaction object.
        """
        # ephemeral: the mask belongs to one student, nobody else may click it
        _ = await interaction.response.send_message(
            view=SelectView(interaction.user.id),
            ephemeral=True,
        )

    @app_commands.command(
    name="standard_plan",
    description="gibt Bild des Regelstudienplans"
)
    async def s_plan(self, interaction: discord.Interaction):
        """ Draws the official study plan of the student's own programme.

            Parameters:
                interaction: automatically provided interaction object.
        """
        await open_standard_plan(interaction)





    @app_commands.command(
        name="feedback",
        description="gib uns gerne bescheid, was du über unseren Bot denkst"
    )
    async def feedback(self,interaction: discord.Interaction):
        """ Command to open the feedback dialog for the user

            Parameters:
                interaction: automatically provided interaction object.
        """
        await open_feedback(interaction)

    @app_commands.command(name="semesterplan", description="geradiger semesterplan")
    async def plan(self, interaction: discord.Interaction):
        """ Command to open the semester plan dialog for the user

            Parameters:
                interaction: automatically provided interaction object.
        """
        # ephemeral: a semester plan is personal, and its delete buttons write to the
        # plan of the student the view was built for
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        _ = await interaction.followup.send(
            view=SemesterplanView(user_id=user_id),
            ephemeral=True,
        )


    @app_commands.command(
        name="studybuddy",
        description="Finde Lernpartner:innen für Module (Find study buddies for modules)",
    )
    @app_commands.describe(
        modul="Modulname zur gezielten Lerngruppensuche (optional)",
    )
    @app_commands.autocomplete(modul=module_autocomplete)
    async def studybuddy(
        self, interaction: discord.Interaction, modul: str | None = None
    ):
        """ Command to find or form study groups for modules.

            Parameters:
                interaction: automatically provided interaction object.
                modul: optional module name or ID.
        """
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        module_id: int | None = None
        if modul:
            try:
                mod = resolve_module(modul)
                module_id = mod.id_
            except IndexError:
                pass

        _ = await interaction.followup.send(
            view=StudyBuddyView(user_id=user_id, module_id=module_id),
            ephemeral=True,
        )


    @app_commands.command(
        name="start",
        description="use this command fpr your first interaction with OSCAR",
    )
    async def start(self, interaction: discord.Interaction):
        """ Command to open the start dialog for the user

            Parameters:
                interaction: automatically provided interaction object.
        """
        member = interaction.user
        semester_number: int = -1
        user_id = interaction.user.id

        for role in member.roles:
            match = re.match(r"Semester\s+(\d+)", role.name)
            if match:
                semester_number = int(match.group(1))  # Hier hast du die Zahl als Integer
                break


        # ephemeral: these buttons overwrite the settings of the student named here
        _ = await interaction.response.send_message(
            view=StartView(
                user_id,
                semester_number
            ),
            ephemeral=True,
        )


    @app_commands.command(
        name="rate",
        description="Bewerte ein Modul und teile Erfahrungen (Rate a module and share reviews)",
    )
    @app_commands.describe(
        modul="Das zu bewertende Modul (The module to rate)",
        bewertung="Bewertung von 1 bis 5 Sternen (Rating 1-5 stars)",
        schwierigkeit="Schwierigkeit von 1 (sehr leicht) bis 5 (sehr schwer)",
        kommentar="Optionaler Erfahrungsbericht oder Tipps",
    )
    @app_commands.choices(
        bewertung=[
            app_commands.Choice(name="⭐ 1 - Sehr unzufrieden / Poor", value=1),
            app_commands.Choice(name="⭐⭐ 2 - Eher unzufrieden / Below Average", value=2),
            app_commands.Choice(name="⭐⭐⭐ 3 - Durchschnittlich / Average", value=3),
            app_commands.Choice(name="⭐⭐⭐⭐ 4 - Gut / Good", value=4),
            app_commands.Choice(name="⭐⭐⭐⭐⭐ 5 - Ausgezeichnet / Excellent", value=5),
        ],
        schwierigkeit=[
            app_commands.Choice(name="1 - Sehr leicht / Very easy", value=1),
            app_commands.Choice(name="2 - Eher leicht / Easy", value=2),
            app_commands.Choice(name="3 - Moderat / Moderate", value=3),
            app_commands.Choice(name="4 - Anspruchsvoll / Hard", value=4),
            app_commands.Choice(name="5 - Sehr schwer / Very hard", value=5),
        ],
    )
    @app_commands.autocomplete(modul=module_autocomplete)
    async def rate_command(
        self,
        interaction: discord.Interaction,
        modul: str,
        bewertung: int | None = None,
        schwierigkeit: int | None = None,
        kommentar: str | None = None,
    ):
        """ Allows a student to rate a module and its difficulty."""
        language = get_user_language(interaction.user.id)
        try:
            module = resolve_module(modul)
        except IndexError:
            await interaction.response.send_message(
                t(language, "not_found", MODULE_TEXTS).format(name=modul),
                ephemeral=True,
            )
            return

        if bewertung is None or schwierigkeit is None:
            # pylint: disable=import-outside-toplevel
            from oscar.ui.rating_modal import ModuleRatingModal
            await interaction.response.send_modal(
                ModuleRatingModal(module=module, language=language)
            )
            return

        db = get_database()
        db.rate_module(
            user_id=interaction.user.id,
            module_id=module.id_,
            rating=bewertung,
            difficulty=schwierigkeit,
            comment=kommentar.strip() if kommentar else None,
        )

        msg = t(language, "rate_success", RATING_TEXTS).format(
            title=module.get_title(language),
            rating=bewertung,
            difficulty=schwierigkeit,
        )
        await interaction.response.send_message(msg, ephemeral=True)


    @app_commands.command(
        name="klausuren",
        description="Altklausuren-Archive der Fachschaftsräte (past exam archives)",
    )
    async def klausuren_command(self, interaction: discord.Interaction):
        """ Names every past exam archive OSCAR knows, one link button each.

            Parameters:
                interaction: automatically provided interaction object.
        """
        await open_exams(interaction)


    @app_commands.command(
        name="here",
        description="Infos zum Modul dieses Kanals (module info for this channel)",
    )
    async def here_command(self, interaction: discord.Interaction):
        """ Opens the module the current channel is named after.

            Parameters:
                interaction: automatically provided interaction object.
        """
        await self.answer_here(interaction)


    async def answer_here(self, interaction: discord.Interaction):
        """ Answers with the module the current channel is named after.

            The FinEmporium server keeps one channel per module, so the channel name
            already says which module a student is reading about. Typing the title
            again is work the bot can do.

            A hit is opened straight away only when it is certain. Otherwise the
            student picks from a short list, and a channel about no module at all is
            told so instead of being shown something at random.

            Parameters:
                interaction: automatically provided interaction object.
        """
        language = get_user_language(interaction.user.id)
        channel_name: str | None = channel_name_of(interaction)
        if not channel_name:
            await interaction.response.send_message(
                t(language, "here_no_channel", HERE_TEXTS),
                ephemeral=True,
            )
            return

        _ = await interaction.response.defer(ephemeral=True)

        # The first call fills the catalogue from the Tables API, which blocks.
        candidates: list[tuple[ModuleMatch, float]] = await asyncio.to_thread(
            find_candidates, self.module_catalogue, channel_name
        )

        if not candidates:
            logger.debug(f"No module matches the channel '{channel_name}'")
            await interaction.followup.send(
                t(language, "here_not_found", HERE_TEXTS).format(channel=channel_name),
                ephemeral=True,
            )
            return

        if is_certain(candidates, channel_name):
            module = Module.from_id(candidates[0][0].id_)
            await interaction.followup.send(
                view=ModuleView(interaction.user.id, module),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            view=ChannelModuleView(interaction.user.id, channel_name, candidates),
            ephemeral=True,
        )



async def setup(bot: commands.Bot):
    """ Setup the Module cog."""
    # SERVER_ID = int(os.getenv("DISCORD_SERVER_ID"))
    # guild = discord.Object(id=SERVER_ID)

    await bot.add_cog(ModulSearch(bot))

    # bot.tree.add_command(ModulSearch.search, guild=guild)
