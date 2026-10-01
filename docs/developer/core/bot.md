# Bot Core System

The `Oscar` class is the heart of the application. It inherits from `discord.ext.commands.Bot` and orchestrates the startup process, extension loading, and environment configuration.

## The Oscar Class


```mermaid
graph TD
    A["Bot Started"] --> B["Load Cogs"]
    B --> C["Sync Commands"]
    C --> D["Bot Ready"]
    D --> E["Wait for Command"]

    E --> F{Command Type?}

    F -->|/module| G["Search Module"]
    F -->|/filter| H["Open Filter"]
    F -->|/semesterplan| I["View Plan"]
    F -->|/feedback| J["Open Feedback"]
    F -->|/review_feedback| K["Admin: View Feedback"]
    F -->|/help| L["Display Help"]
    F -->|/ping| M["Show Latency"]

    G --> G1["Query Tables API"]
    G1 --> G2["Display Module Info"]
    G2 --> G3{User Action?}
    G3 -->|Add to Plan| G4["Save to DB"]
    G3 -->|More Info| G5["Show Details"]
    G3 -->|Back| E
    G4 --> E
    G5 --> E

    H --> H1["Show Filter Options"]
    H1 --> H2["Apply CP/SWS Filter"]
    H2 --> H3["Show Results"]
    H3 --> E

    I --> I1["Fetch User Plan"]
    I1 --> I2["Display Modules"]
    I2 --> I3{Action?}
    I3 -->|Remove| I4["Delete from Plan"]
    I3 -->|View Detail| I5["Show Module Info"]
    I4 --> E
    I5 --> E

    J --> J1["Open Feedback Form"]
    J2["Rate 3 Dimensions"]
    J1 --> J2
    J2 --> J3["Add Optional Text"]
    J3 --> J4["Submit & Save"]
    J4 --> E

    K --> K1["Generate Plots"]
    K1 --> K2["Select Time Range"]
    K2 --> K3["Update Charts"]
    K3 --> K4{Export?}
    K4 -->|Yes| K5["Download JSON"]
    K4 -->|No| E
    K5 --> E

    L --> L1["Select Topic"]
    L1 --> L2["Show Help Text"]
    L2 --> E

    M --> M1["Calculate Latency"]
    M1 --> M2["Display ms"]
    M2 --> E

    style A fill:#5f6af0,color:#fff
    style D fill:#5f6af0,color:#fff
    style E fill:#4a9bc4,color:#fff
    style F fill:#6b7280,color:#fff
    style G fill:#5ab5e0,color:#000
    style H fill:#5ab5e0,color:#000
    style I fill:#5ab5e0,color:#000
    style J fill:#6ac5e8,color:#000
    style K fill:#d4af37,color:#000
    style L fill:#5ab5e0,color:#000
    style M fill:#6b7280,color:#fff
```


**Responsibilities:**

1.  **Initialization:** Loads environment variables (`DISCORD_SERVER_ID`, `BOT_TOKEN`) and validates them.
2.  **Extension Loading:** Iterates through the `src.oscar.cogs` package and loads all available modules automatically using `pkgutil`.
3.  **Command Sync:** Synchronizes the Application Command Tree (Slash Commands) with the Discord API upon startup (`on_ready`).

::: src.oscar.oscar.Oscar
    options:
        show_source: true
        heading_level: 3
        members:
            - __init__
            - setup_bot

## Main Entry Point
The `main.py` script serves as the bootstrapper. It configures the `discord.Intents` (specifically enabling `message_content`) and instantiates the `Oscar` bot.

::: src.oscar.main.main
    options:
        show_source: true
