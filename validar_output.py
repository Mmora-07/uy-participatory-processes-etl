"""Valida un output.json ya generado contra el contrato de datos del enunciado.

Script aparte, opcional: no forma parte del comando de referencia
(python main.py --state all --limit 30) ni de main.py. Automatiza los mismos
checks manuales que se hicieron a mano en documentation.md (Fase 5), para
poder re-correrlos sin repetir el trabajo cada vez.

No hace requests de red a propósito (ver documentation.md, Fase 5.1/5.2):
valida que las URLs tengan forma de URL, no que respondan 200 -- esa
verificación puntual ya se hizo a mano una vez y quedó documentada.

Uso: python validar_output.py [ruta/al/output.json]  (default: output.json)
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from config import CAMPOS_NULEABLES, LIMITE_MINIMO_PROCESOS
from models import Proceso
from output import loguear_resumen_nulos
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _url_valida(valor: str) -> bool:
    partes = urlparse(valor)
    return partes.scheme in ("http", "https") and bool(partes.netloc)


def validar(procesos: list[Proceso]) -> list[str]:
    """Devuelve la lista de problemas encontrados (vacía si todo está bien).
    La presencia de los 7 campos + tipos ya la garantiza la reconstrucción de
    cada registro como Proceso (pydantic) antes de llegar acá -- esto solo
    chequea reglas que el tipo por sí solo no puede expresar.
    """
    problemas = []

    if len(procesos) < LIMITE_MINIMO_PROCESOS:
        problemas.append(f"Solo {len(procesos)} procesos, se esperaban >= {LIMITE_MINIMO_PROCESOS}")

    slugs = [p.slug for p in procesos]
    duplicados = sorted({s for s in slugs if slugs.count(s) > 1})
    if duplicados:
        problemas.append(f"Slugs duplicados: {duplicados}")

    for p in procesos:
        for campo in CAMPOS_NULEABLES:
            if getattr(p, campo) == "":
                problemas.append(f"{p.slug}: {campo} es string vacío, debería ser null")

        for campo in ("fecha_inicio", "fecha_fin"):
            valor = getattr(p, campo)
            if valor is not None and not FECHA_RE.match(valor):
                problemas.append(f"{p.slug}: {campo}={valor!r} no tiene formato YYYY-MM-DD")

        for campo in ("descripcion_url", "formulario_url"):
            valor = getattr(p, campo)
            if valor is not None and not _url_valida(valor):
                problemas.append(f"{p.slug}: {campo}={valor!r} no parece una URL válida")

    return problemas


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=Path("output.json"))
    args = parser.parse_args()

    data = json.loads(args.path.read_text(encoding="utf-8"))
    procesos = [Proceso(**item) for item in data]  # valida presencia/tipos de los 7 campos
    logger.info("Validando %d procesos desde %s", len(procesos), args.path)

    loguear_resumen_nulos(procesos)
    problemas = validar(procesos)

    if problemas:
        for problema in problemas:
            logger.error(problema)
        logger.error("VALIDACIÓN FALLIDA: %d problema(s) encontrado(s)", len(problemas))
        sys.exit(1)

    logger.info("VALIDACIÓN OK: %d procesos, sin problemas encontrados", len(procesos))


if __name__ == "__main__":
    main()
