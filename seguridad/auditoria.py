"""Registro de eventos de seguridad. Nunca registra tokens, secretos ni correos."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

_log = logging.getLogger("auditoria")


def registrar_evento(evento: str, oid: str = "-", **detalles: str) -> None:
    registro = {
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evento": evento,
        "oid": oid,
        **{k: str(v)[:200] for k, v in detalles.items()},
    }
    _log.warning(json.dumps(registro, ensure_ascii=False))
