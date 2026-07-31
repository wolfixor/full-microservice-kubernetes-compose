#!/bin/sh
set -e

echo "Checking database connection..."

DB_HOST=${POSTGRES_HOST:-notification-service-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-notification_db}
DB_USER=${POSTGRES_USER:-postgres}
MAX_RETRIES=30
RETRY_COUNT=0

while ! nc -z "$DB_HOST" "$DB_PORT" && [ "$RETRY_COUNT" -lt "$MAX_RETRIES" ]; do
    echo "Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; then
    echo "Database not available after $MAX_RETRIES retries"
    exit 1
fi

echo "Database is ready"

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
elif [ "${CHECK_MIGRATIONS:-true}" = "true" ]; then
    echo "Checking if database tables exist..."
    if ! PGPASSWORD=${POSTGRES_PASSWORD} psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM notifications LIMIT 0;" > /dev/null 2>&1; then
        echo "Database tables not found. Did migrations run?"
        exit 1
    fi
fi

echo "Starting application..."
exec "$@"
