#!/usr/bin/env sh
set -e

# Wait for Postgres when running against it (docker-compose / production).
if [ "$USE_POSTGRES" = "1" ]; then
    echo "Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."
    until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
sys.exit(0) if not s.connect_ex((os.getenv('DB_HOST','db'), int(os.getenv('DB_PORT','5432')))) else sys.exit(1)" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL is up."
fi

# Apply database migrations.
python manage.py migrate --noinput

exec "$@"
