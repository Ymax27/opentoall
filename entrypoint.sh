#!/usr/bin/env sh
set -e

# Wait for Postgres when we know a discrete host (docker-compose).
# With DATABASE_URL (Neon / Render) we skip the socket wait and retry migrate.
if [ -z "$DATABASE_URL" ] && [ "$USE_POSTGRES" = "1" ]; then
    echo "Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."
    until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
sys.exit(0) if not s.connect_ex((os.getenv('DB_HOST','db'), int(os.getenv('DB_PORT','5432')))) else sys.exit(1)" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL is up."
fi

# Migrations must not block the HTTP port.
# On Render free, every wake re-runs this script. cron-job.org gives up after
# ~30s. Waiting here for Neon + migrate made both cron jobs time out until
# cron-job.org marked them inactive.
(
    i=0
    until python manage.py migrate --noinput; do
        i=$((i + 1))
        if [ "$i" -ge 10 ]; then
            echo "migrate failed after $i attempts" >&2
            exit 1
        fi
        echo "migrate attempt $i failed — retrying in 3s..."
        sleep 3
    done

    if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
        python manage.py bootstrap_admin || true
    fi
) &

exec "$@"
