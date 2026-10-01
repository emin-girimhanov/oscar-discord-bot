import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Set default env vars for testing (won't override real values)
os.environ.setdefault("TABLES_URL", "http://dummy/")
os.environ.setdefault("TABLES_USERNAME", "dummy")
os.environ.setdefault("TABLES_PASSWORD", "dummy")

# Add src to sys.path to allow importing modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# The scripts in tools/ are not part of the package, but the rules they hold are worth
# testing. `generate_bookstack_map` picks which handbook book a programme is linked to,
# and picking the wrong one is silent.
tools_path = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(tools_path))

import asyncio
_real_get_running_loop = asyncio.get_running_loop

def _safe_get_running_loop():
    try:
        return _real_get_running_loop()
    except RuntimeError:
        mock_loop = MagicMock()
        mock_loop.create_future.return_value = MagicMock()
        return mock_loop

asyncio.get_running_loop = _safe_get_running_loop

import pytest  # noqa: E402

@pytest.fixture
def sample_module_dict():
    return {
        "Identifizierung": 123,
        "Modulsprache": 1, # DE
        "Status": 1,
        "Modultitel": "Test Modul",
        "Modultitel (englisch)": "Test Module",
        "Lehrstuhl": 1,
        "Modulverantwortung": "Prof. X",
        "Dozent:in": "Dr. Y",
        "Credit Points": "5",
        "Semesterlage": 1,
        "Fachsemester": 1,
        "Angestrebte Lernergebnisse": "Lernen",
        "Inhalt": "Inhalt",
        "Verwendbarkeit B.Sc. INF": []
    }

@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get and return a specific JSON response."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_get.return_value = mock_response
        yield mock_get, mock_response


@pytest.fixture(autouse=True)
def reset_tables_cache():
    """Fixture to reset the tables in-memory cache before and after every test."""
    try:
        from util.tables import clear_tables_cache
        clear_tables_cache()
    except (ImportError, AttributeError):
        pass
    yield
    try:
        from util.tables import clear_tables_cache
        clear_tables_cache()
    except (ImportError, AttributeError):
        pass
