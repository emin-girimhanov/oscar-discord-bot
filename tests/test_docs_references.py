"""Every mkdocstrings reference in the documentation must point at code that exists.

A rename in `src` that forgets the documentation does not fail any other test. It fails
the `pages` job, and only on the default branch, which is the worst place to find out.
That happened once: `oscar.cogs.help.Test` was renamed to `Help` and the release
pipeline aborted with `Could not collect 'src.oscar.cogs.help.Test'`.
"""

import importlib
import re
from pathlib import Path

import pytest


DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

# mkdocstrings pulls a symbol into a page with a line like `::: src.util.module.Module`
REFERENCE = re.compile(r"^:::\s*(src\.[A-Za-z0-9_.]+)", re.MULTILINE)


def _references() -> list[tuple[str, str]]:
    """Collects every documented symbol as `(page, dotted name)`."""
    found: list[tuple[str, str]] = []
    for page in sorted(DOCS_DIR.rglob("*.md")):
        for match in REFERENCE.finditer(page.read_text(encoding="utf8")):
            found.append((page.relative_to(DOCS_DIR).as_posix(), match.group(1)))
    return found


def _resolves(reference: str) -> bool:
    """Tells whether a dotted name can still be imported and reached.

    The leading `src.` is a path prefix for mkdocstrings, not part of the package, so
    it is dropped. The split between module path and attribute path is unknown, so
    every split is tried, longest module first.
    """
    parts = reference[len("src.") :].split(".")

    for split in range(len(parts), 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:split]))
        except Exception:  # pylint: disable=W0718
            continue

        for attribute in parts[split:]:
            if not hasattr(obj, attribute):
                break
            obj = getattr(obj, attribute)
        else:
            return True

    return False


@pytest.mark.parametrize("page, reference", _references())
def test_documented_symbol_exists(page, reference):
    """A documented symbol that was renamed or removed aborts the whole site build."""
    assert _resolves(reference), (
        f"docs/{page} documents `{reference}`, which no longer exists. "
        "Update the page, or mkdocs aborts and the documentation site is not published."
    )


def test_the_documentation_references_the_code_at_all():
    """Guards against a broken pattern quietly collecting nothing."""
    assert len(_references()) > 20


@pytest.mark.parametrize("gone", [
    "src.oscar.cogs.help.Test",           # the real rename that broke the release
    "src.util.module.ModuleThatNeverWas",
    "src.util.does_not_exist",
])
def test_a_missing_symbol_is_detected(gone):
    """Proves the check can fail. A detector that always passes protects nothing."""
    assert not _resolves(gone)
