# **Admin Guide – Installation & Maintenance**

Welcome to OSCAR's administration documentation. This guide covers installation, deployment, configuration, and day-to-day maintenance of the OSCAR Discord bot.

## **Deployment Overview**

??? info "Deployment Flowchart"
    ```mermaid
    flowchart TD
        Start([Admin Starts Installation]) --> Prerequisites{Prerequisites<br/>Met?}

        Prerequisites -->|No| InstallTools[Install Docker/Python/Git]
        InstallTools --> Prerequisites

        Prerequisites -->|Yes| ChooseMethod{Choose<br/>Deployment<br/>Method}

        %% Docker Path
        ChooseMethod -->|Docker<br/>Recommended| DockerClone[Clone Repository]
        DockerClone --> DockerEnv[Create .env File]
        DockerEnv --> DockerBuild[Build Docker Image]
        DockerBuild --> DockerRun[Start Container]
        DockerRun --> Verify

        %% Bare Python Path
        ChooseMethod -->|Bare Python<br/>Development| PythonClone[Clone Repository]
        PythonClone --> PythonVenv[Create Virtual<br/>Environment]
        PythonVenv --> PythonDeps[Install Dependencies]
        PythonDeps --> PythonEnv[Configure .env]
        PythonEnv --> PythonRun[Start Bot]
        PythonRun --> SystemdOptional{Setup<br/>Systemd?}
        SystemdSetup --> Verify

        %% Verification
        Verify[Verify Deployment]
        Verify --> VerifyChecks{Checks<br/>Passed?}
        VerifyChecks -->|✓ /help works<br/>✓ Commands synced<br/>✓ DB created| Success([Bot Running!])
        VerifyChecks -->|✗ Errors| Troubleshoot[Troubleshooting]
        Troubleshoot --> LogCheck[Check Logs]
        LogCheck --> FixIssue{Problem<br/>Identified?}
        FixIssue -->|.env Error| DockerEnv
        FixIssue -->|Permissions| PermFix[Fix Permissions<br/>chmod 600]
        PermFix --> Verify
        FixIssue -->|API Error| APICheck[Verify Credentials]
        APICheck --> DockerEnv

        %% Ongoing Maintenance
        Success --> Monitoring[Monitoring &<br/>Maintenance]
        Monitoring --> MonitorTasks[Monitor Logs<br/>Check Resources<br/>Create Backups]
        MonitorTasks --> UpdateCheck{Update<br/>Available?}
        UpdateCheck -->|Yes| UpdateProcess[Pull Changes<br/>Rebuild & Restart]
        UpdateProcess --> Verify
        UpdateCheck -->|No| MonitorTasks

        %% Styling
        style Start fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
        style Success fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
        style ChooseMethod fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
        style DockerRun fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
        style PythonRun fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
        style Verify fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff
        style Troubleshoot fill:#F44336,stroke:#C62828,stroke-width:2px,color:#fff
        style Monitoring fill:#00BCD4,stroke:#00838F,stroke-width:2px,color:#fff
    ```

=== "Option 1: Docker Installation (Recommended)"

    ### Prerequisites
    - Docker installed on your server
    - Discord Bot Token
    - Nextcloud Tables API credentials
    - GitLab repository access (or Docker image)

    ### Step 1: Build Docker Image

    ```bash
    # Clone repository
    git clone https://github.com/emin-girimhanov/oscar-discord-bot.git discord-bot
    cd discord-bot

    # Create .env file with your credentials (see Configuration Guide below)
    touch .env
    # Edit .env with your token and API credentials

    # Prepare and Build Package
    pip install build && python -m build
    ```

    ### Step 2: Run Docker Container

    ```bash
    # Run with environment file and persistent data volume
    docker run -d \
      --name oscar-bot \
      --env-file .env \
      -v oscar_data:/database \
      --restart unless-stopped \
      oscar-bot:latest
    ```

    **Options Explained:**
    - `-d` = Run in detached mode (background)
    - `--name oscar-bot` = Container name (for easy reference)
    - `--env-file .env` = Load environment variables
    - `-v oscar_data:/database` = Persistent volume to prevent data loss on updates
    - `--restart unless-stopped` = Auto-restart on failure

    ### Step 3: Verify Bot is Running

    ```bash
    # Check container logs
    docker logs oscar-bot

    # Follow logs in real-time
    docker logs -f oscar-bot

    # Check container status
    docker ps | grep oscar-bot
    ```

    **Expected output:**
    ```
    2026-03-05 14:00:00 | INFO     | Logged in as OSCAR#1234
    2026-03-05 14:00:00 | INFO     | Loaded ModulSearch cog
    2026-03-05 14:00:00 | INFO     | Loaded Help cog
    2026-03-05 14:00:00 | INFO     | Synced application commands
    ```

    ### Step 4: Docker Management

    ```bash
    # Stop the bot
    docker stop oscar-bot

    # Start the bot
    docker start oscar-bot

    # Restart the bot
    docker restart oscar-bot

    # Remove container (careful!)
    docker rm oscar-bot

    # Update bot (rebuild)
    docker build -t oscar-bot:latest .
    docker stop oscar-bot
    docker rm oscar-bot
    docker run -d --name oscar-bot --env-file .env -v oscar_data:/database --restart unless-stopped oscar-bot:latest
    ```

    ---

=== "Option 2: Bare Python Installation"

    ### Prerequisites
    - Python 3.12+
    - pip package manager
    - Git

    ### Step 1: Clone Repository

    ```bash
    git clone https://github.com/emin-girimhanov/oscar-discord-bot.git discord-bot
    cd discord-bot
    ```

    ### Step 2: Create Virtual Environment

    ```bash
    # Create venv
    python3 -m venv venv

    # Activate (Linux/Mac)
    source venv/bin/activate

    # Activate (Windows)
    venv\Scripts\activate
    ```

    ### Step 3: Install Dependencies

    ```bash
    # Upgrade pip
    pip install --upgrade pip

    # Install package and dependencies
    pip install .
    ```

    ### Step 4: Configure Environment

    ```bash
    # Create the config file manually
    touch .env

    # Edit .env with your credentials (see Configuration Guide below)
    nano .env
    # Or use any text editor

    # Verify configuration
    cat .env
    ```

    ### Step 5: Run the Bot

    ```bash
    # From activated venv
    oscar_ovgu
    ```

    **To run in background (Linux):**

    ```bash
    # Using nohup
    nohup oscar_ovgu > oscar.log 2>&1 &

    # Using systemd (Highly Recommended - see Step 6)
    ```

    ### Step 6: Systemd Service (for Auto-Start)

    Create `/etc/systemd/system/oscar.service`:

    ```ini
    [Unit]
    Description=OSCAR Discord Bot
    After=network.target

    [Service]
    Type=simple
    User=oscar
    WorkingDirectory=/home/oscar/discord-bot
    Environment="PATH=/home/oscar/discord-bot/venv/bin"
    EnvironmentFile=/home/oscar/discord-bot/.env
    ExecStart=/home/oscar/discord-bot/venv/bin/oscar_ovgu

    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

    Enable and start:

    ```bash
    # Reload systemd
    sudo systemctl daemon-reload

    # Enable auto-start on boot
    sudo systemctl enable oscar

    # Start the service
    sudo systemctl start oscar

    # Check status
    sudo systemctl status oscar

    # View logs
    sudo journalctl -u oscar -f
    ```

    ---

## **Configuration Guide**

### Environment Variables (.env)

```env
# ===== DISCORD CONFIGURATION =====
BOT_TOKEN=your_bot_token_here
DISCORD_SERVER_ID=your_server_id_here

# ===== NEXTCLOUD TABLES API =====
TABLES_URL=https://cloud.ovgu.de/apps/tables/
TABLES_USERNAME=your_username
TABLES_PASSWORD=your_app_password
```

### **How to Get Credentials**

#### Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application → Name it "OSCAR"
3. Go to "Bot" section → Click "Add Bot"
4. Copy the token (keep secret!)
5. Under "Intents", enable:
   - Message Content Intent

#### Nextcloud App Password

1. Log in to <https://cloud.ovgu.de>
2. Click your profile → Settings
3. Go to "Security" tab → "App Passwords"
4. Enter app name: `OSCAR Bot`
5. Click "Generate password"
6. Copy the shown password (won't be shown again!)

#### Discord Server ID

1. Enable Developer Mode in Discord
   - User Settings → Advanced → Developer Mode
2. Right-click your server name → Copy Server ID

---

## **Database Setup**

### Automatic (Recommended)

The bot automatically creates and migrates the SQLite database on first run.

```
First run: Creates database/oscar.db with schema v3
Subsequent runs: Checks version, migrates if needed
```

### Manual Database Management

```bash
# View database location
docker exec oscar-bot python -c "from util.database import get_database; db = get_database(); print(db.db_path)"

# Or on bare Python
python -c "from util.database import get_database; db = get_database(); print(db.db_path)"

# Backup database
cp database/oscar.db database/oscar.db.backup

# Reset database (WARNING: Deletes all user data!)
rm database/oscar.db  # Will be recreated on bot restart
```

---

## **Security Best Practices**

### 1. Protect Your Credentials

```bash
# .env should NEVER be committed to Git
git config core.hooksPath .githooks  # Use pre-commit hooks
chmod 600 .env  # Make .env readable only by owner
```

### 2. Best Practices

```bash
# Discord Bot Token: Do not share or commit this token!
# If accidentally exposed, regenerate immediately via the Developer Portal.

# Nextcloud Password: Uses app-specific passwords rather than your main university login.
```

### 3. Access Control

- **Database file:** Only accessible to bot user
- **Environment variables:** Not shown in logs
- **Docker secrets:** Consider Docker Secrets for production

### 4. Network Security

```bash
# Only expose Discord connection (outbound)
# Restrict database file permissions
chmod 600 database/oscar.db

# Use HTTPS for all external APIs
# Keep dependencies updated
pip install --upgrade .
```

---

## **Monitoring**

### Docker Health Check

```bash
# Check bot is responsive
docker exec oscar-bot python -c "print('OK')"

# Monitor resource usage
docker stats oscar-bot
```

### Logging

```bash
# View last 100 lines
docker logs oscar-bot 2>&1 | tail -100

# Search logs for errors
docker logs oscar-bot 2>&1 | grep "ERROR"

# Live log monitoring
docker logs -f oscar-bot
```

---

## **Installation Checklist**

After installation, verify:

- [ ] Bot appears online in Discord server
- [ ] `/help` command responds
- [ ] `/module` autocomplete works (takes ~5 seconds first time)
- [ ] User preferences saved (database created)
- [ ] No errors in logs
- [ ] Environment variables loaded correctly
- [ ] Database file exists and is accessible

---

## **Troubleshooting**

### Bot not connecting

```
Error: "BOT_TOKEN Environment Variable not set"

Solution:
1. Check .env file exists
2. Verify BOT_TOKEN=xxx format (not empty)
3. Restart container: docker restart oscar-bot
```

### Database locked

```
Error: "database is locked" / "unable to open database file"

Solution:
1. Check file permissions: chmod 600 database/oscar.db
2. Ensure only one bot instance running: docker ps
3. Restart container to release lock
```

### API connection failed

```
Error: "TABLES_URL connection timeout"

Solution:
1. Test API connectivity: curl -u $USER:$PASS $TABLES_URL
2. Verify credentials in .env
3. Check network connectivity from server
```

### Cogs not loading

```
Error: "Couldn't load oscar.cogs.modul"

Solution:
1. Check Python syntax in cog files
2. Verify imports are correct
3. Check logs for full error message
4. Rebuild Docker image if code changed
```

---

## **Updates & Maintenance**

### Update Bot Code

```bash
# Pull latest changes
git pull origin main

# 1. Build Python Package (Creates 'dist/' folder required by Dockerfile)
pip install build
python -m build

# 2. Build Docker image
docker build -t oscar-bot:latest .

# Stop old container
docker stop oscar-bot

# Remove old container
docker rm oscar-bot

# Start new container
docker run -d \
  --name oscar-bot \
  --env-file .env \
  -v oscar_data:/database \
  --restart unless-stopped \
  oscar-bot:latest
```

### Update Dependencies

```bash
# Keep dependencies updated
pip install --upgrade .

# Update specific package
pip install --upgrade discord.py

# Test everything still works
docker restart oscar-bot
```

---

## **Next Steps**

1. **Install OSCAR** – Follow the Docker or Bare Python options above
2. **Run** – Set up monitoring
3. **Review [Admin Commands](../features/commands.md)** – Understand server management
4. **Test in Discord** – Verify bot functionality

---

**Installation complete! Your OSCAR bot is ready to serve.**
