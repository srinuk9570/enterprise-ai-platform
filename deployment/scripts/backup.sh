#!/bin/bash
# Database backup script

set -e

BACKUP_DIR="/opt/enterprise-ai-platform/data/backups"
DB_PATH="/opt/enterprise-ai-platform/data/database/app.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/app_backup_$TIMESTAMP.db"
RETENTION_DAYS=30

echo "📦 Creating database backup..."

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Backup database
if [ -f "$DB_PATH" ]; then
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
    echo "✅ Backup created: $BACKUP_FILE"
    
    # Compress backup
    gzip "$BACKUP_FILE"
    echo "✅ Compressed: $BACKUP_FILE.gz"
else
    echo "⚠️  Database file not found: $DB_PATH"
    exit 1
fi

# Cleanup old backups
echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "app_backup_*.db.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed!"