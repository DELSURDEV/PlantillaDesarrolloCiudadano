"""Punto de entrada de seguridad para la app Streamlit (login contra WAPI_ACCESS).

Uso (desde interfaz.ejecutar_aplicacion): navegacion = iniciar_aplicacion(PAGINAS, pantalla)
Uso en cada página: usuario = requerir_permiso("modulo:accion")

La sesión vive en el servidor, ligada a la pestaña del navegador: no se guarda ninguna
cookie ni token. Recargar la página o abrir otra pestaña pide iniciar sesión de nuevo.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from . import wapi
from .auditoria import registrar_evento
from .configuracion import ConfiguracionSeguridad, ErrorConfiguracion, cargar_configuracion
from .identidad import (
    ControlIntentos,
    PermisoDenegado,
    SesionVencida,
    Usuario,
    crear_usuario,
    verificar_vigencia,
)

_log = logging.getLogger("seguridad")
CLAVE_USUARIO = "_seguridad_usuario"
CLAVE_ACTIVIDAD = "_seguridad_ultima_actividad"
CLAVE_AVISO = "_seguridad_aviso"
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos, o su usuario no tiene acceso a esta aplicación."
MENSAJE_SERVICIO = "El servicio de autenticación no está disponible. Intente de nuevo más tarde."

# iniciar(usuario, contrasena) devuelve None si la sesión quedó iniciada o un mensaje de error.
IniciarSesion = Callable[[str, str], Optional[str]]
PantallaInicio = Callable[[IniciarSesion, Optional[str]], None]


@dataclass(frozen=True)
class Pagina:
    """Página de la aplicación, con el permiso que exige y su grupo en el menú."""

    archivo: str
    titulo: str
    permiso: str
    icono: str | None = None
    grupo: str = "General"


@dataclass(frozen=True)
class EntradaMenu:
    pagina: Pagina
    destino: object  # st.Page

    @property
    def titulo(self) -> str:
        return self.pagina.titulo

    @property
    def grupo(self) -> str:
        return self.pagina.grupo


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
            registrar_evento("accion_denegada", self.usuario.id, permiso=denegado.permiso)
            st.error("No tiene permiso para realizar esta acción.")


@st.cache_resource
def _control_intentos() -> ControlIntentos:
    return ControlIntentos()


def _leer_secretos() -> dict:
    try:
        return st.secrets.to_dict()
    except FileNotFoundError:
        return {}


def _autenticar_wapi(config: ConfiguracionSeguridad, usuario: str, contrasena: str) -> wapi.RespuestaLogin:
    return wapi.autenticar(config, usuario, contrasena)


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


def _validar_paginas(paginas: Sequence[Pagina], config: ConfiguracionSeguridad) -> None:
    archivos = [p.archivo for p in paginas]
    problemas = [f"página repetida: {a}" for a in sorted({a for a in archivos if archivos.count(a) > 1})]
    faltantes = {p.permiso for p in paginas} - config.catalogo_permisos
    if faltantes:
        problemas.append(f"permisos que no existen en config/permisos.toml: {', '.join(sorted(faltantes))}")
    if problemas:
        _cerrar("La aplicación está cerrada por un error en PAGINAS de app.py: " + "; ".join(problemas))


def _intentar_inicio(config: ConfiguracionSeguridad, usuario: str, contrasena: str) -> str | None:
    """Valida las credenciales. Devuelve None si la sesión quedó iniciada o un mensaje de error."""
    usuario = (usuario or "").strip()
    auditado = usuario[:128] or "-"
    ahora = time.time()
    control = _control_intentos()
    espera = control.segundos_bloqueado(usuario, config, ahora)
    if espera:
        registrar_evento("inicio_bloqueado", auditado)
        return f"Demasiados intentos fallidos. Intente de nuevo en {max(1, round(espera / 60))} minuto(s)."
    try:
        respuesta = _autenticar_wapi(config, usuario, contrasena)
    except wapi.CredencialesInvalidas:
        control.registrar_fallo(usuario, ahora)
        registrar_evento("inicio_fallido", auditado)
        return MENSAJE_CREDENCIALES
    except wapi.ServicioNoDisponible as error:
        _log.error("WAPI_ACCESS no disponible: %s", error)
        registrar_evento("servicio_no_disponible", auditado)
        return MENSAJE_SERVICIO
    control.limpiar(usuario)
    nuevo = crear_usuario(respuesta, config, ahora)
    st.session_state[CLAVE_USUARIO] = nuevo
    st.session_state[CLAVE_ACTIVIDAD] = ahora
    registrar_evento("inicio_sesion", nuevo.id, roles=",".join(nuevo.roles))
    return None


def _pantalla_basica(iniciar: IniciarSesion, aviso: str | None) -> None:
    st.title("Iniciar sesión", anchor=False)
    if aviso:
        st.info(aviso)
    with st.form("acceso", clear_on_submit=True):
        usuario = st.text_input("Usuario", max_chars=wapi.LARGO_MAXIMO_USUARIO)
        contrasena = st.text_input("Contraseña", type="password", max_chars=wapi.LARGO_MAXIMO_CONTRASENA)
        if st.form_submit_button("Iniciar sesión", type="primary"):
            error = iniciar(usuario, contrasena)
            if error:
                st.error(error)
            else:
                st.rerun()


def _limpiar_sesion() -> None:
    for clave in (CLAVE_USUARIO, CLAVE_ACTIVIDAD):
        st.session_state.pop(clave, None)


def cerrar_sesion() -> None:
    """Cierra la sesión del usuario actual."""
    usuario = st.session_state.get(CLAVE_USUARIO)
    registrar_evento("sesion_cerrada", usuario.id if isinstance(usuario, Usuario) else "-", motivo="logout")
    _limpiar_sesion()
    st.rerun()


def _sesion_vigente(config: ConfiguracionSeguridad) -> Usuario | None:
    usuario = st.session_state.get(CLAVE_USUARIO)
    if not isinstance(usuario, Usuario):
        return None
    ahora = time.time()
    try:
        verificar_vigencia(usuario.inicio_sesion, st.session_state.get(CLAVE_ACTIVIDAD, 0.0), config, ahora)
    except SesionVencida:
        registrar_evento("sesion_cerrada", usuario.id, motivo="vencida")
        _limpiar_sesion()
        st.session_state[CLAVE_AVISO] = "Su sesión venció. Vuelva a iniciar sesión."
        return None
    st.session_state[CLAVE_ACTIVIDAD] = ahora
    return usuario


def iniciar_aplicacion(paginas: Sequence[Pagina], pantalla_inicio: PantallaInicio | None = None) -> Navegacion:
    """Valida configuración y sesión. Devuelve solo las páginas permitidas.

    Si algo falla, detiene la ejecución: nunca devuelve una navegación sin sesión válida.
    ``pantalla_inicio`` solo dibuja la pantalla de acceso; no participa en la validación.
    Una página se muestra solo si alguno de los roles del usuario (WAPI_ACCESS) tiene
    el permiso de la página (config/permisos.toml).
    """
    config = _configuracion()
    _validar_paginas(paginas, config)

    usuario = _sesion_vigente(config)
    if usuario is None:
        aviso = st.session_state.pop(CLAVE_AVISO, None)
        (pantalla_inicio or _pantalla_basica)(lambda u, c: _intentar_inicio(config, u, c), aviso)
        st.stop()

    entradas = [
        EntradaMenu(p, st.Page(p.archivo, title=p.titulo, icon=p.icono))
        for p in paginas
        if usuario.tiene_permiso(p.permiso)
    ]
    if not entradas:
        registrar_evento("sin_permisos", usuario.id, roles=",".join(usuario.roles))
        if st.button("Cerrar sesión"):
            cerrar_sesion()
        _cerrar("Su usuario no tiene un rol con acceso a esta aplicación. Solicite el acceso a IT.")
    navegador = st.navigation([e.destino for e in entradas], position="hidden")
    actual = next((e for e in entradas if e.destino.url_path == navegador.url_path), entradas[0])
    return Navegacion(usuario, config.ambiente, tuple(entradas), actual, navegador)


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
        registrar_evento("acceso_denegado", usuario.id, permiso=permiso)
        _cerrar("No tiene permiso para ver esta página.")
    return usuario
