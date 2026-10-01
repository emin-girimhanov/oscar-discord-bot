# Feedback Review Logic

The Feedback Review system allows administrators and developers to analyze user feedback directly within Discord. It combines database queries with `matplotlib` visualizations to generate interactive reports.

## The Administration Cog

This Cog handles the `/review_feedback` command, which fetches data from the database and passes it to the plotting utilities. It is protected by a permission check (`may_review_feedback`) ensuring only authorized personnel can access sensitive user feedback. Authorized are the developers, the owner of the Discord application and the administrators of the home server, the one `DISCORD_SERVER_ID` names. An administrator of any other server is refused: OSCAR is a public bot, and anybody is the administrator of a server they made themselves. The answer is ephemeral, so the channel does not see the charts.

::: src.oscar.cogs.admin.Administration
    options:
        show_source: true
        members:
            - review_feedback
        heading_level: 3

## The Review View

The `ReviewFeedbackView` is the interactive UI component. It extends `TranslatedView` to support both English and German.

**Key Features:**

* **Dynamic Filtering:** Filters feedback by time range (1 Hour, 12 Hours, 1 Day, 1 Week, 1/6 Months, 1/2/4 Years, All Time).
* **Live Updates:** Regenerates charts on-the-fly when filters change.
* **Data Export:** Includes a download button (`⤓`) to export the complete dataset as a `.json` file.

> **GDPR & Confidentiality Notice:** The exported JSON contains pseudonymized feedback linked to Discord User IDs. As an administrator, you must treat this data as confidential and delete local exports once the analysis is complete. Ensure exports are not shared publicly.

::: src.oscar.cogs.admin.ReviewFeedbackView
    options:
        show_source: true
        heading_level: 3
        members:
            - _build_content
            - _ReviewFeedbackView__filter_feedback

## Visualizations (Matplotlib)

The bot uses `matplotlib` with the **Agg backend** (headless) to generate images purely in memory (`io.BytesIO`), preventing GUI blocking on the server.

> **Limitation (Discord File Sizes):** Discord enforces an 8 MB upload limit (25 MB for Nitro servers). For extremely massive datasets, the generated PNG or JSON export may hit this API limit. This typically requires tens of thousands of records.

### Boxplots

Visualizes the statistical distribution of the three core metrics on a Likert scale from **1 (Very Poor/Disagree) to 4 (Excellent/Agree)**. It shows medians, quartiles, and outliers.

::: src.util.plots.create_feedback_boxplot
    options:
        show_source: true
        heading_level: 4

### Timelines

Visualizes feedback volume over time. It uses dynamic binning (hourly/daily/weekly) depending on the selected time span and highlights the active filter range.

::: src.util.plots.create_feedback_timeline
    options:
        show_source: true
        heading_level: 4

## Data Model

The visualizations are based on the following typed dictionary structure retrieved from the SQLite database:

::: src.util.typed_dicts.FeedbackReviewDict
    options:
        show_source: true
        heading_level: 3
