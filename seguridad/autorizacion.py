"""Punto de entrada de seguridad para la app Streamlit.

Uso (desde interfaz.ejecutar_aplicacion): navegacion = iniciar_aplicacion(PAGINAS)
Uso en cada página: usuario = requerir_permiso("modulo:accion")
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import streamlit as st

from .auditoria import registrar_evento
from .configuracion import ConfiguracionSeguridad, ErrorConfiguracion, cargar_configuracion
from .identidad import (
    IdentidadRechazada,
    PermisoDenegado,
    RegistroActividad,
    Usuario,
    validar_identidad,
)

_log = logging.getLogger("seguridad")
CLAVE_USUARIO = "_seguridad_usuario"


@dataclass(frozen=True)
class Pagina:
    archivo: str
    titulo: str
    permiso: str
    icono: str | None = None
    grupo: str = "General"


@dataclass(frozen=True)
class EntradaMenu:
    pagina: Pagina
    destino: object  # st.Page


@dataclass(frozen=True)
class Navegacion:
    """Resultado de una autenticación válida: lo que el usuario puede ver."""

    usuario: Usuario
    ambiente: str
    entradas: tuple[EntradaMenu, ...]
    actual: EntradaMenu
    _navegador: object

    def ejecutar(self) -> None:
        """Ejecuta la página actual. Un PermisoDenegado de un servicio se muestra y se audita."""
        try:
            self._navegador.run()
        except PermisoDenegado as denegado:
            registrar_evento("accion_denegada", self.usuario.oid, permiso=denegado.permiso)
            st.error("No tiene permiso para realizar esta acción.")


@st.cache_resource
def _registro_actividad() -> RegistroActividad:
    return RegistroActividad()


def _leer_secretos() -> dict:
    try:
        return st.secrets.to_dict()
    except FileNotFoundError:
        return {}


def _leer_reclamaciones() -> dict:
    return st.user.to_dict()


def _cerrar(mensaje: str) -> None:
    st.error(mensaje)
    st.stop()


def _configuracion() -> ConfiguracionSeguridad:
    try:
        return cargar_configuracion(_leer_secretos())
    except ErrorConfiguracion as error:
        _log.error("Aplicación cerrada por configuración insegura: %s", error.problemas)
        st.error("La aplicación está cerrada porque su configuración de seguridad está incompleta.")
        secretos = _leer_secretos()
        if (secretos.get("seguridad") or {}).get("ambiente") != "produccion":
            st.markdown("\n".join(f"- {p}" for p in error.problemas))
        st.stop()
        raise  # st.stop() detiene la ejecución; esto solo satisface al analizador.


PantallaInicio = Callable[[Callable[[], None]], None]


def _pantalla_inicio_sesion(dibujar: PantallaInicio | None = None) -> None:
    """Muestra la pantalla de acceso. ``dibujar`` recibe la función que inicia sesión."""
    if dibujar is not None:
        dibujar(st.login)
        st.stop()
    with st.container(key="delsur-login"):
        st.caption("ACCESO CORPORATIVO")
        st.title("Iniciar sesión", anchor=False)
        st.write("Para continuar inicie sesión con su cuenta corporativa de Microsoft.")
        if st.button("Iniciar sesión con Microsoft", type="primary", icon=":material/login:"):
            st.login()
    st.stop()


def cerrar_sesion() -> None:
    """Cierra la sesión del usuario actual (también en Microsoft)."""
    usuario = st.session_state.get(CLAVE_USUARIO)
    _cerrar_sesion("logout", usuario.oid if isinstance(usuario, Usuario) else "-")


def _cerrar_sesion(motivo: str, oid: str = "-") -> None:
    registrar_evento("sesion_cerrada", oid, motivo=motivo)
    st.session_state.pop(CLAVE_USUARIO, None)
    st.logout()
    st.stop()


def _autenticar(config: ConfiguracionSeguridad, dibujar: PantallaInicio | None) -> Usuario:
    reclamaciones = _leer_reclamaciones()
    if not reclamaciones.get("is_logged_in"):
        _pantalla_inicio_sesion(dibujar)
    ahora = time.time()
    try:
        usuario = validar_identidad(reclamaciones, config, ahora)
        if _registro_actividad().registrar(usuario, config, ahora):
            registrar_evento("inicio_sesion", usuario.oid, roles=",".join(usuario.roles))
    except IdentidadRechazada as rechazo:
        oid = str(reclamaciones.get("oid", "-"))
        if rechazo.motivo in {"sesion_vencida", "sesion_inactiva"}:
            st.info("Su sesión venció. Vuelva a iniciar sesión.")
        _cerrar_sesion(rechazo.motivo, oid)
        raise
    return usuario


def iniciar_aplicacion(
    paginas: Sequence[Pagina], pantalla_inicio: PantallaInicio | None = None
) -> Navegacion:
    """Valida configuración e identidad. Devuelve solo las páginas permitidas.

    Si algo falla, detiene la ejecución: nunca devuelve una navegación sin sesión válida.
    ``pantalla_inicio`` solo dibuja la pantalla de acceso; no participa en la validación.
    """
    config = _configuracion()
    faltantes = {p.permiso for p in paginas} - config.catalogo_permisos
    if faltantes:
        _cerrar(
            "La aplicación está cerrada: hay páginas con permisos que no existen en "
            f"config/permisos.toml ({', '.join(sorted(faltantes))})."
        )
    usuario = _autenticar(config, pantalla_inicio)
    st.session_state[CLAVE_USUARIO] = usuario

    entradas = tuple(
        EntradaMenu(p, st.Page(p.archivo, title=p.titulo, icon=p.icono))
        for p in paginas
        if usuario.tiene_permiso(p.permiso)
    )
    if not entradas:
        registrar_evento("sin_permisos", usuario.oid, roles=",".join(usuario.roles))
        _cerrar("Su cuenta no tiene un rol asignado para esta aplicación. Solicítelo a IT.")
    navegador = st.navigation([e.destino for e in entradas], position="hidden")
    actual = next(
        (e for e in entradas if e.destino.url_path == navegador.url_path), entradas[0]
    )
    return Navegacion(usuario, config.ambiente, entradas, actual, navegador)


def usuario_actual() -> Usuario:
    usuario = st.session_state.get(CLAVE_USUARIO)
    if not isinstance(usuario, Usuario):
        _cerrar("Debe iniciar sesión.")
    return usuario


def tiene_permiso(permiso: str) -> bool:
    return usuario_actual().tiene_permiso(permiso)


def requerir_permiso(permiso: str) -> Usuario:
    """Primera línea de cada página. Detiene la página si el usuario no tiene el permiso."""
    usuario = usuario_actual()
    if not usuario.tiene_permiso(permiso):
        registrar_evento("acceso_denegado", usuario.oid, permiso=permiso)
        _cerrar("No tiene permiso para ver esta página.")
    return usuario
