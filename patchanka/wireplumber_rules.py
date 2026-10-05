"""Gestion des regles de renommage Lua pour WirePlumber.

Patchanka stocke les noms personnalises sous forme de regles Lua
dans un fichier dedie, avec un marqueur permettant de les identifier
et de les supprimer proprement.

Emplacement : ~/.config/wireplumber/wireplumber.conf.d/
Nom du fichier : 99-patchanka-rename.conf
"""

import logging
import re
from pathlib import Path

_logger = logging.getLogger(__name__)


_MARKER = "# patchanka-managed"
_CONFIG_FILE_NAME = "99-patchanka-rename.conf"
_FORMAT_VERSION = "1"


def _config_dir() -> Path:
    """Retourne le dossier de configuration WirePlumber utilisateur."""
    xdg_config = Path.home() / ".config"
    return xdg_config / "wireplumber" / "wireplumber.conf.d"


def _config_file() -> Path:
    """Retourne le chemin du fichier de regles Patchanka."""
    return _config_dir() / _CONFIG_FILE_NAME


def _escape_lua_string(value: str) -> str:
    """Echappe une chaine pour inclusion dans une string Lua."""
    return (value
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n"))


def _parse_rules(content: str) -> dict[str, str]:
    """Parse le fichier de regles et retourne {node_name: display_name}."""
    result: dict[str, str] = {}

    pattern = re.compile(
        r'--\s*patchanka-managed\s*'
        r'\{[^{}]*matches\s*=\s*\{\s*\{\s*'
        r'\{\s*"node\.name"\s*,\s*"equals"\s*,\s*"([^"]+)"\s*\}'
        r'\s*,\s*\}\s*,\s*\}'
        r'.*?\[\s*"node\.description"\s*\]\s*=\s*"([^"]*)"',
        re.DOTALL
    )

    for match in pattern.finditer(content):
        node_name = match.group(1)
        display_name = match.group(2)
        result[node_name] = display_name

    return result


def load_rules() -> dict[str, str]:
    """Charge les regles Patchanka depuis le fichier."""
    path = _config_file()
    if not path.is_file():
        return {}

    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        _logger.exception(f"Lecture impossible : {path}")
        return {}

    return _parse_rules(content)


def _build_file_content(rules: dict[str, str]) -> str:
    """Construit le contenu complet du fichier de regles."""
    lines = [
        "# Regles de renommage creees par Patchanka.",
        f"# Format : {_FORMAT_VERSION}",
        "#",
        "# Ce fichier est gere automatiquement.",
        "# Ne pas editer manuellement sauf si vous savez ce que vous faites.",
        "",
        "monitor.alsa.rules = [",
    ]

    for node_name, display_name in rules.items():
        node_esc = _escape_lua_string(node_name)
        disp_esc = _escape_lua_string(display_name)

        lines.append(f"    -- {_MARKER}")
        lines.append("    {")
        lines.append("        matches = [")
        lines.append("            {")
        lines.append(f'                node.name = "{node_esc}"')
        lines.append("            }")
        lines.append("        ]")
        lines.append("        actions = {")
        lines.append("            update-props = {")
        lines.append(f'                node.description = "{disp_esc}"')
        lines.append("            }")
        lines.append("        }")
        lines.append("    },")

    lines.append("]")
    lines.append("")

    return "\n".join(lines)


def save_rules(rules: dict[str, str]):
    """Ecrit les regles dans le fichier de configuration."""
    path = _config_file()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        _logger.exception(f"Impossible de creer {path.parent}")
        return

    content = _build_file_content(rules)

    try:
        path.write_text(content, encoding="utf-8")
        _logger.info(f"Regles Patchanka sauvegardees : {path}")
    except Exception:
        _logger.exception(f"Ecriture impossible : {path}")


def set_custom_name(node_name: str, display_name: str):
    """Ajoute ou met a jour le nom personnalise d'un noeud."""
    rules = load_rules()

    if display_name:
        rules[node_name] = display_name
    else:
        rules.pop(node_name, None)

    save_rules(rules)


def remove_custom_name(node_name: str):
    """Supprime le nom personnalise d'un noeud."""
    rules = load_rules()
    rules.pop(node_name, None)
    save_rules(rules)


def clear_all_rules():
    """Supprime toutes les regles creees par Patchanka."""
    path = _config_file()
    if path.is_file():
        try:
            path.unlink()
            _logger.info(f"Fichier de regles supprime : {path}")
        except Exception:
            _logger.exception(f"Suppression impossible : {path}")
