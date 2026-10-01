# Helper Utilities

This section documents general utility modules used for visualization and data processing.

## Plotting (Matplotlib)
The `src.util.plots` module generates static charts for the Admin Feedback System.

**Technical Implementation:**
* **Headless Backend:** The module explicitly sets `matplotlib.use("Agg")` to ensure charts can be generated in server environments without a display driver (X-Server).
* **Adaptive Binning:** The timeline logic dynamically adjusts the resolution (hourly, daily, weekly, monthly) based on the total timespan of the data.
* **Interpolation:** To ensure smooth graphs when zooming into specific time ranges, the code implements linear interpolation to calculate data points exactly at the cut-off boundaries.

::: src.util.plots
    options:
        show_source: true
        members:
            - create_feedback_boxplot
            - create_feedback_timeline
