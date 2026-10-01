# Module Filtering

The `ModulesFilter` class encapsulates the logic for filtering the raw module list based on numerical criteria like Credit Points (CP) or Semester Hours (SWS).

## Filter Logic

**Key Behaviors:**
* **Auto-Initialization:** If instantiated without a list, it automatically fetches the latest module catalogue (`get_rows(720)`) from the API.
* **Regex Parsing:** Since the source API returns CP and SWS as free-text strings (e.g., "5 CP" or "2 SWS"), the filter uses `re.findall(r"\d+", ...)` to extract comparable integers.
* **SWS Sanitization:** The SWS filter performs aggressive string cleaning (removing newlines, spaces, uppercasing) to handle inconsistent formatting. Note that the source code marks this method as potentially "flawed" due to the non-standardized input data.

::: src.util.modules_filter.ModulesFilter
    options:
        show_source: true
        members:
            - __init__
            - filter_cp
            - filter_sws

## Filter Enums
These Enums define the comparison operators used by the `SelectView` UI.

::: src.util.modules_filter.CpFilter
    options:
        show_source: true
        show_root_heading: false

::: src.util.modules_filter.SwsFilter
    options:
        show_source: true
        show_root_heading: false
