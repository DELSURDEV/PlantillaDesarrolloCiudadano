"""Validación de la configuración de seguridad. Si algo no es seguro, la app no abre."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

PATRON_PERMISO = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")
PATRON_APLICACION = re.compile(r"^/[A-Za-z0-9_-]{1,50}$")
# Servicio de autenticación y código de aplicación fijos para todas las apps de desarrollo ciudadano.
# Solo los cambia el equipo dueño de la plantilla (zona protegida).
URL_LOGIN_WAPI = "http://192.168.132.1/WAPI_ACCESS/api/v2/Auth/login"
APLICACION_WAPI = "/DCIU"
CLAVES_WAPI = {"tiempo_espera_s", "permitir_http", "referencia_excepcion_http"}
RUTA_PERMISOS = Path(__file__).resolve().parents[1] / "config" / "permisos.toml"


class ErrorConfiguracion(Exception):
    """La configuración no es segura. ``problemas`` nunca incluye valores sensibles."""

    def __init__(self, problemas: list[str]):
        super().__init__("; ".join(problemas))
        self.problemas = problemas


@dataclass(frozen=True)
class ConfiguracionSeguridad:
    ambiente: str
    url_login: str
    aplicacion: str
    tiempo_espera_s: float
    sesion_max_s: int
    inactividad_s: int
    intentos_maximos: int
    bloqueo_s: int
    roles_permisos: dict[str, frozenset[str]]

    @property
    def es_produccion(self) -> bool:
        return self.ambiente == "produccion"

    @property
    def catalogo_permisos(self) -> frozenset[str]:
        return frozenset().union(*self.roles_permisos.values())


def _es_marcador(valor: object) -> bool:
    return not isinstance(valor, str) or not valor.strip() or valor.strip().startswith("<")


def _entero(seccion: dict, clave: str, defecto: int, minimo: int, maximo: int, problemas: list[str]) -> int:
    valor = seccion.get(clave, defecto)
    if not isinstance(valor, int) or isinstance(valor, bool) or not minimo <= valor <= maximo:
        problemas.append(f"[seguridad].{clave} debe ser un entero entre {minimo} y {maximo}")
        return defecto
    return valor


def _validar_wapi(wapi: dict, ambiente: str, problemas: list[str]) -> tuple[str, str, float]:
    if {"url_login", "aplicacion"} & set(wapi):
        problemas.append("[wapi].url_login y [wapi].aplicacion son fijos de la plantilla: quítelos de secrets.toml")
    extras = set(wapi) - CLAVES_WAPI - {"url_login", "aplicacion"}
    if extras:
        problemas.append(f"[wapi] tiene claves no permitidas: {', '.join(sorted(extras))}")

    url = URL_LOGIN_WAPI
    partes = urlsplit(url)
    if ambiente == "produccion" and partes.scheme != "https":
        excepcion = str(wapi.get("referencia_excepcion_http", "")).strip()
        if wapi.get("permitir_http") is not True or len(excepcion) < 5:
            problemas.append(
                "En producción WAPI_ACCESS debe usar HTTPS, o registrar en [wapi] permitir_http = true "
                "con referencia_excepcion_http (aprobación de IT)"
            )
    if not PATRON_APLICACION.match(APLICACION_WAPI):
        problemas.append("El código de aplicación de la plantilla no es válido")

    tiempo = wapi.get("tiempo_espera_s", 10)
    if not isinstance(tiempo, (int, float)) or isinstance(tiempo, bool) or not 2 <= tiempo <= 30:
        problemas.append("[wapi].tiempo_espera_s debe ser un número entre 2 y 30")
        tiempo = 10
    return url, APLICACION_WAPI, float(tiempo)


def _validar_roles(datos: dict, problemas: list[str]) -> dict[str, frozenset[str]]:
    roles = datos.get("roles")
    if not isinstance(roles, dict) or not roles:
        problemas.append("config/permisos.toml debe definir al menos un rol en [roles]")
        return {}
    resultado: dict[str, frozenset[str]] = {}
    for rol, permisos in roles.items():
        if not isinstance(permisos, list) or not all(isinstance(p, str) for p in permisos):
            problemas.append(f"El rol {rol} debe tener una lista de permisos")
            continue
        invalidos = [p for p in permisos if not PATRON_PERMISO.match(p)]
        if invalidos:
            problemas.append(f"Permisos con formato inválido en {rol}: {', '.join(invalidos)}")
        # Los roles de WAPI_ACCESS se comparan sin distinguir mayúsculas.
        resultado[str(rol).strip().upper()] = frozenset(permisos)
    return resultado


def cargar_configuracion(secretos: dict, roles: dict | None = None) -> ConfiguracionSeguridad:
    """Valida ``secretos`` (contenido de secrets.toml) y los roles. Falla cerrado."""
    problemas: list[str] = []
    seguridad = secretos.get("seguridad") or {}
    ambiente = seguridad.get("ambiente", "")
    if ambiente not in {"desarrollo", "produccion"}:
        problemas.append("[seguridad].ambiente debe ser 'desarrollo' o 'produccion'")

    wapi = secretos.get("wapi") or {}
    if not isinstance(wapi, dict):
        problemas.append("[wapi] en .streamlit/secrets.toml debe ser una sección")
        wapi = {}
    url, aplicacion, tiempo = _validar_wapi(dict(wapi), ambiente, problemas)

    max_horas = _entero(seguridad, "sesion_max_horas", 8, 1, 12, problemas)
    inactividad_min = _entero(seguridad, "inactividad_min", 30, 5, 60, problemas)
    intentos = _entero(seguridad, "intentos_maximos", 5, 3, 10, problemas)
    bloqueo_min = _entero(seguridad, "bloqueo_min", 15, 1, 60, problemas)

    if roles is None:
        try:
            roles = tomllib.loads(RUTA_PERMISOS.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            problemas.append("No se pudo leer config/permisos.toml")
            roles = {}
    roles_permisos = _validar_roles(roles, problemas)

    if problemas:
        raise ErrorConfiguracion(problemas)
    return ConfiguracionSeguridad(
        ambiente=ambiente,
        url_login=url,
        aplicacion=aplicacion,
        tiempo_espera_s=tiempo,
        sesion_max_s=max_horas * 3600,
        inactividad_s=inactividad_min * 60,
        intentos_maximos=intentos,
        bloqueo_s=bloqueo_min * 60,
        roles_permisos=roles_permisos,
    )
