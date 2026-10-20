"""Registro de eventos de seguridad. Nunca registra contraseñas, tokens ni secretos."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

_log = logging.getLogger("auditoria")


def registrar_evento(evento: str, usuario: str = "-", **detalles: str) -> None:
    registro = {
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evento": evento,
        "usuario": usuario,
        **{k: str(v)[:200] for k, v in detalles.items()},
    }
    _log.warning(json.dumps(registro, ensure_ascii=False))
