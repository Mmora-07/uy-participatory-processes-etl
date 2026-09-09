"""Valida un output.json ya generado contra el contrato de datos del enunciado.

Script aparte, opcional: no forma parte del comando de referencia
(python main.py --state all --limit 30) ni de main.py. Automatiza los mismos
checks manuales que se hicieron a mano en documentation.md (Fase 5), para
poder re-correrlos sin repetir el trabajo cada vez. Loguea cada chequeo por
separado (ver documentation.md, Fase 5.3, para el detalle de qué evalúa cada
uno y qué queda deliberadamente fuera).

No hace requests de red a propósito (ver documentation.md, Fase 5.1/5.2):
valida que las URLs tengan forma de URL, no que respondan 200 -- esa
verificación puntual ya se hizo a mano una vez y quedó documentada.

Uso: python validar_output.py [ruta/al/output.json]  (default: output.json)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from re import compile as re_compile
from urllib.parse import urlparse

from config import CAMPOS_NULEABLES, LIMITE_MINIMO_PROCESOS
from models import Proceso
from output import loguear_resumen_nulos
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

FECHA_RE = re_compile(r"^\d{4}-\d{2}-\d{2}$")

# Campos que el contrato exige siempre presentes y no-vacíos (nunca null,
# nunca ""). Distinto de CAMPOS_NULEABLES (config.py), donde null es válido
# pero "" no lo es.
CAMPOS_SIEMPRE_REQUERIDOS = ("slug", "nombre_largo", "nombre_corto", "descripcion_url")


def _url_valida(valor: str) -> bool:
    partes = urlparse(valor)
    return partes.scheme in ("http", "https") and bool(partes.netloc)


def _chequear_cantidad_minima(procesos: list[Proceso]) -> list[str]:
    if len(procesos) < LIMITE_MINIMO_PROCESOS:
        return [f"Solo {len(procesos)} procesos, se esperaban >= {LIMITE_MINIMO_PROCESOS}"]
    return []


def _chequear_slugs_unicos(procesos: list[Proceso]) -> list[str]:
    slugs = [p.slug for p in procesos]
    duplicados = sorted({s for s in slugs if slugs.count(s) > 1})
    return [f"Slugs duplicados: {duplicados}"] if duplicados else []


def _chequear_sin_vacios(procesos: list[Proceso]) -> list[str]:
    problemas = []
    for p in procesos:
        for campo in CAMPOS_SIEMPRE_REQUERIDOS:
            if getattr(p, campo) == "":
                problemas.append(f"{p.slug}: {campo} es string vacío, nunca debería estarlo")
        for campo in CAMPOS_NULEABLES:
            if getattr(p, campo) == "":
                problemas.append(f"{p.slug}: {campo} es string vacío, debería ser null")
    return problemas


def _chequear_formato_fechas(procesos: list[Proceso]) -> list[str]:
    problemas = []
    for p in procesos:
        for campo in ("fecha_inicio", "fecha_fin"):
            valor = getattr(p, campo)
            if valor is not None and not FECHA_RE.match(valor):
                problemas.append(f"{p.slug}: {campo}={valor!r} no tiene formato YYYY-MM-DD")
    return problemas


def _chequear_forma_urls(procesos: list[Proceso]) -> list[str]:
    problemas = []
    for p in procesos:
        for campo in ("descripcion_url", "formulario_url"):
            valor = getattr(p, campo)
            if valor is not None and not _url_valida(valor):
                problemas.append(f"{p.slug}: {campo}={valor!r} no parece una URL válida")
    return problemas


# Nombre descriptivo del check (va al log) + la función que lo implementa.
# El orden es el orden en que se loguean.
CHECKS = (
    (f"cantidad de procesos >= {LIMITE_MINIMO_PROCESOS}", _chequear_cantidad_minima),
    ("slugs únicos (sin duplicados)", _chequear_slugs_unicos),
    ("sin strings vacíos donde el contrato pide null o un valor real", _chequear_sin_vacios),
    ("fecha_inicio/fecha_fin en formato YYYY-MM-DD cuando no son null", _chequear_formato_fechas),
    ("descripcion_url/formulario_url con forma de URL válida cuando no son null", _chequear_forma_urls),
)


def validar(procesos: list[Proceso]) -> list[str]:
    """Corre todos los CHECKS, logueando el resultado de cada uno, y devuelve
    la lista combinada de problemas (vacía si todo está bien).

    La presencia de los 7 campos + sus tipos ya la garantiza la reconstrucción
    de cada registro como Proceso (pydantic) en main() antes de llegar acá --
    si un registro no tuviera un campo o tuviera el tipo equivocado, el script
    ya habría fallado ahí con un error explícito, antes de este punto.
    """
    logger.info("Chequeo [estructura y tipos de los 7 campos + componentes]: OK (validado por el modelo Proceso al cargar el archivo)")

    problemas = []
    for nombre, check in CHECKS:
        encontrados = check(procesos)
        estado = "OK" if not encontrados else f"FALLÓ ({len(encontrados)} caso(s))"
        logger.info("Chequeo [%s]: %s", nombre, estado)
        problemas.extend(encontrados)
    return problemas


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=Path("output.json"))
    args = parser.parse_args()

    data = json.loads(args.path.read_text(encoding="utf-8"))
    procesos = [Proceso(**item) for item in data]
    logger.info("Validando %d procesos desde %s", len(procesos), args.path)

    loguear_resumen_nulos(procesos)
    problemas = validar(procesos)

    if problemas:
        logger.error("--- Detalle de los problemas encontrados ---")
        for problema in problemas:
            logger.error(problema)
        logger.error("VALIDACIÓN FALLIDA: %d problema(s) encontrado(s)", len(problemas))
        sys.exit(1)

    logger.info("VALIDACIÓN OK: %d procesos, sin problemas encontrados", len(procesos))


if __name__ == "__main__":
    main()
