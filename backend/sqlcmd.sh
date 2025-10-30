#!/bin/bash
set -e

echo "⏳ Waiting for SQL Server to start..."

while ! /opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST,$DB_PORT" \
     -U "$DB_USER" -P "$DB_PASSWORD" -Q "SELECT 1" -C > /dev/null 2>&1; do
    echo "⏳ SQL Server not ready yet... retrying in 2s"
    sleep 2
done

echo "✅ SQL Server is up!"

echo "🔍 Checking if database exists..."
DB_CHECK=$(/opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST,$DB_PORT" \
     -U "$DB_USER" -P "$DB_PASSWORD" \
     -Q "IF DB_ID(N'$DB_NAME') IS NOT NULL PRINT 'EXISTS'" -h -1 -C)

if [ "$DB_CHECK" == "EXISTS" ]; then
    echo "✅ Database $DB_NAME already exists"
else
    echo "📦 Creating database $DB_NAME"
    /opt/mssql-tools18/bin/sqlcmd -S "$DB_HOST,$DB_PORT" \
     -U "$DB_USER" -P "$DB_PASSWORD" \
     -Q "CREATE DATABASE [$DB_NAME]" -C
    echo "🎉 Database created!"
fi

echo "🚀 Running Alembic migrations..."
alembic upgrade head

echo "✅ Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
