"""Tests for the main entry point."""

import pytest
from unittest.mock import patch, MagicMock

import discord


class TestMain:
    def test_main_success(self):
        """main() should create Oscar, call setup_bot, and run."""
        with patch("oscar.main.Oscar") as mock_oscar_cls:
            mock_oscar = MagicMock()
            mock_oscar.bot_token = "test_token"
            mock_oscar_cls.return_value = mock_oscar

            from oscar.main import main

            with patch.object(mock_oscar, "run"):
                main()
                mock_oscar.setup_bot.assert_called_once()
                mock_oscar.run.assert_called_once_with("test_token")

    def test_main_exception_exits(self):
        """If Oscar() raises, main() should sys.exit(1)."""
        with patch("oscar.main.Oscar", side_effect=RuntimeError("No env")):
            from oscar.main import main

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
