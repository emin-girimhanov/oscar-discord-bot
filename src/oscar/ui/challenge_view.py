""" Interactive view and modal dialog for Code Golf challenges.

    Allows students to browse weekly programming puzzles, submit concise code solutions,
    view the byte-count leaderboard, and inspect their own submissions (Issue #53).
"""

from typing import override
import datetime
import discord
from discord import ui
from discord.ui import (
    ActionRow,
    Button,
    Container,
    LayoutView,
    Select,
    Separator,
    TextDisplay,
    TextInput,
)

from oscar.ui.translated_view import TranslatedView
from util.challenges import (
    CHALLENGES,
    Challenge,
    get_challenge_by_id,
    get_current_weekly_challenge,
)
from util.database import get_database
from util.enums import LanguageCode
from util.translations import CODE_GOLF_TEXTS, t


class ChallengeSubmitModal(ui.Modal):
    """Modal dialog allowing students to submit a Code Golf solution."""

    def __init__(self, challenge: Challenge, language: LanguageCode):
        modal_title = t(language, "modal_title", CODE_GOLF_TEXTS).format(
            number=challenge.number
        )
        super().__init__(title=modal_title[:45])
        self.challenge: Challenge = challenge
        self.language: LanguageCode = language

        self.lang_input: TextInput[ui.Modal] = TextInput(
            label=t(language, "modal_lang_label", CODE_GOLF_TEXTS),
            placeholder=t(language, "modal_lang_placeholder", CODE_GOLF_TEXTS),
            min_length=1,
            max_length=50,
            required=True,
        )
        self.code_input: TextInput[ui.Modal] = TextInput(
            label=t(language, "modal_code_label", CODE_GOLF_TEXTS),
            style=discord.TextStyle.long,
            placeholder=t(language, "modal_code_placeholder", CODE_GOLF_TEXTS),
            min_length=1,
            max_length=4000,
            required=True,
        )

        _ = self.add_item(self.lang_input)
        _ = self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):  # pylint: disable=arguments-differ
        """Handles submission of the code golf solution."""
        prog_lang = self.lang_input.value.strip()
        code = self.code_input.value

        db = get_database()
        is_best, prev_len, new_len = db.submit_challenge_solution(
            user_id=interaction.user.id,
            challenge_id=self.challenge.id,
            language=prog_lang,
            code_snippet=code,
        )

        if is_best and prev_len == 0:
            msg = t(self.language, "submit_new_best", CODE_GOLF_TEXTS).format(
                length=new_len,
                language=prog_lang,
            )
        elif is_best:
            msg = t(self.language, "submit_improved", CODE_GOLF_TEXTS).format(
                new_len=new_len,
                prev_len=prev_len,
                language=prog_lang,
            )
        else:
            msg = t(self.language, "submit_worse", CODE_GOLF_TEXTS).format(
                new_len=new_len,
                prev_len=prev_len,
            )

        await interaction.response.send_message(msg, ephemeral=True)


class ChallengeView(TranslatedView):
    """View that displays weekly challenges, problem details, and leaderboards."""

    def __init__(
        self,
        default_language: LanguageCode = LanguageCode.DE,
        initial_challenge_id: str | None = None,
        initial_show_leaderboard: bool = False,
    ):
        curr = get_current_weekly_challenge()
        self.selected_challenge_id: str = initial_challenge_id or curr.id
        self.show_leaderboard: bool = initial_show_leaderboard
        super().__init__(default_language=default_language)

    def _create_challenge_select(self, lang: LanguageCode) -> ActionRow[LayoutView]:
        """Creates the challenge selection dropdown."""
        options: list[discord.SelectOption] = []
        for c in CHALLENGES:
            options.append(
                discord.SelectOption(
                    label=f"#{c.number}: {c.title(lang)}"[:100],
                    value=c.id,
                    description=c.description(lang)[:100],
                    default=c.id == self.selected_challenge_id,
                )
            )

        placeholder = (
            "Challenge auswählen..." if lang == LanguageCode.DE
            else "Select challenge..."
        )
        select: Select[LayoutView] = Select(
            options=options,
            placeholder=placeholder,
        )

        async def on_select(interaction: discord.Interaction):
            self.selected_challenge_id = select.values[0]
            self.show_leaderboard = False
            await self._update(interaction)

        select.callback = on_select
        return ActionRow[LayoutView](select)

    @staticmethod
    def _render_challenge_details(
        challenge: Challenge, lang: LanguageCode
    ) -> list[TextDisplay]:
        """Formats the problem description, I/O formats, and examples."""
        current_challenge = get_current_weekly_challenge()
        iso_week = datetime.date.today().isocalendar().week

        items: list[TextDisplay] = []
        if challenge.id == current_challenge.id:
            banner = t(lang, "active_week", CODE_GOLF_TEXTS).format(
                week=iso_week,
                number=challenge.number,
                title=challenge.title(lang),
            )
            items.append(TextDisplay(f"🌟 {banner}"))

        title_block = (
            f"## ⛳ #{challenge.number}: {challenge.title(lang)}\n"
            f"{challenge.description(lang)}"
        )
        items.append(TextDisplay(title_block))

        in_label = t(lang, "input_label", CODE_GOLF_TEXTS)
        out_label = t(lang, "output_label", CODE_GOLF_TEXTS)
        spec_block = (
            f"{in_label} {challenge.input_format(lang)}\n"
            f"{out_label} {challenge.output_format(lang)}"
        )
        items.append(TextDisplay(spec_block))

        ex_in = t(lang, "example_input_label", CODE_GOLF_TEXTS)
        ex_out = t(lang, "example_output_label", CODE_GOLF_TEXTS)
        example_block = (
            f"{ex_in} `{challenge.example_input}`\n"
            f"{ex_out}\n```{challenge.example_output}```"
        )
        items.append(TextDisplay(example_block))

        rules = t(lang, "rules_note", CODE_GOLF_TEXTS)
        items.append(TextDisplay(rules))
        return items

    @staticmethod
    def _render_leaderboard(
        challenge: Challenge, lang: LanguageCode
    ) -> list[TextDisplay]:
        """Formats the top 10 leaderboard for the selected challenge."""
        db = get_database()
        leaderboard = db.get_challenge_leaderboard(challenge.id, limit=10)

        title = t(lang, "leaderboard_title", CODE_GOLF_TEXTS).format(
            number=challenge.number,
            title=challenge.title(lang),
        )

        if not leaderboard:
            empty_msg = t(lang, "leaderboard_empty", CODE_GOLF_TEXTS)
            return [TextDisplay(f"{title}\n\n{empty_msg}")]

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines: list[str] = [title, ""]
        for entry in leaderboard:
            rank_str = medals.get(entry["rank"], f"**{entry['rank']}.**")
            name_str = entry["name"] or f"Student {entry['user_id']}"
            line = t(lang, "leaderboard_entry", CODE_GOLF_TEXTS).format(
                rank=rank_str,
                name=name_str,
                length=entry["code_length"],
                language=entry["language"],
            )
            lines.append(line)

        return [TextDisplay("\n".join(lines))]

    @override
    def _build_content(self) -> None:
        lang: LanguageCode = self.language_code
        challenge: Challenge | None = get_challenge_by_id(self.selected_challenge_id)
        if challenge is None:
            challenge = get_current_weekly_challenge()
            self.selected_challenge_id = challenge.id

        container = Container[LayoutView]()
        header = f"# {t(lang, 'golf_title', CODE_GOLF_TEXTS)}"
        _ = container.add_item(TextDisplay(header))
        _ = container.add_item(Separator())
        _ = container.add_item(self._create_challenge_select(lang))
        _ = container.add_item(Separator())

        if self.show_leaderboard:
            for item in self._render_leaderboard(challenge, lang):
                _ = container.add_item(item)
        else:
            for item in self._render_challenge_details(challenge, lang):
                _ = container.add_item(item)

        _ = container.add_item(Separator())

        # Submit Button
        btn_submit = Button[LayoutView](
            label=t(lang, "btn_submit", CODE_GOLF_TEXTS),
            style=discord.ButtonStyle.primary,
        )

        async def on_submit_clicked(interaction: discord.Interaction):
            modal = ChallengeSubmitModal(challenge=challenge, language=self.language_code)
            await interaction.response.send_modal(modal)

        btn_submit.callback = on_submit_clicked

        # Toggle Leaderboard / Details Button
        toggle_label = (
            t(lang, "btn_details", CODE_GOLF_TEXTS)
            if self.show_leaderboard
            else t(lang, "btn_leaderboard", CODE_GOLF_TEXTS)
        )
        btn_toggle = Button[LayoutView](
            label=toggle_label,
            style=discord.ButtonStyle.secondary,
        )

        async def on_toggle_clicked(interaction: discord.Interaction):
            self.show_leaderboard = not self.show_leaderboard
            await self._update(interaction)

        btn_toggle.callback = on_toggle_clicked

        # My Submission Button
        btn_my = Button[LayoutView](
            label=t(lang, "btn_my_submission", CODE_GOLF_TEXTS),
            style=discord.ButtonStyle.secondary,
        )

        async def on_my_clicked(interaction: discord.Interaction):
            db = get_database()
            sub = db.get_user_challenge_submission(interaction.user.id, challenge.id)
            if sub is None:
                msg = t(self.language_code, "no_submission_yet", CODE_GOLF_TEXTS).format(
                    number=challenge.number
                )
            else:
                msg = t(self.language_code, "my_submission_info", CODE_GOLF_TEXTS).format(
                    number=challenge.number,
                    title=challenge.title(self.language_code),
                    language=sub["language"],
                    length=sub["code_length"],
                    code=sub["code_snippet"],
                )
            await interaction.response.send_message(msg, ephemeral=True)

        btn_my.callback = on_my_clicked

        _ = container.add_item(
            ActionRow[LayoutView](
                btn_submit,
                btn_toggle,
                btn_my,
                self._create_language_toggle(),
            )
        )
        _ = self.add_item(container)
