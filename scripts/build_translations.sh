#!/bin/bash
# build_translations.sh - Build all translation files.
#
# Steps:
# 1. Create .ts files if missing (for locales listed in LOCALES)
# 2. Update .ts from source code
# 3. Compile .ts to .qm

set -e
cd "$(dirname "$0")/.."

# List of locales to support
LOCALES=("fr" "en")

# Step 1: Create .ts if missing
for loc in "${LOCALES[@]}"; do
    if [ ! -f "patchanka/locale/patchanka_${loc}.ts" ]; then
        echo "Creating translation file for locale: $loc"
        ./scripts/create_translation.sh "$loc"
    fi
done

# Step 2: Update .ts from source
echo ""
echo "Updating .ts files from source..."
make update

# Step 3: Compile to .qm
echo ""
echo "Compiling .ts to .qm..."
make compile

echo ""
echo "Done. Translation files:"
ls -la patchanka/locale/*.qm 2>/dev/null || echo "  (none)"