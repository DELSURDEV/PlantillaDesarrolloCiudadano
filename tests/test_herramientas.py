"""Pruebas de los scripts de herramientas/ (preparación, pruebas y arranque). Protegidas: no modificar."""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import RAIZ

POWERSHELL = shutil.which("powershell")
GIT = shutil.which("git")
EJECUTOR = "ejecutar_pruebas.ps1"
VARIABLE_TEMPORAL = "PYTEST_DEBUG_TEMPROOT"
CODIGO_RECHAZO = 2
# La preparación corre las pruebas del proyecto copiado; esta variable evita repetir ahí las pruebas
# que vuelven a preparar un proyecto. Es la única omisión intencional.
PRUEBA_ANIDADA = "PLANTILLA_PRUEBA_ANIDADA"
IGNORAR = shutil.ignore_patterns(".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".vs", "secrets.toml")
AYUDANTE = '''
import os
import subprocess


def test_ayudante(tmp_path):
    destino = os.environ["DESTINO_ENLACE"]
    subprocess.run(["cmd", "/c", "mklink", "/J", str(tmp_path / "enlace"), destino], capture_output=True, check=True)
    assert os.environ["RESULTADO_ESPERADO"] == "pasa"
'''
DISCO_DEL_BLOQUE = '$disco = "E:\\"'
# Reemplazan la descarga y la preparación: en PowerShell una función tiene prioridad sobre el comando.
FALSOS_DE_DESCARGA = r'''
function Invoke-WebRequest {
    param([string]$Uri, [string]$OutFile, [switch]$UseBasicParsing)
    Add-Content -LiteralPath $env:REGISTRO_DESCARGA "URL=$Uri"
    Compress-Archive -Path $env:PLANTILLA_FALSA -DestinationPath $OutFile
}
function powershell { Add-Content -LiteralPath $env:REGISTRO_DESCARGA "PREPARAR=$args" }
'''

# Omisiones por falta de algo en el equipo ("no disponible") frente a la omisión intencional.
requiere_powershell = pytest.mark.skipif(POWERSHELL is None, reason="no disponible en este equipo: Windows PowerShell")
requiere_git = pytest.mark.skipif(GIT is None, reason="no disponible en este equipo: Git")
requiere_entorno_activo = pytest.mark.skipif(
    sys.prefix == sys.base_prefix, reason="no disponible: las pruebas no se ejecutan con el entorno .venv"
)
requiere_entorno_del_proyecto = pytest.mark.skipif(
    not (RAIZ / ".venv" / "Scripts" / "python.exe").exists(), reason="no disponible: falta .venv en el proyecto"
)
omitir_si_es_anidada = pytest.mark.skipif(
    os.environ.get(PRUEBA_ANIDADA) == "1", reason="omisión intencional: ya corre dentro de una preparación de prueba"
)


def _ejecutar_script(proyecto: Path, nombre: str, *argumentos: str, entorno: dict | None = None):
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(proyecto / "herramientas" / nombre), *argumentos],
        capture_output=True, text=True, errors="replace", env=entorno, timeout=600, check=False,
    )


def _ejecutar_comando(comando: str, entorno: dict):
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
        capture_output=True, text=True, errors="replace", env=entorno, timeout=600, check=False,
    )


def _copiar_proyecto(carpeta: Path) -> Path:
    proyecto = carpeta / "proy"
    shutil.copytree(RAIZ, proyecto, ignore=IGNORAR)
    return proyecto


@contextlib.contextmanager
def _entorno_enlazado(proyecto: Path):
    """Reutiliza el entorno actual con un enlace (junction) para no descargar librerías."""
    entorno_real = Path(sys.prefix)
    enlace = proyecto / ".venv"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(enlace), str(entorno_real)], capture_output=True, check=True)
    try:
        yield
    finally:
        os.rmdir(enlace)  # quita solo el enlace; el entorno real no se toca
    assert (entorno_real / "Scripts" / "python.exe").exists()


def _git(carpeta: Path, *argumentos: str) -> str:
    opciones = [
        "-c", "user.name=Prueba", "-c", "user.email=prueba@example.invalid",
        "-c", "commit.gpgsign=false", "-c", "core.longpaths=true",
    ]
    resultado = subprocess.run(
        [GIT, "-C", str(carpeta), *opciones, *argumentos], capture_output=True, text=True, check=True
    )
    return resultado.stdout.strip()


def _crear_repositorio_propio(carpeta: Path, remoto: str) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    _git(carpeta, "init", "-q")
    _git(carpeta, "checkout", "-q", "-b", "mi-rama")
    _git(carpeta, "remote", "add", "origin", remoto)
    _git(carpeta, "config", "proyecto.responsable", "area-de-prueba")
    (carpeta / "NOTAS.txt").write_text("Trabajo propio.\n", encoding="utf-8")
    _git(carpeta, "add", "NOTAS.txt")
    _git(carpeta, "commit", "-q", "-m", "Trabajo propio")


def _estado_repositorio(carpeta: Path) -> dict:
    return {
        "historial": _git(carpeta, "log", "--format=%H %s"),
        "rama": _git(carpeta, "rev-parse", "--abbrev-ref", "HEAD"),
        "remotos": _git(carpeta, "remote", "-v"),
        "configuracion": (carpeta / ".git" / "config").read_bytes(),
    }


def _base_temporal() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "pytest-plantilla"


def _carpeta_de_la_ejecucion(salida: str) -> Path:
    encontrada = re.search(r"^Carpeta temporal de pruebas: (.+)$", salida, re.MULTILINE)
    assert encontrada, salida
    return Path(encontrada.group(1).strip())


def _correr_ayudante(tmp_path: Path, resultado_esperado: str):
    """Corre el ejecutor sobre una prueba que deja un enlace a una carpeta externa en su tmp_path."""
    ayudante = tmp_path / "test_ayudante.py"
    ayudante.write_text(AYUDANTE, encoding="utf-8")
    destino = tmp_path / "destino"
    destino.mkdir()
    (destino / "archivo.txt").write_text("intacto", encoding="utf-8")
    entorno = {**os.environ, "DESTINO_ENLACE": str(destino), "RESULTADO_ESPERADO": resultado_esperado}
    comando = (
        f"$env:{VARIABLE_TEMPORAL} = 'valor-previo'; "
        f"& '{RAIZ / 'herramientas' / EJECUTOR}' -q '{ayudante}'; "
        f"Write-Output ('CODIGO=' + $LASTEXITCODE); Write-Output ('VARIABLE=' + $env:{VARIABLE_TEMPORAL})"
    )
    return _ejecutar_comando(comando, entorno), destino


# --- Preparación ----------------------------------------------------------------


@requiere_powershell
@requiere_git
@requiere_entorno_activo
@omitir_si_es_anidada
def test_preparar_de_nuevo_conserva_el_repositorio_propio_y_el_trabajo(tmp_path):
    proyecto = _copiar_proyecto(tmp_path)
    contexto = proyecto / "CONTEXTO_PROYECTO.md"
    contexto.write_text("# Contexto del proyecto\nAvance propio del usuario.\n", encoding="utf-8")
    secretos = proyecto / ".streamlit" / "secrets.toml"
    ejemplo = (proyecto / ".streamlit" / "secrets.toml.example").read_text(encoding="utf-8")
    secretos.write_text(ejemplo + "# ajuste propio\n", encoding="utf-8")
    _crear_repositorio_propio(proyecto, "https://example.invalid/area/mi-proyecto.git")
    anidado = proyecto / "documentos" / "anexo"
    _crear_repositorio_propio(anidado, "https://example.invalid/area/anexo.git")
    antes = {"propio": _estado_repositorio(proyecto), "anidado": _estado_repositorio(anidado)}
    textos_antes = (contexto.read_bytes(), secretos.read_bytes())

    with _entorno_enlazado(proyecto):
        resultado = _ejecutar_script(
            proyecto, "preparar_proyecto.ps1", entorno={**os.environ, PRUEBA_ANIDADA: "1"}
        )

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert _estado_repositorio(proyecto) == antes["propio"]
    assert _estado_repositorio(anidado) == antes["anidado"]
    assert (contexto.read_bytes(), secretos.read_bytes()) == textos_antes
    # En la ejecución anidada solo se omiten, de forma intencional, las pruebas que vuelven a preparar.
    omitidas = [linea for linea in resultado.stdout.splitlines() if linea.startswith("SKIPPED")]
    assert omitidas and all("intencional" in linea for linea in omitidas), resultado.stdout


@requiere_powershell
def test_preparar_se_detiene_sin_cambios_si_la_carpeta_es_el_repositorio_de_la_plantilla(tmp_path):
    proyecto = _copiar_proyecto(tmp_path)
    configuracion = (
        '[remote "origin"]\n\turl = https://github.com/DELSURDEV/PlantillaDesarrolloCiudadano.git\n'
    )
    (proyecto / ".git").mkdir()
    (proyecto / ".git" / "config").write_text(configuracion, encoding="utf-8")
    contexto_antes = (proyecto / "CONTEXTO_PROYECTO.md").read_bytes()

    resultado = _ejecutar_script(proyecto, "preparar_proyecto.ps1")

    assert resultado.returncode != 0
    assert "repositorio de la plantilla" in resultado.stdout + resultado.stderr
    assert (proyecto / ".git" / "config").read_text(encoding="utf-8") == configuracion
    assert (proyecto / "CONTEXTO_PROYECTO.md").read_bytes() == contexto_antes
    assert not (proyecto / ".streamlit" / "secrets.toml").exists()
    assert not (proyecto / ".venv").exists()


@requiere_powershell
@requiere_entorno_activo
@omitir_si_es_anidada
def test_preparar_propaga_el_fallo_del_ejecutor_de_pruebas(tmp_path):
    proyecto = _copiar_proyecto(tmp_path)
    prohibida = tmp_path / "prohibida"
    # El ejecutor rechaza --basetemp y termina con error; la preparación debe fallar también.
    entorno = {**os.environ, PRUEBA_ANIDADA: "1", "PYTEST_ADDOPTS": f"--basetemp={prohibida}"}

    with _entorno_enlazado(proyecto):
        resultado = _ejecutar_script(proyecto, "preparar_proyecto.ps1", entorno=entorno)

    salida = resultado.stdout + resultado.stderr
    assert resultado.returncode != 0, salida
    assert "No se permite --basetemp" in salida
    assert "Hay pruebas que no pasan" in salida
    assert r"E:\<usuario>\<proyecto>" in salida  # la copia de prueba está fuera de la ubicación esperada
    assert not prohibida.exists()


# --- Creación del proyecto (bloque de AGENTS_ARRANQUE.md) ---------------------------


def _correr_bloque_de_descarga(tmp_path: Path, usuario: str, nombre: str, disco: Path | None = None):
    """Corre el bloque real del arranque contra un disco simulado, sin red y sin preparar el entorno."""
    if disco is None:
        disco = tmp_path / "disco"
        disco.mkdir(exist_ok=True)
    plantilla = tmp_path / "PlantillaFalsa-0"
    if not plantilla.exists():
        plantilla.mkdir()
        (plantilla / "archivo.txt").write_text("plantilla", encoding="utf-8")
    texto = (RAIZ / "herramientas" / "AGENTS_ARRANQUE.md").read_text(encoding="utf-8")
    encontrado = re.search(r'```powershell\n(\s*\$usuario = "<USUARIO>".*?)\n\s*```', texto, re.DOTALL)
    assert encontrado, "No se encontró el bloque de descarga en AGENTS_ARRANQUE.md"
    assert DISCO_DEL_BLOQUE in encontrado.group(1)
    bloque = (
        encontrado.group(1).replace("<USUARIO>", usuario).replace("<NOMBRE>", nombre)
        .replace(DISCO_DEL_BLOQUE, f'$disco = "{disco}"')
    )
    script = tmp_path / "bloque.ps1"
    script.write_text(FALSOS_DE_DESCARGA + bloque, encoding="utf-8-sig")
    registro = tmp_path / "registro.txt"
    entorno = {**os.environ, "REGISTRO_DESCARGA": str(registro), "PLANTILLA_FALSA": str(plantilla)}
    resultado = subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        capture_output=True, text=True, errors="replace", env=entorno, timeout=120, check=False,
    )
    return resultado, disco, registro


@requiere_powershell
def test_descarga_crea_el_proyecto_dentro_de_la_carpeta_del_usuario(tmp_path):
    resultado, disco, registro = _correr_bloque_de_descarga(tmp_path, "kehernandez", "GTMP")

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    proyecto = disco / "kehernandez" / "GTMP"
    assert (proyecto / "archivo.txt").read_text(encoding="utf-8") == "plantilla"
    assert [p.name for p in disco.iterdir()] == ["kehernandez"]
    assert [p.name for p in (disco / "kehernandez").iterdir()] == ["GTMP"]  # sin restos temporales
    version = (RAIZ / "VERSION").read_text(encoding="utf-8").strip()
    lineas = registro.read_text(encoding="utf-8-sig").splitlines()
    assert lineas[0].endswith(f"/archive/refs/tags/v{version}.zip"), lineas
    assert str(proyecto / "herramientas" / "preparar_proyecto.ps1") in lineas[1], lineas


@requiere_powershell
def test_descarga_reutiliza_la_carpeta_del_usuario_sin_tocar_sus_proyectos(tmp_path):
    _, disco, _ = _correr_bloque_de_descarga(tmp_path, "kehernandez", "GTMP")
    trabajo = disco / "kehernandez" / "GTMP" / "trabajo.txt"
    trabajo.write_text("avance", encoding="utf-8")

    resultado, _, _ = _correr_bloque_de_descarga(tmp_path, "kehernandez", "OTRO")

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert (disco / "kehernandez" / "OTRO" / "archivo.txt").exists()
    assert trabajo.read_text(encoding="utf-8") == "avance"
    assert sorted(p.name for p in (disco / "kehernandez").iterdir()) == ["GTMP", "OTRO"]


@requiere_powershell
def test_descarga_no_sobrescribe_un_proyecto_existente(tmp_path):
    _, disco, registro = _correr_bloque_de_descarga(tmp_path, "kehernandez", "GTMP")
    trabajo = disco / "kehernandez" / "GTMP" / "trabajo.txt"
    trabajo.write_text("avance", encoding="utf-8")
    lineas_antes = registro.read_text(encoding="utf-8-sig")

    resultado, _, _ = _correr_bloque_de_descarga(tmp_path, "kehernandez", "GTMP")

    assert resultado.returncode != 0
    assert "Ya existe" in resultado.stdout + resultado.stderr
    assert trabajo.read_text(encoding="utf-8") == "avance"
    assert registro.read_text(encoding="utf-8-sig") == lineas_antes  # no descargó ni preparó de nuevo


@requiere_powershell
@pytest.mark.parametrize(
    ("usuario", "nombre"),
    [
        (r"..\otro", "GTMP"),
        ("ke hernandez", "GTMP"),
        ("kehernandez.", "GTMP"),
        ("CON", "GTMP"),
        ("kehernandez", r"..\GTMP"),
        ("kehernandez", "G T"),
        ("kehernandez", "NUL"),
    ],
)
def test_descarga_rechaza_nombres_no_validos_sin_crear_nada(tmp_path, usuario, nombre):
    resultado, disco, registro = _correr_bloque_de_descarga(tmp_path, usuario, nombre)

    assert resultado.returncode != 0
    assert "no v" in resultado.stdout + resultado.stderr  # "no válido", con la tilde según la consola
    assert list(disco.iterdir()) == []
    assert not registro.exists()


@requiere_powershell
def test_descarga_avisa_si_no_existe_el_disco(tmp_path):
    no_existe = tmp_path / "no-existe"

    resultado, _, registro = _correr_bloque_de_descarga(tmp_path, "kehernandez", "GTMP", disco=no_existe)

    assert resultado.returncode != 0
    assert "No existe el disco" in resultado.stdout + resultado.stderr
    assert not no_existe.exists()
    assert not registro.exists()


# --- Ejecución de pruebas ---------------------------------------------------------


@requiere_powershell
@requiere_entorno_del_proyecto
def test_ejecutar_pruebas_usa_carpeta_propia_restaura_la_variable_y_limpia_sin_seguir_enlaces(tmp_path):
    resultado, destino = _correr_ayudante(tmp_path, "pasa")

    salida = resultado.stdout + resultado.stderr
    assert "CODIGO=0" in resultado.stdout, salida
    assert "VARIABLE=valor-previo" in resultado.stdout, salida
    carpeta = _carpeta_de_la_ejecucion(resultado.stdout)
    assert str(carpeta.parent).lower() == str(_base_temporal()).lower()
    assert RAIZ not in carpeta.parents
    assert not carpeta.exists()
    assert (destino / "archivo.txt").read_text(encoding="utf-8") == "intacto"


@requiere_powershell
@requiere_entorno_del_proyecto
def test_ejecutar_pruebas_propaga_el_fallo_y_conserva_la_carpeta(tmp_path):
    resultado, destino = _correr_ayudante(tmp_path, "falla")

    salida = resultado.stdout + resultado.stderr
    assert "CODIGO=1" in resultado.stdout, salida
    assert "VARIABLE=valor-previo" in resultado.stdout, salida
    carpeta = _carpeta_de_la_ejecucion(resultado.stdout)
    assert carpeta.is_dir()
    assert str(carpeta.parent).lower() == str(_base_temporal()).lower()
    assert re.fullmatch(r"ejecucion-[0-9a-f]{8}", carpeta.name)
    subprocess.run(["cmd", "/d", "/c", "rmdir", "/s", "/q", str(carpeta)], capture_output=True, check=True)
    assert not carpeta.exists()
    assert (destino / "archivo.txt").read_text(encoding="utf-8") == "intacto"


@requiere_powershell
@requiere_entorno_del_proyecto
@pytest.mark.parametrize("caso", ["proyecto", "disco_e", "basetemp_unido", "basetemp_separado", "pytest_addopts"])
def test_ejecutar_pruebas_rechaza_carpetas_temporales_no_seguras(caso, tmp_path):
    entorno = dict(os.environ)
    argumentos = ["-q", "tests/test_integridad.py"]
    prohibida = tmp_path / "prohibida"
    if caso == "proyecto":
        entorno["LOCALAPPDATA"] = str(RAIZ)
    elif caso == "disco_e":
        entorno["LOCALAPPDATA"] = r"E:\kehernandez"
    elif caso == "basetemp_unido":
        argumentos.append(f"--basetemp={prohibida}")
    elif caso == "basetemp_separado":
        argumentos += ["--basetemp", str(prohibida)]
    else:
        entorno["PYTEST_ADDOPTS"] = f"--basetemp={prohibida}"

    resultado = _ejecutar_script(RAIZ, EJECUTOR, *argumentos, entorno=entorno)

    assert resultado.returncode == CODIGO_RECHAZO, resultado.stdout + resultado.stderr
    assert "Carpeta temporal de pruebas" not in resultado.stdout
    assert not (RAIZ / "pytest-plantilla").exists()
    assert not prohibida.exists()


# --- Arranque ---------------------------------------------------------------------


@requiere_powershell
@requiere_entorno_del_proyecto
def test_abrir_con_puerto_ocupado_explica_como_usar_otro_y_no_cierra_nada():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ocupado:
        ocupado.bind(("127.0.0.1", 0))
        ocupado.listen()
        puerto = ocupado.getsockname()[1]

        resultado = _ejecutar_script(RAIZ, "abrir_aplicacion.ps1", "-Puerto", str(puerto), "-SinNavegador")

        assert resultado.returncode == 3, resultado.stdout + resultado.stderr
        assert f"abrir_aplicacion.ps1 -Puerto {puerto + 1}" in resultado.stdout
        with socket.create_connection(("127.0.0.1", puerto), timeout=5):
            pass  # el programa que ocupaba el puerto sigue funcionando
