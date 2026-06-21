#!/bin/bash
set -e

echo "🔍 Checking database connection..."

# Use environment variables
DB_HOST=${POSTGRES_HOST:-user-service-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-user_db}
DB_USER=${POSTGRES_USER:-postgres}
MAX_RETRIES=30
RETRY_COUNT=0

# Wait for database to be ready
while ! nc -z $DB_HOST $DB_PORT && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "⏳ Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Database not available after $MAX_RETRIES retries"
    exit 1
fi

echo "✅ Database is ready!"

# Check if migrations have been run by checking if users table exists
# (This is a simple check that works for user-service)
echo "🔍 Checking if database tables exist..."
if [ "${CHECK_MIGRATIONS:-true}" = "true" ]; then
    if ! PGPASSWORD=${POSTGRES_PASSWORD} psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1 FROM users LIMIT 0;" > /dev/null 2>&1; then
        echo "❌ Database tables not found. Did migrations run?"
        echo "💡 To fix this, run migrations using: alembic upgrade head"
        exit 1
    fi
    echo "✅ Database tables exist"
fi

# Start the application
echo "🎯 Starting application..."
exec "$@"