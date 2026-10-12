#!/bin/bash
# install.sh - Build and install Patchanka.
#
# This script:
#   1. Detects the distribution and required tools
#   2. Initializes git submodules
#   3. Builds HoustonPatchbay, pw-bridge, and translations
#   4. Installs Patchanka in $XDG_DATA_HOME/patchanka
#   5. Creates a launcher in ~/.local/bin
#
# Usage:
#   ./install.sh            # build and install
#   ./install.sh --build    # build only, no install
#   ./install.sh --uninstall

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

ok()   { echo -e "  ${GREEN}OK${NC}   $1"; }
warn() { echo -e "  ${YELLOW}WARN${NC} $1"; }
fail() { echo -e "  ${RED}FAIL${NC} $1" >&2; }

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# Detect distribution from /etc/os-release
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "${ID:-unknown}"
    else
        echo "unknown"
    fi
}

# Detect distribution family (debian, fedora, arch, suse)
detect_distro_family() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "${ID:-}" in
            debian|ubuntu|linuxmint|pop|elementary|zorin)
                echo "debian" ;;
            fedora|rhel|centos|rocky|alma)
                echo "fedora" ;;
            arch|manjaro|endeavouros|garuda)
                echo "arch" ;;
            opensuse*|sles)
                echo "suse" ;;
            *)
                case "${ID_LIKE:-}" in
                    *debian*) echo "debian" ;;
                    *fedora*|*rhel*) echo "fedora" ;;
                    *arch*) echo "arch" ;;
                    *suse*) echo "suse" ;;
                    *) echo "unknown" ;;
                esac
                ;;
        esac
    else
        echo "unknown"
    fi
}

# Print install hint for a package
install_hint() {
    local family
    family=$(detect_distro_family)

    case "$family" in
        debian)
            echo "  sudo apt install $1"
            ;;
        fedora)
            echo "  sudo dnf install $2"
            ;;
        arch)
            echo "  sudo pacman -S $3"
            ;;
        suse)
            echo "  sudo zypper install $4"
            ;;
        *)
            echo "  (unknown distribution: install $1 manually)"
            ;;
    esac
}

# XDG paths with fallbacks
XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
XDG_BIN_HOME="$HOME/.local/bin"
INSTALL_DIR="$XDG_DATA_HOME/patchanka"
LAUNCHER="$XDG_BIN_HOME/patchanka"

# ----------------------------------------------------------------------
# Parse arguments
# ----------------------------------------------------------------------

BUILD_ONLY=false
UNINSTALL=false

for arg in "$@"; do
    case "$arg" in
        --build)     BUILD_ONLY=true ;;
        --uninstall) UNINSTALL=true ;;
        --help|-h)
            echo "Usage: $0 [--build|--uninstall]"
            exit 0
            ;;
    esac
done

# ----------------------------------------------------------------------
# Uninstall
# ----------------------------------------------------------------------

if [ "$UNINSTALL" = true ]; then
    section "Uninstalling Patchanka"

    if [ -f "$LAUNCHER" ]; then
        rm -f "$LAUNCHER"
        ok "Removed launcher: $LAUNCHER"
    else
        warn "Launcher not found: $LAUNCHER"
    fi

    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        ok "Removed install directory: $INSTALL_DIR"
    else
        warn "Install directory not found: $INSTALL_DIR"
    fi

    echo ""
    echo "  Patchanka has been uninstalled."
    exit 0
fi

# ----------------------------------------------------------------------
# 1. Detect distribution
# ----------------------------------------------------------------------

section "1. Detecting system"

DISTRO=$(detect_distro)
FAMILY=$(detect_distro_family)

ok "Distribution: $DISTRO (family: $FAMILY)"
ok "Install directory: $INSTALL_DIR"
ok "Launcher: $LAUNCHER"

# ----------------------------------------------------------------------
# 2. Check required tools
# ----------------------------------------------------------------------

section "2. Checking required tools"

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

check_tool "Python 3"              "command -v python3"
check_tool "C compiler"            "command -v cc || command -v gcc"
check_tool "pkg-config"            "command -v pkg-config"
check_tool "libpipewire-0.3 (dev)" "pkg-config --exists libpipewire-0.3"
check_tool "pyuic6"                "command -v pyuic6"
check_tool "lrelease"              "command -v lrelease || command -v lrelease-qt6"
check_tool "pylupdate6"            "command -v pylupdate6"

# Distribution-specific package names for missing tools
if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo ""
    echo "Missing tools: ${MISSING_TOOLS[*]}"
    echo ""
    echo "Install them with:"
    install_hint \
        "python3 python3-pip pkg-config libpipewire-0.3-dev pyqt6-dev-tools qt6-l10n-tools" \
        "python3 pkg-config pipewire-devel python3-qt6-devel qt6-linguist" \
        "python pkg-config pipewire python-pyqt6 qt6-tools" \
        "python3 pkg-config pipewire-devel python3-qt6-devel qt6-linguist"
    exit 1
fi

# ----------------------------------------------------------------------
# 3. Check Python packages
# ----------------------------------------------------------------------

section "3. Checking Python packages"

MISSING_MODULES=()

check_py_module() {
    local module="$1"
    local pkg_name="$2"

    if python3 -c "import $module" 2>/dev/null; then
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
check_py_module "PyQt6.QtSvg" "PyQt6.QtSvg"

# HoustonPatchbay dependencies
check_py_module "jack"    "JACK-Client (required by HoustonPatchbay)"

if [ ${#MISSING_MODULES[@]} -ne 0 ]; then
    echo ""
    echo "Missing Python packages: ${MISSING_MODULES[*]}"
    echo ""
    echo "Prefer system packages:"
    install_hint \
        "python3-qtpy python3-pyqt6 python3-pyqt6.qtsvg python3-jack-client" \
        "python3-qtpy python3-pyqt6 python3-pyqt6-svg python3-jack-client" \
        "python-qtpy python-pyqt6 python-jack-client" \
        "python3-qtpy python3-qt6 python3-qt6-svg python3-jack-client"
    echo ""
    echo "If system packages are not available, use pip:"
    echo "  pip install --user qtpy PyQt6 JACK-Client"
    exit 1
fi

# ----------------------------------------------------------------------
# 4. Initialize submodules
# ----------------------------------------------------------------------

section "4. Initializing git submodules"

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
# 5. Build HoustonPatchbay
# ----------------------------------------------------------------------

section "5. Building HoustonPatchbay"

HP_DIR="libs/HoustonPatchbay"

if [ ! -d "$HP_DIR" ]; then
    fail "$HP_DIR not found"
    exit 1
fi

if [ -f "$HP_DIR/source/patchbay/ui/canvas_options.py" ]; then
    ok "Qt UI files already generated"
else
    echo "  Generating Qt UI files..."
    (cd "$HP_DIR" && make)
    ok "HoustonPatchbay built"
fi

# ----------------------------------------------------------------------
# 6. Build pw-bridge C wrapper
# ----------------------------------------------------------------------

section "6. Building pw-bridge C wrapper"

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

ok "C wrapper built"

# ----------------------------------------------------------------------
# 7. Build Patchanka translations
# ----------------------------------------------------------------------

section "7. Building Patchanka translations"

if [ -d "patchanka/locale" ]; then
    if [ ! -f "patchanka/locale/patchanka_fr.ts" ]; then
        ./scripts/create_translation.sh fr
    fi

    make update >/dev/null
    make compile
    ok "Translations built"
else
    warn "patchanka/locale/ not found, skipping translations"
fi

# ----------------------------------------------------------------------
# 8. Install (unless --build only)
# ----------------------------------------------------------------------

if [ "$BUILD_ONLY" = true ]; then
    section "Build complete (install skipped)"
    echo "  Run with: python3 run.py"
    exit 0
fi

section "8. Installing Patchanka"

mkdir -p "$INSTALL_DIR"
mkdir -p "$XDG_BIN_HOME"

# Copy the entire project tree (excluding git and build artifacts)
echo "  Copying files to $INSTALL_DIR..."
rsync -a --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.qm' \
    ./ "$INSTALL_DIR/"

# Rebuild translations in the install directory
(cd "$INSTALL_DIR" && make compile >/dev/null 2>&1) || true

ok "Files installed to $INSTALL_DIR"

# Create the launcher script
cat > "$LAUNCHER" << EOF
#!/bin/bash
# Patchanka launcher
cd "$INSTALL_DIR"
exec python3 "$INSTALL_DIR/run.py" "\$@"
EOF

chmod +x "$LAUNCHER"
ok "Launcher created: $LAUNCHER"

# ----------------------------------------------------------------------
# 9. Check PATH
# ----------------------------------------------------------------------

section "9. Checking PATH"

if echo "$PATH" | grep -q "$XDG_BIN_HOME"; then
    ok "$XDG_BIN_HOME is in PATH"
else
    warn "$XDG_BIN_HOME is not in PATH"
    echo ""
    echo "  Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "  Then reload your shell:"
    echo "    source ~/.bashrc"
fi

# ----------------------------------------------------------------------
# Done
# ----------------------------------------------------------------------

section "Done"

echo "  Patchanka has been installed."
echo ""
echo "  Run it with:"
echo "    patchanka"
echo ""
echo "  Or directly:"
echo "    python3 $INSTALL_DIR/run.py"
echo ""
