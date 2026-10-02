""" Every documentation page has to survive the macros plugin.

    `mkdocs-macros` runs each page through Jinja before it becomes html, code blocks
    included. A shell command with a Go template in it,

        docker volume inspect -f '{{ .Mountpoint }}' discord-bot_oscar-db

    is not valid Jinja. The plugin replaced the **whole page** with "Macro Syntax
    Error". Version 1.5 of the plugin did that silently, so `mkdocs build --strict`
    passed on the machine the page was written on. The current version warns, strict
    mode turns the warning into a failure, and the pipeline on GitHub stopped
    publishing the documentation for four pushes in a row before anybody looked.

    The plugin version is not pinned, so the local build cannot be trusted to behave
    like the pipeline. This test asks Jinja directly, which behaves the same everywhere.
"""

import re
from pathlib import Path

import pytest


jinja2 = pytest.importorskip("jinja2", reason="the docs extras are not installed")

REPO = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO / "docs"

PAGES = sorted(DOCS_DIR.rglob("*.md"))

# what `docs/main.py` registers with `@env.macro`, plus what the plugin brings along
MACRO = re.compile(r"^\s*def\s+([a-z_]+)\(", re.MULTILINE)
BUILT_IN = {"now", "fix_url", "context", "macros_info"}

# a call such as `{{ project_info() | indent(4) }}`
CALL = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")


def defined_macros() -> set[str]:
    source = (DOCS_DIR / "main.py").read_text(encoding="utf8")
    return set(MACRO.findall(source)) | BUILT_IN


def test_there_are_pages_to_check():
    assert len(PAGES) > 20


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(DOCS_DIR).as_posix())
def test_the_page_is_valid_jinja(page: Path):
    """ A page that is not, is replaced by an error message when the site is built."""
    text = page.read_text(encoding="utf8")
    try:
        _ = jinja2.Environment().parse(text)
    except jinja2.TemplateSyntaxError as error:
        line = text.splitlines()[error.lineno - 1].strip()
        pytest.fail(
            f"line {error.lineno}: {error.message}\n    {line}\n"
            "Write the example without `{{` and `}}`, or wrap it in "
            "{% raw %} and {% endraw %}."
        )


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(DOCS_DIR).as_posix())
def test_every_macro_a_page_calls_exists(page: Path):
    """An unknown name renders as nothing, and a section silently goes missing."""
    called = set(CALL.findall(page.read_text(encoding="utf8")))
    unknown = called - defined_macros()
    assert not unknown, f"{sorted(unknown)} is not defined in docs/main.py"
