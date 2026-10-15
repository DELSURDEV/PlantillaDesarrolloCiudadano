"""Validación de la identidad que entrega Microsoft Entra ID y control de sesión.

Streamlit valida la firma, emisor, audiencia y nonce del ID token al iniciar sesión,
pero su cookie dura 30 días. Aquí se vuelve a validar el tenant y se impone la
duración máxima y el tiempo de inactividad de la política.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from .configuracion import PATRON_GUID, ConfiguracionSeguridad

TOLERANCIA_RELOJ_S = 300


class PermisoDenegado(Exception):
    """El usuario no tiene el permiso requerido para una operación."""

    def __init__(self, permiso: str):
        super().__init__(f"Permiso requerido: {permiso}")
        self.permiso = permiso


class IdentidadRechazada(Exception):
    """La sesión no es válida. ``motivo`` es un código sin datos personales."""

    def __init__(self, motivo: str):
        super().__init__(motivo)
        self.motivo = motivo


@dataclass(frozen=True)
class Usuario:
    oid: str
    nombre: str
    correo: str
    roles: tuple[str, ...]
    permisos: frozenset[str]
    inicio_sesion: int

    def tiene_permiso(self, permiso: str) -> bool:
        return permiso in self.permisos

    def exigir(self, permiso: str) -> None:
        """Para servicios: lanza PermisoDenegado si el usuario no tiene el permiso."""
        if permiso not in self.permisos:
            raise PermisoDenegado(permiso)


def permisos_de(roles: tuple[str, ...], config: ConfiguracionSeguridad) -> frozenset[str]:
    """Une los permisos de los roles conocidos. Roles desconocidos no dan permisos."""
    return frozenset().union(*(config.roles_permisos.get(rol, frozenset()) for rol in roles))


def validar_identidad(
    reclamaciones: dict, config: ConfiguracionSeguridad, ahora: float
) -> Usuario:
    if reclamaciones.get("is_logged_in") is not True:
        raise IdentidadRechazada("sin_sesion")
    if str(reclamaciones.get("tid", "")).lower() != config.tenant_id:
        raise IdentidadRechazada("tenant_no_permitido")
    if reclamaciones.get("iss") != config.emisor:
        raise IdentidadRechazada("emisor_no_valido")
    audiencia = reclamaciones.get("aud")
    audiencias = audiencia if isinstance(audiencia, list) else [audiencia]
    if config.client_id not in [str(a).lower() for a in audiencias]:
        raise IdentidadRechazada("audiencia_no_valida")
    oid = str(reclamaciones.get("oid", "")).lower()
    if not PATRON_GUID.match(oid):
        raise IdentidadRechazada("oid_no_valido")
    iat = reclamaciones.get("iat")
    if not isinstance(iat, int) or isinstance(iat, bool):
        raise IdentidadRechazada("sin_fecha_inicio")
    if iat > ahora + TOLERANCIA_RELOJ_S:
        raise IdentidadRechazada("fecha_inicio_futura")
    if ahora - iat > config.sesion_max_s:
        raise IdentidadRechazada("sesion_vencida")

    roles_crudos = reclamaciones.get("roles") or []
    if not isinstance(roles_crudos, list):
        roles_crudos = []
    roles = tuple(sorted({str(r) for r in roles_crudos}))
    return Usuario(
        oid=oid,
        nombre=str(reclamaciones.get("name") or "Usuario"),
        correo=str(reclamaciones.get("preferred_username") or reclamaciones.get("email") or ""),
        roles=roles,
        permisos=permisos_de(roles, config),
        inicio_sesion=iat,
    )


class RegistroActividad:
    """Última actividad por sesión (oid + hora de inicio), compartida entre pestañas.

    Una sesión vencida por inactividad queda marcada y no puede reutilizarse aunque
    la cookie siga en el navegador.
    """

    def __init__(self) -> None:
        self._actividad: dict[tuple[str, int], float] = {}
        self._vencidas: dict[tuple[str, int], float] = {}
        self._candado = threading.Lock()

    def registrar(self, usuario: Usuario, config: ConfiguracionSeguridad, ahora: float) -> bool:
        """Devuelve True si es la primera actividad de esta sesión (nuevo inicio)."""
        clave = (usuario.oid, usuario.inicio_sesion)
        with self._candado:
            self._limpiar(config, ahora)
            if clave in self._vencidas:
                raise IdentidadRechazada("sesion_inactiva")
            anterior = self._actividad.get(clave)
            if anterior is not None and ahora - anterior > config.inactividad_s:
                self._vencidas[clave] = ahora
                del self._actividad[clave]
                raise IdentidadRechazada("sesion_inactiva")
            self._actividad[clave] = ahora
            return anterior is None

    def _limpiar(self, config: ConfiguracionSeguridad, ahora: float) -> None:
        limite = ahora - config.sesion_max_s - TOLERANCIA_RELOJ_S
        for tabla in (self._actividad, self._vencidas):
            for clave in [c for c in tabla if c[1] < limite]:
                del tabla[clave]
