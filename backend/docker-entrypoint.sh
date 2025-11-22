#!/usr/bin/env bash
set -euo pipefail

# --- Critical: Self-Correct Line Endings and Permissions ---
echo "🛠️ Ensuring all shell scripts have correct Unix line endings and permissions..."

# 1. Clean the line endings of the entrypoint script itself
tr -d '\r' < "$0" > /tmp/entrypoint_cleaned && mv /tmp/entrypoint_cleaned "$0"

# 2. Clean the line endings of the called script
tr -d '\r' < /app/sqlcmd.sh > /tmp/sqlcmd_cleaned && mv /tmp/sqlcmd_cleaned /app/sqlcmd.sh

# 3. CRITICAL: Explicitly force execute permission inside the container, 
# mitigating any host filesystem or caching issues.
chmod +x /app/docker-entrypoint.sh
chmod +x /app/sqlcmd.sh
# -----------------------------------------------------------

MAX_WAIT=120 # Still 120 seconds for high robustness
RETRY_DELAY=5

echo "⏳ Waiting for SQL Server to accept connections..."

# Use the cleaner 'until' loop with combined host/port variable
until /opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST,$DB_PORT" -U "$DB_USER" -P "$DB_PASSWORD" -Q "SELECT 1" -C > /dev/null 2>&1; do
    echo "⚠️ SQL Server not ready — retrying in $RETRY_DELAY seconds..."
    sleep $RETRY_DELAY
done

echo "✅ SQL Server is ready."

# Run initial DDL creation (Database creation/Schema setup)
/app/sqlcmd.sh

# --- CRITICAL FIX: Change directory to /app before running Alembic ---
echo "📂 Changing directory to /app to ensure alembic.ini is found..."
cd /app
echo "Current directory: $(pwd)"
# -------------------------------------------------------------------

echo "🟦 Running Alembic migrations..."
alembic upgrade head || {
  echo "❌ Alembic failed! Check logs for migration errors."
  # Add extra check for environment variables if alembic fails
  echo "DEBUG: Check if DATABASE_URL is set correctly in the container."
  exit 1
}

echo "✅ Migrations complete."

# --- POST-MIGRATION TABLE VERIFICATION (Keep this diagnostic step) ---
# This step forces the script to print all tables that were just created.
echo "🔍 Verifying table creation in database [$DB_NAME]..."
/opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST,$DB_PORT" -U "$DB_USER" -P "$DB_PASSWORD" -C \
-d "$DB_NAME" -Q "SELECT name FROM sys.tables ORDER BY name;"

if [ $? -eq 0 ]; then
    echo "✅ Table verification successful. All tables created by Alembic should be listed above."
else
    echo "❌ Failed to query tables immediately after migration. Check environment variables or permissions."
    exit 1
fi
# ----------------------------------------------


echo "🚀 Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000