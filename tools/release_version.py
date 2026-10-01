#!/usr/bin/env python3
"""Works out the next release version from the conventional commits since the last tag.

The pipeline runs this on the default branch. It reads the git history, decides whether the
next version is a patch, a minor or a major step, and hands the result to the jobs that build
the wheel, the container image, the documentation and the GitLab release.

Run it without arguments for a dry run. A dry run changes no file and creates no tag, it only
prints what a real run would produce. Pass `--write` to update `pyproject.toml` and to write the
handover files.

The rules follow the table in `README.md`:

* `fix` and `perf` move the PATCH number.
* `feat` moves the MINOR number.
* A `!` after the type or scope, or a `BREAKING CHANGE:` footer, moves the MAJOR number.
* Every other type, and every commit that is not a conventional commit, moves nothing.

The script exits with code 0 when it knows the answer, even when the answer is "release nothing".
It exits with code 1 when it cannot work the version out. The pipeline must then stop, because a
guessed tag is worse than a failed job.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PYPROJECT = REPO_ROOT / "pyproject.toml"

# Tags look like `v1.2.3`. The glob keeps `git describe` away from any other tag.
TAG_PREFIX = "v"
TAG_GLOB = "v[0-9]*"

# Conventional commit types that move the patch number.
PATCH_TYPES = frozenset({"fix", "perf"})
# Conventional commit types that move the minor number.
MINOR_TYPES = frozenset({"feat"})

BUMP_NONE = "none"
BUMP_PATCH = "patch"
BUMP_MINOR = "minor"
BUMP_MAJOR = "major"

# Highest wins when several commits ask for different steps.
BUMP_RANK: Dict[str, int] = {BUMP_NONE: 0, BUMP_PATCH: 1, BUMP_MINOR: 2, BUMP_MAJOR: 3}

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
# `type(scope)!: subject`, where scope and `!` are optional.
HEADER_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^()]*)\))?(?P<breaking>!)?:\s*(?P<subject>\S.*)$"
)
BREAKING_FOOTER_RE = re.compile(r"^BREAKING[ -]CHANGE\s*:", re.MULTILINE)


# Record separator between commits in the `git log` output. It cannot appear in a commit message.
RECORD_SEP = "\x1e"


class ReleaseError(RuntimeError):
    """Raised when the next version cannot be worked out. This always stops the pipeline."""


def run_git(*args: str) -> str:
    """Runs a git command in the repository and returns its standard output."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise ReleaseError(f"Cannot run git: {exc}") from exc

    if result.returncode != 0:
        command = " ".join(["git", *args])
        raise ReleaseError(
            f"`{command}` failed with code {result.returncode}: {result.stderr.strip()}"
        )

    return result.stdout



def parse_version(text: str) -> Tuple[int, int, int]:
    """Turns `1.2.3` into `(1, 2, 3)`."""
    match = SEMVER_RE.match(text.strip())
    if not match:
        raise ReleaseError(f"'{text}' is not a MAJOR.MINOR.PATCH version")

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_version(version: Tuple[int, int, int]) -> str:
    """Turns `(1, 2, 3)` into `1.2.3`."""
    return f"{version[0]}.{version[1]}.{version[2]}"


def read_pyproject_version(pyproject: Path) -> str:
    """Reads the version out of the `[project]` table of pyproject.toml."""
    if not pyproject.exists():
        raise ReleaseError(f"{pyproject} does not exist")

    text = _read_preserving_newlines(pyproject)
    match = _project_version_match(text)
    if not match:
        raise ReleaseError(f"{pyproject} has no `version` entry in its [project] table")

    return match.group("version")


def _read_preserving_newlines(path: Path) -> str:
    """Reads a text file without translating its line endings, so a rewrite keeps them."""
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _project_version_match(text: str) -> Optional[re.Match[str]]:
    """Finds the `version = "..."` line that belongs to the `[project]` table.

    pyproject.toml holds several tables and more than one of them may carry a version one day.
    The search therefore starts at the `[project]` header and stops at the next table header.
    """
    project_header = re.search(r"^\[project\]\s*$", text, re.MULTILINE)
    if not project_header:
        return None

    start = project_header.end()
    next_header = re.search(r"^\[", text[start:], re.MULTILINE)
    end = start + next_header.start() if next_header else len(text)

    section = text[start:end]
    match = re.search(
        r"^(?P<prefix>version\s*=\s*[\"'])(?P<version>[^\"']+)(?P<suffix>[\"'])",
        section,
        re.MULTILINE,
    )
    if not match:
        return None

    # Re-run the search on the whole text so the caller gets offsets it can use for a rewrite.
    escaped_ver = re.escape(match.group("version"))
    pattern = rf"(?P<prefix>version\s*=\s*[\"'])(?P<version>{escaped_ver})(?P<suffix>[\"'])"
    return re.compile(pattern).search(text, start, end)


def write_pyproject_version(pyproject: Path, version: str) -> None:
    """Writes a new version into the `[project]` table and leaves the rest of the file alone."""
    text = _read_preserving_newlines(pyproject)
    match = _project_version_match(text)
    if not match:
        raise ReleaseError(f"{pyproject} has no `version` entry in its [project] table")

    updated = (
        text[: match.start()]
        + match.group("prefix")
        + version
        + match.group("suffix")
        + text[match.end() :]
    )
    with open(pyproject, "w", encoding="utf-8", newline="") as handle:
        _ = handle.write(updated)



def last_tag() -> Optional[str]:
    """Returns the newest release tag that HEAD can reach, or None when there is none yet."""
    try:
        output = run_git("describe", "--tags", "--abbrev=0", "--match", TAG_GLOB, "HEAD")
    except ReleaseError:
        # `git describe` fails when no matching tag is reachable. That is a normal first release.
        return None

    tag = output.strip()
    return tag or None


def commit_messages(since_tag: Optional[str]) -> List[str]:
    """Returns the full message of every commit after `since_tag`, newest first."""
    revision_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    output = run_git("log", f"--format=%B{RECORD_SEP}", revision_range)

    return [message.strip() for message in output.split(RECORD_SEP) if message.strip()]


def classify_commit(message: str) -> str:
    """Decides which step a single commit message asks for."""
    header = message.strip().splitlines()[0] if message.strip() else ""
    match = HEADER_RE.match(header)
    if not match:
        # Merge commits and anything else that is not a conventional commit ask for nothing.
        return BUMP_NONE

    if match.group("breaking") or BREAKING_FOOTER_RE.search(message):
        return BUMP_MAJOR

    commit_type = match.group("type").lower()
    if commit_type in MINOR_TYPES:
        return BUMP_MINOR
    if commit_type in PATCH_TYPES:
        return BUMP_PATCH

    return BUMP_NONE


def decide_bump(messages: List[str]) -> str:
    """Returns the largest step that any of the commits asks for."""
    bump = BUMP_NONE
    for message in messages:
        candidate = classify_commit(message)
        if BUMP_RANK[candidate] > BUMP_RANK[bump]:
            bump = candidate

    return bump


def bump_version(base: str, bump: str) -> str:
    """Applies a step to a version.

    A major step resets minor and patch, a minor step resets patch.
    """
    major, minor, patch = parse_version(base)

    if bump == BUMP_MAJOR:
        return format_version((major + 1, 0, 0))
    if bump == BUMP_MINOR:
        return format_version((major, minor + 1, 0))
    if bump == BUMP_PATCH:
        return format_version((major, minor, patch + 1))
    if bump == BUMP_NONE:
        return format_version((major, minor, patch))

    raise ReleaseError(f"'{bump}' is not a known version step")


def tag_exists(tag: str) -> bool:
    """Reports whether a tag of that name is already in the repository."""
    output = run_git("tag", "--list", tag)
    return bool(output.strip())


def build_notes(version: str, previous_tag: Optional[str], messages: List[str]) -> str:
    """Renders the release description from the commits that went into the release."""
    groups: Dict[str, List[str]] = {BUMP_MAJOR: [], BUMP_MINOR: [], BUMP_PATCH: []}
    headings = {
        BUMP_MAJOR: "Breaking changes",
        BUMP_MINOR: "Features",
        BUMP_PATCH: "Fixes",
    }

    for message in messages:
        bump = classify_commit(message)
        if bump in groups:
            groups[bump].append(message.strip().splitlines()[0])

    lines = [f"# OSCAR {version}", ""]
    if previous_tag:
        lines.append(f"Changes since `{previous_tag}`.")
    else:
        lines.append("First automated release. It covers the whole history up to this commit.")
    lines.append("")

    for bump in (BUMP_MAJOR, BUMP_MINOR, BUMP_PATCH):
        subjects = groups[bump]
        if not subjects:
            continue
        lines.append(f"## {headings[bump]}")
        lines.append("")
        lines.extend(f"* {subject}" for subject in subjects)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_env_file(path: Path, values: Dict[str, str]) -> None:
    """Writes the handover file that the following CI jobs read as a dotenv report."""
    lines = [f"{key}={value}" for key, value in values.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Builds the command line."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "update pyproject.toml and write the handover files. "
            "Without it the run changes nothing."
        ),
    )
    parser.add_argument(
        "--base",
        default=None,
        help="start from this version instead of the last tag. Use it to seed the first release.",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=DEFAULT_PYPROJECT,
        help="path to pyproject.toml.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="write RELEASE_* variables here for the following CI jobs.",
    )
    parser.add_argument(
        "--notes-file",
        type=Path,
        default=None,
        help="write the release description here.",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Works the next version out and reports it. Returns the process exit code."""
    args = parse_arguments(argv)

    previous_tag = last_tag()
    if args.base is not None:
        base_version = args.base
        source = "the --base option"
    elif previous_tag is not None:
        base_version = previous_tag[len(TAG_PREFIX) :]
        source = f"the last tag {previous_tag}"
    else:
        base_version = read_pyproject_version(args.pyproject)
        source = f"{args.pyproject.name}, because the repository has no release tag yet"

    # Fails loudly when the base is not a version, instead of inventing one.
    _ = parse_version(base_version)

    messages = commit_messages(previous_tag)
    bump = decide_bump(messages)
    next_version = bump_version(base_version, bump)
    next_tag = f"{TAG_PREFIX}{next_version}"

    print(f"Base version {base_version}, taken from {source}.")
    print(
        f"Looked at {len(messages)} commit(s) since "
        f"{previous_tag or 'the start of the history'}."
    )
    print(f"Version step: {bump}.")

    if bump == BUMP_NONE:
        print(
            "No feat, fix, perf or breaking commit since the last tag. "
            "There is nothing to release."
        )
    else:
        print(f"Next version: {next_version} (tag {next_tag}).")
        if tag_exists(next_tag):
            raise ReleaseError(
                f"Tag {next_tag} already exists. Refusing to move it. "
                "Check whether an earlier pipeline already released this version."
            )

    if not args.write:
        print("Dry run, nothing was written. Pass --write to apply this.")
    else:
        if bump != BUMP_NONE:
            write_pyproject_version(args.pyproject, next_version)
            print(f"Wrote version {next_version} into {args.pyproject}.")
        if args.notes_file is not None:
            notes = build_notes(next_version, previous_tag, messages)
            args.notes_file.write_text(notes, encoding="utf-8")
            print(f"Wrote the release description into {args.notes_file}.")


    if args.env_file is not None:
        write_env_file(
            args.env_file,
            {
                "RELEASE_BUMP": bump,
                "RELEASE_VERSION": next_version,
                "RELEASE_TAG": next_tag,
                "RELEASE_PREVIOUS_TAG": previous_tag or "",
                "RELEASE_COMMIT_COUNT": str(len(messages)),
            },
        )
        print(f"Wrote the handover variables into {args.env_file}.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ReleaseError as error:
        print(f"Cannot determine the next version: {error}", file=sys.stderr)
        sys.exit(1)
