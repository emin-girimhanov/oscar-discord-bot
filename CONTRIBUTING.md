# Contributing to OSCAR

Thank you for your interest in OSCAR. This page is the short version. The
[Developer Guide](https://emin-girimhanov.github.io/oscar-discord-bot/developer/) has the
details.

## Report a bug or suggest a feature

Open an [issue](https://github.com/emin-girimhanov/oscar-discord-bot/issues). Say what you
did, what you expected and what happened. Add the output of `/version` if the bot runs.

Do not put a security problem into an issue. See [SECURITY.md](SECURITY.md).

## Set up the project

You need Python 3.12 or newer.

```bash
git clone https://github.com/emin-girimhanov/oscar-discord-bot.git
cd oscar-discord-bot
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev,docs]"
```

To start the bot you also need a `.env` file. Copy `.env.example` and fill it in.
[Setup & Install](https://emin-girimhanov.github.io/oscar-discord-bot/developer/setup/)
explains where each value comes from.

## Run the checks

The pipeline runs these three checks. Run them before you push.

```bash
# the tests never touch the network, the three values only have to exist
export TABLES_URL=http://dummy/ TABLES_USERNAME=dummy TABLES_PASSWORD=dummy

pytest -q                          # the whole suite
pylint --recursive=y src           # the score must be 9.5 or higher
mkdocs build --strict              # the documentation must build without a warning
```

`mkdocs serve` shows the documentation at `http://127.0.0.1:8000` while you write.

## Make a change

1. Fork the repository and create a branch from `main`. Name it after the change,
   for example `feat/module-search` or `fix/filter-crash`.
2. Keep one topic per pull request. Add a test for a bug you fix and for a feature
   you add.
3. Document what you change. A new command belongs into
   `docs/features/commands.md`. Every text the bot says needs a German and an English
   version in `src/util/translations.py`.
4. Write the commit message as a
   [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/), for example
   `fix(filter): keep the selection after a page change`.
5. Open a pull request against `main` and describe what changes and why.

## Where things are

| Path | Content |
| :--- | :--- |
| `src/oscar` | the Discord bot: commands (`cogs`) and views (`ui`) |
| `src/util` | everything that is not Discord: module data, plans, database, texts |
| `tests` | one test file per area |
| `docs` | the documentation, built with MkDocs |
| `assets` | study plans, pictures and generated lookup tables |

## License

OSCAR is licensed under the [Apache License 2.0](LICENSE). You agree that your
contribution is published under the same license.
