#!/bin/bash
# build.sh - Compile le wrapper C de Patchanka.

set -e
cd "$(dirname "$0")"

if ! pkg-config --exists libpipewire-0.3; then
    echo "Erreur : libpipewire-0.3 introuvable."
    echo "Installez libpipewire-0.3-dev (Debian/Ubuntu) ou l'équivalent."
    exit 1
fi

make clean
make

echo "Wrapper compilé : $(pwd)/libpatchanka_pw.so"
