"""Extracción de campos desde el HTML de una ficha de proceso.

Sin I/O de red: recibe el HTML ya descargado (más el slug y la URL que el
crawler usó para pedirlo) y devuelve un modelo Proceso. Esto es lo que
permite testear contra fixtures locales sin red (ver tests/test_parser.py).
"""

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    BASE_URL,
    HERO_SLOGAN_SELECTOR,
    HERO_TITLE_SELECTOR,
    METADATA_ITEM_SELECTOR,
    METADATA_ITEM_TITLE_SELECTOR,
    METADATA_LABEL_ENTIDAD,
    METADATA_LABEL_FECHAS,
    NAV_ITEM_SELECTOR,
    SITE_TITLE_SUFFIX,
)
from models import Componente, Proceso
from utils.dates import parse_rango_fechas
from utils.text import extract_text, normalize_whitespace, truncate

logger = logging.getLogger(__name__)


def _extraer_nombre_largo(soup: BeautifulSoup) -> str:
    """Título visible (h1 del hero). ~16% de las fichas no tienen ese bloque
    (plantilla distinta, sin fechas tampoco) -> fallback a og:title / <title>,
    quitando el sufijo fijo del sitio.
    """
    hero = soup.select_one(HERO_TITLE_SELECTOR)
    if hero:
        return extract_text(hero)

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        texto = og_title["content"]
    elif soup.title and soup.title.string:
        texto = soup.title.string
    else:
        logger.warning("No se encontró título ni fallback (og:title/<title>)")
        return ""

    texto = normalize_whitespace(texto)
    if texto.endswith(SITE_TITLE_SUFFIX):
        texto = texto[: -len(SITE_TITLE_SUFFIX)]
    return texto


def _extraer_metadata_item(soup: BeautifulSoup, label: str) -> str | None:
    """Busca el bloque .participatory-space__metadata-item cuyo título
    (.participatory-space__metadata-item-title span) coincide con `label`,
    y devuelve el texto del span de valor. None si el bloque no existe.
    """
    for item in soup.select(METADATA_ITEM_SELECTOR):
        title_span = item.select_one(METADATA_ITEM_TITLE_SELECTOR)
        if not title_span or extract_text(title_span) != label:
            continue
        value_span = title_span.parent.find_next_sibling("span")
        if value_span:
            return extract_text(value_span)
    return None


def _extraer_entidad(soup: BeautifulSoup) -> str | None:
    """Grupo promotor declarado en el bloque de metadata (fuente primaria,
    estructurada con una etiqueta explícita). En ~27% de las fichas reales
    ese bloque no existe, pero la entidad promotora igual aparece en pantalla
    como bajada del título (.participatory-space__hero-slogan) -> fallback.
    Ninguna ficha real observada carece de ambas fuentes a la vez, pero el
    contrato sigue siendo None si eso llegara a pasar.

    Nota: el fallback es texto libre sin estructura fija -- a veces trae
    prefijos como "Consulta pública ||" en vez de solo el nombre de la
    entidad (ver documentation.md, Fase 5.1). Se documenta como limitación
    conocida en vez de intentar recortarlo con heurísticas frágiles.
    """
    entidad = _extraer_metadata_item(soup, METADATA_LABEL_ENTIDAD)
    if entidad:
        return entidad

    slogan = soup.select_one(HERO_SLOGAN_SELECTOR)
    return extract_text(slogan) if slogan else None


def _extraer_componentes(soup: BeautifulSoup) -> list[Componente]:
    componentes = []
    for nav_item in soup.select(NAV_ITEM_SELECTOR):
        href = nav_item.get("href")
        if not href:
            continue
        componentes.append(
            Componente(
                texto=extract_text(nav_item),
                url=urljoin(BASE_URL, href),
            )
        )
    return componentes


def parse_ficha(html: str, slug: str, url: str) -> Proceso:
    soup = BeautifulSoup(html, "lxml")

    nombre_largo = _extraer_nombre_largo(soup)
    fechas_raw = _extraer_metadata_item(soup, METADATA_LABEL_FECHAS)
    fecha_inicio, fecha_fin = parse_rango_fechas(fechas_raw)
    entidad = _extraer_entidad(soup)
    componentes = _extraer_componentes(soup)

    return Proceso(
        slug=slug,
        nombre_largo=nombre_largo,
        nombre_corto=truncate(nombre_largo),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        entidad=entidad,
        descripcion_url=url,
        formulario_url=componentes[0].url if componentes else None,
        componentes=componentes or None,
    )
