#!/usr/bin/env bash
set -euo pipefail

# --- CRITICAL: Self-Correct Line Endings and Permissions ---
# This ensures the script can execute correctly even if copied with CRLF line endings.
tr -d '\r' < "$0" > /tmp/sqlcmd_cleaned && mv /tmp/sqlcmd_cleaned "$0"
chmod +x "$0"
# -----------------------------------------------------------

echo "⏳ Checking SQL Server at $DB_HOST:$DB_PORT ..."

# Wait until SQL Server responds
until /opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST,$DB_PORT" -U "$DB_USER" -P "$DB_PASSWORD" -Q "SELECT 1" -C > /dev/null 2>&1; do
    echo "❌ SQL Server not ready — retrying..."
    sleep 3
done

echo "✅ SQL Server is ready"

echo "📦 Ensuring database [$DB_NAME] exists..."
/opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST,$DB_PORT" -U "$DB_USER" -P "$DB_PASSWORD" -C \
-Q "IF NOT EXISTS(SELECT name FROM sys.databases WHERE name = '$DB_NAME') CREATE DATABASE [$DB_NAME];"

echo "✅ Database verified"