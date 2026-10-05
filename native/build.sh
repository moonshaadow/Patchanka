#!/bin/bash
# build.sh - Build the Patchanka C wrapper.

set -e
cd "$(dirname "$0")"

if ! pkg-config --exists libpipewire-0.3; then
    echo "Error: libpipewire-0.3 not found."
    echo "Install libpipewire-0.3-dev (Debian/Ubuntu) or the equivalent."
    exit 1
fi

make clean
make

echo "Wrapper built: $(pwd)/libpatchanka_pw.so"