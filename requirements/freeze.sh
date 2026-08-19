#!/bin/bash
# Freeze current dependencies to requirements files

echo "📦 Freezing dependencies..."

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Create backups
if [ -f "requirements/base.txt" ]; then
    cp requirements/base.txt requirements/base.txt.bak
fi

# Generate frozen requirements
pip freeze > requirements/frozen.txt

# Filter and organize
echo "# Auto-generated frozen requirements" > requirements/frozen.txt
echo "# Generated on: $(date)" >> requirements/frozen.txt
echo "" >> requirements/frozen.txt

pip freeze >> requirements/frozen.txt

echo "✅ Dependencies frozen to requirements/frozen.txt"

# Show outdated packages
echo ""
echo "📋 Checking for outdated packages..."
pip list --outdated