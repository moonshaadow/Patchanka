#!/bin/bash
# create_translation.sh - Create a new translation file for a locale.
#
# Usage:
#   ./scripts/create_translation.sh fr
#
# This creates patchanka/locale/patchanka_<locale>.ts

set -e
cd "$(dirname "$0")/.."

if [ -z "$1" ]; then
    echo "Usage: $0 <locale>"
    echo "Example: $0 fr"
    exit 1
fi

LOCALE="$1"
LOCALE_DIR="patchanka/locale"
TS_FILE="$LOCALE_DIR/patchanka_${LOCALE}.ts"

if [ -f "$TS_FILE" ]; then
    echo "Translation file already exists: $TS_FILE"
    exit 0
fi

mkdir -p "$LOCALE_DIR"

echo "Creating $TS_FILE..."

# Empty XML skeleton. pylupdate will fill it later.
cat > "$TS_FILE" << EOF
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="${LOCALE}">
</TS>
EOF

echo "Created $TS_FILE"
echo ""
echo "Run 'make update' to populate it from the source code."