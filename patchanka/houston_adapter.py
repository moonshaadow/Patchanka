"""Adaptateur entre les concepts PipeWire et l'interface de HoustonPatchbay.

HP utilise plusieurs types de donnees qui portent des noms historiquement
herites de JACK. Ces noms et valeurs sont internes a HP et n'ont aucune
dependance technique a JACK. Ils constituent le vocabulaire que HP attend
pour afficher correctement le graphe.

Ce module centralise la conversion des donnees PipeWire vers ces valeurs.
"""

from enum import IntFlag

from patshared import PortType, PortSubType


# ======================================================================
# Flags attendus par HP dans PortData.flags
# ======================================================================

class HpPortFlags(IntFlag):
    """Flags attendus par HP dans le champ PortData.flags."""
    INPUT    = 0x1
    OUTPUT   = 0x2
    PHYSICAL = 0x4
    MONITOR  = 0x8
    TERMINAL = 0x10


# ======================================================================
# Conversion media.class -> PortType HP
# ======================================================================

_MEDIA_CLASS_TO_PORT_TYPE = {
    "Audio/Sink":          PortType.AUDIO_JACK,
    "Audio/Source":        PortType.AUDIO_JACK,
    "Audio/Duplex":        PortType.AUDIO_JACK,
    "Stream/Output/Audio": PortType.AUDIO_JACK,
    "Stream/Input/Audio":  PortType.AUDIO_JACK,
    "Midi/Bridge":         PortType.MIDI_JACK,
    "Midi/Source":         PortType.MIDI_JACK,
    "Midi/Sink":           PortType.MIDI_JACK,
    "Midi/Duplex":         PortType.MIDI_JACK,
    "Video/Source":        PortType.VIDEO,
    "Video/Sink":          PortType.VIDEO,
}


def media_class_to_port_type(media_class: str) -> PortType:
    """Convertit media.class PipeWire en PortType HP."""
    return _MEDIA_CLASS_TO_PORT_TYPE.get(media_class, PortType.AUDIO_JACK)


# ======================================================================
# Categorisation des noeuds
# ======================================================================

_HARDWARE_MEDIA_CLASS_PREFIXES = (
    "Audio/Sink",
    "Audio/Source",
    "Audio/Duplex",
    "Video/Source",
    "Video/Sink",
    "Midi/Bridge",
)

_APPLICATION_MEDIA_CLASS_PREFIXES = (
    "Stream/Input",
    "Stream/Output",
)

_FILTER_FACTORY_NAMES = (
    "filter-chain",
    "loopback",
    "echo-cancel",
)


def is_hardware_media_class(media_class: str) -> bool:
    """Determine si un media.class correspond a un peripherique materiel."""
    if not media_class:
        return False
    return media_class.startswith(_HARDWARE_MEDIA_CLASS_PREFIXES)


def is_application_media_class(media_class: str) -> bool:
    """Determine si un media.class correspond a un flux applicatif."""
    if not media_class:
        return False
    return media_class.startswith(_APPLICATION_MEDIA_CLASS_PREFIXES)


def is_filter_node(media_class: str, props: dict) -> bool:
    """Determine si un noeud correspond a un filtre PipeWire."""
    factory_name = props.get("factory.name", "")
    if factory_name in _FILTER_FACTORY_NAMES:
        return True
    if props.get("node.link-group"):
        return True
    return False


def categorize_node(media_class: str, props: dict) -> str:
    """Retourne la categorie d'un noeud PipeWire.

    Categories : 'filter', 'device', 'application', 'other'.
    """
    if is_filter_node(media_class, props):
        return "filter"
    if is_hardware_media_class(media_class):
        return "device"
    if is_application_media_class(media_class):
        return "application"
    return "other"


# ======================================================================
# Calcul des flags HP pour un port
# ======================================================================

def port_flags(
        direction: str,
        is_hardware: bool,
        port_name: str = "") -> int:
    """Calcule les flags HP pour un port PipeWire."""
    flags = HpPortFlags.INPUT if direction == "in" else HpPortFlags.OUTPUT

    if is_hardware:
        flags |= HpPortFlags.PHYSICAL

    if port_name.startswith("monitor_"):
        flags |= HpPortFlags.MONITOR

    return int(flags)


# ======================================================================
# Sous-type de port
# ======================================================================

def port_subtype(node_name: str, port_type: PortType) -> PortSubType:
    """Retourne le sous-type HP d'un port."""
    if node_name.startswith(("Midi-Bridge", "a2j")):
        return PortSubType.A2J
    return PortSubType.REGULAR


# ======================================================================
# Nom d'affichage d'un noeud
# ======================================================================

def node_display_name(
        props: dict,
        custom_names: dict | None = None) -> str:
    """Determine le nom d'affichage d'un noeud.

    Ordre de priorite :
    1. Nom personnalise de Patchanka (custom_names)
    2. node.description (nom lisible fourni par PipeWire)
    3. node.nick (surnom court, s'il existe)
    4. node.name (identifiant technique)
    """
    node_name = props.get("node.name", "")

    if custom_names and node_name in custom_names:
        return custom_names[node_name]

    description = props.get("node.description", "")
    if description:
        return description

    nick = props.get("node.nick", "")
    if nick:
        return nick

    return node_name or "inconnu"



def is_midi_port(port_props: dict, node_media_class: str = "") -> bool:
    """Determine si un port PipeWire est un port MIDI.

    Le critere le plus fiable est format.dsp :
    - "8 bit raw midi" pour les ports MIDI
    - autre valeur pour les ports audio/video
    """
    # 1. format.dsp (critere principal)
    format_dsp = port_props.get("format.dsp", "").lower()
    if "midi" in format_dsp:
        return True

    # 2. media.class du noeud parent
    if "Midi" in node_media_class or "midi" in node_media_class.lower():
        return True

    # 3. port.name (fallback)
    port_name = port_props.get("port.name", "").lower()
    if "midi" in port_name:
        return True

    return False