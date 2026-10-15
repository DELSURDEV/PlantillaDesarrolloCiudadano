"""Reglas de seguridad verificadas sobre el código del proyecto. Protegidas: no modificar."""

from __future__ import annotations

import ast
import re
try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

import pytest

from conftest import RAIZ

EXCLUIDOS = {"tests", "seguridad", "interfaz", "herramientas", ".venv", "venv", "__pycache__"}
PROHIBIDOS = {
    r"unsafe_allow_html\s*=\s*True": "HTML sin escapar (riesgo XSS)",
    r"\bst\.html\s*\(": "st.html (riesgo XSS)",
    r"components\.(v1\.)?html|components\.v1|declare_component": "componentes HTML/JS",
    r"\bst\.user\b": "st.user directo; use usuario_actual() o requerir_permiso()",
    r"\bst\.(login|logout)\s*\(": "inicio/cierre de sesión fuera de seguridad/",
    r"(?<![\w.])(eval|exec)\s*\(": "eval/exec",
    r"\bpickle\b": "pickle (deserialización insegura)",
    r"shell\s*=\s*True": "subprocess con shell=True",
    r"verify\s*=\s*False": "verificación TLS desactivada",
    r"\.execute\w*\(\s*f[\"']": "SQL armado con f-string; use parámetros",
    r"\.execute\w*\([^)]*[\"']\s*(%|\+|\.format\()": "SQL concatenado; use parámetros",
    r"(client_secret|password|contrasena|token)\s*=\s*[\"'][^\"'<]{6,}": "posible secreto en el código",
    r"AUTH_DISABLED|SIN_AUTENTICACION|MODO_PRUEBA|saltar_login": "desactivar autenticación",
    # Marca (MARCA.md): el diseño sale del tema y de interfaz/, nunca de cada página.
    r"[\"'][^\"'\n]*#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?\b": "color fijo en el código; use el tema o interfaz.componentes.COLORES",
    r"<style|\bcss\b|\bstyle\s*=": "CSS propio",
    r"\bst\.(set_page_config|logo|navigation|Page)\s*\(": "configuración de página o navegación fuera de interfaz/ y seguridad/",
    r":(red|blue|green|orange|violet|gray|grey|rainbow|primary)\[": "texto con color manual",
    r"icon\s*=\s*[\"'](?!:material/)": "ícono que no es Material (:material/nombre:)",
    "[\U0001F300-\U0001FAFF\u2600-\u27BF]": "emoji",
}


def _archivos_proyecto():
    for ruta in RAIZ.rglob("*.py"):
        if not EXCLUIDOS.intersection(ruta.relative_to(RAIZ).parts):
            yield ruta


@pytest.mark.parametrize("ruta", list(_archivos_proyecto()), ids=lambda r: r.relative_to(RAIZ).as_posix())
def test_codigo_sin_patrones_prohibidos(ruta):
    texto = ruta.read_text(encoding="utf-8")
    encontrados = [motivo for patron, motivo in PROHIBIDOS.items() if re.search(patron, texto)]
    assert not encontrados, f"{ruta.relative_to(RAIZ)}: {encontrados}"


def _paginas():
    return sorted((RAIZ / "paginas").rglob("*.py"))


@pytest.mark.parametrize("ruta", _paginas(), ids=lambda r: r.name)
def test_cada_pagina_empieza_exigiendo_permiso(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    sentencias = [n for n in arbol.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    if sentencias and isinstance(sentencias[0], ast.Expr) and isinstance(sentencias[0].value, ast.Constant):
        sentencias = sentencias[1:]  # docstring
    primera = sentencias[0] if sentencias else None
    llamada = getattr(primera, "value", None)
    assert (
        isinstance(llamada, ast.Call)
        and getattr(llamada.func, "id", None) == "requerir_permiso"
        and llamada.args
        and isinstance(llamada.args[0], ast.Constant)
    ), f"{ruta.name}: la primera instrucción debe ser requerir_permiso(\"modulo:accion\")"


@pytest.mark.parametrize("ruta", _paginas(), ids=lambda r: r.name)
def test_cada_pagina_usa_el_encabezado_estandar(ruta):
    texto = ruta.read_text(encoding="utf-8")
    assert texto.count("encabezado(") == 1, f"{ruta.name}: use encabezado(...) una sola vez"
    assert not re.search(r"\bst\.(title|header)\s*\(", texto), (
        f"{ruta.name}: use encabezado() y seccion() en lugar de st.title/st.header"
    )


def test_archivos_publicos_solo_fuentes_y_marca():
    permitidos = {"fuentes": {".woff2"}, "marca": {".svg"}}
    publicos = [p for p in (RAIZ / "static").rglob("*") if p.is_file()]
    no_permitidos = [
        p.relative_to(RAIZ).as_posix()
        for p in publicos
        if p.suffix not in permitidos.get(p.relative_to(RAIZ / "static").parts[0], set())
    ]
    assert not no_permitidos, f"static/ es público sin inicio de sesión; no permitido: {no_permitidos}"


def test_app_usa_el_marco_estandar():
    texto = (RAIZ / "app.py").read_text(encoding="utf-8")
    assert texto.count("ejecutar_aplicacion(") == 1, "app.py debe terminar con ejecutar_aplicacion(APLICACION, PAGINAS)"


def test_cada_pagina_esta_registrada_en_app():
    texto = (RAIZ / "app.py").read_text(encoding="utf-8")
    sin_registrar = [p.relative_to(RAIZ).as_posix() for p in _paginas() if p.relative_to(RAIZ).as_posix() not in texto]
    assert not sin_registrar, f"Páginas sin registrar en app.py: {sin_registrar}"


def _importaciones(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            nombres.add(nodo.module.split(".")[0])
    return nombres


def _archivos_de(carpeta):
    return sorted((RAIZ / carpeta).rglob("*.py")) if (RAIZ / carpeta).exists() else []


@pytest.mark.parametrize(
    "ruta", _archivos_de("servicios") + _archivos_de("datos"), ids=lambda r: r.relative_to(RAIZ).as_posix()
)
def test_servicios_y_datos_no_dependen_de_la_interfaz(ruta):
    prohibidas = _importaciones(ruta) & {"streamlit", "interfaz", "paginas", "componentes"}
    assert not prohibidas, f"{ruta.relative_to(RAIZ)}: no debe importar {sorted(prohibidas)}"


@pytest.mark.parametrize(
    "ruta", _paginas() + _archivos_de("componentes"), ids=lambda r: r.relative_to(RAIZ).as_posix()
)
def test_paginas_y_componentes_no_acceden_a_datos(ruta):
    assert "datos" not in _importaciones(ruta), (
        f"{ruta.relative_to(RAIZ)}: use servicios/ para obtener datos, nunca datos/ directamente"
    )


def test_configuracion_streamlit_segura():
    config = tomllib.loads((RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    servidor = config["server"]
    assert servidor["enableXsrfProtection"] is True
    assert servidor["enableCORS"] is True
    assert "trustedUserHeaders" not in servidor
    assert config["client"]["showErrorDetails"] == "none"


def test_secretos_ignorados_por_git():
    ignorados = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".streamlit/secrets.toml" in ignorados
    assert ".env" in ignorados


def test_dependencias_directas_coinciden_con_restricciones():
    fijadas = {}
    for linea in (RAIZ / "restricciones.txt").read_text(encoding="utf-8").splitlines():
        if "==" in linea and not linea.startswith("#"):
            nombre, version = linea.split(";")[0].strip().split("==")
            fijadas[nombre.lower()] = version
    distintas = []
    for linea in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].split(";")[0].strip()
        if "==" in linea:
            nombre, version = linea.split("==")
            nombre = nombre.split("[")[0].lower()
            if nombre in fijadas and fijadas[nombre] != version:
                distintas.append(f"{nombre} {version} (restricciones: {fijadas[nombre]})")
    assert not distintas, f"Versiones distintas a restricciones.txt: {distintas}"
