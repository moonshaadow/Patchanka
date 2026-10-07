"""Translation setup for Patchanka.

Loads both Patchanka and HoustonPatchbay translation files (.qm)
and installs them on the QApplication.

Order matters: translators installed later take precedence.
We install HoustonPatchbay first, then Patchanka, so Patchanka
strings win if contexts ever overlap (which should not happen
since contexts are different).
"""

import logging
from pathlib import Path

from qtpy.QtCore import QTranslator, QLocale
from qtpy.QtWidgets import QApplication

_logger = logging.getLogger(__name__)

# Keep strong references to translators so they are not
# garbage collected by Python.
_translators: list[QTranslator] = []


def _load_translator(
        app: QApplication,
        locale_dir: Path,
        prefix: str) -> bool:
    """Try to load a translation file matching the system locale.

    Args:
        app: QApplication instance.
        locale_dir: Directory containing .qm files.
        prefix: Filename prefix (e.g. "patchanka", "patchbay").

    Returns:
        True if a translation was loaded, False otherwise.
    """
    if not locale_dir.is_dir():
        _logger.debug(f"Locale directory not found: {locale_dir}")
        return False

    locale = QLocale.system()
    locale_name = locale.name()  # e.g. "fr_FR"

    # Candidate names, in order of preference
    candidates = [
        locale_name,                # "fr_FR"
        locale_name.split('_')[0],  # "fr"
        "en",                       # fallback
    ]

    for candidate in candidates:
        qm_file = locale_dir / f"{prefix}_{candidate}.qm"
        if not qm_file.is_file():
            continue

        translator = QTranslator(app)
        if translator.load(str(qm_file)):
            app.installTranslator(translator)
            _translators.append(translator)
            _logger.info(f"Loaded translation: {qm_file}")
            return True
        else:
            _logger.warning(f"Failed to load: {qm_file}")

    _logger.info(f"No translation found for prefix '{prefix}'")
    return False


def install_translations(app: QApplication) -> None:
    """Install all available translations on the application.

    Loads (in this order):
    1. HoustonPatchbay translations
    2. Patchanka translations

    The last installed takes precedence for identical contexts.
    """
    root = Path(__file__).parent.parent

    # HoustonPatchbay translations
    hp_locale_dir = root / "libs" / "HoustonPatchbay" / "locale"
    _load_translator(app, hp_locale_dir, "patchbay")

    # Patchanka translations
    pk_locale_dir = Path(__file__).parent / "locale"
    _load_translator(app, pk_locale_dir, "patchanka")