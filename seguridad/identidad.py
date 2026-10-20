"""Usuario autenticado, permisos, vigencia de la sesión y control de intentos fallidos."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from .configuracion import ConfiguracionSeguridad
from .wapi import RespuestaLogin


class PermisoDenegado(Exception):
    """El usuario no tiene el permiso requerido para una operación."""

    def __init__(self, permiso: str):
        super().__init__(f"Permiso requerido: {permiso}")
        self.permiso = permiso


class SesionVencida(Exception):
    """La sesión superó la duración máxima o el tiempo de inactividad."""


@dataclass(frozen=True)
class Usuario:
    id: str  # userName de WAPI_ACCESS; identifica al usuario en datos y auditoría
    nombre: str
    roles: tuple[str, ...]
    permisos: frozenset[str]
    inicio_sesion: float

    def tiene_permiso(self, permiso: str) -> bool:
        return permiso in self.permisos

    def exigir(self, permiso: str) -> None:
        """Para servicios: lanza PermisoDenegado si el usuario no tiene el permiso."""
        if permiso not in self.permisos:
            raise PermisoDenegado(permiso)


def permisos_de(roles: tuple[str, ...], config: ConfiguracionSeguridad) -> frozenset[str]:
    """Une los permisos de los roles conocidos. Roles desconocidos no dan permisos."""
    return frozenset().union(*(config.roles_permisos.get(rol.upper(), frozenset()) for rol in roles))


def crear_usuario(respuesta: RespuestaLogin, config: ConfiguracionSeguridad, ahora: float) -> Usuario:
    return Usuario(
        id=respuesta.usuario.lower(),
        nombre=respuesta.nombre,
        roles=respuesta.roles,
        permisos=permisos_de(respuesta.roles, config),
        inicio_sesion=ahora,
    )


def verificar_vigencia(
    inicio: float, ultima_actividad: float, config: ConfiguracionSeguridad, ahora: float
) -> None:
    if ahora - inicio > config.sesion_max_s or ahora - ultima_actividad > config.inactividad_s:
        raise SesionVencida()


class ControlIntentos:
    """Bloquea temporalmente un usuario tras varios intentos fallidos (compartido entre sesiones)."""

    def __init__(self) -> None:
        self._fallos: dict[str, list[float]] = {}
        self._candado = threading.Lock()

    def segundos_bloqueado(self, usuario: str, config: ConfiguracionSeguridad, ahora: float) -> int:
        with self._candado:
            recientes = [t for t in self._fallos.get(usuario.lower(), []) if ahora - t < config.bloqueo_s]
            self._fallos[usuario.lower()] = recientes
            if len(recientes) < config.intentos_maximos:
                return 0
            return int(config.bloqueo_s - (ahora - recientes[-config.intentos_maximos])) + 1

    def registrar_fallo(self, usuario: str, ahora: float) -> None:
        with self._candado:
            self._fallos.setdefault(usuario.lower(), []).append(ahora)

    def limpiar(self, usuario: str) -> None:
        with self._candado:
            self._fallos.pop(usuario.lower(), None)
