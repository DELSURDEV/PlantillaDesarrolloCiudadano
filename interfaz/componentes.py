"""Componentes visuales estándar DELSUR para Streamlit. NO MODIFICAR (zona protegida).

Las páginas usan estas funciones en lugar de dar formato por su cuenta. Así todas las
aplicaciones se ven igual y cumplen el manual de marca.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass

import streamlit as st

ACENTOS = ("azul", "cyan", "lima")
COLORES = {
    "azul": "#0058A2",
    "cyan": "#009FE3",
    "lima": "#9DC431",
    "gris": "#706F6F",
    "azul_noche": "#1D2F4C",
    "verde_epm": "#007934",
}
CLAVE_CONTADOR = "_delsur_contador"


def reiniciar_contador() -> None:
    st.session_state[CLAVE_CONTADOR] = 0


def _clave(tipo: str) -> str:
    # Claves estables entre ejecuciones: se reinician en aplicar_marca().
    numero = st.session_state.get(CLAVE_CONTADOR, 0)
    st.session_state[CLAVE_CONTADOR] = numero + 1
    return f"delsur-{tipo}-{numero}"


@dataclass(frozen=True)
class Estado:
    """Indicador breve de estado bajo el encabezado (por ejemplo, "Datos: actualizado")."""

    texto: str
    tipo: str = "exito"  # exito | aviso | error | info


_COLOR_ESTADO = {"exito": "green", "aviso": "orange", "error": "red", "info": "blue"}
_ICONO_ESTADO = {"exito": "check_circle", "aviso": "warning", "error": "error", "info": "info"}
_PATRON_ICONO = re.compile(r"^[a-z0-9_]+$")


def _icono(nombre: str | None) -> str:
    if nombre is None:
        return ""
    if not _PATRON_ICONO.match(nombre):
        raise ValueError("El ícono debe ser un nombre de Material Symbols, por ejemplo 'payments'")
    return f":material/{nombre}:"


def encabezado(
    titulo: str,
    descripcion: str = "",
    antetitulo: str = "",
    icono: str | None = None,
    estados: Sequence[Estado] = (),
) -> None:
    """Panel de encabezado de la página. Una sola vez, al inicio de cada página.

    antetitulo: módulo o área (se muestra en mayúsculas). icono: nombre Material, p. ej. "shield".
    estados: hasta 4 indicadores breves de estado.
    """
    if len(estados) > 4:
        raise ValueError("Use como máximo 4 estados en el encabezado")
    with st.container(key=_clave("encabezado")):
        if antetitulo:
            with st.container(key=_clave("antetitulo")):
                st.caption(f"{_icono(icono)} {antetitulo.upper()}".strip())
        st.title(titulo, anchor=False)
        if descripcion:
            with st.container(key=_clave("descripcion")):
                st.write(descripcion)
        if estados:
            with st.container(horizontal=True, key=_clave("estados")):
                for estado in estados:
                    st.badge(
                        estado.texto,
                        icon=_icono(_ICONO_ESTADO[estado.tipo]),
                        color=_COLOR_ESTADO[estado.tipo],
                    )


def seccion(titulo: str) -> None:
    """Título de sección dentro de una página (se muestra en mayúsculas)."""
    with st.container(key=_clave("seccion")):
        st.subheader(titulo, anchor=False)


@contextmanager
def tarjeta(titulo: str = "", acento: str = "azul") -> Iterator[None]:
    """Contenedor tipo tarjeta con banda superior de color (azul, cyan o lima).

    Uso:
        with tarjeta("Consumo del mes", acento="cyan"):
            st.write(...)
    """
    if acento not in ACENTOS:
        raise ValueError(f"acento debe ser uno de {ACENTOS}")
    with st.container(border=True, key=_clave(f"tarjeta-{acento}")):
        if titulo:
            st.markdown(f"**{titulo}**")
        yield


@dataclass(frozen=True)
class Indicador:
    etiqueta: str
    valor: str
    detalle: str | None = None
    icono: str | None = None
    variacion: str | None = None
    ayuda: str | None = None
    variacion_positiva_es_buena: bool = True
    acento: str = "azul"


def fila_indicadores(indicadores: Sequence[Indicador], columnas: int | None = None) -> None:
    """Indicadores clave en tarjetas. Hasta 4 por fila; si hay más, se agregan filas."""
    por_fila = columnas or min(len(indicadores), 4)
    if not 1 <= por_fila <= 4:
        raise ValueError("Use entre 1 y 4 columnas")
    for inicio in range(0, len(indicadores), por_fila):
        fila = indicadores[inicio : inicio + por_fila]
        for columna, indicador in zip(st.columns(por_fila), fila, strict=False):
            with columna:
                _indicador(indicador)


def _indicador(indicador: Indicador) -> None:
    if indicador.acento not in ACENTOS:
        raise ValueError(f"acento debe ser uno de {ACENTOS}")
    with st.container(border=True, key=_clave(f"kpi-{indicador.acento}")):
        if indicador.icono:
            with st.container(key=_clave("kpi-icono")):
                st.markdown(_icono(indicador.icono))
        st.metric(
            indicador.etiqueta,
            indicador.valor,
            delta=indicador.variacion,
            delta_color="normal" if indicador.variacion_positiva_es_buena else "inverse",
            help=indicador.ayuda,
        )
        if indicador.detalle:
            st.caption(indicador.detalle)


def confirmar_accion(clave: str, mensaje: str, etiqueta_boton: str) -> bool:
    """Acción destructiva en dos pasos. Devuelve True solo tras confirmar."""
    if st.button(etiqueta_boton, key=f"{clave}-pedir"):
        st.session_state[f"{clave}-confirmando"] = True
    if st.session_state.get(f"{clave}-confirmando"):
        st.warning(mensaje)
        col_si, col_no = st.columns(2)
        if col_si.button("Confirmar", type="primary", key=f"{clave}-si"):
            st.session_state[f"{clave}-confirmando"] = False
            return True
        if col_no.button("Cancelar", key=f"{clave}-no"):
            st.session_state[f"{clave}-confirmando"] = False
            st.rerun()
    return False
