# Running OSCAR yourself

The faculty server pulls the image from an internal registry and updates on a timer.
That is out of your hands. This page shows how to run the bot on your own machine or
home server instead.

The bot only opens **outgoing** connections, to `discord.com` and to
`cloud.ovgu.de`. Both are public. You need no university network, no VPN and no
open ports.

!!! warning "One bot, one instance"
    A Discord token may only run in one place at a time. If the faculty container
    and yours use the same token, both answer every command. Use your own test
    application while the faculty one is running.

## 1. Create your own bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications)
   and click **New Application**.
2. Go to **Bot** and press **Reset Token**. Copy the token.
3. On the same page enable **Message Content Intent**. The prefix commands such as
   `!resync` need it.
4. Go to **OAuth2 → URL Generator**. Tick the scopes `bot` and
   `applications.commands`. Without the second one no slash command can register.
5. Under **Bot Permissions** tick *Send Messages*, *Embed Links* and
   *Use Slash Commands*.
6. Open the generated link and invite the bot to a test server.

## 2. Fill in the settings

```bash
cp .env.example .env
```

Then edit `.env`:

| Variable | Where it comes from |
| --- | --- |
| `BOT_TOKEN` | the token from step 1 |
| `DISCORD_SERVER_ID` | Developer Mode on, right click the server, *Copy Server ID* |
| `TABLES_URL` | already filled in, `https://cloud.ovgu.de/apps/tables/` |
| `TABLES_USERNAME` | your Nextcloud account |
| `TABLES_PASSWORD` | cloud.ovgu.de → Settings → Security → **App passwords** |

`.env` is in `.gitignore`. Never commit it.

## 3. Start it

```bash
docker compose up -d --build
docker compose logs -f
```

The log should show `Logged in as ...` followed by the number of synced commands.

`compose.yaml` uses `Containerfile.selfhost`. Unlike the CI `Containerfile` it builds
the wheel itself, so no artifact from a pipeline is needed, and it bakes in no
secrets. They arrive at runtime from `.env`.

Both files sit on `python:3.14-slim-trixie`. The finished image is about 520 MB on
disk. The compiler toolchain of the full image is only needed while the wheel is
built, and that happens in a first stage that is thrown away.

## 4. Check which build is running

Type `!resync` on your home server, the one `DISCORD_SERVER_ID` names, or `/version`
anywhere. `!resync` answers to the owner of the application and to the administrators
of the home server. Both commands name the build:

```
🔄 Build `76cb5e1` synced 9 commands to 1 server(s): /help, /module, ...
```

`!resync` is a prefix command. It works even when the slash menu is still empty,
which makes it the reliable way to see what is actually deployed.

The build only carries a useful name if you stamp it. Without the variable it stays
the word `selfhost`, which tells you nothing:

```bash
OSCAR_REVISION=$(git rev-parse --short HEAD) docker compose build
docker compose up -d
```

On Windows PowerShell:

```powershell
docker compose build --build-arg OSCAR_REVISION=$(git rev-parse --short HEAD)
docker compose up -d
```

If the slash menu stays empty in the client, press `Ctrl+R` in Discord. The
client caches the command list.

## Making commands appear at once

By default the commands are registered globally. That reaches every server, but
a client can take up to an hour to notice a change.

While developing, add this to `.env`:

```
OSCAR_COMMAND_SCOPE=guild
```

Now they are registered only in the servers the bot is in, and they appear
immediately.

!!! warning "Never both scopes"
    Discord keeps global and guild commands apart and lists **both**. A command
    registered in both scopes shows up **twice** in the picker. Whichever scope
    is set, OSCAR empties the other one, so this cannot happen by accident.
    Switching the value once and restarting is enough to clean up.

## Everyday commands

```bash
docker compose logs -f          # follow the log
docker compose restart          # restart
docker compose up -d --build    # rebuild after a code change
docker compose down             # stop, the database volume stays
```

## Keeping the database

The SQLite file lives in a named volume, mounted at `/database`. A rebuild keeps it.
`docker compose down -v` deletes it, so avoid that flag.

`compose.yaml` calls the volume `oscar-db`, but Docker prefixes it with the project
name, which is the directory you start from. In a checkout called `discord-bot` the
real name is `discord-bot_oscar-db`. Ask Docker rather than guessing:

```bash
docker volume ls | grep oscar
```

Copy the database file once, by hand:

```bash
docker compose cp oscar:/database/oscar.db ./oscar-backup.db
```

That is fine while the bot is stopped. While it runs, a plain copy can catch the file
in the middle of a write. [Backing it up every night](#backing-it-up-every-night)
uses the SQLite backup API instead.

Restoring overwrites a file SQLite may have open, so stop the bot first:

```bash
docker compose stop
docker compose cp ./oscar-backup.db oscar:/database/oscar.db
docker compose start
```

## Running it on a home server

Nothing about the bot needs a data centre. It opens no listening port and needs no
university network, so a machine at home behind a normal router is enough. Nothing
has to be forwarded, and the server does not need to be reachable from outside.

### Surviving a reboot

`compose.yaml` already sets `restart: unless-stopped`, so Docker starts the container
again after a crash and after a reboot. That only holds if the Docker service itself
starts at boot:

```bash
sudo systemctl enable --now docker
```

Check it once by rebooting and then asking how long the container has been up:

```bash
docker compose ps
```

!!! note "`unless-stopped` remembers what you did"
    If you stop the container with `docker compose stop`, Docker leaves it stopped
    across a reboot. That is the point of the policy. Start it again with
    `docker compose start`.

### Updating to a newer version

Pull the code, rebuild with the commit as the build stamp, restart:

```bash
git pull
OSCAR_REVISION=$(git rev-parse --short HEAD) docker compose up -d --build
```

The stamp matters. Without it every build calls itself `selfhost` and `!resync` can
no longer tell you which version is answering.

The database volume survives this. Only the image is replaced.

### Backing it up every night

The database holds what students saved, and it lives in one volume. `tools/oscar-backup.sh`
copies it with the SQLite backup API, checks that the copy opens, and deletes copies
older than 14 days. A copy is personal data like the original: the script keeps it in
`/var/backups/oscar`, readable by root only. The 14 days are what the
[privacy page](../privacy.md) promises, change both together.

```bash
sudo install -m 700 tools/oscar-backup.sh /usr/local/sbin/oscar-backup
sudo /usr/local/sbin/oscar-backup          # run it once and read what it says
```

Run it every night with a systemd timer:

```ini title="/etc/systemd/system/oscar-backup.service"
[Unit]
Description=Copy the OSCAR database to /var/backups/oscar
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/oscar-backup
```

```ini title="/etc/systemd/system/oscar-backup.timer"
[Unit]
Description=Nightly copy of the OSCAR database

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now oscar-backup.timer
```

The copies sit on the same disk as the original. They save you from a bad update and
from a deleted volume, not from a dead disk. Copy the folder to a second machine if
that matters to you, and keep it as closed there as it is here.

### Running it without root

The container needs to write to `/database` and to a scratch `/tmp`, nothing else. Give
the volume to an unprivileged user once, while the bot is stopped:

```bash
docker compose down
sudo chown -R 10001:10001 "$(docker volume inspect -f '{{ .Mountpoint }}' discord-bot_oscar-db)"
```

Then add this to the `oscar` service in `compose.yaml` and start it again:

```yaml
    environment:
      LOGURU_LEVEL: INFO      # the debug lines are not worth keeping
      HOME: /tmp
    user: "10001:10001"
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
```

A bug in the bot or in a library can then do no more than the bot itself. Check it:

```bash
docker compose exec oscar id          # uid=10001
docker compose exec oscar touch /x    # Read-only file system
```

### Keeping the log small

`compose.yaml` caps the container log at five files of 10 MB, so it can never fill
the disk. That is enough for several days of history. Read it with
`docker compose logs -f`, or a slice of it with `docker compose logs --since 1h`.

### Reaching the server

You never need to reach the bot. It talks to Discord, Discord does not talk to it.

You do need to reach the **server** to update it. SSH on the local network is enough
at home. [Tailscale](https://tailscale.com/) is one way to get the same SSH access
from anywhere without opening a port on the router, but it is a convenience for you,
not a requirement for OSCAR.
