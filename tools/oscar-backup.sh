#!/bin/sh
# Nightly copy of the OSCAR database.
#
# The database holds what students saved: programme, plans, ratings. It lives in one
# docker volume and nowhere else, so one bad migration or one `docker volume rm`
# would have been the end of it.
#
# The copy is made with the sqlite backup API, inside the container. Copying the file
# with `cp` while the bot writes can produce a copy that does not open.
#
# A copy is personal data like the original. It is readable by root only, and it is
# deleted after KEEP_DAYS. A student who deletes their data with /my_data is gone from
# the last copy after that many days, which is what the privacy page promises.
set -eu
umask 077

DIR=/var/backups/oscar
KEEP_DAYS=14
TARGET="$DIR/oscar-$(date +%F).db"
SCRATCH=/tmp/oscar-backup.db

mkdir -p "$DIR"
chmod 700 "$DIR"

docker exec oscar python -c '
import sqlite3, sys
source = sqlite3.connect("/database/oscar.db")
copy = sqlite3.connect("'"$SCRATCH"'")
source.backup(copy)
verdict = copy.execute("PRAGMA integrity_check").fetchone()[0]
copy.close()
source.close()
sys.exit(0 if verdict == "ok" else 1)
'

# /tmp in the container is a tmpfs, which `docker cp` cannot read, so the copy is piped
docker exec oscar cat "$SCRATCH" > "$TARGET.part"
docker exec oscar rm -f "$SCRATCH"

# an empty file would silently replace a good copy of the same day
test -s "$TARGET.part"
mv "$TARGET.part" "$TARGET"
chmod 600 "$TARGET"

find "$DIR" -name 'oscar-*.db' -mtime +"$KEEP_DAYS" -delete
find "$DIR" -name '*.part' -mtime +1 -delete

echo "oscar-backup: wrote $TARGET ($(stat -c %s "$TARGET") bytes), keeping $(find "$DIR" -name 'oscar-*.db' | wc -l) copies"
