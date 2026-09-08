"""Parseo de fechas es-UY del sitio, sin depender de locale del sistema.

Formato observado en el sitio real: "DD mon YYYY / DD mon YYYY"
(ej. "29 sep 2025 / 15 nov 2025"), meses abreviados en español, minúsculas,
sin punto. Ver documentation.md (Fase 0) para el detalle de cómo se confirmó.
"""

import logging
import re

logger = logging.getLogger(__name__)

MESES_ES = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}

_FECHA_RE = re.compile(
    r"(?P<dia>\d{1,2})\s+(?P<mes>[a-záéíóú]{3,4})\.?\s+(?P<anio>\d{4})",
    re.IGNORECASE,
)


def _parse_una_fecha(raw: str) -> str | None:
    match = _FECHA_RE.search(raw)
    if not match:
        return None

    mes_nombre = match.group("mes").lower()
    mes = MESES_ES.get(mes_nombre)
    if mes is None:
        logger.warning("Mes no reconocido en fecha %r", raw)
        return None

    dia = int(match.group("dia"))
    anio = int(match.group("anio"))
    return f"{anio:04d}-{mes:02d}-{dia:02d}"


def parse_rango_fechas(raw: str | None) -> tuple[str | None, str | None]:
    """Recibe el string crudo del rango (o None si el bloque no existía en el HTML)
    y devuelve (fecha_inicio, fecha_fin) en formato YYYY-MM-DD, o None cada una
    si no se pudo extraer. Nunca lanza excepción ante formato inesperado.
    """
    if not raw or not raw.strip():
        return None, None

    partes = raw.split("/")
    if len(partes) != 2:
        logger.warning("Formato de rango de fechas inesperado: %r", raw)
        return None, None

    fecha_inicio = _parse_una_fecha(partes[0])
    fecha_fin = _parse_una_fecha(partes[1])

    if fecha_inicio is None or fecha_fin is None:
        logger.warning("No se pudo parsear alguna fecha del rango: %r", raw)

    return fecha_inicio, fecha_fin
