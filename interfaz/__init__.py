"""Interfaz estándar DELSUR. NO MODIFICAR (zona protegida). Ver MARCA.md."""

from . import formatos
from .componentes import (
    COLORES,
    Estado,
    Indicador,
    confirmar_accion,
    encabezado,
    fila_indicadores,
    seccion,
    tarjeta,
)
from .marco import Aplicacion, ejecutar_aplicacion

__all__ = [
    "COLORES",
    "Aplicacion",
    "Estado",
    "Indicador",
    "confirmar_accion",
    "ejecutar_aplicacion",
    "encabezado",
    "fila_indicadores",
    "formatos",
    "seccion",
    "tarjeta",
]
