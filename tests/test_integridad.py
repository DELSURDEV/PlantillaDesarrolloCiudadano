import subprocess
import sys

from conftest import RAIZ


def test_base_de_seguridad_sin_modificar():
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "herramientas" / "verificar_plantilla.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout
