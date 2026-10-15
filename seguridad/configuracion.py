"""Validación de la configuración de seguridad. Si algo no es seguro, la app no abre."""

from __future__ import annotations

import re
try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

PATRON_GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
PATRON_METADATOS = re.compile(
    r"^https://login\.microsoftonline\.com/(?P<tenant>[0-9a-fA-F-]{36})"
    r"/v2\.0/\.well-known/openid-configuration$"
)
PATRON_PERMISO = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")
HOSTS_LOCALES = {"localhost", "127.0.0.1"}
CLAVES_AUTH_PERMITIDAS = {
    "redirect_uri",
    "cookie_secret",
    "client_id",
    "client_secret",
    "server_metadata_url",
}
RUTA_PERMISOS = Path(__file__).resolve().parents[1] / "config" / "permisos.toml"


class ErrorConfiguracion(Exception):
    """La configuración no es segura. ``problemas`` nunca incluye valores secretos."""

    def __init__(self, problemas: list[str]):
        super().__init__("; ".join(problemas))
        self.problemas = problemas


@dataclass(frozen=True)
class ConfiguracionSeguridad:
    ambiente: str
    tenant_id: str
    client_id: str
    emisor: str
    sesion_max_s: int
    inactividad_s: int
    roles_permisos: dict[str, frozenset[str]]

    @property
    def es_produccion(self) -> bool:
        return self.ambiente == "produccion"

    @property
    def catalogo_permisos(self) -> frozenset[str]:
        return frozenset().union(*self.roles_permisos.values())


def _es_marcador(valor: object) -> bool:
    return not isinstance(valor, str) or not valor.strip() or valor.strip().startswith("<")


def _validar_auth(auth: dict, ambiente: str, problemas: list[str]) -> tuple[str, str]:
    extras = set(auth) - CLAVES_AUTH_PERMITIDAS
    if extras:
        # expose_tokens, proveedores adicionales o client_kwargs cambian el flujo aprobado.
        problemas.append(f"[auth] tiene claves no permitidas: {', '.join(sorted(extras))}")
    for clave in sorted(CLAVES_AUTH_PERMITIDAS):
        if _es_marcador(auth.get(clave)):
            problemas.append(f"Falta [auth].{clave}")

    client_id = str(auth.get("client_id", "")).strip().lower()
    if client_id and not client_id.startswith("<") and not PATRON_GUID.match(client_id):
        problemas.append("[auth].client_id debe ser un GUID")

    tenant_id = ""
    metadatos = str(auth.get("server_metadata_url", "")).strip()
    if metadatos and not metadatos.startswith("<"):
        coincidencia = PATRON_METADATOS.match(metadatos)
        tenant = coincidencia.group("tenant").lower() if coincidencia else ""
        if not PATRON_GUID.match(tenant):
            problemas.append(
                "[auth].server_metadata_url debe ser "
                "https://login.microsoftonline.com/<TENANT_ID GUID>/v2.0/.well-known/"
                "openid-configuration (no se permiten common/organizations)"
            )
        else:
            tenant_id = tenant

    secreto_cookie = auth.get("cookie_secret")
    if not _es_marcador(secreto_cookie) and len(secreto_cookie) < 32:
        problemas.append("[auth].cookie_secret debe tener al menos 32 caracteres")

    redirect = str(auth.get("redirect_uri", "")).strip()
    if redirect and not redirect.startswith("<"):
        partes = urlsplit(redirect)
        if partes.path != "/oauth2callback" or partes.query or partes.fragment:
            problemas.append("[auth].redirect_uri debe terminar exactamente en /oauth2callback")
        if "*" in redirect:
            problemas.append("[auth].redirect_uri no admite comodines")
        local = partes.hostname in HOSTS_LOCALES
        if partes.scheme != "https" and not (partes.scheme == "http" and local):
            problemas.append("[auth].redirect_uri debe usar HTTPS (HTTP solo en localhost)")
        if ambiente == "produccion" and (partes.scheme != "https" or local):
            problemas.append("En producción [auth].redirect_uri debe ser HTTPS y no local")
    return tenant_id, client_id


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
        resultado[rol] = frozenset(permisos)
    return resultado


def cargar_configuracion(
    secretos: dict, roles: dict | None = None
) -> ConfiguracionSeguridad:
    """Valida ``secretos`` (contenido de secrets.toml) y los roles. Falla cerrado."""
    problemas: list[str] = []
    seguridad = secretos.get("seguridad") or {}
    ambiente = seguridad.get("ambiente", "")
    if ambiente not in {"desarrollo", "produccion"}:
        problemas.append("[seguridad].ambiente debe ser 'desarrollo' o 'produccion'")

    auth = secretos.get("auth")
    if not isinstance(auth, dict) or not auth:
        problemas.append("Falta la sección [auth] en .streamlit/secrets.toml")
        auth = {}
    tenant_id, client_id = _validar_auth(dict(auth), ambiente, problemas)

    max_horas = seguridad.get("sesion_max_horas", 8)
    inactividad_min = seguridad.get("inactividad_min", 30)
    if not isinstance(max_horas, int) or not 1 <= max_horas <= 12:
        problemas.append("[seguridad].sesion_max_horas debe ser un entero entre 1 y 12")
        max_horas = 8
    if not isinstance(inactividad_min, int) or not 5 <= inactividad_min <= 60:
        problemas.append("[seguridad].inactividad_min debe ser un entero entre 5 y 60")
        inactividad_min = 30

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
        tenant_id=tenant_id,
        client_id=client_id,
        emisor=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        sesion_max_s=max_horas * 3600,
        inactividad_s=inactividad_min * 60,
        roles_permisos=roles_permisos,
    )
