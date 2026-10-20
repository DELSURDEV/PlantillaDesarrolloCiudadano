"""Base de seguridad de la plantilla (login contra WAPI_ACCESS). NO MODIFICAR.

Cambios solo por el equipo dueño de la plantilla. Ver AGENTS.md.
"""

from .autorizacion import (
    Navegacion,
    Pagina,
    cerrar_sesion,
    iniciar_aplicacion,
    requerir_permiso,
    tiene_permiso,
    usuario_actual,
)
from .identidad import PermisoDenegado, Usuario

__all__ = [
    "Navegacion",
    "Pagina",
    "PermisoDenegado",
    "Usuario",
    "cerrar_sesion",
    "iniciar_aplicacion",
    "requerir_permiso",
    "tiene_permiso",
    "usuario_actual",
]
