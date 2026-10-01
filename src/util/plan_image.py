""" This module draws a standard study plan as a picture.

    Only two programmes ship a hand drawn plan. Every other plan used to be shown as
    plain text, which is hard to read for seven semesters. The picture is rendered
    from the same json the text comes from, so both always agree.
"""

import io
import textwrap

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from util.enums import LanguageCode
from util.semesterplans import Semesterplan


matplotlib.use("Agg")  # Essential for bots (makes matplotlib run headless)


# Discord colour scheme, same values as in `util.plots`
PRIMARY_COLOR: str = "#5f6af0"
BACKGROUND_COLOR: str = "#323339"
SURFACE_COLOR: str = "#393a41"
FOREGROUND_COLOR: str = "#dfe0e2"
MUTED_COLOR: str = "#a6a7ad"

# Elective entries carry no module number and are drawn in a calmer colour.
ELECTIVE_COLOR: str = "#4a4b54"

# A box the student already has in their plan. This says nothing about a grade,
# OSCAR never learns one, so the mark only ever means "planned".
PLANNED_COLOR: str = "#43b581"

# `✓` is a plain glyph of the default font. A coloured emoji like `✅` would be
# drawn as an empty box, because matplotlib ships no emoji font.
PLANNED_MARK: str = "✓"

COLUMN_WIDTH: float = 2.7
ROW_HEIGHT: float = 1.0
WRAP_WIDTH: int = 24
MAX_LINES: int = 3


def _wrap(title: str) -> str:
    """ Breaks a module title into at most `MAX_LINES` lines.

        Words are never split. A box fits about 44 characters per line at this font
        size, so a single long word like `Managementinformationssysteme` still has
        room, while `Informationstechnolo gie` would only look like a typo.
    """
    lines: list[str] = textwrap.wrap(
        title.strip(), width=WRAP_WIDTH, break_long_words=False, break_on_hyphens=False
    ) or [""]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        lines[-1] = lines[-1][: WRAP_WIDTH - 1] + "…"
    return "\n".join(lines)


# pylint: disable=R0913 # (too-many-arguments)
# pylint: disable=R0917 # (too-many-positional-arguments)
def _draw_semester(
    axes,
    index: int,
    semester,
    rows: int,
    is_german: bool,
    covered: list[bool] | None = None,
) -> None:
    """ Draws one column: the heading with its credit total and every module box.

        Parameters:
            axes: The axes to draw on.
            index: The zero based column, so semester one sits at 0.
            semester: The modules of that semester.
            rows: The height of the whole grid, used to place the first box.
            is_german: Whether the heading is German.
            covered: One flag per box, `True` for a module the student has in their
                plan. `None` draws the official plan without any mark.
    """
    marks: list[bool] = covered if covered is not None else [False] * len(semester)
    total: int = sum(module.credit_points for module in semester)
    planned: int = sum(
        module.credit_points
        for module, is_marked in zip(semester, marks)
        if is_marked
    )
    credits_str: str = f"{planned}/{total}" if covered is not None else f"{total}"
    _ = axes.text(
        index + 0.5, rows + 0.75,
        f"{index + 1}. Semester · {credits_str} CP" if is_german
        else f"Semester {index + 1} · {credits_str} CP",
        ha="center", va="center",
        color=PRIMARY_COLOR, fontsize=11, fontweight="bold",
    )

    for position, module in enumerate(semester):
        bottom: float = rows - position - 1
        # an entry without a module number is a placeholder, for example "WPF Informatik"
        colour: str = ELECTIVE_COLOR if module.identification is None else BACKGROUND_COLOR
        is_planned: bool = position < len(marks) and marks[position]
        axes.add_patch(
            FancyBboxPatch(
                (index + 0.06, bottom + 0.08),
                0.88, 0.84,
                boxstyle="round,pad=0.01,rounding_size=0.06",
                linewidth=2.0 if is_planned else 1.0,
                edgecolor=PLANNED_COLOR if is_planned else PRIMARY_COLOR,
                facecolor=colour,
            )
        )
        if is_planned:
            _ = axes.text(
                index + 0.13, bottom + 0.78,
                PLANNED_MARK,
                ha="center", va="center",
                color=PLANNED_COLOR, fontsize=11, fontweight="bold",
            )
        _ = axes.text(
            index + 0.5, bottom + 0.58,
            _wrap(module.title),
            ha="center", va="center",
            color=FOREGROUND_COLOR, fontsize=8,
        )
        _ = axes.text(
            index + 0.5, bottom + 0.20,
            f"{module.credit_points} CP",
            ha="center", va="center",
            color=MUTED_COLOR, fontsize=8, fontweight="bold",
        )


def render_semesterplan(
    plan: Semesterplan,
    language: LanguageCode = LanguageCode.DE,
    covered: list[list[bool]] | None = None,
) -> io.BytesIO:
    """ Draws the plan as one column per semester.

        Parameters:
            plan: The plan to draw.
            language: The language for the headings.
            covered: One flag per box, in the shape of `plan.semesters`, marking the
                modules the student has in their plan. `None` draws the official plan
                the way everybody sees it, without any mark.

        Returns:
            A PNG in a buffer, ready for `discord.File`.
    """
    is_german: bool = language == LanguageCode.DE
    semesters: list[list] = plan.semesters  # pyright: ignore[reportMissingTypeArgument]
    columns: int = max(1, len(semesters))
    rows: int = max((len(semester) for semester in semesters), default=0)

    figure, axes = plt.subplots(
        figsize=(COLUMN_WIDTH * columns, ROW_HEIGHT * (rows + 2))
    )
    figure.patch.set_facecolor(SURFACE_COLOR)
    axes.set_facecolor(SURFACE_COLOR)
    axes.set_xlim(0, columns)
    axes.set_ylim(0, rows + 2)
    axes.axis("off")

    heading: str = "Regelstudienplan" if is_german else "Standard study plan"
    _ = axes.text(
        columns / 2, rows + 1.55,
        f"{heading} · {plan.title}",
        ha="center", va="center",
        color=FOREGROUND_COLOR, fontsize=15, fontweight="bold",
    )

    for index, semester in enumerate(semesters):
        # a short list of marks still marks, the missing columns simply stay empty
        marks: list[bool] | None = None
        if covered is not None:
            marks = covered[index] if index < len(covered) else []
        _draw_semester(axes, index, semester, rows, is_german, marks)

    # an empty plan has no boxes, and matplotlib then warns that it cannot fit them
    if rows > 0:
        plt.tight_layout()

    buffer: io.BytesIO = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=150, facecolor=SURFACE_COLOR, bbox_inches="tight")
    _ = buffer.seek(0)
    plt.close(figure)

    return buffer
