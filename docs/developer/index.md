# **Developer Overview**

Welcome to the **OSCAR Bot** developer documentation. This guide helps you understand, set up, and extend the bot.

{{ project_badges_with_links() }}

---

## **Quick Start**

<div class="grid cards" markdown>

- :material-account-plus: **New Contributors**
    ---

    First time here? Start with the **[Setup Guide](setup.md)** to get OSCAR running locally.

- :material-sitemap: **Architecture**
    ---

    Understand how the components fit together.
    [:octicons-arrow-right-24: View System Architecture](core/bot.md)

- :material-database: **Database & Data**
    ---

    Learn about the SQLite schema and Data Models.
    [:octicons-arrow-right-24: View Database Schema](core/database.md)

- :material-shield-account: **Administrators**
    ---

    Need to deploy or maintain?
    [:octicons-arrow-right-24: Admin Guide](../admin/index.md)

</div>

---

## **High-Level Architecture**

OSCAR connects Discord users with University module data. For detailed component diagrams and data flows, see the **[Architecture Guide](core/bot.md)**.

```mermaid
graph LR
    %% --- STYLING ---
    classDef user fill:#0068b4,stroke:#dfe0e2,stroke-width:2px,color:#ffffff,font-weight:bold;
    classDef discord fill:#5865F2,stroke:#dfe0e2,stroke-width:2px,color:#ffffff,font-weight:bold;
    classDef oscar fill:#5f6af0,stroke:#dfe0e2,stroke-width:3px,color:#ffffff,font-weight:bold;
    classDef nextcloud fill:#0082c9,stroke:#dfe0e2,stroke-width:2px,color:#ffffff,font-weight:bold;
    classDef database fill:#727378,stroke:#dfe0e2,stroke-width:2px,color:#ffffff,font-weight:bold;

    %% --- NODES ---
    User("Discord User"):::user
    Discord("Discord API"):::discord
    OSCAR("OSCAR Bot"):::oscar

    %% Grouping data sources visually via positioning
    Nextcloud("Nextcloud tables<br/>Module Data"):::nextcloud
    Database("SQLite<br/>User Data & Cache"):::database

    %% --- CONNECTIONS ---
    %% Forward Flow
    User -->|Command| Discord
    Discord -->|Event| OSCAR

    %% Data Retrieval (Parallel)
    OSCAR <-->|Read/Write| Database
    OSCAR <-->|Fetch Data| Nextcloud

    %% Return Flow
    OSCAR -->|Response| Discord
    Discord -->|Result| User

    %% --- LINK STYLES ---
    linkStyle 0 stroke:#0068b4,stroke-width:2px,fill:none
    linkStyle 1 stroke:#5865F2,stroke-width:2px,fill:none
    linkStyle 2 stroke:#727378,stroke-width:2px,fill:none
    linkStyle 3 stroke:#0082c9,stroke-width:2px,fill:none
    linkStyle 4 stroke:#5f6af0,stroke-width:2px,fill:none
    linkStyle 5 stroke:#5865F2,stroke-width:2px,fill:none
```

```mermaid
graph TB
    subgraph System["OSCAR Discord Bot System"]
        subgraph Frontend["Frontend Layer"]
            Discord["Discord API<br/>Events & Interactions"]
        end

        subgraph Application["Application Layer"]
            BotCore["Bot Core<br/>oscar.py"]

            subgraph CommandLayer["Command Layer - Cogs"]
                ModulCog["🔍 Module Cog<br/>Search & Filter"]
                AdminCog["📊 Admin Cog<br/>Feedback Review"]
                HelpCog["❓ Help Cog<br/>Support"]
            end

            subgraph PresentationLayer["Presentation Layer - UI"]
                Views["Views<br/>Start, Module, Feedback<br/>Semesterplan, Select"]
                Components["Components<br/>Buttons, Selects<br/>Custom Elements"]
            end
        end

        subgraph Business["Business Logic Layer"]
            Filter["Filter Engine<br/>CP/SWS Filtering"]
            Analytics["Analytics Engine<br/>Statistics & Plots"]
        end

        subgraph Data["Data Layer"]
            Database["SQLite<br/>User Data & Cache"]
            ModuleCache["Module Cache<br/>In Memory"]
        end

        subgraph Integration["Integration Layer"]
            TableAPI["Tables API Client<br/>Nextcloud API"]
        end

        subgraph Resources["Resources & Config"]
            i18n["i18n System<br/>Translations"]
            Enums["Enums & Types<br/>LanguageCode<br/>StudyCourse"]
            TypedDicts["TypedDicts<br/>Data Structures"]
        end
    end

    Discord -->|Events| BotCore
    BotCore -->|Routes Commands| CommandLayer

    ModulCog -->|Creates| Views
    AdminCog -->|Creates| Views
    HelpCog -->|Creates| Views

    Views -->|Contains| Components
    Views -->|Reads| i18n
    Views -->|Action| Database

    ModulCog -->|Uses| Filter
    Filter -->|Search| ModuleCache
    ModuleCache -->|Fetch Raw| TableAPI

    AdminCog -->|Uses| Analytics
    Analytics -->|Visualize| Database
    Analytics -->|Labels| i18n

    Database -->|Stores| ModuleCache
    Database -->|Validates| Enums
    Database -->|Types| TypedDicts

    Views -->|Respects| Enums
    Views -->|Maps| TypedDicts

    style System fill:#1e3a8a,color:#fff
    style Frontend fill:#5f6af0,color:#fff
    style Application fill:#4a9bc4,color:#fff
    style CommandLayer fill:#5ab5e0,color:#000
    style PresentationLayer fill:#6ac5e8,color:#000
    style Business fill:#6b7280,color:#fff
    style Data fill:#d4af37,color:#000
    style Integration fill:#10b981,color:#fff
    style Resources fill:#f59e0b,color:#000
```

## **Project Structure**

OSCAR is built using `discord.py` and structured into several key components:

``` bash
discord-bot/
├── src/
│   ├── oscar/                   # Bot core
│   │   ├── main.py              # Entry point (sets up intents)
│   │   ├── oscar.py             # Custom Bot class (auto-loads cogs)
│   │   │
│   │   ├── cogs/                # Command handlers
│   │   │   ├── modul.py         # /module, /filter, /semesterplan, /standard_plan
│   │   │   ├── admin.py         # /feedback_review (admin-only)
│   │   │   ├── help.py          # /help (with translations)
│   │   │   └── examples.py      # /colors, /buttons (dev tools)
│   │   │
│   │   └── ui/                  # UI framework
│   │       ├── base_views.py    # TranslatedView, CustomView
│   │       ├── all_info_view.py # Detailed module attributes view
│   │       ├── custom_view.py   # Base class wrapper
│   │       ├── paginated_view.py    # Pagination logic for long lists
│   │       ├── select_button.py     # Selection UI components
│   │       ├── semesterplan_view.py # Semester planning interface
│   │       ├── translated_view.py   # i18n-aware base view
│   │       ├── buttons.py       # Reusable button components
│   │       ├── start_view.py    # /start onboarding
│   │       ├── module_view.py   # Module display card
│   │       ├── select_view.py   # /filter interface
│   │       └── feedback_view.py # /feedback form
│   │
│   └── util/                    # Helper modules
│       ├── database.py          # SQLite wrapper (singleton)
│       ├── tables.py            # Nextcloud API client
│       ├── module.py            # Module data model
│       ├── translations.py      # i18n dictionaries
│       ├── enums.py             # LanguageCode, StudyCourse
│       ├── modules_filter.py    # Filter logic (CP, SWS)
│       ├── typed_dicts.py       # Type definitions
│       └── plots.py             # Matplotlib charts (feedback)
│
├── docs/                        # MkDocs documentation (this site)
├── database/                    # SQLite files (auto-created)
│   └── oscar.db                 # Main database
├── .env                         # Environment config (YOU create)
├── .gitlab-ci.yml               # CI/CD pipeline
├── pyproject.toml               # Dependencies & metadata
└── README.md                    # Project overview
```

## **Tech Stack & Prerequisites**

 We use `pyproject.toml` for dependency management.
??? info "Check pyproject.toml"
    ```toml title="pyproject.toml"
    --8<-- "pyproject.toml"
    ```

| Technology       | Version | Purpose            | Why this choice?                                  |
| ---------------- | ------- | ------------------ | ------------------------------------------------- |
| Python           | 3.12+   | Language           | Modern async/await, type hints, rich ecosystem    |
| discord.py       | Latest  | Discord API        | Most mature & actively maintained Discord library |
| SQLite           | 3.x     | Database           | Zero-config, perfect for caching, ACID compliant  |
| loguru           | Latest  | Logging            | Structured logs, better DX than stdlib logging    |
| matplotlib       | 3.9+    | Visualization      | Admin feedback charts (boxplot, timeline)         |
| basedpyright     | Latest  | Type checking      | Strict typing catches bugs at dev time            |

| Nextcloud Tables | API v1  | Data source        | Faculty's existing module management system       |
| MkDocs Material  | Latest  | Documentation      | Beautiful, searchable, mobile-friendly            |

## **Next Steps**

- [Branch Structure & Git Workflow](workflow.md)
- [Setup](setup.md)
- [Database Internals](core/database.md)
- [Cogs & Commands](cogs/module.md)
- [UI Framework](ui/architecture.md)
- [Admin Overview](../admin/index.md)
