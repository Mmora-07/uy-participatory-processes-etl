"""Normalización y truncado de texto libre extraído del HTML."""

import re

from config import NOMBRE_CORTO_MAX_LEN


def normalize_whitespace(text: str) -> str:
    """Colapsa espacios/saltos de línea múltiples en uno solo y recorta bordes."""
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, max_len: int = NOMBRE_CORTO_MAX_LEN) -> str:
    """Trunca a max_len caracteres cortando en el último espacio completo,
    nunca a mitad de palabra, y agrega "…" cuando hubo corte.
    """
    text = normalize_whitespace(text)
    if len(text) <= max_len:
        return text

    cut = text[:max_len]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    return cut.rstrip() + "…"
