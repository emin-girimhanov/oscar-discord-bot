---
hide:
  - navigation
  - toc
  - path
---

<div class="oscar-hero" markdown>

  <div class="hero-logo-container">
    <img src="assets/images/oscar_logo.svg" class="hero-logo" alt="OSCAR Logo">

    <div class="speech-bubble">
      <p><strong>O</strong>rganized <strong>S</strong>tudy <strong>C</strong>hoice & <strong>A</strong>cademic <strong>R</strong>oadmapper</p><br>
      <p class="speech-sub">Plan your semesters, avoid bad module choices, and stop juggling PDFs – directly in Discord.</p>
    </div>
  </div>

  <div class="hero-buttons">
    <a href="https://discord.gg/hkzZKhnRvW" class="hero-btn btn-primary">Join Beta Server</a>
    <a href="features/commands/" class="hero-btn btn-secondary">View Commands</a>
  </div>

   {{ project_badges_with_links() }}

  <div class="scroll-indicator" onclick="document.querySelector('.oscar-intro').scrollIntoView({behavior:'smooth'})">
    <span></span>
    <span></span>
    <span></span>
  </div>

</div>

<p style="font-size: 2em; line-height: 1.5;">
  Made by students for students.
</p>

<div class="oscar-intro" markdown>

<p style="text-align: center; font-size: 1.8em; font-weight: 500; color: #0068b4; margin-top: 0;">
  Made by students for students.
</p>

<p style="font-size: 2em; line-height: 1.5;">
  🔍 <strong>Search modules</strong> by name, CP, SWS &amp; exam type <br>
  📅 <strong>Build your personal study plan</strong><br>
  🗓️ <strong>Curriculum preview &amp; comparison</strong><br>
  - all in one place -
</p>

## **[Why OSCAR?](about_oscar.md)**

OSCAR is a Discord-based assistant that helps FIN students at Otto-von-Guericke-University Magdeburg plan their semesters and choose modules by turning complex catalogs, exam regulations, and scattered PDFs into one clear, accessible place.

<div class="grid" markdown>

!!! failure "The Problem"
    Finding module info as a FIN student is fragmented and time-consuming:

    * ❌ **Scattered sources** — exam regulations (PDFs), [module handbook](https://bookstack.cs.ovgu.de/), and [LSF portal](https://lsf.ovgu.de/) are all separate.
    * ❌ **Context switching** — students already discuss their study plans on Discord ([FinEmporium](https://farafin.de/studierende/fin-community/)), then switch to the browser and back.
    * ❌ **Screenshot chaos** — module details are shared as images in chat instead of structured data.
    * ❌ **Inefficient planning** leading to suboptimal module choices.

!!! success "The OSCAR Solution"
    OSCAR meets students where they already are — on Discord:

    * ✅ **One Platform:** search modules, filter by CP/SWS/exam type, and plan semesters without leaving Discord.
    * ✅ **Up-to-date:** Synced with official faculty data.
    * ✅ **Focused scope** — FIN modules only, no unreliable AI integrations, fewer but better features.
    * ✅ **Privacy-first** — study plan stays local. No messages stored, no profiles, no analytics.

</div>

</div>

## **Choose Your Path**

=== "For Students"

    ### **Your Personal Study Assistant**

    Plan your studies where you chat: OSCAR brings the official [module catalog](https://bookstack.cs.ovgu.de/) to Discord, helping you build your academic roadmap with ease.

    ??? note "Data Accuracy & Scope"
        The bot syncs module data regularly from the faculty's Nextcloud.
        However, always verify exam details in the official LSF/Prüfungsamt documents.

        **OSCAR is for personal planning only.** You must still register for courses, exams, and events through official platforms such as [LSF](https://lsf.ovgu.de), e-learning portals, or other university websites. OSCAR does not replace any official registration process.

    ## **Features**

    <div class="grid cards" markdown>

    -   🚀 **Get Started**
        ---
        Set up your course of study and semester. An interactive wizard guides you through the process.

        ```bash
        /start
        ```

        ![Start Interface](assets/images/oscar_start.png){ width="400" .img-center }

    -   🔍 **Find Modules**
        ---
        Here you will find credit points (CP), exams, and course content; we will add LSF links soon.

        ```bash
        /module [name]
        ```

        ![Search Autocomplete](assets/images/oscar_module_name.png){ width="400" .img-center }
        ![Module Result](assets/images/oscar_module_advancetopicsnetwork.png){ width="400" .img-center }

    -   🎯 **Smart Filters**
        ---
        Find modules that fit your CP, SWS, or Exam Type preferences.

        ```bash
        /filter
        ```

        ![Module Filter](assets/images/oscar_filter.png){ width="400" .img-center }

    -   📅 **Plan Semesters**
        ---
        Create, customize, and save your personal study roadmap.

        ```bash
        /semesterplan
        ```

        ![Semester Overview](assets/images/oscar_semesterplan.png){ width="400" .img-center }


    -   � **Standard Curriculum**
        ---
        View the official Regelstudienplan for your degree – see which modules are planned per semester at a glance.

        ```bash
        /standard_plan
        ```

        ![Standard Plan](assets/images/oscar_standardplan.png){ width="400" .img-center }

    -   💬 **Send Feedback**
        ---
        Help us improve OSCAR with your suggestions and bug reports.

        ```bash
        /feedback
        ```
        ![Feedback](assets/images/oscar_feedback.png){ width="400" .img-center }

    </div>


    ### **Getting Started**

    Follow these steps to get your personal study assistant running.

    === "Step 1: Get Discord"
        To use OSCAR, you need a **Discord account**. Discord is a free communication platform available on all devices.

        **Available on:**

        * 📱 **Mobile:** iOS, Android, [Volla OS](https://volla.online/en/index.php) and [GrapheneOS](https://grapheneos.org/)
        * 💻 **Computer:** Windows, macOS, Linux
        * 🌐 **Web Browser:** [discord.com](https://discord.com)

        **Set up Discord:**

        1.  **Already have Discord?** → Sign in with your existing account.
        2.  **New to Discord?** → Create a free account:
            * Go to [discord.com](https://discord.com)
            * Click "Sign up" and follow the steps
            * Verify your email address  → Done!

    === "Step 2: Join Server"
        The (unofficial) community for FIN students is the **FinEmporium**.

        ![FinEmporium Server Icon](assets/images/finemporium-1.480x0-is.png){ width="120" align="left" }

        **[Join FinEmporium Discord Server](https://discord.com/invite/m4vQhrK)**

        For more information about FinEmporium, see the [FIN-Community Page](https://farafin.de/en/students/fin-community/).

        ---

        !!! warning "Test Server Required"
            OSCAR has completed its university project phase (**v1.0.0**). Currently, the bot is hosted on a dedicated **Test Server** pending the final deployment to FinEmporium.

            [**Click here to join the OSCAR Test Server**](https://discord.gg/hkzZKhnRvW){ .md-button .md-button--primary }

    === "Step 3: Start OSCAR"
        Once you are on the server, you can add your **Course of Study** and **Semester**.

        Type this command in any text channel:
        ```
        /start
        ```

        *An interactive setup wizard will guide you through the process.*

        ![Start Interface](assets/images/oscar_start.png){ width="400" .img-center }

    === "Step 4: Try it out"
        After setup, use the bot to explore and plan:

        <div class="cmd-row" markdown>
        ```
        /module [name]
        ```
        🔍 Here you will find credit points (CP), exams, and course content; links to LSF will be added soon.
        </div>

        <div class="cmd-row" markdown>
        ```
        /filter
        ```
        🧩 Find modules that fit your CP or SWS budget.
        </div>

        <div class="cmd-row" markdown>
        ```
        /semesterplan
        ```
        📅 View and edit your saved schedule – including automatic comparison with the standard curriculum (Regelstudienplan) and total CP sum.
        </div>

        <div class="cmd-row" markdown>
        ```
        /standard_plan
        ```
        🗓️ View the standard curriculum for your degree and Examination Regulations.
        </div>

        <div class="cmd-row" markdown>
        ```
        /feedback
        ```
        💬 Help us improve OSCAR.
        </div>

        [View all Commands](features/commands.md){ .md-button .md-button--primary }

=== "For Developers"

    ### **Contribute to OSCAR**

    OSCAR is a Python project. We welcome contributions!

    {{ project_info() | indent(4)}}
    {{ show_tech_stack() | indent(4) }}

     We use `pyproject.toml` for dependency management.

    ??? info "Check pyproject.toml"
        ```toml title="pyproject.toml"
        --8<-- "pyproject.toml"
        ```

    <div class="grid cards" markdown>

    -   :fontawesome-brands-github: **Source Code**
        ---
        Clone the repository and start coding.
        [:octicons-arrow-right-24: Go to GitHub](https://github.com/emin-girimhanov/oscar-discord-bot)

    -   :material-bug: **Issue Tracker**
        ---
        Found a bug? Report it or pick up an issue.
        [:octicons-arrow-right-24: View Issues](https://github.com/emin-girimhanov/oscar-discord-bot/issues)

    -   :fontawesome-solid-book: **Architecture**
        ---
        Understand the database models and module system.
        [:octicons-arrow-right-24: See Developer Guide](developer/index.md)

    </div>

    === "Quick Setup"

        See [Setup & Installation](developer/setup.md) for more details.

        ```bash
        # 1. Clone Repo
        git clone https://github.com/emin-girimhanov/oscar-discord-bot.git discord-bot
        cd discord-bot
        ```

        ```bash
        # 2. Configure Environment
        # Create a .env file with required variables:
        cat > .env << EOF
        BOT_TOKEN=your_discord_bot_token_here
        DISCORD_SERVER_ID=your_discord_server_id_here
        TABLES_URL=https://your-nextcloud.de/apps/tables/
        TABLES_USERNAME=oscar-bot
        TABLES_PASSWORD=your_nextcloud_app_token_here
        EOF
        ```

        ```bash
        # 3. Install dependencies
        # Option A: Using uv (recommended for development)
        # Install uv first: https://docs.astral.sh/uv/getting-started/installation/
        uv sync

        # Option B: Using pip
        #pip install -e .
        ```

        ```bash
        # 4. Run Bot
        oscar_ovgu
        ```

        ✅ When you see "Logged in as OSCAR#...", you're ready!

    === "Development Standards"

        See [Git-Workflow](developer/workflow.md) for more details.

        To ensure the CI pipeline passes:

        * **Commits:** Use [Conventional Commits](https://www.conventionalcommits.org/)
            - Examples: `feat: add new filter`, `fix: crash on startup`
            !!! warning
                Non-conforming commits will fail the [commitlint](https://commitlint.js.org/) check

        * **Linting:** We use [pylint](https://pypi.org/project/pylint/), and [basedpyright](https://pypi.org/project/basedpyright/)
            ```bash
            # Check code quality before pushing
            # (Pylint score must be >= 9.5 to pass CI/CD)
            pylint --recursive=y src

            # Type checking
            basedpyright src
            ```

        * **Testing:** Run the test suite with pytest:
            ```bash
            pytest
            # With coverage report:
            pytest --cov=src
            ```
            - Contributions with additional unit tests are welcome
            - Test your changes on a development server before pushing

    === "CI/CD Pipeline"

        See [Git-Workflow](developer/workflow.md) for more details.

        The GitLab CI pipeline runs automatically on every push:

        1. **Lint Stage:**
            - `commitlint` - Validates commit messages
            - `pylint` - Code quality check (must score >= 9.5)
            - `basedpyright` - Static type checking


        2. **Build Stage:**
            - Creates Python package (`python -m build`)
            - Generates wheel file in `dist/`


        3. **Publish Stage:**
            - Builds container image with Buildah
            - Pushes to internal GitLab registry
            - Publishes documentation to GitLab Pages

        ??? info "Check .gitlab-ci.yml"
            ```yaml title=".gitlab-ci.yml"
            --8<-- ".gitlab-ci.yml"
            ```

        !!! tip "OVGU Developers: CI/CD Variables"
            The required secrets (tokens, keys) for the pipeline are stored as GitLab CI/CD variables.
            Access them at:
            [:octicons-arrow-right-24: CI/CD Variable Settings](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/settings/ci_cd#js-cicd-variables-settings)

    ### **Resources**

    <div class="grid cards" markdown>

    -   :material-book-open-variant: **discord.py Docs**
        ---
        Official library reference for all Discord API interactions.
        [:octicons-arrow-right-24: discordpy.readthedocs.io](https://discordpy.readthedocs.io/en/stable/)

    -   :material-puzzle: **Discord Components**
        ---
        Reference for buttons, select menus, modals and other UI components.
        [:octicons-arrow-right-24: Discord Dev Docs](https://docs.discord.com/developers/components/reference)

    -   :material-rocket-launch: **Discord Quick Start**
        ---
        Getting started guide for building Discord bots.
        [:octicons-arrow-right-24: Getting Started](https://docs.discord.com/developers/quick-start/getting-started)

    -   :simple-discord: **Invite OSCAR (Beta)**
        ---
        Add the current bot instance to your test server.
        [:octicons-arrow-right-24: Invite Bot](https://discord.com/oauth2/authorize?client_id=1417432722581884979)

    </div>

    [View full Developer Guide](developer/index.md){ .md-button .md-button--primary }
    ---

=== "For Administrators"

    OSCAR can be self‑hosted on your own infrastructure. This section gives you everything you need to install, configure and operate the bot as a **server** admin.

    ### **Bot Management & Deployment**

    Tools and documentation for maintaining OSCAR on your own infrastructure.

    !!! info "OVGU Data Source Dependency"
        OSCAR currently fetches module data from **OVGU's Nextcloud Tables** instance.
        External self-hosting requires either access to the OVGU Nextcloud or setting up
        a compatible Nextcloud Tables instance with your own module data.

    ### **Configuration (Required)**

    OSCAR requires specific environment variables to function. The bot checks for these on startup and will terminate if critical variables are missing.

    Create a `.env` file with the following keys:

    | Variable | Example | Description | Where to Get |
    |----------|---------|-------------|--------------|
    | `BOT_TOKEN` | `MTk4NjIy...` | Discord Bot Token | [Discord Developer Portal](https://discord.com/developers/applications) |
    | `DISCORD_SERVER_ID` | `987654321` | Your Discord Server ID | Right-click server → "Copy Server ID" *(requires **Developer Mode**: Settings → Advanced → Developer Mode)* |
    | `TABLES_URL` | `https://cloud.ovgu.de/apps/tables/` | Nextcloud Tables API URL | From your Nextcloud admin |
    | `TABLES_USERNAME` | `oscar-bot` | Nextcloud user account | Create in Nextcloud |
    | `TABLES_PASSWORD` | `nc_app_token_...` | Nextcloud app password | Generate in Nextcloud → Settings → Security |

    !!! warning ".env"
        **Never commit `.env` to Git!** Use `.gitignore` to prevent accidents.
        Leaked tokens and passwords can cause real breaches within seconds.


        **⚠️ AI Coding Assistants** (Cursor, Copilot, Claude Code, ...) may read your
        `.env` unprompted and send secrets to third-party servers — even if git-ignored.

        * Add `.cursorignore` / `.aiderignore` to exclude sensitive files.
        * Restrict workspace access in your AI tool's settings.


    ### **Quick Start**

    === "Step 1: Get Discord Bot Token"

        1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
        2. Click "New Application" and give it a name
        3. Go to "Bot" section → Click "Add Bot"
        4. Under TOKEN section, click "Copy" to copy your bot token
        5. Paste in `.env` as `BOT_TOKEN`

    === "Step 2: Set Bot Permissions"
        In the [Discord Developer Portal](https://discord.com/developers/applications) under the "Bot" tab:

        1. Scroll down to "Privileged Gateway Intents".
        2. Enable Message Content Intent (Required by src/oscar/main.py).
        3. Save Changes.

        Then generate the invite link:

        4.  Go to "OAuth2" → "URL Generator"
        5.  Select Scopes: `bot`, `applications.commands`
        6.  Select Permissions: `Send Messages`, `Read Message History`, `Embed Links`, `Attach Files`
            > **Note:** Slash commands are registered via the `applications.commands` scope (already selected above), not via a bot permission.
        7.  Copy generated URL → Open in browser → Select your server and authorize
    === "Step 3: Setup OSCAR"

        ```bash
        # 1. Clone the repository
        git clone https://github.com/emin-girimhanov/oscar-discord-bot.git discord-bot
        cd discord-bot
        ```

        ```bash
        # 2. Create .env file with your values
        # ⚠️ TABLES_URL must point to the App root (ending with /), not a specific table ID.
        cat > .env << EOF
        BOT_TOKEN=your_token_from_step_1_here
        DISCORD_SERVER_ID=your_server_id_here
        # OVGU Nextcloud Configuration
        TABLES_URL=https://cloud.ovgu.de/apps/tables/
        TABLES_USERNAME=oscar-bot
        TABLES_PASSWORD=your_nextcloud_app_token_here
        EOF
        ```

        ```bash
        # 3. Install dependencies (Requires Python >= 3.12)
        # Tip: activate a virtual environment first to avoid PEP 668 errors on modern Linux:
        # python3 -m venv .venv && source .venv/bin/activate
        pip install .
        ```

        ```bash
        # 4. Run the bot
        oscar_ovgu
        ```

        ✅ When you see `Logged in as OSCAR#...`, you're ready!

    ### **Deployment Options**

    We recommend using **Docker** (see Option C below) to ensure the database is persisted correctly via volumes. If you prefer running the Python application directly, follow these options.

    === "Option A: Direct Installation (Virtual Environment)"

        Use a virtual environment to keep dependencies and the database isolated.

        ```bash
        # 1. Create and activate venv
        python3 -m venv .venv
        source .venv/bin/activate
        ```

        ```bash
        # 2. Install the package
        pip install .
        ```

        ```bash
        # 3. Setup Environment
        # Ensure your .env file is present!
        ```

        ```bash
        # 4. Run in background
        # (Output is redirected to oscar.log)
        nohup oscar_ovgu > oscar.log 2>&1 &
        ```

    === "Option B: systemd Service (Recommended for Linux)"

        This ensures the bot auto-starts and runs under a restricted user context.

        ```bash
        # 1. Prepare Directory & User
        # Create user and directory
        sudo useradd -r -s /bin/false oscar
        sudo mkdir -p /opt/oscar
        sudo chown oscar:oscar /opt/oscar

        # Switch to user oscar to install
        # Note: use 'sudo -u oscar bash' (not -i) since the shell is /bin/false
        sudo -u oscar bash
        cd /opt/oscar

        # Clone Repo (or copy files) and setup venv
        git clone https://github.com/emin-girimhanov/oscar-discord-bot.git .
        python3 -m venv .venv
        source .venv/bin/activate
        pip install .
        ```

        ```bash
        # 2. Create Service File
        sudo nano /etc/systemd/system/oscar-bot.service
        ```

        Paste this configuration (adjust paths if necessary):

        ```ini
        [Unit]
        Description=OSCAR Discord Bot
        After=network.target

        [Service]
        Type=simple
        User=oscar
        WorkingDirectory=/opt/oscar
        # Load environment variables
        EnvironmentFile=/opt/oscar/.env
        # Use the executable inside the virtual environment
        ExecStart=/opt/oscar/.venv/bin/oscar_ovgu
        Restart=always
        RestartSec=10

        [Install]
        WantedBy=multi-user.target
        ```

        Then enable and start:

        ```bash
        # Reload systemd
        sudo systemctl daemon-reload

        # Enable auto-start
        sudo systemctl enable oscar-bot

        # Start the bot
        sudo systemctl start oscar-bot

        # Check status
        sudo systemctl status oscar-bot

        # View logs
        journalctl -u oscar-bot -f
        ```

    === "Option C: Docker / Podman"

        Because the `Containerfile` relies on a pre-built wheel file, you must build the package first.

        > **Note:** The image uses a `Containerfile` (Podman convention). Docker supports it via `-f Containerfile`, but you can rename it to `Dockerfile` for standard Docker setups.

        ```bash
        # 1. Build the Python package (requires 'build' tool)
        pip install build
        python -m build
        ```

        ```bash
        # 2. Build the Docker image
        # Replace 'latest' with the actual version tag if needed (check pyproject.toml)
        docker build -f Containerfile -t oscar-bot:latest .
        ```

        ```bash
        # 3. Run the container
        # The database is stored in the /database volume inside the container.
        docker run \
            --env-file .env \
            --name oscar-bot \
            --restart unless-stopped \
            -v oscar_data:/database \
            oscar-bot:latest
        ```

        ```bash
        # 4. View logs
        docker logs -f oscar-bot
        ```

    ### Monitoring & Health

    **Check if bot is online:**

    In your Discord server, type (requires **Administrator** permission):
    ```
    !ping
    ```

    Expected response: `Latency is 0.04` (~40 ms — note: the bot reports seconds, not ms)

    **View logs:**

    - **Direct run:** Check terminal output
    - **systemd:** `journalctl -u oscar-bot -f`
    - **Docker:** `docker logs -f oscar-bot`

    **Database health (Local Install):**

    Since the bot is installed as a package, the database is located inside the virtual environment.

    To find the exact location:

    ```bash
    # Print the actual database path used by the bot
    # (Run this inside your active venv)
    python -c "from util.database import get_database; print(get_database().db_path)"

    # Then verify schema version using the printed path, e.g.:
    # sqlite3 /path/to/your/venv/lib/site-packages/util/database/oscar.db "PRAGMA user_version;"
    # Expected Output: 3 (current schema version)
    ```

    ### **Resources**

    <div class="grid cards" markdown>

    -   :material-rocket-launch: **Discord Quick Start**
        ---
        Getting started guide for creating a bot application.
        [:octicons-arrow-right-24: Getting Started](https://docs.discord.com/developers/quick-start/getting-started)

    -   :simple-discord: **Invite OSCAR (Beta)**
        ---
        Add the currently hosted beta bot to your server.
        [:octicons-arrow-right-24: Invite Bot](https://discord.com/oauth2/authorize?client_id=1417432722581884979)

    </div>

    [View Full Admin Guide](admin/index.md){ .md-button .md-button--primary }
---

## **Quick Links**

<div class="grid cards" markdown>

- :fontawesome-brands-github: **OSCAR-REPO**
    ---

    View the source code and contribute.

    [:octicons-arrow-right-24: GitHub](https://github.com/emin-girimhanov/oscar-discord-bot)

- :material-school: **Faculty (FIN)**
    ---

    Official website of the Faculty.

    [:octicons-arrow-right-24: FIN Website](https://www.fin.ovgu.de/)

- :material-information-outline: **About OSCAR**
    ---

    Team, goals, and timeline.

    [:octicons-arrow-right-24: About OSCAR](about_oscar.md)

- :material-shield-account: **Privacy Policy**
    ---

    GDPR compliant data handling.

    [:octicons-arrow-right-24: Privacy Policy](privacy.md)

</div>

<br>

---

## **Contact the Project Authors**

If you have questions or need support, reach out to the team:
<div class="author-grid" markdown>

- **Christos Lachanas** <br> :material-server-network: *DevOps & API Integration* <br> <a data-email="Y2hyaXN0b3MubGFjaGFuYXNAc3Qub3ZndS5kZQ==" href="#">christos.lachanas [at] st.ovgu.de</a>
- **Malte Hedrich** <br> :material-brush: *Frontend & User Experience* <br> <a data-email="bWFsdGUuaGVkcmljaEBzdC5vdmd1LmRl" href="#">malte.hedrich [at] st.ovgu.de</a>
- **Malte Heiß** <br> :material-database: *Backend & Database Architecture* <br> <a data-email="bWFsdGUuaGVpc3NAc3Qub3ZndS5kZQ==" href="#">malte.heiss [at] st.ovgu.de</a>
- **Emin Girimhanov** <br> :material-file-document: *Backend & Documentation* <br> <a data-email="ZW1pbi5naXJpbWhhbm92QHN0Lm92Z3UuZGU=" href="#">emin.girimhanov [at] st.ovgu.de</a>

</div>
