"""Cliente HTTP compartido: sesión reutilizable, reintentos con backoff
exponencial ante timeout/5xx y delay entre requests. Separado de la
orquestación del crawler para que este último no implemente reintentos inline.
"""

import logging
import time

import httpx

from config import (
    HTTP_BACKOFF_FACTOR,
    HTTP_MAX_RETRIES,
    HTTP_TIMEOUT_SECONDS,
    REQUEST_DELAY_SECONDS,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


def build_client() -> httpx.Client:
    return httpx.Client(
        timeout=HTTP_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
    )


def get_with_retries(client: httpx.Client, url: str) -> httpx.Response:
    """GET con reintentos ante timeout o 5xx, backoff exponencial
    (HTTP_BACKOFF_FACTOR * 2**intento). Deja pasar 4xx sin reintentar
    (son errores del cliente, reintentar no los arregla). Propaga la
    excepción si se agotan los reintentos; el llamador decide qué hacer
    con un proceso individual que falla.
    """
    ultimo_error: Exception | None = None

    for intento in range(HTTP_MAX_RETRIES + 1):
        if intento > 0:
            time.sleep(HTTP_BACKOFF_FACTOR * (2 ** (intento - 1)))

        try:
            response = client.get(url)
            if response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}", request=response.request, response=response
                )
            response.raise_for_status()
            time.sleep(REQUEST_DELAY_SECONDS)
            return response
        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            ultimo_error = exc
            logger.warning("Intento %d/%d falló para %s: %s", intento + 1, HTTP_MAX_RETRIES + 1, url, exc)

    assert ultimo_error is not None
    raise ultimo_error
