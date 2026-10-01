import functools
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import toml

# Path to pyproject.toml relative to this file (docs/main.py)
PYPROJECT_FILE = Path(__file__).resolve().parent.parent / "pyproject.toml"

# the bot's own source, so the FAQ on this site is the one the bot answers with
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@functools.lru_cache(maxsize=1)
def load_pyproject() -> Optional[Dict[str, Any]]:
    # loads and caches pyproject.toml so we don't open the file a million times
    if not PYPROJECT_FILE.exists():
        return None

    try:
        with open(PYPROJECT_FILE, "r", encoding="utf-8") as f:
            return toml.load(f)
    except Exception as e:
        # clear cache on failure so MkDocs live-reload can try again when file is fixed
        load_pyproject.cache_clear()
        raise RuntimeError(f"Failed to read pyproject.toml: {e}") from e


def get_project_metadata() -> Dict[str, Any]:
    # grabs project metadata like version and name directly from pyproject.toml
    data = load_pyproject()
    if not data or "project" not in data:
        return {}

    project = data["project"]
    version = project.get("version", "unknown")

    # checking if it's a beta built (e.g. 0.2.0)
    try:
        is_beta = int(version.split(".")[0]) == 0
    except (ValueError, IndexError):
        is_beta = False

    return {
        "name": project.get("name", "unknown"),
        "version": version,
        "is_beta": is_beta,
        "description": project.get("description", ""),
        "license": project.get("license", "unknown"),
        "requires_python": project.get("requires-python", "unknown"),
    }


def parse_version_spec(spec: str) -> Tuple[str, str]:
    # splits strings like "requests (>=2.0)" into ("requests", ">=2.0")
    match = re.match(r"([a-zA-Z0-9._-]+)(.*)", spec.strip())
    if not match:
        return spec, ""

    name, version = match.groups()
    return name.strip(), version.strip() or "any"


def extract_dependencies(data: Dict[str, Any]) -> Dict[str, List[str]]:
    # normalizes dependencies whether they use standard PEP 621, UV, or Poetry formats
    deps = {"main": [], "dev": [], "docs": []}

    # standard PEP 621
    if "project" in data and "dependencies" in data["project"]:
        deps["main"] = data["project"]["dependencies"]

    # poetry fallback
    elif "tool" in data and "poetry" in data["tool"]:
        poetry_deps = data["tool"]["poetry"].get("dependencies", {})
        deps["main"] = [
            f"{name} ({ver})" for name, ver in poetry_deps.items()
            if name.lower() != "python"
        ]

    # UV / PEP 735 dependency groups
    if "dependency-groups" in data:
        for group, items in data["dependency-groups"].items():
            if group in deps:
                deps[group] = items

    return deps


def render_faq(language: str = "en") -> str:
    """Renders the bot's FAQ as markdown.

    The questions and answers live in `src/util/translations.py`, because `/help` has
    to read them at runtime. Rendering the page from the same dictionaries means the
    site and the bot cannot say different things, which is what happened while the FAQ
    existed only here.
    """
    try:
        from util.enums import LanguageCode
        from util.translations import FAQ_ANSWERS, FAQ_QUESTIONS
    except ImportError as exc:
        return f"⚠️ **FAQ unavailable:** {exc}"

    code = LanguageCode.DE if language.lower().startswith("de") else LanguageCode.EN

    lines: List[str] = []
    for key, question in FAQ_QUESTIONS.items():
        lines.append(f"### {question[code]}")
        lines.append("")
        # one answer line per markdown line, the bot shows them the same way
        for answer_line in FAQ_ANSWERS[key][code].split("\n"):
            lines.append(answer_line)
            lines.append("")

    return "\n".join(lines)


def define_env(env):
    # mkdocs-macros hook. Registers custom macros for our templates
    # https://mkdocs-macros-plugin.readthedocs.io/

    # pyproject.toml is the only place that carries the version. mkdocs.yml used to keep a second
    # copy in `extra.version`, which drifted as soon as someone bumped one and forgot the other.
    # `env.conf` is the live MkDocs config, so writing into it here reaches the theme and every
    # page that reads `{{ config.extra.version }}`.
    env.conf.setdefault("extra", {})["version"] = get_project_metadata().get("version", "unknown")

    @env.macro
    def show_faq(language: str = "en") -> str:
        # renders the same questions and answers that `/help` shows in discord
        return render_faq(language)

    @env.macro
    def project_version() -> str:
        # simply returns the current version string
        return get_project_metadata().get("version", "unknown")
    @env.macro
    def project_badge(style: str = "inline") -> str:
        # returns either a text badge or a nice shields.io svg
        meta = get_project_metadata()
        version = meta.get("version", "unknown")
        is_beta = meta.get("is_beta", False)

        if style == "inline":
            badge = f"**v{version}**"
            if is_beta:
                badge += " 🔄 *Beta (Pre-Release)*"
            return badge

        if style == "shield":
            status = "beta" if is_beta else "stable"
            color = "orange" if is_beta else "green"
            return (
                f'![Version](https://img.shields.io/badge/version-{version}-{color}.svg?style=flat-square)\n'
                f'![Status](https://img.shields.io/badge/status-{status}-orange.svg?style=flat-square)'
            )

        return version

    @env.macro
    def project_info() -> str:
        """Renders a standard 'Project Information' admonition block."""
        meta = get_project_metadata()
        is_beta = meta.get("is_beta", False)
        status_badge = "🔄 **Beta (Pre-Release)**" if is_beta else "✅ **Stable**"

        return (
            '!!! info "Project Information"\n\n'
            f'    **Name:** {meta.get("name", "unknown")}  \n'
            f'    **Version:** `{meta.get("version", "unknown")}` {status_badge}  \n'
            f'    **Python:** {meta.get("requires_python", "unknown")}  \n'
            f'    **License:** {meta.get("license", "unknown")}  \n'
            f'    **Description:** {meta.get("description", "N/A")}\n'
        )

    @env.macro
    def project_badges_with_links(
        version_link: str = "about_oscar/",
        status_link: str = "https://discord.com/invite/m4vQhrK",
        license_link: str = "https://github.com/emin-girimhanov/oscar-discord-bot/blob/main/LICENSE"
    ) -> str:
        # renders the clickable shields.io badges for the top page header
        meta = get_project_metadata()
        version = meta.get("version", "unknown")
        is_beta = meta.get("is_beta", False)
        license_name = meta.get("license", "unknown")

        # shields.io breaks if we don't escape double hyphens (e.g. Apache-2.0 -> Apache--2.0)
        license_encoded = license_name.replace("-", "--")
        version_encoded = str(version).replace("-", "--")

        status = "beta" if is_beta else "stable"
        status_color = "bf616a" if is_beta else "a3be8c" # we use Nord theme colors here
        license_color = "a3be8c"

        return f"""
<div class="hero-badges">
    <a href="{version_link}"><img src="https://img.shields.io/badge/version-{version_encoded}-blue.svg?style=flat-square&color=2e3440" alt="Version"></a>
    <a href="{status_link}"><img src="https://img.shields.io/badge/status-{status}-orange.svg?style=flat-square&color={status_color}" alt="Status"></a>
    <a href="{license_link}"><img src="https://img.shields.io/badge/license-{license_encoded}-green.svg?style=flat-square&color={license_color}" alt="License"></a>
</div>
""".strip()

    @env.macro
    def show_tech_stack() -> str:
        # renders the nice frontend tech stack table by reading dependencies from pyproject.toml
        data = load_pyproject()
        if not data:
            return "⚠️ **pyproject.toml not found**"

        try:
            deps = extract_dependencies(data)
            # map raw package names (like discord-py) -> version string for easier lookup afterwards
            main_deps = {
                name.split('[')[0].split('(')[0].lower(): name
                for name in deps["main"]
            }

            # hardcoded stack structure - this is what gets rendered on the UI
            stack_layout = {
                "🐍 **Core**": {
                    "Python 3.12+ (CI/Docker uses 3.14-rc)": None,
                    "discord.py": main_deps.get("discord-py"),
                },
                "🔧 **Utils**": {
                    "cyclopts (CLI)": main_deps.get("cyclopts"),
                    "loguru (Logging)": main_deps.get("loguru"),
                    "requests (HTTP)": main_deps.get("requests"),
                    "rapidfuzz (Fuzzy Matching)": main_deps.get("rapidfuzz"),
                    "translate (i18n)": main_deps.get("translate"),
                    "numpy (Arrays/Math)": main_deps.get("numpy"),
                },
                "💾 **Data**": {
                    "SQLite3 (Persistent Storage)": None,
                },
                "📊 **Visualization**": {
                    "matplotlib (Data Plotting)": main_deps.get("matplotlib"),
                },
                "📚 **Docs**": {
                    "MkDocs (Material Theme)": None,
                    "mkdocstrings (API Docs)": None,
                },
                "✅ **Quality**": {
                    "pylint (Linting)": None,
                    "basedpyright (Type Checking)": None,
                    "ruff (Linter & Formatter)": None,
                },
                "🛠️ **Build Tools**": {
                    "hatchling": None,
                    "build": None,
                },
                "🚀 **CI/CD**": {
                    "GitLab CI (Automation)": None,
                    "buildah (Container Images)": None,
                },
                "📦 **Dependency Management**": {
                    "pyproject.toml (uv recommended)": None,
                },
                "🔗 **Version Control**": {
                    "Git": None,
                    "commitlint (Conventional Commits)": None,
                },
                "⚙️ **Environment**": {
                    "python-dotenv (Configuration)": None,
                },
                "🌐 **External APIs**": {
                    "TABLES API (Nextcloud)": None,
                    "Discord API": None,
                },
            }

            lines = ['!!! info "Tech Stack"', ""]
            for category, items in stack_layout.items():
                lines.append(f"    {category}")
                for label, package_spec in items.items():
                    if package_spec:
                        pkg_name, pkg_version = parse_version_spec(package_spec)
                        # Extract description from label (e.g. "requests (HTTP)" -> "HTTP")
                        desc = label.split('(')[-1].strip(')') if '(' in label else ""
                        description = f" — {desc}" if desc and desc != label else ""
                        lines.append(f"    * `{pkg_name}` {pkg_version}{description}")
                    else:
                        lines.append(f"    * {label}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"⚠️ **Error generating tech stack:** {e}"

    @env.macro
    def show_dependencies(render_format: str = "table") -> str:
        # simple renderer for dependencies directly fetched from pyproject
        # supports basic table, list or a raw grid
        data = load_pyproject()
        if not data:
            return "⚠️ **pyproject.toml not found**"

        deps = extract_dependencies(data)
        categories = [("main", "Production", "📦"), ("dev", "Development", "🔧"), ("docs", "Documentation", "📚")]

        output = []

        if render_format == "table":
            for cat_key, label, icon in categories:
                items = deps.get(cat_key, [])
                if not items:
                    continue

                output.append(f"\n#### {icon} {label}\n")
                output.append("| Package | Version |")
                output.append("| :--- | :--- |")

                for item in sorted(items):
                    pkg_name, pkg_version = parse_version_spec(item)
                    link = f"[{pkg_name}](https://pypi.org/project/{pkg_name.replace('_', '-')}/)"
                    output.append(f"| {link} | `{pkg_version}` |")
            return "\n".join(output)

        elif render_format == "list":
            for cat_key, label, _ in categories:
                items = deps.get(cat_key, [])
                if not items:
                    continue
                output.append(f"\n**{label}**")
                for item in sorted(items):
                    pkg_name, pkg_version = parse_version_spec(item)
                    output.append(f"- `{pkg_name}` {pkg_version}")
            return "\n".join(output)

        elif render_format == "grid":
            for cat_key, _, _ in categories:
                items = deps.get(cat_key, [])
                if not items:
                    continue
                output.append(f"\n**{cat_key.upper()}**\n")
                output.append("```")
                for item in sorted(items):
                    pkg_name, pkg_version = parse_version_spec(item)
                    output.append(f"{pkg_name:<20} {pkg_version}")
                output.append("```")
            return "\n".join(output)

        return f"❌ Unknown format: `{render_format}`"
