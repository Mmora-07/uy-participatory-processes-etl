"""Orquestación: listado paginado, extracción de slugs y armado de cada Proceso.

Los reintentos/backoff/delay viven en utils/http_client.py, no acá. El manejo
de errores por proceso individual está aislado en build_proceso(): así el
try/except amplio vive en un único lugar bien delimitado.
"""

import logging

import httpx
from bs4 import BeautifulSoup

from config import BASE_URL, LISTING_PER_PAGE, PROCESSES_PATH
from models import Proceso
from parser import parse_ficha
from utils.http_client import build_client, get_with_retries

logger = logging.getLogger(__name__)


def _extraer_slugs(html: str) -> list[str]:
    """Slugs en orden de aparición, tal como vienen (nunca lowercased,
    hay slugs con mayúscula reales: Homicidios, Consulta65, etc.).
    """
    soup = BeautifulSoup(html, "lxml")
    slugs = []
    prefix = f"{PROCESSES_PATH}/"
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(prefix) and href.count("/") == 2:
            slugs.append(href[len(prefix) :])
    return slugs


def listar_slugs(client: httpx.Client, state: str, limit: int | None) -> list[str]:
    """Recorre /processes?filter[with_date]={state}&page=N acumulando slugs
    únicos hasta juntar `limit` o hasta que una página no traiga slugs nuevos.
    Deduplicación acá, al armar la lista (no sobre el resultado final).
    """
    vistos: dict[str, None] = {}  # dict en vez de set: preserva orden de inserción
    page = 1

    while limit is None or len(vistos) < limit:
        url = f"{BASE_URL}{PROCESSES_PATH}?filter[with_date]={state}&per_page={LISTING_PER_PAGE}&page={page}"
        response = get_with_retries(client, url)
        slugs_pagina = _extraer_slugs(response.text)

        nuevos = [s for s in slugs_pagina if s not in vistos]
        if not slugs_pagina:
            break
        for s in nuevos:
            vistos[s] = None

        logger.info("Página %d: %d slugs (%d nuevos, %d acumulados)", page, len(slugs_pagina), len(nuevos), len(vistos))
        page += 1

    resultado = list(vistos.keys())
    if limit is not None:
        resultado = resultado[:limit]
    return resultado


def build_proceso(client: httpx.Client, slug: str) -> Proceso | None:
    """Fetch + parse de un único proceso. Cualquier excepción (red, parseo)
    se loguea con slug + URL y devuelve None en vez de tumbar la corrida completa.
    """
    url = f"{BASE_URL}{PROCESSES_PATH}/{slug}"
    try:
        response = get_with_retries(client, url)
        return parse_ficha(response.text, slug=slug, url=url)
    except Exception:
        logger.exception("Fallo procesando slug=%s url=%s", slug, url)
        return None


def crawl(state: str, limit: int | None) -> list[Proceso]:
    with build_client() as client:
        slugs = listar_slugs(client, state, limit)
        logger.info("Procesando %d slugs", len(slugs))

        procesos = []
        for slug in slugs:
            proceso = build_proceso(client, slug)
            if proceso is not None:
                procesos.append(proceso)

        return procesos
