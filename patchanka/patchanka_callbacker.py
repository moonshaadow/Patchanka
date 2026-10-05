"""Callbacker Patchanka : transmet les actions de l'utilisateur au moteur.

HP appelle ces methodes quand l'utilisateur interagit avec le canvas.
Par defaut, elles ne font rien. On les redefinit pour creer ou
supprimer des liens PipeWire.
"""

import logging

from patchbay.calbacker import Callbacker

_logger = logging.getLogger(__name__)


class PatchankaCallbacker(Callbacker):
    """Herite du Callbacker de HP pour brancher les actions sur PipeWire."""

    def ports_connect(
            self, group_out_id: int, port_out_id: int,
            group_in_id: int, port_in_id: int) -> bool:
        """Appele quand l'utilisateur tire un cable entre deux ports."""
        _logger.info(
            f"ports_connect group_out={group_out_id} port_out={port_out_id} "
            f"group_in={group_in_id} port_in={port_in_id}")

        mng = self.mng

        port_out = mng.get_port_from_id(group_out_id, port_out_id)
        port_in = mng.get_port_from_id(group_in_id, port_in_id)

        if port_out is None or port_in is None:
            _logger.warning(
                f"Port introuvable : out={port_out} in={port_in}")
            return False

        out_name = port_out.full_name
        in_name = port_in.full_name

        _logger.info(f"Connexion demandee : {out_name!r} -> {in_name!r}")

        engine = getattr(mng, '_engine', None)
        if engine is None:
            _logger.warning("Pas de moteur disponible")
            return False

        result = engine.connect_ports(out_name, in_name)
        _logger.info(f"  resultat={result}")
        return result

    def ports_disconnect(self, connection_id: int) -> bool:
        """Appele quand l'utilisateur supprime un cable."""
        _logger.info(f"ports_disconnect connection_id={connection_id}")

        mng = self.mng

        connection = None
        for conn in mng.connections:
            if conn.connection_id == connection_id:
                connection = conn
                break

        if connection is None:
            _logger.warning(f"Connexion {connection_id} introuvable")
            return False

        out_name = connection.port_out.full_name
        in_name = connection.port_in.full_name

        _logger.info(f"Deconnexion demandee : {out_name!r} -> {in_name!r}")

        engine = getattr(mng, '_engine', None)
        if engine is None:
            _logger.warning("Pas de moteur disponible")
            return False

        result = engine.connect_ports(out_name, in_name, disconnect=True)
        _logger.info(f"  resultat={result}")
        return result
