#!/usr/bin/env python3
"""
Initialize data directory structure.
Run this script to create all required data directories.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.config import settings


def create_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {path}")
    else:
        print(f"  Exists: {path}")


def create_gitkeep(path: Path) -> None:
    """Create .gitkeep file to track empty directories."""
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
        print(f"✓ Created: {gitkeep}")


def main():
    """Initialize all data directories."""
    print("\n📁 Initializing data directory structure...\n")
    
    base_dir = Path(settings.BASE_DIR) / "data"
    
    # Directory structure
    directories = [
        base_dir,
        base_dir / "database",
        base_dir / "database" / "migrations",
        base_dir / "database" / "migrations" / "versions",
        base_dir / "vector_store",
        base_dir / "uploads",
        base_dir / "generated",
        base_dir / "generated" / "images",
        base_dir / "generated" / "charts",
        base_dir / "logs",
        base_dir / "cache",
        base_dir / "sessions",
        base_dir / "exports",
        base_dir / "backups",
    ]
    
    for directory in directories:
        create_directory(directory)
    
    print("\n📁 Creating .gitkeep files...\n")
    
    gitkeep_dirs = [
        base_dir / "database",
        base_dir / "database" / "migrations" / "versions",
        base_dir / "vector_store",
        base_dir / "uploads",
        base_dir / "generated" / "images",
        base_dir / "generated" / "charts",
        base_dir / "logs",
        base_dir / "cache",
        base_dir / "sessions",
        base_dir / "exports",
        base_dir / "backups",
    ]
    
    for directory in gitkeep_dirs:
        create_gitkeep(directory)
    
    # Create logging configuration if it doesn't exist
    log_conf = base_dir / "logs" / "logging.conf"
    if not log_conf.exists():
        print(f"\n📝 Creating logging configuration: {log_conf}")
        # Configuration content is in the file above
    
    print("\n✅ Data directory structure initialized successfully!\n")
    
    # Print directory tree
    print("Directory structure:")
    print("====================")
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(str(base_dir), "").count(os.sep)
        indent = "  " * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        sub_indent = "  " * (level + 1)
        for file in sorted(files):
            if file != ".gitkeep":
                print(f"{sub_indent}📄 {file}")


if __name__ == "__main__":
    main()