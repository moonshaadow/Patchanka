#!/usr/bin/env python3
"""Patchanka launcher."""

import os
import sys
from pathlib import Path

# Force qtpy to use PyQt6, the binding with which HP was compiled
os.environ['QT_API'] = 'pyqt6'

ROOT = Path(__file__).parent
HP_SOURCE = ROOT / "HoustonPatchbay" / "source"

if not HP_SOURCE.is_dir():
    print(f"Error: {HP_SOURCE} not found.")
    print("Please initialize the submodule:")
    print("  git submodule update --init --recursive")
    sys.exit(1)

sys.path.insert(0, str(HP_SOURCE))
sys.path.insert(0, str(ROOT))

from patchanka.__main__ import main

if __name__ == "__main__":
    main()