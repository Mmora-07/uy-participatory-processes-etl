"""CLI: parsea argumentos y orquesta crawler -> output. Sin lógica de negocio
propia (esa vive en crawler.py, parser.py y output.py).

Comando de referencia: python main.py --state all --limit 30
"""

import argparse
import logging
from pathlib import Path

from config import VALID_STATES
from crawler import crawl
from output import escribir_json
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ETL de procesos participativos de la Plataforma de Participación Ciudadana Digital (Uruguay)."
    )
    parser.add_argument("--limit", type=int, default=None, help="Tope de procesos a procesar.")
    parser.add_argument(
        "--state",
        choices=VALID_STATES,
        default="all",
        help="Filtro de estado (mapeado a filter[with_date]).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output.json"),
        help="Ruta del JSON de salida.",
    )
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()

    logger.info("Iniciando crawl: state=%s limit=%s", args.state, args.limit)
    procesos = crawl(state=args.state, limit=args.limit)
    escribir_json(procesos, args.output)


if __name__ == "__main__":
    main()
