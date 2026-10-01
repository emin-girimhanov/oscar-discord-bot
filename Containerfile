FROM python:3.14-slim-trixie
ARG OSCAR_REVISION=unknown
# CI injects these, because the server starts the image without its own env file.
# A runtime `-e` / `--env-file` still overrides them.
ARG BOT_TOKEN=
ARG DISCORD_SERVER_ID=
ARG TABLES_URL=
ARG TABLES_USERNAME=
ARG TABLES_PASSWORD=
LABEL org.opencontainers.image.title=oscar-ovgu \
	org.opencontainers.image.description=discordbot \
	org.opencontainers.image.revision=${OSCAR_REVISION}
ENV BOT_TOKEN="${BOT_TOKEN}"
ENV DISCORD_SERVER_ID="${DISCORD_SERVER_ID}"
ENV TABLES_URL="${TABLES_URL}"
ENV TABLES_USERNAME="${TABLES_USERNAME}"
ENV TABLES_PASSWORD="${TABLES_PASSWORD}"
# the wheel only contains python code, images and semesterplan json files live here
ENV OSCAR_ASSETS_DIR=/assets
ENV OSCAR_DB_PATH=/database/oscar.db
ENV OSCAR_REVISION=${OSCAR_REVISION}
# unbuffered output so the container log shows a line the moment it happens,
# and a writable matplotlib config directory so it stops warning on every start
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLCONFIGDIR=/tmp/matplotlib
ADD ["dist", "/"]
ADD ["assets", "/assets"]
RUN mkdir database
RUN pip install --no-cache-dir oscar_ovgu-*.whl
VOLUME [ "/database" ]
ENTRYPOINT ["oscar_ovgu"]
