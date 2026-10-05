#!/usr/bin/env python3
"""Lanceur de Patchanka."""

import os
import sys
from pathlib import Path

# Forcer qtpy a utiliser PyQt6, le binding avec lequel HP a ete compile
os.environ['QT_API'] = 'pyqt6'

ROOT = Path(__file__).parent
HP_SOURCE = ROOT / "HoustonPatchbay" / "source"

if not HP_SOURCE.is_dir():
    print(f"Erreur : {HP_SOURCE} introuvable.")
    print("Initialisez le submodule :")
    print("  git submodule update --init --recursive")
    sys.exit(1)

sys.path.insert(0, str(HP_SOURCE))
sys.path.insert(0, str(ROOT))

from patchanka.__main__ import main

if __name__ == "__main__":
    main()
