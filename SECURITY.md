# Security

## Report a problem

Do not open a public issue for a security problem.

Use **Report a vulnerability** on the
[Security tab](https://github.com/emin-girimhanov/oscar-discord-bot/security/advisories/new)
of this repository. The report stays private until a fix is published.

Please include:

- what the problem is and how to reproduce it,
- which version is affected, `/version` in Discord names the build,
- what an attacker could do with it.

## What counts

OSCAR stores what students enter: programme, saved plans, module ratings and reviews.
A way to read or change the data of another user is a security problem. So is a way
to make the bot leak its token or the Nextcloud password.

## Secrets

The bot token and the Nextcloud app password belong into `.env` and nowhere else.
`.env` is in `.gitignore`. If a secret reached a commit, treat it as leaked: reset the
token in the Discord Developer Portal and revoke the app password in Nextcloud.
