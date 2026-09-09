"""Escritura del JSON final. Aislado del resto del pipeline para que cambiar
el destino (ej. a una base de datos, ver Fase 7) no toque crawler/parser/main.
"""

import json
import logging
from pathlib import Path

from config import CAMPOS_NULEABLES
from models import Proceso

logger = logging.getLogger(__name__)


def escribir_json(procesos: list[Proceso], path: Path) -> None:
    data = [p.to_dict() for p in procesos]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Escritos %d procesos en %s", len(data), path)


def loguear_resumen_nulos(procesos: list[Proceso]) -> None:
    """Cuenta nulls por campo nulleable y los loguea en una sola línea.
    Automatiza el conteo manual que se hizo para la tabla de documentation.md
    (Fase 5.1) -- no cambia ningún dato, es solo observabilidad.
    """
    total = len(procesos)
    if total == 0:
        logger.warning("Resumen de nulos: 0 procesos procesados")
        return

    partes = []
    for campo in CAMPOS_NULEABLES:
        nulos = sum(1 for p in procesos if getattr(p, campo) is None)
        partes.append(f"{campo}={nulos}/{total} ({nulos / total:.0%})")
    logger.info("Resumen de nulos: %s", " | ".join(partes))
