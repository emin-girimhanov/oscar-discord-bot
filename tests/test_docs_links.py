"""The documentation site is only reachable over plain http, and must stay written that way.

`studium-lehre.gitlabpages.cs.ovgu.de` refuses port 443. A browser sent to the `https`
address gets a connection error, not a warning it can click past. Rewriting the link to
`https` therefore looks like a security improvement and silently breaks it.

Only faculty IT can put a certificate on that host. Until they do, this test keeps the
scheme from being tidied up by someone who means well.
"""

import re
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent

PAGES_HOST = "studium-lehre.gitlabpages.cs.ovgu.de"

# any scheme in front of the host, so the test can say which one it found
LINK = re.compile(rf"(https?)://{re.escape(PAGES_HOST)}")

SKIP_DIRS = {".git", ".venv", "venv", "site", "node_modules", "__pycache__", ".idea"}

SEARCHED_SUFFIXES = {".md", ".yml", ".yaml", ".py", ".toml", ".cfg", ".txt"}


def _text_files() -> list[Path]:
    """Every file in the repository that could carry the link."""
    found: list[Path] = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in SEARCHED_SUFFIXES:
            continue
        if SKIP_DIRS.intersection(path.relative_to(REPO).parts):
            continue
        found.append(path)
    return found


@pytest.mark.parametrize("path", _text_files(), ids=lambda p: p.relative_to(REPO).as_posix())
def test_the_pages_link_is_never_https(path):
    """An https link to the pages host is a dead link, not a safer one."""
    for scheme in LINK.findall(path.read_text(encoding="utf8", errors="replace")):
        assert scheme == "http", (
            f"{path.relative_to(REPO).as_posix()} links to {PAGES_HOST} over https. "
            "That host refuses port 443, so the link does not answer. Use http until "
            "faculty IT provides a certificate."
        )


def test_the_link_is_actually_written_down():
    """Guards against the pattern quietly matching nothing after a rename."""
    carriers = {
        path.relative_to(REPO).as_posix()
        for path in _text_files()
        if LINK.search(path.read_text(encoding="utf8", errors="replace"))
    }
    assert "README.md" in carriers
    # the public copy builds its own site on GitHub Pages, so `mkdocs.yml` no longer
    # names the faculty host. The legal notice still points readers to it.
    assert "docs/legal_notice.md" in carriers


@pytest.mark.parametrize("line", [
    f"> **Documentation:** <https://{PAGES_HOST}/discord-bot>",
    f'site_url: "https://{PAGES_HOST}/discord-bot"',
])
def test_an_https_link_is_detected(line):
    """Proves the check can fail. A guard that always passes guards nothing."""
    assert LINK.findall(line) == ["https"]
