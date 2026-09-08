"""Configuración centralizada del logger. Se llama una sola vez desde main.py;
el resto de los módulos solo hacen logging.getLogger(__name__).
"""

import logging


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
