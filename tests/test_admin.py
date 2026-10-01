import unittest
from unittest.mock import MagicMock, AsyncMock, patch, ANY
import discord
from discord.ext import commands
import pytest
from oscar.cogs.admin import (
    Administration,
    DEVELOPER_IDS,
    ReviewFeedbackView,
    is_admin_or_developer,
    may_review_feedback,
)
from util.enums import LanguageCode

HOME_SERVER = 111
FOREIGN_SERVER = 222


@patch.dict("os.environ", {"DISCORD_SERVER_ID": str(HOME_SERVER)})
class TestAdminUtils(unittest.TestCase):
    """ OSCAR is a public bot. Anybody can invite it to a server of their own and is
        the administrator there, so "administrator" alone must open nothing.
    """

    def test_is_admin_or_developer_developer(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = DEVELOPER_IDS[0]
        interaction.guild_id = FOREIGN_SERVER
        self.assertTrue(is_admin_or_developer(interaction))

    def test_is_admin_or_developer_admin(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.guild_id = HOME_SERVER
        interaction.user.guild_permissions.administrator = True
        self.assertTrue(is_admin_or_developer(interaction))

    def test_an_admin_of_another_server_is_a_stranger(self):
        """The hole: `/review_feedback` on a server the attacker made themselves."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.guild_id = FOREIGN_SERVER
        interaction.user.guild_permissions.administrator = True
        self.assertFalse(is_admin_or_developer(interaction))

    def test_is_admin_or_developer_nobody(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.guild_id = HOME_SERVER
        interaction.user.guild_permissions.administrator = False
        self.assertFalse(is_admin_or_developer(interaction))

    def test_a_direct_message_has_no_administrator(self):
        """A plain user carries no `guild_permissions`, that used to raise."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.User)
        interaction.user.id = 12345
        interaction.guild_id = None
        self.assertFalse(is_admin_or_developer(interaction))

    def test_a_missing_home_server_closes_the_command(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.guild_id = None
        interaction.user.guild_permissions.administrator = True
        with patch.dict("os.environ", {"DISCORD_SERVER_ID": ""}):
            self.assertFalse(is_admin_or_developer(interaction))


@patch.dict("os.environ", {"DISCORD_SERVER_ID": str(HOME_SERVER)})
class TestMayReviewFeedback(unittest.IsolatedAsyncioTestCase):
    async def test_the_owner_of_the_application_may(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.guild_id = FOREIGN_SERVER
        interaction.user.guild_permissions.administrator = False
        interaction.client.is_owner = AsyncMock(return_value=True)
        self.assertTrue(await may_review_feedback(interaction))

    async def test_a_foreign_admin_may_not(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.guild_id = FOREIGN_SERVER
        interaction.user.guild_permissions.administrator = True
        interaction.client.is_owner = AsyncMock(return_value=False)
        self.assertFalse(await may_review_feedback(interaction))

    def test_the_command_carries_the_check(self):
        """A check that exists but is not attached protects nothing."""
        self.assertIn(may_review_feedback, Administration.review_feedback.checks)


class TestAdministrationCog(unittest.IsolatedAsyncioTestCase):
    async def test_review_feedback_command(self):
        bot = MagicMock(spec=commands.Bot)
        cog = Administration(bot)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        mock_db = MagicMock()
        mock_db.get_feedback.return_value = [{"timestamp": 123, "intuitiveness": 5}]

        with patch("oscar.cogs.admin.get_database", return_value=mock_db), \
             patch("oscar.cogs.admin.create_feedback_boxplot", new_callable=AsyncMock) as mock_box, \
             patch("oscar.cogs.admin.create_feedback_timeline", new_callable=AsyncMock) as mock_line, \
             patch("oscar.cogs.admin.ReviewFeedbackView") as MockView:

            mock_box.return_value = MagicMock(spec=discord.File)
            mock_line.return_value = MagicMock(spec=discord.File)

            await cog.review_feedback.callback(cog, interaction)

        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()
        MockView.assert_called_once()
        # the plots are built from what students wrote, the channel must not see them
        self.assertTrue(interaction.response.defer.call_args.kwargs.get("ephemeral"))
        self.assertTrue(interaction.followup.send.call_args.kwargs.get("ephemeral"))

    async def test_setup(self):
        from oscar.cogs.admin import setup
        bot = MagicMock(spec=commands.Bot)
        bot.add_cog = AsyncMock()
        await setup(bot)
        bot.add_cog.assert_called_once()

class TestReviewFeedbackView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.interaction = MagicMock(spec=discord.Interaction)
        self.interaction.user.id = 123
        self.feedback = [{"timestamp": 1000, "intuitiveness": 5}]
        self.images = [MagicMock(spec=discord.File), MagicMock(spec=discord.File)]

        self.component_names = [
            "ActionRow", "Button", "Container", "Section",
            "MediaGallery", "MediaGalleryItem", "TextDisplay", "Separator"
        ]
        self.patchers = []
        self.mocks = {}

        for name in self.component_names:
            p = patch(f"oscar.cogs.admin.{name}")
            self.patchers.append(p)
            mock_class = p.start()
            self.mocks[name] = mock_class

            # Configure mock instance to behave like a discord.ui.Item
            instance = mock_class.return_value
            instance.spec = discord.ui.Item
            instance.__class__ = discord.ui.Item # Hack for isinstance check
            instance.width = 1
            # discord.py internals use _total_count or similar
            instance._total_count = 1
            # ActionRow specific? ActionRow has no width limit?

        self.MockButton = self.mocks["Button"]

    def tearDown(self):
        for p in reversed(self.patchers):
            p.stop()

    async def test_init_periods_logic_default(self):
        # Test default periods processing
        view = ReviewFeedbackView(self.interaction, self.feedback, self.images)
        self.assertTrue(len(view.periods) > 0)
        self.assertIsNone(view.periods[-1])

    async def test_init_periods_logic_empty(self):
        with patch.object(ReviewFeedbackView, 'periods', [None]):
            view = ReviewFeedbackView(self.interaction, self.feedback, self.images)
            self.assertEqual(view.periods, [None])

    async def test_init_periods_logic_many(self):
        # Create a subclass with many periods to trigger filtering
        class ManyPeriodsView(ReviewFeedbackView):
            periods = list(range(100)) + [None]

        view = ManyPeriodsView(self.interaction, self.feedback, self.images)
        self.assertTrue(len(view.periods) <= 6) # 5 + None
        self.assertIsNone(view.periods[-1])

    async def test_check_user_authorized(self):
        view = ReviewFeedbackView(self.interaction, self.feedback, self.images)
        self.interaction.user = MagicMock()
        check_interaction = MagicMock(spec=discord.Interaction)
        check_interaction.user = self.interaction.user
        self.assertTrue(await view.check_user(check_interaction))

    async def test_check_user_unauthorized(self):
        view = ReviewFeedbackView(self.interaction, self.feedback, self.images)
        self.interaction.user = MagicMock()
        check_interaction = MagicMock(spec=discord.Interaction)
        check_interaction.user = MagicMock() # Different user
        check_interaction.response.send_message = AsyncMock()

        self.assertFalse(await view.check_user(check_interaction))
        check_interaction.response.send_message.assert_called_once()

    async def test_filter_feedback(self):
        view = ReviewFeedbackView(self.interaction, self.feedback, self.images)
        view.selected_zoom = None
        self.assertEqual(len(view.feedback_filtered), 1)

        with patch("time.time", return_value=2000):
            view.selected_zoom = 500 # timestamp 1000, diff 1000 > 500 -> filtered out
            # Call private method
            view._ReviewFeedbackView__filter_feedback()
            self.assertEqual(len(view.feedback_filtered), 0)

            view.selected_zoom = 1500 # diff 1000 <= 1500 -> kept
            view._ReviewFeedbackView__filter_feedback()
            self.assertEqual(len(view.feedback_filtered), 1)

    async def test_update(self):
        view = ReviewFeedbackView(self.interaction, self.feedback, self.images)
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        with patch.object(view, '_create_boxplot_image', new_callable=AsyncMock) as _, \
             patch.object(view, '_create_timeline_image', new_callable=AsyncMock) as _:

             await view._update(interaction)

             interaction.response.defer.assert_called_once()
             interaction.edit_original_response.assert_called_once()

    async def test_create_images(self):
        view = ReviewFeedbackView(self.interaction, self.feedback, self.images)
        with patch("oscar.cogs.admin.create_feedback_boxplot", new_callable=AsyncMock) as mock_box:
            await view._create_boxplot_image()
            mock_box.assert_called_once()

        with patch("oscar.cogs.admin.create_feedback_timeline", new_callable=AsyncMock) as mock_line:
            await view._create_timeline_image()
            mock_line.assert_called_once()

    async def test_callbacks_via_traversal(self):
        """Test callbacks by finding buttons in the view hierarchy."""
        # Unpatch Button so we get real objects (or mocks that behave like them if we prefer,
        # but better to use the real view structure if possible).
        # However, TestReviewFeedbackView.setUp patches 'Button' and 'ActionRow' etc.
        # We need to unpatch them to let ReviewFeedbackView build the real structure
        # OR ensure the mocks reflect the structure.
        # The setUp mocks `Button` to return a `MagicMock`.
        # Passing `Container(Section(..., Button(...)))` means passing Mocks.
        # If we rely on the Mocks, we can't easily traverse `children` unless we set them up.

        # Strategy:
        # 1. Stop the patchers for this test to use real classes if available?
        #    But `Container`, `Section`, `MediaGallery` might need Discord connection or strict state?
        #    Typically discord.ui.View works offline if we don't send it.
        # 2. Configure the mocks in setUp to actually store children?

        # Let's try to unpatch for this test to rely on real logic if imports allow.
        # We imported them in the test file from `oscar.cogs.admin`.
        # If they are available, we can use them.

        # Reverting mocks:
        for p in self.patchers:
            p.stop()

        # We need to mock functions that ReviewFeedbackView calls:
        # - format_duration
        # - translations
        # - database/plots (already mocked in methods, but we need them here)

        try:
            view = ReviewFeedbackView(self.interaction, self.feedback, self.images)

            # Now traverse view.children
            buttons = []

            def traverse(items):
                for item in items:
                    if isinstance(item, discord.ui.Button):
                        buttons.append(item)

                    # Check for nested structures
                    # ActionRow?
                    if isinstance(item, discord.ui.ActionRow):
                        traverse(item.children)

                    # Container / Section (if they are custom or new discord.ui items)
                    # We might need to check attributes dynamically since we don't know their exact API
                    has_children = getattr(item, "children", [])
                    if has_children:
                        traverse(has_children)

                    # Section might have 'accessory'
                    accessory = getattr(item, "accessory", None)
                    if accessory:
                        traverse([accessory])

                    # Items might be in 'rows' or 'items' ?
                    # Let's assume 'children' covers most.

            traverse(view.children)

            # Identify buttons
            # We expect time span buttons and download button.
            time_buttons = [b for b in buttons if b.label and ("h" in b.label or "d" in b.label or "w" in b.label)]
            download_btn = next((b for b in buttons if b.label == "⤓"), None)

            # Verify we found them
            # If structure is mocked/wrong, this will fail.
            # If standard discord.py, View.children should have them.
            # But wait, ReviewFeedbackView uses `Container` from `discord.ui`.
            # If these are real classes, we should find them.

            if not buttons and len(view.children) > 0:
                 # Debug: inspect children types
                 pass

            # Note: If `discord.py` version in environment doesn't strictly match or if `Container` is a mock
            # (if we didn't unpatch correctly), this might fail.
            # But we stopped patchers.

            self.assertTrue(download_btn is not None, "Download button not found")

            # Test Download Callback
            cba = download_btn.callback
            self.assertTrue(callable(cba))

            # Invoke callback
            view.check_user = AsyncMock(return_value=True)
            mock_inter = MagicMock(spec=discord.Interaction)
            mock_inter.user = self.interaction.user
            mock_inter.response.send_message = AsyncMock()

            await cba(mock_inter)
            mock_inter.response.send_message.assert_called_once()

            # Test Time Span Callback
            if time_buttons:
                btn = time_buttons[0]
                cbb = btn.callback
                self.assertTrue(callable(cbb))

                view._update = AsyncMock()
                mock_inter.reset_mock()

                await cbb(mock_inter)
                view._update.assert_called_once()

        finally:
            # Restore patchers for other tests (teardown does it too, but safe to restart if needed?
            # toggle setUp/tearDown handles it per test method)
            # unittest tears down after test, so stopping patchers here is fine as long as we don't leak.
            pass
