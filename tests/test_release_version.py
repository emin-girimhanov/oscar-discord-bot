"""Tests for the release version tool that the CI pipeline runs on the default branch.

The tool lives in `tools/`, which is not an importable package, so the module is loaded from its
file. Every test works on synthetic commit messages and on a temporary pyproject.toml. None of
them touches the real repository, creates a tag or talks to GitLab.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "tools" / "release_version.py"


def _load_module():
    """Loads tools/release_version.py as a module."""
    spec = importlib.util.spec_from_file_location("release_version", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["release_version"] = module
    spec.loader.exec_module(module)
    return module


release_version = _load_module()


PYPROJECT_TEMPLATE = """[build-system]
requires = ["hatchling >= 1.27"]

[project]
name = "oscar_ovgu"
version = "1.2.3"
description = "Organized Study Choice & Academic Roadmapper"

[project.optional-dependencies]
dev = ["pytest>=8.0.0"]
"""


@pytest.fixture
def pyproject(tmp_path: Path) -> Path:
    """Writes a small pyproject.toml into a temporary directory."""
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT_TEMPLATE, encoding="utf-8")
    return path


class TestClassifyCommit:
    """The mapping from a commit message to a version step, see README.md."""

    @pytest.mark.parametrize(
        "message, expected",
        [
            ("fix(db): resolve connection timeout", "patch"),
            ("perf(module): cache the catalog lookup", "patch"),
            ("feat(ui): add new timetable view", "minor"),
            ("feat: add a command without a scope", "minor"),
            ("feat!: drop the old command names", "major"),
            ("feat(api)!: rename every endpoint", "major"),
            ("fix!: change the database path", "major"),
            ("docs(readme): update setup steps", "none"),
            ("chore(ci): update pipeline image", "none"),
            ("style(lint): fix pylint errors", "none"),
            ("refactor(auth): simplify login logic", "none"),
            ("test(api): add unit test for login", "none"),
            ("Merge branch 'feat/compare-modules' into 'develop'", "none"),
            ("just some words without a type", "none"),
            ("", "none"),
        ],
    )
    def test_header_decides_the_step(self, message: str, expected: str):
        assert release_version.classify_commit(message) == expected

    def test_breaking_change_footer_wins_over_the_type(self):
        message = "feat(db): move the database\n\nBREAKING CHANGE: the old path is gone."
        assert release_version.classify_commit(message) == "major"

    def test_breaking_change_footer_with_a_hyphen_is_accepted(self):
        message = "fix(db): move the database\n\nBREAKING-CHANGE: the old path is gone."
        assert release_version.classify_commit(message) == "major"

    def test_breaking_change_in_the_subject_is_not_a_footer(self):
        # Only a real footer counts, otherwise a commit that talks about one would bump the major.
        message = "docs(readme): explain what a BREAKING CHANGE: footer looks like"
        assert release_version.classify_commit(message) == "none"

    def test_the_type_is_case_insensitive(self):
        assert release_version.classify_commit("FEAT(ui): add a view") == "minor"


class TestDecideBump:
    """The largest step among all commits wins."""

    def test_the_largest_step_wins(self):
        messages = ["docs: a", "fix: b", "feat: c", "chore: d"]
        assert release_version.decide_bump(messages) == "minor"

    def test_a_single_breaking_commit_wins(self):
        messages = ["fix: a", "feat: b", "refactor!: c"]
        assert release_version.decide_bump(messages) == "major"

    def test_no_relevant_commit_means_no_step(self):
        messages = ["docs: a", "chore: b", "Merge branch 'x' into 'develop'"]
        assert release_version.decide_bump(messages) == "none"

    def test_an_empty_history_means_no_step(self):
        assert release_version.decide_bump([]) == "none"


class TestBumpVersion:
    """The arithmetic behind the README table."""

    @pytest.mark.parametrize(
        "base, bump, expected",
        [
            ("1.0.0", "patch", "1.0.1"),
            ("1.0.0", "minor", "1.1.0"),
            ("1.0.0", "major", "2.0.0"),
            ("1.2.3", "minor", "1.3.0"),
            ("1.2.3", "major", "2.0.0"),
            ("0.2.0", "minor", "0.3.0"),
            ("1.2.3", "none", "1.2.3"),
        ],
    )
    def test_steps(self, base: str, bump: str, expected: str):
        assert release_version.bump_version(base, bump) == expected

    def test_a_major_step_resets_minor_and_patch(self):
        assert release_version.bump_version("3.7.9", "major") == "4.0.0"

    def test_a_minor_step_resets_patch(self):
        assert release_version.bump_version("3.7.9", "minor") == "3.8.0"

    def test_an_unknown_step_fails_loudly(self):
        with pytest.raises(release_version.ReleaseError):
            _ = release_version.bump_version("1.0.0", "enormous")


class TestParseVersion:
    """A version that cannot be read must stop the pipeline instead of becoming a guess."""

    def test_a_plain_version_is_read(self):
        assert release_version.parse_version("10.20.30") == (10, 20, 30)

    @pytest.mark.parametrize("text", ["1.2", "v1.2.3", "1.2.3-rc1", "", "not a version", "1.2.3.4"])
    def test_anything_else_fails_loudly(self, text: str):
        with pytest.raises(release_version.ReleaseError):
            _ = release_version.parse_version(text)


class TestPyprojectRoundTrip:
    """Reading and writing the version must leave the rest of the file untouched."""

    def test_the_version_is_read_from_the_project_table(self, pyproject: Path):
        assert release_version.read_pyproject_version(pyproject) == "1.2.3"

    def test_writing_only_changes_the_version_line(self, pyproject: Path):
        release_version.write_pyproject_version(pyproject, "2.0.0")
        written = pyproject.read_text(encoding="utf-8")

        assert 'version = "2.0.0"' in written
        assert 'version = "1.2.3"' not in written
        # Everything around it survives, including the comment-free build table and the extras.
        assert 'requires = ["hatchling >= 1.27"]' in written
        assert 'name = "oscar_ovgu"' in written
        assert 'dev = ["pytest>=8.0.0"]' in written

    def test_a_second_write_is_read_back(self, pyproject: Path):
        release_version.write_pyproject_version(pyproject, "2.0.0")
        release_version.write_pyproject_version(pyproject, "2.1.0")
        assert release_version.read_pyproject_version(pyproject) == "2.1.0"

    def test_a_version_outside_the_project_table_is_ignored(self, tmp_path: Path):
        path = tmp_path / "pyproject.toml"
        path.write_text(
            '[tool.something]\nversion = "9.9.9"\n\n[project]\nname = "x"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )

        assert release_version.read_pyproject_version(path) == "1.0.0"

        release_version.write_pyproject_version(path, "1.1.0")
        written = path.read_text(encoding="utf-8")
        assert 'version = "9.9.9"' in written
        assert 'version = "1.1.0"' in written

    def test_a_missing_file_fails_loudly(self, tmp_path: Path):
        with pytest.raises(release_version.ReleaseError):
            _ = release_version.read_pyproject_version(tmp_path / "nothing.toml")

    def test_a_missing_version_entry_fails_loudly(self, tmp_path: Path):
        path = tmp_path / "pyproject.toml"
        path.write_text('[project]\nname = "x"\n', encoding="utf-8")

        with pytest.raises(release_version.ReleaseError):
            _ = release_version.read_pyproject_version(path)

    def test_the_real_pyproject_is_readable(self):
        # Guards against someone reformatting the version line out of the tool's reach.
        version = release_version.read_pyproject_version(REPO_ROOT / "pyproject.toml")
        assert release_version.parse_version(version)


class TestReleaseNotes:
    """The release description groups the commits the release is made of."""

    def test_the_groups_carry_their_commits(self):
        messages = [
            "feat(ui): add a view",
            "fix(db): close the connection",
            "feat(api)!: rename an endpoint",
            "docs: explain it",
        ]
        notes = release_version.build_notes("2.0.0", "v1.4.2", messages)

        assert "# OSCAR 2.0.0" in notes
        assert "Changes since `v1.4.2`." in notes
        assert "## Breaking changes" in notes
        assert "* feat(api)!: rename an endpoint" in notes
        assert "## Features" in notes
        assert "* feat(ui): add a view" in notes
        assert "## Fixes" in notes
        assert "* fix(db): close the connection" in notes
        # A docs commit is part of no group, so it stays out of the description.
        assert "explain it" not in notes

    def test_the_first_release_says_so(self):
        notes = release_version.build_notes("0.3.0", None, ["feat: a"])
        assert "First automated release" in notes

    def test_an_empty_group_gets_no_heading(self):
        notes = release_version.build_notes("1.0.1", "v1.0.0", ["fix: a"])
        assert "## Fixes" in notes
        assert "## Features" not in notes
        assert "## Breaking changes" not in notes


class TestEnvFile:
    """The handover file that the following CI jobs read."""

    def test_every_variable_is_written(self, tmp_path: Path):
        path = tmp_path / "release.env"
        release_version.write_env_file(path, {"RELEASE_BUMP": "minor", "RELEASE_TAG": "v1.3.0"})

        lines = path.read_text(encoding="utf-8").splitlines()
        assert "RELEASE_BUMP=minor" in lines
        assert "RELEASE_TAG=v1.3.0" in lines


class TestDryRun:
    """A dry run must be able to answer the question without changing anything."""

    def test_a_dry_run_leaves_pyproject_alone(self, tmp_path: Path, pyproject: Path):
        env_file = tmp_path / "release.env"
        before = pyproject.read_text(encoding="utf-8")

        exit_code = release_version.main(
            ["--base", "1.2.3", "--pyproject", str(pyproject), "--env-file", str(env_file)]
        )

        assert exit_code == 0
        assert pyproject.read_text(encoding="utf-8") == before
        # The answer is still handed over, so a dry run in CI can print what it would produce.
        assert "RELEASE_VERSION=" in env_file.read_text(encoding="utf-8")

    def test_a_write_run_updates_pyproject(self, tmp_path: Path, pyproject: Path):
        env_file = tmp_path / "release.env"
        notes_file = tmp_path / "release_notes.md"

        exit_code = release_version.main(
            [
                "--write",
                "--base",
                "1.2.3",
                "--pyproject",
                str(pyproject),
                "--env-file",
                str(env_file),
                "--notes-file",
                str(notes_file),
            ]
        )

        assert exit_code == 0
        env = env_file.read_text(encoding="utf-8")
        bump = [line for line in env.splitlines() if line.startswith("RELEASE_BUMP=")][0].split("=", 1)[1]
        written = release_version.read_pyproject_version(pyproject)

        if bump == "none":
            # The repository history decides the step, so both outcomes are legitimate here.
            assert written == "1.2.3"
        else:
            assert written == release_version.bump_version("1.2.3", bump)
            assert notes_file.exists()

    def test_an_unreadable_base_stops_the_run(self, pyproject: Path):
        with pytest.raises(release_version.ReleaseError):
            _ = release_version.main(["--base", "not-a-version", "--pyproject", str(pyproject)])
