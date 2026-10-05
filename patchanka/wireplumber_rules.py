"""Management of WirePlumber Lua rename rules.

Patchanka stores custom names as Lua rules in a dedicated file,
with a marker allowing them to be identified and cleanly removed.

Location: ~/.config/wireplumber/wireplumber.conf.d/
File name: 99-patchanka-rename.conf
"""

import logging
import re
from pathlib import Path

_logger = logging.getLogger(__name__)


_MARKER = "# patchanka-managed"
_CONFIG_FILE_NAME = "99-patchanka-rename.conf"
_FORMAT_VERSION = "1"


def _config_dir() -> Path:
    """Return the user WirePlumber configuration directory."""
    xdg_config = Path.home() / ".config"
    return xdg_config / "wireplumber" / "wireplumber.conf.d"


def _config_file() -> Path:
    """Return the path to the Patchanka rules file."""
    return _config_dir() / _CONFIG_FILE_NAME


def _escape_lua_string(value: str) -> str:
    """Escape a string for inclusion in a Lua string."""
    return (value
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n"))


def _parse_rules(content: str) -> dict[str, str]:
    """Parse the rules file and return {node_name: display_name}."""
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
    """Load the Patchanka rules from the file."""
    path = _config_file()
    if not path.is_file():
        return {}

    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        _logger.exception(f"Read failed: {path}")
        return {}

    return _parse_rules(content)


def _build_file_content(rules: dict[str, str]) -> str:
    """Build the complete content of the rules file."""
    lines = [
        "# Rename rules created by Patchanka.",
        f"# Format: {_FORMAT_VERSION}",
        "#",
        "# This file is managed automatically.",
        "# Do not edit manually unless you know what you are doing.",
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
    """Write the rules to the configuration file."""
    path = _config_file()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        _logger.exception(f"Failed to create {path.parent}")
        return

    content = _build_file_content(rules)

    try:
        path.write_text(content, encoding="utf-8")
        _logger.info(f"Patchanka rules saved: {path}")
    except Exception:
        _logger.exception(f"Write failed: {path}")


def set_custom_name(node_name: str, display_name: str):
    """Add or update a node custom name."""
    rules = load_rules()

    if display_name:
        rules[node_name] = display_name
    else:
        rules.pop(node_name, None)

    save_rules(rules)


def remove_custom_name(node_name: str):
    """Remove a node custom name."""
    rules = load_rules()
    rules.pop(node_name, None)
    save_rules(rules)


def clear_all_rules():
    """Remove all rules created by Patchanka."""
    path = _config_file()
    if path.is_file():
        try:
            path.unlink()
            _logger.info(f"Rules file deleted: {path}")
        except Exception:
            _logger.exception(f"Delete failed: {path}")