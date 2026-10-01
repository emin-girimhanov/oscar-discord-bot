# Generic UI Components

This page documents the reusable UI components used across various views of the bot. These components encapsulate logic for state management, navigation, and database interaction.

## Interactive Buttons

The button logic is split between `src.oscar.ui.buttons` (generic toggles) and `src.oscar.ui.select_button` (domain-specific actions).

### 1. ToggleButton
A general-purpose button that switches between two states (On/Off) and updates its appearance automatically.

*   **Logic:** Executes an async `on_changed` callback when clicked, passing the new boolean state.
*   **Usage:** Used in `TranslatedView` to switch languages.

::: src.oscar.ui.buttons.ToggleButton
    options:
        show_source: true
        heading_level: 3

### 2. SelectButton (Radio Group)
A button designed for **single-choice selections** within a group (Radio Button behavior).

*   **Group Logic:** It iterates recursively through the parent view's children. When clicked, it deselects all other `SelectButton` instances that share the same `group` string.
*   **Side Effect:** If the group is named `"Semester"`, it automatically writes the selection to the user's preferences in the database.

::: src.oscar.ui.select_button.SelectButton
    options:
        show_source: true
        heading_level: 3

### 3. FilterButton (Multi-Select)
A specialized button for the filter mask (`SelectView`). Unlike `SelectButton`, it allows multiple active selections.

*   **Visual Feedback:** Changes style to `Success` (Green) when selected and back to `Secondary` (Grey) when deselected.
*   **Data Flow:** The parent view iterates over these buttons to build the filter query.

::: src.oscar.ui.select_button.FilterButton
    options:
        show_source: true
        heading_level: 3

### 4. Action Buttons (Info & Delete)
Buttons that perform specific operations on `Module` objects.

*   **InfoButton:** Fetches a module by name (`Module.from_name`) and opens a `ModuleView`.
*   **DeleteButton:** Removes a module from the semester plan via the database.
    *   *Requirement:* Must be attached to a `CustomView`. It calls `view.build_view()` to trigger a full UI refresh after deletion.

::: src.oscar.ui.select_button.InfoButton
    options:
        show_source: true
        heading_level: 3

::: src.oscar.ui.select_button.DeleteButton
    options:
        show_source: true
        heading_level: 3

## Pagination System

The `PaginatedView` is an abstract base class for navigating large datasets (e.g., search results or example lists).

### Core Logic
*   **Navigation:** Implements 4 buttons: First (`❙❮`), Previous (`❮`), Next (`❯`), Last (`❯❙`).
*   **State Management:** Automatically disables navigation buttons when reaching the start or end of the list (e.g., disables "Next" on the last page).
*   **Security:** Includes a `check_user` method to ensure only the user who initiated the command can navigate the view.

### Implementation
To use this, you must provide a `get_page` callback function that returns a `discord.Embed` for a given index.

::: src.oscar.ui.paginated_view.PaginatedView
    options:
        show_source: true
        members:
            - setup
            - check_user
            - first
            - previous
            - next
            - last

see [Views](views.md)
