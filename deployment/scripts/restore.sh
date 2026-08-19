#!/bin/bash
# Database restore script

set -e

BACKUP_DIR="/opt/enterprise-ai-platform/data/backups"
DB_PATH="/opt/enterprise-ai-platform/data/database/app.db"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -la "$BACKUP_DIR"/*.db.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Decompress if gzipped
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📦 Decompressing backup..."
    gunzip -c "$BACKUP_FILE" > "${BACKUP_FILE%.gz}"
    BACKUP_FILE="${BACKUP_FILE%.gz}"
fi

# Stop services
echo "🛑 Stopping services..."
systemctl stop backend.service || true

# Backup current database
if [ -f "$DB_PATH" ]; then
    echo "📦 Backing up current database..."
    cp "$DB_PATH" "$DB_PATH.bak.$(date +%Y%m%d_%H%M%S)"
fi

# Restore
echo "🔄 Restoring database from $BACKUP_FILE..."
sqlite3 "$DB_PATH" ".restore '$BACKUP_FILE'"

# Start services
echo "🚀 Starting services..."
systemctl start backend.service

echo "✅ Database restored successfully!"