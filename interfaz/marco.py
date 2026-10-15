"""Marco de la aplicación: acceso, barra lateral, barra superior y pie. NO MODIFICAR (zona protegida).

El contenido de estos bloques sale de la configuración de la aplicación y de Entra ID;
todo texto se escapa antes de mostrarse.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from html import escape
from itertools import groupby
from pathlib import Path

import streamlit as st

from seguridad import Navegacion, Pagina, cerrar_sesion, iniciar_aplicacion

from .componentes import reiniciar_contador

RAIZ = Path(__file__).resolve().parents[1]
LOGO_BLANCO = RAIZ / "recursos" / "delsur-logo-white.svg"
ESTILOS = Path(__file__).with_name("estilos.css")
NOMBRES_AMBIENTE = {"desarrollo": "Desarrollo", "produccion": "Producción"}


@dataclass(frozen=True)
class Aplicacion:
    """Datos de la aplicación que se muestran en el acceso, la barra superior y el pie."""

    nombre: str
    version: str = "0.1.0"
    descripcion: str = ""
    modulo: str = ""  # Texto corto sobre el nombre en el acceso, p. ej. "Periodos de Facturación".
    area_responsable: str = "Tecnología de la Información"


def ejecutar_aplicacion(aplicacion: Aplicacion, paginas: Sequence[Pagina]) -> None:
    """Única instrucción de app.py: marca, seguridad, marco y página actual."""
    st.set_page_config(page_title=f"{aplicacion.nombre} | DELSUR", layout="wide")
    reiniciar_contador()
    st.html(ESTILOS)

    # Se detiene aquí si no hay sesión válida (muestra la pantalla de acceso).
    navegacion = iniciar_aplicacion(paginas, lambda iniciar: _pantalla_acceso(aplicacion, iniciar))

    _barra_lateral(navegacion)
    _barra_superior(aplicacion, navegacion)
    navegacion.ejecutar()
    _pie_de_pagina(aplicacion, navegacion)


# ---------------------------------------------------------------- Acceso


def _pantalla_acceso(aplicacion: Aplicacion, iniciar: Callable[[], None]) -> None:
    modulo = aplicacion.modulo or aplicacion.nombre
    with st.container(key="delsur-acceso"):
        marca, acceso = st.columns([1.1, 1], gap=None)
        with marca, st.container(key="delsur-acceso-marca"):
            st.image(str(LOGO_BLANCO), width=130)
            st.caption(f"GRUPO EPM · {modulo.upper()}")
            st.title(aplicacion.nombre, anchor=False)
            if aplicacion.descripcion:
                st.write(aplicacion.descripcion)
            with st.container(key="delsur-acceso-nota"):
                st.caption("Acceso exclusivo para personal autorizado")
        with acceso, st.container(key="delsur-acceso-formulario"):
            st.caption(modulo)
            st.header("Ingrese a su cuenta", anchor=False)
            st.write(
                f"Use su cuenta corporativa de Microsoft para acceder a {aplicacion.nombre}."
            )
            if st.button(
                "Iniciar sesión con Microsoft",
                type="primary",
                icon=":material/login:",
                width="stretch",
            ):
                iniciar()


# ---------------------------------------------------------------- Barra lateral


def _iniciales(nombre: str) -> str:
    partes = [p for p in nombre.replace("@", " ").replace(".", " ").split() if p]
    return "".join(p[0] for p in partes[:2]).upper() or "U"


def _barra_lateral(navegacion: Navegacion) -> None:
    usuario = navegacion.usuario
    with st.sidebar:
        with st.container(key="delsur-logo"):
            st.image(str(LOGO_BLANCO), width=140)
        with st.container(key="delsur-menu"):
            for grupo, entradas in groupby(navegacion.entradas, key=lambda e: e.pagina.grupo):
                st.caption(grupo.upper())
                for entrada in entradas:
                    st.page_link(entrada.destino)
        with st.container(key="delsur-usuario", horizontal=True, vertical_alignment="center"):
            st.html(
                '<div class="delsur-usuario">'
                f'<span class="avatar">{escape(_iniciales(usuario.nombre))}</span>'
                f'<span class="datos"><strong>{escape(usuario.nombre)}</strong>'
                f'<small>{escape(", ".join(usuario.roles) or "Sin rol")}</small></span></div>',
                width="stretch",
            )
            if st.button(":material/logout:", key="delsur-cerrar-sesion", help="Cerrar sesión"):
                cerrar_sesion()


# ---------------------------------------------------------------- Barra superior


def _barra_superior(aplicacion: Aplicacion, navegacion: Navegacion) -> None:
    actual = navegacion.actual
    inicio = navegacion.entradas[0]
    primera_del_grupo = next(e for e in navegacion.entradas if e.pagina.grupo == actual.pagina.grupo)
    with st.container(key="delsur-barra", horizontal=True, vertical_alignment="center"):
        with st.container(key="delsur-migas", horizontal=True, vertical_alignment="center", gap="small"):
            st.page_link(inicio.destino, label=aplicacion.nombre, icon=None)
            st.caption("/")
            if primera_del_grupo is actual:
                st.caption(actual.pagina.grupo)
            else:
                st.page_link(primera_del_grupo.destino, label=actual.pagina.grupo, icon=None)
            st.caption("/")
            with st.container(key="delsur-migas-actual", width="content"):
                st.caption(actual.pagina.titulo)
        ambiente = ""
        if navegacion.ambiente != "produccion":
            ambiente = f'<span class="pastilla aviso">{escape(NOMBRES_AMBIENTE[navegacion.ambiente])}</span>'
        st.html(
            f'<div class="delsur-estado">{ambiente}'
            '<span class="pastilla exito"><i></i>Conectado</span></div>',
            width="content",
        )


# ---------------------------------------------------------------- Pie de página


def _pie_de_pagina(aplicacion: Aplicacion, navegacion: Navegacion) -> None:
    ambiente = NOMBRES_AMBIENTE[navegacion.ambiente]
    informacion = [
        f"Versión {escape(aplicacion.version)}",
        f"Ambiente: {escape(ambiente)}",
        f"Desarrollado por {escape(aplicacion.area_responsable)}",
    ]
    with st.container(key="delsur-pie"):
        st.html(
            '<footer class="delsur-footer">'
            '<div class="banda"><i class="lima"></i><i class="cyan"></i><i class="azul"></i></div>'
            '<div class="columnas">'
            '<div class="marca"><img src="app/static/marca/delsur-logo-white.svg" alt="DELSUR Grupo EPM">'
            f'<div><p class="app">{escape(aplicacion.nombre)}</p>'
            f'<p>{escape(aplicacion.descripcion)}</p></div></div>'
            '<div class="info"><h4>Información</h4><ul>'
            + "".join(f"<li>{i}</li>" for i in informacion)
            + "</ul></div></div>"
            f'<div class="legal"><span>© {date.today().year} DELSUR · Grupo EPM. '
            'Todos los derechos reservados.</span>'
            f'<span>Uso interno · {escape(aplicacion.nombre)} v{escape(aplicacion.version)} · '
            f'{escape(ambiente)}</span></div>'
            '</footer>'
        )
