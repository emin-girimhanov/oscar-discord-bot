""" Module for creating plots and visualizations."""

import io
import time
from bisect import bisect_right
from datetime import timedelta
from datetime import datetime
from discord import File
from loguru import logger
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from util.enums import LanguageCode
from util.translations import FEEDBACK_REVIEW, format_duration
from util.typed_dicts import FeedbackReviewDict




matplotlib.use("Agg") # Essential for bots (makes matplotlib run headless)


# Dicord color scheme
PRIMARY_COLOR       = "#5f6af0"    # blurple color
SECONDARY_COLOR     = "#727378"    # gray color (not the actual secondary discord color)
SUCCESS_COLOR       = "#2b843b"    # green color
DANGER_COLOR        = "#c7333d"    # red color
BACKGROUND_COLOR    = "#323339"    # dark background color
SURFACE_COLOR       = "#393a41"    # container backgroudn color
FOREGROUND_COLOR    = "#dfe0e2"    # text foreground color



async def create_feedback_boxplot(
        feedback_data: list[FeedbackReviewDict],
        language_code: LanguageCode=LanguageCode.EN
    ) -> File:
    """
    Create a boxplot visualization of feedback metrics.

    Args:
        feedback_data: List of feedback dictionaries

    Returns:
        Discord file object containing the plot image
    """
    if not feedback_data:
        logger.warning("No feedback data provided for boxplot creation.")

    # Extract the three metrics
    intuitiveness: list[float] = [float(fb["intuitiveness"]) for fb in feedback_data]
    discoverability: list[float] = [float(fb["discoverability"]) for fb in feedback_data]
    usefulness: list[float] = [float(fb["usefulness"]) for fb in feedback_data]

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(SURFACE_COLOR)

    # Create boxplots
    bp = ax.boxplot(
        [intuitiveness, discoverability, usefulness],
        labels=[
            FEEDBACK_REVIEW["intuitiveness"][language_code],
            FEEDBACK_REVIEW["discoverability"][language_code],
            FEEDBACK_REVIEW["usefulness"][language_code]
        ],
        patch_artist=True,
        notch=True,
    )

    # Style the boxplots
    for patch in bp["boxes"]:
        patch.set_facecolor(PRIMARY_COLOR)
        patch.set_edgecolor(SURFACE_COLOR)
        patch.set_alpha(0.7)

        # Style text and foreground elements
    for whisker in bp["whiskers"]:
        whisker.set_color(FOREGROUND_COLOR)
        whisker.set_linewidth(1.5)
    for cap in bp["caps"]:
        cap.set_color(FOREGROUND_COLOR)
        cap.set_linewidth(1.5)
    for median in bp["medians"]:
        median.set_color(FOREGROUND_COLOR)
        median.set_linewidth(2.0)
    for flier in bp["fliers"]:
        # set outlier marker edge color to foreground color
        flier.set_markeredgecolor(FOREGROUND_COLOR)
        # optional: make marker face match background so it looks outlined
        flier.set_markerfacecolor(SURFACE_COLOR)
        flier.set_markersize(5)

    # Axes / background
    ax.patch.set_color(BACKGROUND_COLOR)
    ax.spines["bottom"].set_color(FOREGROUND_COLOR)
    ax.spines["left"].set_color(FOREGROUND_COLOR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=FOREGROUND_COLOR)

    # Ticks and tick labels
    ax.tick_params(colors=FOREGROUND_COLOR, labelsize=12)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=16, color=FOREGROUND_COLOR)

    # Set labels and title
    ax.set_ylabel(FEEDBACK_REVIEW["rating"][language_code], fontsize=14, color=FOREGROUND_COLOR)
    _ = ax.set_ylim(0, 5)
    ax.set_title(
        # pylint: disable=C0301 # (line-too-long)
        label=f"{FEEDBACK_REVIEW['metrics_overview'][language_code]} ({len(feedback_data)} {FEEDBACK_REVIEW["responses"][language_code]})\n{time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(time.time()))}",
        fontsize=18,
        fontweight="bold",
        color=FOREGROUND_COLOR,
        pad=20
    )
    ax.grid(axis="y", color=FOREGROUND_COLOR, alpha=0.3, linestyle="--")

    # Adjust layout
    plt.tight_layout()
    # plt.show()

    # Save to bytes buffer
    buf = io.BytesIO()

    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    _ = buf.seek(0)
    plt.close(fig)

    # Create Discord file
    return File(buf, filename="feedback_metrics_boxplot.png")


# pylint: disable=R0914 # (too-many-locals)
# pylint: disable=R0912 # (too-many-branches)
# pylint: disable=R0915 # (too-many-statements)
async def create_feedback_timeline(
    feedback_data: list[FeedbackReviewDict],
    selected_duration: int|None = None,
    language_code: LanguageCode = LanguageCode.EN
) -> File:
    """
    Create a timeline visualization of feedback timestamps with highlighted selected range.
    Now renders a line graph showing counts of feedback over time and highlights the selected range.

    Args:
        feedback_data: List of feedback dictionaries containing timestamps
        selected_duration: Duration in seconds from current time to highlight (None = all time)
        language_code: Language code for labels

    Returns:
        Discord file object containing the timeline plot
    """
    if not feedback_data:
        # Create empty plot with message
        fig, ax = plt.subplots(figsize=(12, 4))
        fig.patch.set_facecolor(SURFACE_COLOR)
        ax.patch.set_color(BACKGROUND_COLOR)
        ax.text(0.5, 0.5, 'No feedback data available',
                ha='center', va='center', fontsize=16, color=FOREGROUND_COLOR)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        # Extract timestamps and convert to datetime
        timestamps = [fb['timestamp'] for fb in feedback_data]
        datetime_objects = [datetime.fromtimestamp(ts) for ts in timestamps]
        datetime_objects.sort()

        current_time = time.time()
        current_datetime = datetime.fromtimestamp(current_time)

        # Determine selected range
        if selected_duration is None:
            cutoff_datetime = None
        else:
            cutoff_time = current_time - selected_duration
            cutoff_datetime = datetime.fromtimestamp(cutoff_time)

        # Determine plotting range: from earliest feedback to now (with small padding)
        start_datetime = datetime_objects[0]
        end_datetime = max(current_datetime, datetime_objects[-1])
        # Add a small padding to end for visual space
        end_datetime = end_datetime + timedelta(hours=6)

        # Choose bin interval based on span
        span_seconds = (end_datetime - start_datetime).total_seconds()
        if span_seconds <= 60 * 60 * 24 * 2:        # <= 2 days -> hourly bins
            delta = timedelta(hours=1)
            fmt = '%d-%m %H:%M'
        elif span_seconds <= 60 * 60 * 24 * 90:     # <= 90 days -> daily bins
            delta = timedelta(days=1)
            fmt = '%d-%m-%Y'
        elif span_seconds <= 60 * 60 * 24 * 730:    # <= 2 years -> weekly bins
            delta = timedelta(weeks=1)
            fmt = '%d-%m-%Y'
        else:                                       # larger -> monthly-ish bins (30 days)
            delta = timedelta(days=30)
            fmt = '%b %Y'

        # Create bin edges as matplotlib date numbers
        edges_dt = list(mdates.drange(start_datetime, end_datetime + delta, delta))
        edges = edges_dt  # already matplotlib date floats

        # Convert each timestamp to matplotlib date number
        md_dates = [mdates.date2num(dt) for dt in datetime_objects]

        # Count occurrences per bin
        counts = [0] * (len(edges) - 1)
        for md in md_dates:
            idx = bisect_right(edges, md) - 1
            if 0 <= idx < len(counts):
                counts[idx] += 1

        # Compute bin centers for plotting the line
        centers = [(edges[i] + edges[i + 1]) / 2 for i in range(len(counts))]

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 4))
        fig.patch.set_facecolor(SURFACE_COLOR)
        ax.patch.set_color(BACKGROUND_COLOR)

        # convert to numpy for masking and plotting segments with different colors
        centers_np = np.array(centers)
        counts_np = np.array(counts, dtype=float)

        # Determine selected range boundaries
        if cutoff_datetime is None:
            cutoff_md = None
            current_md = None
        else:
            cutoff_md = mdates.date2num(cutoff_datetime)
            current_md = mdates.date2num(current_datetime)

        # Build extended arrays with interpolated points at boundaries
        x_plot = list(centers_np)
        y_plot = list(counts_np)

        if cutoff_md is not None:
            # Add interpolated points at cutoff_md and current_md
            for boundary_md in [cutoff_md, current_md]:
                if centers_np[0] <= boundary_md <= centers_np[-1]:
                    # Find where to insert this boundary point
                    idx = np.searchsorted(centers_np, boundary_md)
                    if 0 <= idx < len(centers_np):
                        # Linear interpolation
                        x0, x1 = centers_np[idx-1], centers_np[idx]
                        y0, y1 = counts_np[idx-1], counts_np[idx]
                        y_interp = y0 + (y1 - y0) * (boundary_md - x0) / (x1 - x0)

                        x_plot.insert(idx, boundary_md)
                        y_plot.insert(idx, y_interp)

        # Sort by x values
        sorted_indices = np.argsort(x_plot)
        x_plot = np.array(x_plot)[sorted_indices]
        y_plot = np.array(y_plot)[sorted_indices]

        # Now create masks for primary/secondary
        if cutoff_md is None:
            selected_mask = np.ones_like(y_plot, dtype=bool)
        else:
            selected_mask = (x_plot >= cutoff_md) & (x_plot <= current_md)

        primary_y = np.where(selected_mask, y_plot, np.nan)
        secondary_y = np.where(~selected_mask, y_plot, np.nan)

        # Helper: plot contiguous non-NaN segments so isolated segments draw correctly
        def _plot_segments(x_arr, y_arr, color, zorder):
            mask = ~np.isnan(y_arr)
            if not np.any(mask):
                return
            idx = np.where(mask)[0]
            runs = np.split(idx, np.where(np.diff(idx) != 1)[0] + 1)
            for run in runs:
                ax.plot(x_arr[run], y_arr[run], '-', color=color, linewidth=2, zorder=zorder)
                # If primary, fill under the segment
                if color == PRIMARY_COLOR:
                    ax.fill_between(
                        x_arr[run],
                        y_arr[run],
                        color=PRIMARY_COLOR,
                        alpha=0.12,
                        zorder=zorder - 1
                    )

        # Plot secondary (outside selected range) first, then primary on top.
        _plot_segments(x_plot, secondary_y, SECONDARY_COLOR, zorder=2)
        _plot_segments(x_plot, primary_y, PRIMARY_COLOR, zorder=3)

        # Mark boundaries / current time
        if cutoff_datetime is not None:
            ax.axvline(current_md, color=SUCCESS_COLOR, linewidth=2, zorder=4)
            ax.axvline(cutoff_md, color=DANGER_COLOR, linewidth=2, zorder=4)
            ax.axvspan(cutoff_md, current_md, alpha=0.08, color=PRIMARY_COLOR, zorder=0)
        else:
            ax.axvline(
                mdates.date2num(current_datetime),
                color=SUCCESS_COLOR,
                linewidth=2,
                zorder=4
            )

        # Axis formatting — fewer, less-dense ticks
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
        plt.setp(ax.get_xticklabels(), color=FOREGROUND_COLOR)

        ax.tick_params(colors=FOREGROUND_COLOR, labelsize=16)
        ax.spines['bottom'].set_color(FOREGROUND_COLOR)
        ax.spines['left'].set_color(FOREGROUND_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(plt.MaxNLocator(
            nbins=4,
            integer=True,
            prune="both",
            min_n_ticks=2
        ))

        # Title includes selected duration and total count
        total_count = len(feedback_data)
        selected_count: int = sum(
            1 for md in md_dates if cutoff_md is None or (cutoff_md <= md <= current_md)
        )
        duration_str = format_duration(selected_duration)
        ax.set_title(
            # pylint: disable=C0301 # (line-too-long)
            label=f"{FEEDBACK_REVIEW['timeline'][language_code]} ({duration_str}) - {selected_count}/{total_count} {FEEDBACK_REVIEW['responses'][language_code]}:",
            fontsize=18,
            fontweight="bold",
            color=FOREGROUND_COLOR,
            pad=20,
            loc='left'
        )

        ax.grid(axis="y", color=FOREGROUND_COLOR, alpha=0.3, linestyle="--")

    # Adjust layout
    plt.tight_layout()

    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    # Create Discord file
    return File(buf, filename='feedback_timeline.png')
