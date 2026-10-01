""" The reviews other students wrote about a module.

    `/rate` asked for a comment from the day it shipped, stored it in `module_ratings`
    and showed it nowhere. `Database.get_module_comments` existed and nothing called
    it, so every tip a student wrote went into the database and was never read by
    anybody. The module card only ever showed the two averages.

    This view shows them. It is opened from the module card, and it carries the button
    that writes a new one, so reading and writing sit next to each other.

    No name is shown. The table stores a discord id per rating because one student may
    only rate a module once, not so the review can be attributed.
"""

from datetime import datetime, timezone

import discord
from discord.ui import ActionRow, Button, Container, LayoutView, Separator, TextDisplay

from util.database import get_database, get_user_language
from util.enums import LanguageCode
from util.module import Module
from util.safe_text import plain
from util.translations import RATING_TEXTS, ratings_label, t


ACCENT_COLOR: int = 0x4378D5

# How many reviews the view shows. Discord cuts a message off at some point, and
# five recent ones say more than fifty old ones.
REVIEW_LIMIT: int = 5

# A single review is cut here, so one long text cannot push the rest off the screen.
MAX_COMMENT_LENGTH: int = 400


def format_stars(rating: int, difficulty: int) -> str:
    """ The rating and the difficulty of one review, as a short line.

        Parameters:
            rating: One to five stars.
            difficulty: One to five, where five is hard.

        Returns:
            A line such as `⭐⭐⭐⭐☆ · 🏋️ 3/5`.
    """
    stars = "⭐" * max(0, min(5, rating)) + "☆" * max(0, 5 - rating)
    return f"{stars} · 🏋️ {difficulty}/5"


def format_date(timestamp: int, language: LanguageCode) -> str:
    """ The day a review was written.

        Parameters:
            timestamp: Unix seconds, as `module_ratings` stores them.
            language: Picks the order of day and month.

        Returns:
            A date, or the empty string when the timestamp makes no sense.
    """
    try:
        written = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ""
    return written.strftime("%d.%m.%Y" if language == LanguageCode.DE else "%Y-%m-%d")


def shorten(comment: str) -> str:
    """ Cuts one review down so it cannot fill the whole message.

        Parameters:
            comment: What the student wrote.

        Returns:
            The comment, at most `MAX_COMMENT_LENGTH` characters.
    """
    text = comment.strip()
    if len(text) <= MAX_COMMENT_LENGTH:
        return text
    return text[: MAX_COMMENT_LENGTH - 1].rstrip() + "…"


class ModuleReviewsView(LayoutView):
    """ Shows what students wrote about one module, and lets the reader add to it."""

    def __init__(self, user_id: int, module: Module):
        super().__init__()
        self.user_id: int = user_id
        self.module: Module = module
        self.language: LanguageCode = get_user_language(user_id)
        self._build_view()

    def _text(self, key: str) -> str:
        """ Reads one string of the view in the language of its reader."""
        return t(self.language, key, RATING_TEXTS)

    def _summary(self) -> str:
        """ The averages above the reviews, or the invitation to write the first one.

            Returns:
                One line with both averages, or the empty string when nobody has
                rated the module yet.
        """
        info = get_database().get_module_ratings(self.module.id_)
        count = info.get("count", 0) if isinstance(info, dict) else 0
        if not count:
            return ""
        return self._text("reviews_summary").format(
            rating=info.get("avg_rating") or 0.0,
            difficulty=info.get("avg_difficulty") or 0.0,
            count=int(count),
            label=ratings_label(self.language, int(count)),
        )

    def _reviews(self) -> str:
        """ The written reviews themselves.

            Returns:
                One block per review, or the text that asks for the first one.
        """
        comments = get_database().get_module_comments(self.module.id_, limit=REVIEW_LIMIT)
        if not comments:
            return self._text("no_reviews")

        blocks: list[str] = []
        for entry in comments:
            head = format_stars(int(entry["rating"]), int(entry["difficulty"]))
            written = format_date(int(entry["timestamp"]), self.language)
            if written:
                head = f"{head} · {written}"
            # cut first, then escape, so the cut never lands inside an escape
            blocks.append(f"{head}\n> {plain(shorten(str(entry['comment'])))}")
        return "\n\n".join(blocks)

    def _rate_button(self) -> Button[LayoutView]:
        """ Opens the form that writes a review, right under the ones already there."""
        button: Button[LayoutView] = Button(
            label="⭐ Bewerten" if self.language == LanguageCode.DE else "⭐ Rate",
            style=discord.ButtonStyle.success,
        )

        async def callback(interaction: discord.Interaction):
            # pylint: disable=import-outside-toplevel
            from oscar.ui.rating_modal import ModuleRatingModal

            await interaction.response.send_modal(
                ModuleRatingModal(module=self.module, language=self.language)
            )

        button.callback = callback
        return button

    def _build_view(self) -> None:
        """ Draws the heading, the averages, the reviews and the button."""
        _ = self.clear_items()
        parts: list[TextDisplay[LayoutView]] = [
            TextDisplay(
                self._text("reviews_title").format(
                    title=self.module.get_title(self.language)
                )
            )
        ]
        summary = self._summary()
        if summary:
            parts.append(TextDisplay(summary))

        _ = self.add_item(
            Container(
                *parts,
                Separator(),
                TextDisplay(self._reviews()),
                Separator(),
                TextDisplay(self._text("reviews_privacy")),
                ActionRow(self._rate_button()),
                accent_color=discord.Color(ACCENT_COLOR),
            )
        )
