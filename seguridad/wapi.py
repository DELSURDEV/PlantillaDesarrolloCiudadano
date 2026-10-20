"""Cliente del login de WAPI_ACCESS. No usa streamlit, para poder probarlo aislado.

Solo se conservan de la respuesta el usuario, su nombre y sus roles. El resto (sitemaps,
tokens u otros datos) se descarta.
La contraseña nunca se guarda ni se registra.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .configuracion import ConfiguracionSeguridad

LARGO_MAXIMO_USUARIO = 128
LARGO_MAXIMO_CONTRASENA = 256
ESTADOS_CREDENCIALES_INVALIDAS = {400, 401, 403}


class CredencialesInvalidas(Exception):
    """Usuario o contraseña incorrectos, o el usuario no tiene acceso a la aplicación."""


class ServicioNoDisponible(Exception):
    """WAPI_ACCESS no respondió o respondió algo inesperado. La app no deja entrar."""


@dataclass(frozen=True)
class RespuestaLogin:
    usuario: str
    nombre: str
    roles: tuple[str, ...]


def _texto(valor: object, largo: int = 200) -> str:
    return "" if valor is None else str(valor).strip()[:largo]


def interpretar_respuesta(datos: object) -> RespuestaLogin:
    """Convierte el JSON de WAPI_ACCESS en datos validados. Falla cerrado."""
    usuario = datos.get("userData") if isinstance(datos, dict) else None
    if not isinstance(usuario, dict):
        raise CredencialesInvalidas()
    nombre_usuario = _texto(usuario.get("userName"), LARGO_MAXIMO_USUARIO)
    if not nombre_usuario:
        raise CredencialesInvalidas()

    roles_crudos = usuario.get("roles") or []
    if not isinstance(roles_crudos, list):
        raise ServicioNoDisponible("roles con formato inesperado")
    roles = tuple(sorted({_texto(r, 100).upper() for r in roles_crudos if _texto(r, 100)}))

    return RespuestaLogin(
        usuario=nombre_usuario,
        nombre=_texto(usuario.get("displayName"), 150) or nombre_usuario,
        roles=roles,
    )


def autenticar(
    config: ConfiguracionSeguridad,
    usuario: str,
    contrasena: str,
    cliente: httpx.Client | None = None,
) -> RespuestaLogin:
    """Valida las credenciales contra WAPI_ACCESS desde el servidor."""
    usuario = (usuario or "").strip()
    if (
        not usuario
        or not contrasena
        or len(usuario) > LARGO_MAXIMO_USUARIO
        or len(contrasena) > LARGO_MAXIMO_CONTRASENA
    ):
        raise CredencialesInvalidas()
    cuerpo = {"username": usuario, "password": contrasena, "app": config.aplicacion}
    propio = cliente is None
    cliente = cliente or httpx.Client(timeout=config.tiempo_espera_s, follow_redirects=False)
    try:
        respuesta = cliente.post(config.url_login, json=cuerpo, headers={"Accept": "application/json"})
    except httpx.HTTPError:
        raise ServicioNoDisponible("sin respuesta de WAPI_ACCESS") from None
    finally:
        if propio:
            cliente.close()
    if respuesta.status_code in ESTADOS_CREDENCIALES_INVALIDAS:
        raise CredencialesInvalidas()
    if respuesta.status_code != 200:
        raise ServicioNoDisponible(f"estado HTTP {respuesta.status_code}")
    try:
        datos = respuesta.json()
    except ValueError:
        raise ServicioNoDisponible("respuesta no es JSON") from None
    return interpretar_respuesta(datos)
