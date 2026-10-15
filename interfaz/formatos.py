"""Formatos estándar de datos (El Salvador). NO MODIFICAR (zona protegida)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

ZONA_HORARIA = ZoneInfo("America/El_Salvador")


def moneda(valor: float | Decimal) -> str:
    """$1,234.56 (USD)."""
    signo = "-" if valor < 0 else ""
    return f"{signo}${abs(valor):,.2f}"


def numero(valor: float | int | Decimal, decimales: int = 0) -> str:
    """1,234 o 1,234.5"""
    return f"{valor:,.{decimales}f}"


def porcentaje(valor: float, decimales: int = 1) -> str:
    """0.125 -> '12.5 %'"""
    return f"{valor * 100:.{decimales}f} %"


def fecha(valor: date) -> str:
    """dd/mm/aaaa"""
    return valor.strftime("%d/%m/%Y")


def fecha_hora(valor: datetime) -> str:
    """dd/mm/aaaa HH:mm en hora de El Salvador."""
    if valor.tzinfo is not None:
        valor = valor.astimezone(ZONA_HORARIA)
    return valor.strftime("%d/%m/%Y %H:%M")
