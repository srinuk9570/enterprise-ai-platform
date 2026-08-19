#!/usr/bin/env python3
"""
Cleanup old data files.
"""
import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.config import settings


def cleanup_old_files(directory: Path, days_old: int, pattern: str = "*") -> int:
    """
    Delete files older than specified days.
    Returns number of files deleted.
    """
    if not directory.exists():
        return 0
    
    cutoff_time = time.time() - (days_old * 24 * 3600)
    deleted_count = 0
    
    for filepath in directory.glob(pattern):
        if filepath.is_file():
            if filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    deleted_count += 1
                    print(f"  Deleted: {filepath}")
                except Exception as e:
                    print(f"  Error deleting {filepath}: {e}")
    
    return deleted_count


def cleanup_empty_directories(directory: Path) -> int:
    """
    Remove empty subdirectories.
    Returns number of directories removed.
    """
    if not directory.exists():
        return 0
    
    removed_count = 0
    
    for subdir in directory.iterdir():
        if subdir.is_dir():
            try:
                if not any(subdir.iterdir()):
                    subdir.rmdir()
                    removed_count += 1
                    print(f"  Removed empty directory: {subdir}")
            except Exception as e:
                print(f"  Error removing {subdir}: {e}")
    
    return removed_count


def cleanup_logs(days_old: int = 30) -> int:
    """Cleanup old log files."""
    log_dir = Path(settings.LOG_FILE_PATH).parent
    print(f"\n📋 Cleaning logs older than {days_old} days...")
    deleted = cleanup_old_files(log_dir, days_old, "*.log*")
    print(f"  Deleted {deleted} log files")
    return deleted


def cleanup_uploads(days_old: int = 90) -> int:
    """Cleanup old uploaded files."""
    upload_dir = Path(settings.UPLOAD_PATH)
    print(f"\n📁 Cleaning uploads older than {days_old} days...")
    deleted = cleanup_old_files(upload_dir, days_old, "*")
    removed = cleanup_empty_directories(upload_dir)
    print(f"  Deleted {deleted} files, removed {removed} empty directories")
    return deleted


def cleanup_generated(days_old: int = 30) -> int:
    """Cleanup old generated images and charts."""
    images_dir = Path(settings.GENERATED_IMAGES_PATH)
    charts_dir = Path(settings.GENERATED_CHARTS_PATH)
    
    print(f"\n🎨 Cleaning generated assets older than {days_old} days...")
    
    deleted_images = cleanup_old_files(images_dir, days_old, "*")
    deleted_charts = cleanup_old_files(charts_dir, days_old, "*")
    
    removed_images = cleanup_empty_directories(images_dir)
    removed_charts = cleanup_empty_directories(charts_dir)
    
    total = deleted_images + deleted_charts
    print(f"  Deleted {total} files, removed {removed_images + removed_charts} empty directories")
    return total


def cleanup_cache(max_age_hours: int = 24) -> int:
    """Cleanup old cache files."""
    cache_dir = Path(settings.BASE_DIR) / "data" / "cache"
    print(f"\n🗂️  Cleaning cache older than {max_age_hours} hours...")
    
    # Convert hours to days for the function
    days_old = max_age_hours / 24
    deleted = cleanup_old_files(cache_dir, days_old, "*")
    print(f"  Deleted {deleted} cache files")
    return deleted


def create_backup() -> Path:
    """Create a backup of the database."""
    import shutil
    from datetime import datetime
    
    db_path = Path(settings.DATABASE_PATH)
    backup_dir = Path(settings.BASE_DIR) / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"app_backup_{timestamp}.db"
    
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
        print(f"\n💾 Created database backup: {backup_path}")
        
        # Cleanup old backups (keep last 10)
        backups = sorted(backup_dir.glob("app_backup_*.db"))
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                old_backup.unlink()
                print(f"  Removed old backup: {old_backup}")
        
        return backup_path
    else:
        print("\n⚠️  No database file found to backup")
        return None


def main():
    """Run cleanup tasks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup data files")
    parser.add_argument("--logs", type=int, default=30, help="Days to keep logs")
    parser.add_argument("--uploads", type=int, default=90, help="Days to keep uploads")
    parser.add_argument("--generated", type=int, default=30, help="Days to keep generated assets")
    parser.add_argument("--cache", type=int, default=24, help="Hours to keep cache")
    parser.add_argument("--backup", action="store_true", help="Create backup before cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual deletion)")
    
    args = parser.parse_args()
    
    print("\n🧹 Starting data cleanup...")
    print(f"   Dry run: {args.dry_run}")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN - No files will be deleted\n")
        return
    
    if args.backup:
        create_backup()
    
    cleanup_logs(args.logs)
    cleanup_uploads(args.uploads)
    cleanup_generated(args.generated)
    cleanup_cache(args.cache)
    
    print("\n✅ Cleanup completed!\n")


if __name__ == "__main__":
    main()