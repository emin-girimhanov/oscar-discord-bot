""" Resolves where runtime data lives, for local runs from the repo and inside the container."""

import os
from pathlib import Path

# only valid when running from a source checkout, the installed wheel has no assets next to it
_REPO_ROOT: Path = Path(__file__).resolve().parents[2]


def assets_dir() -> Path:
    """ Directory holding images and semesterplan json files.

        Uses `OSCAR_ASSETS_DIR` if set (the container sets it to `/assets`).
    """
    return Path(os.environ.get("OSCAR_ASSETS_DIR", _REPO_ROOT / "assets"))
