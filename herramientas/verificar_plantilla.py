"""Verifica que los archivos protegidos de la plantilla no se hayan modificado.

Uso:   python herramientas/verificar_plantilla.py
Solo el equipo dueño de la plantilla usa --generar al publicar una versión.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = RAIZ / "herramientas" / "MANIFIESTO_PLANTILLA.txt"
PROTEGIDOS = [
    "seguridad/*.py",
    "interfaz/*.py",
    "interfaz/estilos.css",
    "static/**/*",
    "recursos/*.svg",
    ".streamlit/config.toml",
    ".streamlit/secrets.toml.example",
    "tests/test_seguridad.py",
    "tests/test_reglas_codigo.py",
    "tests/test_integridad.py",
    "herramientas/verificar_plantilla.py",
    "herramientas/preparar_proyecto.ps1",
    "restricciones.txt",
]


def _huella(ruta: Path) -> str:
    # Se normalizan los saltos de línea para que Windows (CRLF) no cambie la huella.
    contenido = ruta.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(contenido).hexdigest()


def _archivos() -> list[Path]:
    return sorted({p for patron in PROTEGIDOS for p in RAIZ.glob(patron) if p.is_file()})


def generar() -> None:
    lineas = [f"{_huella(p)}  {p.relative_to(RAIZ).as_posix()}" for p in _archivos()]
    MANIFIESTO.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Manifiesto generado con {len(lineas)} archivos.")


def verificar() -> list[str]:
    if not MANIFIESTO.exists():
        return ["No existe herramientas/MANIFIESTO_PLANTILLA.txt"]
    esperado = {}
    for linea in MANIFIESTO.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            huella, ruta = linea.split(maxsplit=1)
            esperado[ruta] = huella
    actuales = {p.relative_to(RAIZ).as_posix(): p for p in _archivos()}
    problemas = [f"Falta: {r}" for r in esperado if r not in actuales]
    problemas += [f"Archivo nuevo en zona protegida: {r}" for r in actuales if r not in esperado]
    problemas += [
        f"Modificado: {r}"
        for r, p in actuales.items()
        if r in esperado and _huella(p) != esperado[r]
    ]
    return problemas


if __name__ == "__main__":
    if "--generar" in sys.argv:
        generar()
        sys.exit(0)
    resultado = verificar()
    if resultado:
        print("La base de seguridad de la plantilla fue modificada:")
        print("\n".join(f"  - {p}" for p in resultado))
        print("Restaure esos archivos desde la plantilla o pida el cambio al equipo dueño.")
        sys.exit(1)
    print("Plantilla íntegra.")
