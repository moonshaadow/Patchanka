#!/bin/bash
# install.sh - Build script for Patchanka.
#
# This script:
#   1. Checks required tools and Python packages
#   2. Initializes git submodules if missing
#   3. Builds HoustonPatchbay (Qt UI files, resources, translations)
#   4. Builds pw-bridge C wrapper
#   5. Builds Patchanka translations (.qm files)
#
# Usage:
#   ./install.sh

set -e
cd "$(dirname "$0")"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

section() {
    echo ""
    echo "======================================================"
    echo "  $1"
    echo "======================================================"
}

ok()      { echo -e "  ${GREEN}OK${NC}   $1"; }
warn()    { echo -e "  ${YELLOW}WARN${NC} $1"; }
fail()    { echo -e "  ${RED}FAIL${NC} $1" >&2; }

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# Check if a Python module is importable
has_py_module() {
    python3 -c "import $1" 2>/dev/null
}

# Detect the distro package manager
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "${ID:-unknown}"
    else
        echo "unknown"
    fi
}

# Print install hint based on distro
install_hint() {
    local pkg_debian="$1"
    local pkg_fedora="$2"
    local pkg_arch="$3"

    case "$(detect_distro)" in
        debian|ubuntu|linuxmint|pop)
            echo "  sudo apt install $pkg_debian"
            ;;
        fedora|rhel|centos)
            echo "  sudo dnf install $pkg_fedora"
            ;;
        arch|manjaro)
            echo "  sudo pacman -S $pkg_arch"
            ;;
        *)
            echo "  (install manually: $pkg_debian)"
            ;;
    esac
}

# ----------------------------------------------------------------------
# 1. Check required tools
# ----------------------------------------------------------------------

section "1. Checking required tools"

MISSING_TOOLS=()

check_tool() {
    local name="$1"
    local test_cmd="$2"

    if eval "$test_cmd" >/dev/null 2>&1; then
        ok "$name"
    else
        fail "$name"
        MISSING_TOOLS+=("$name")
    fi
}

check_tool "Python 3"                    "command -v python3"
check_tool "C compiler (cc or gcc)"      "command -v cc || command -v gcc"
check_tool "pkg-config"                  "command -v pkg-config"
check_tool "libpipewire-0.3 (dev)"       "pkg-config --exists libpipewire-0.3"
check_tool "pyuic6"                      "command -v pyuic6"
check_tool "lrelease"                    "command -v lrelease || command -v lrelease-qt6"
check_tool "pylupdate6"                  "command -v pylupdate6"

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo ""
    echo "Missing tools: ${MISSING_TOOLS[*]}"
    echo ""
    echo "Install them with:"
    install_hint \
        "python3 python3-pip pkg-config libpipewire-0.3-dev pyqt6-dev-tools qt6-l10n-tools" \
        "python3 pkg-config pipewire-devel python3-qt6-devel qt6-linguist" \
        "python pkg-config pipewire python-pyqt6 qt6-tools"
    exit 1
fi

# ----------------------------------------------------------------------
# 2. Check Python packages
# ----------------------------------------------------------------------

section "2. Checking Python packages"

MISSING_MODULES=()

check_py_module() {
    local module="$1"
    local pkg_name="$2"

    if has_py_module "$module"; then
        local version
        version=$(python3 -c "
try:
    import $module
    print(getattr($module, '__version__', '?'))
except Exception:
    print('?')
" 2>/dev/null)
        ok "$pkg_name (version $version)"
    else
        fail "$pkg_name"
        MISSING_MODULES+=("$pkg_name")
    fi
}

check_py_module "qtpy"    "qtpy"
check_py_module "PyQt6"   "PyQt6"

if [ ${#MISSING_MODULES[@]} -ne 0 ]; then
    echo ""
    echo "Missing Python packages: ${MISSING_MODULES[*]}"
    echo ""
    echo "Prefer system packages:"
    install_hint \
        "python3-qtpy python3-pyqt6" \
        "python3-qtpy python3-pyqt6" \
        "python-qtpy python-pyqt6"
    echo ""
    echo "If system packages are not available, use pip:"
    echo "  pip install --user ${MISSING_MODULES[*]}"
    exit 1
fi

# ----------------------------------------------------------------------
# 3. Initialize submodules
# ----------------------------------------------------------------------

section "3. Initializing git submodules"

if [ ! -d ".git" ]; then
    fail "Not a git repository"
    exit 1
fi

if [ -f "libs/HoustonPatchbay/Makefile" ] \
        && [ -f "libs/pw-bridge/native/Makefile" ]; then
    ok "Submodules already present"
else
    echo "  Initializing submodules..."
    git submodule update --init --recursive
    ok "Submodules initialized"
fi

# ----------------------------------------------------------------------
# 4. Build HoustonPatchbay
# ----------------------------------------------------------------------

section "4. Building HoustonPatchbay"

HP_DIR="libs/HoustonPatchbay"

if [ ! -d "$HP_DIR" ]; then
    fail "$HP_DIR not found"
    exit 1
fi

if [ -f "$HP_DIR/source/patchbay/ui/canvas_options.py" ]; then
    ok "Qt UI files already generated (skipping)"
    echo "     To force rebuild: cd $HP_DIR && make clean && make"
else
    echo "  Generating Qt UI files and resources..."
    (cd "$HP_DIR" && make)
    ok "HoustonPatchbay built"
fi

# ----------------------------------------------------------------------
# 5. Build pw-bridge C wrapper
# ----------------------------------------------------------------------

section "5. Building pw-bridge C wrapper"

PWBRIDGE_NATIVE="libs/pw-bridge/native"

if [ ! -d "$PWBRIDGE_NATIVE" ]; then
    fail "$PWBRIDGE_NATIVE not found"
    exit 1
fi

(cd "$PWBRIDGE_NATIVE" && make clean && make)

if [ ! -f "$PWBRIDGE_NATIVE/libpw_bridge.so" ]; then
    fail "Build failed: libpw_bridge.so not found"
    exit 1
fi

ok "C wrapper built: $PWBRIDGE_NATIVE/libpw_bridge.so"

# ----------------------------------------------------------------------
# 6. Build Patchanka translations
# ----------------------------------------------------------------------

section "6. Building Patchanka translations"

if [ ! -d "patchanka/locale" ]; then
    warn "patchanka/locale/ not found, skipping translations"
else
    if [ ! -f "patchanka/locale/patchanka_fr.ts" ]; then
        echo "  Creating French translation file..."
        ./scripts/create_translation.sh fr
    fi

    make update >/dev/null
    make compile

    ok "Translations built"
fi

# ----------------------------------------------------------------------
# 7. Summary
# ----------------------------------------------------------------------

section "Done"

echo "  Patchanka is ready."
echo ""
echo "  Run it with:"
echo "    python3 run.py"
echo ""