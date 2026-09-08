"""Escritura del JSON final. Aislado del resto del pipeline para que cambiar
el destino (ej. a una base de datos, ver Fase 7) no toque crawler/parser/main.
"""

import json
import logging
from pathlib import Path

from models import Proceso

logger = logging.getLogger(__name__)


def escribir_json(procesos: list[Proceso], path: Path) -> None:
    data = [p.to_dict() for p in procesos]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Escritos %d procesos en %s", len(data), path)
