# Running OSCAR on a FaRaFIN server

The bot is a single container. It opens **outgoing** connections only, to
`discord.com`, `cloud.ovgu.de` and `bookstack.cs.ovgu.de`. It listens on nothing, so
it needs no published port, no reverse proxy, no certificate and no VPN.

---

## What it costs

Measured on the running container, not estimated:

| | |
| :--- | ---: |
| RAM | **94 MB** |
| CPU, idle | 0 % |
| Image on disk | 522 MB |
| Database after months of use | 96 KB |
| Network | one request to `cloud.ovgu.de` every 9 minutes |

Any machine that already runs something else has room for this.

---

## The five settings

They live in `.env` on the server and nowhere else. Never in the repository, never in
the image, never in the compose file.

| Variable | What it is |
| :--- | :--- |
| `BOT_TOKEN` | Discord Developer Portal → the application → Bot → Reset Token |
| `DISCORD_SERVER_ID` | Developer Mode on, right click the server, *Copy Server ID* |
| `TABLES_URL` | `https://cloud.ovgu.de/apps/tables/`, already correct in the example |
| `TABLES_USERNAME` | an OVGU Nextcloud login |
| `TABLES_PASSWORD` | an **app password**, from cloud.ovgu.de → Settings → Security |

```bash
cp .env.example .env
$EDITOR .env
chmod 600 .env
```

!!! warning "One token, one bot"
    A Discord token may run in exactly one place. If a laptop and the server use the
    same token, both answer every command and the student sees two replies. Give the
    server its own Discord application, or stop the other one.

---

## 1. The repository on Forgejo

```bash
git clone --mirror https://isggit3.cs.ovgu.de/studium-lehre/discord-bot.git
cd discord-bot.git
git remote add forgejo https://<forgejo host>/<owner>/oscar.git
git push --mirror forgejo
```

A mirror push carries every branch and tag. After that, set the new remote as
`origin` in a normal clone and work there.

---

## 2. The pipeline

`.forgejo/workflows/ci.yml` is in the repository. It needs two things on the
instance:

1. **A runner.** `forgejo-runner register` against the instance, with the label
   `docker`. One runner is enough.
2. **Actions switched on** for the repository, under *Settings → Units → Actions*.

It then runs on every push to `main` and `develop`, and on every pull request:

| Job | What it does |
| :--- | :--- |
| `lint` | pylint over `src`, fails under 9.5 |
| `test` | the full suite and `mkdocs build --strict` |
| `commitlint` | Conventional Commits on the pushed messages |
| `image` | builds the container and pushes it to the Forgejo registry |

The image job runs only on a branch, not on a pull request, and only after the other
three pass. It needs **no secret**: Forgejo hands the job a token that may write
packages of its own repository.

The image ends up at `<forgejo host>/<owner>/oscar:latest`, and every commit also
gets its own tag, so a rollback is `docker pull ...:<older sha>`.

---

## 3. The server

```bash
mkdir -p /srv/oscar && cd /srv/oscar
# only these two files are needed, not the whole repository
curl -O https://<forgejo host>/<owner>/oscar/raw/branch/main/compose.server.yaml
curl -O https://<forgejo host>/<owner>/oscar/raw/branch/main/.env.example
cp .env.example .env && $EDITOR .env && chmod 600 .env
```

Add the image to `.env`:

```bash
OSCAR_IMAGE=<forgejo host>/<owner>/oscar:latest
```

Log in once, with a Forgejo token that may read packages:

```bash
docker login <forgejo host>
docker compose -f compose.server.yaml pull
docker compose -f compose.server.yaml up -d
docker compose -f compose.server.yaml logs -f
```

A healthy start looks like this:

```text
Finished loading 14 semesterplans
Logged in as OSCAR#0846, running build <sha>
Synced 29 commands to '<server>'
Module table warm: 410 rows in 0.3s
All 13 BookStack books answer
```

If any of those five lines is missing, the answer is in the log above it.

---

## 4. Updating

```bash
docker compose -f compose.server.yaml pull
docker compose -f compose.server.yaml up -d
```

The database is a named volume, so it survives. Nothing else on the container is
worth keeping.

To roll back, put the older commit sha in `OSCAR_IMAGE` and run the same two lines.

---

## The database is the only irreplaceable thing

`/database/oscar.db` holds every student's programme, saved plan, module ratings and
written reviews. The image can be rebuilt from git, the settings from a password
manager. This cannot.

```bash
docker run --rm -v oscar_oscar-db:/db -v "$PWD":/out alpine \
  sh -c 'cp /db/oscar.db /out/oscar-$(date +%F).db'
```

It is under 100 KB. Put it in whatever already backs up on that machine.

---

## What still needs a human, twice a year

**The module handbook links rot.** The faculty renames a BookStack book whenever an
edition rolls over, and on 2026-09-17 all eleven programme books went in one
afternoon. The bot notices at startup and falls back to a search, so nothing breaks,
but the deep links stay gone until somebody runs:

```bash
python tools/generate_bookstack_map.py
```

**The study plans follow the regulation.** When the faculty publishes a new
Studien- und Prüfungsordnung, the page numbers move. See
[Standard study plans](utils/semesterplans.md).

Both are jobs for the start of a semester, not for the pipeline.

---

## Two things that will go wrong

**The bot answers twice.** Two containers share a token. Stop one.

**Every command says "the application did not respond".** The Tables API is
unreachable, or `TABLES_PASSWORD` is a login password rather than an app password.
The log says which.
