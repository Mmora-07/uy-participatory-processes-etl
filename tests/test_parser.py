"""Tests del parser contra fixtures reales guardados en tests/fixtures/.
No requieren red. Ver documentation.md (Fase 0) para el origen de cada fixture.
"""

from pathlib import Path

import pytest

from parser import parse_ficha
from utils.dates import parse_rango_fechas

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _cargar_fixture(nombre: str) -> str:
    return (FIXTURES_DIR / nombre).read_text(encoding="utf-8")


def test_ficha_completa_homicidios():
    html = _cargar_fixture("ficha_homicidios.html")
    proceso = parse_ficha(html, slug="Homicidios", url="https://example.org/processes/Homicidios")

    assert proceso.slug == "Homicidios"  # el slug con mayúscula no se normaliza
    assert "Homicidios" in proceso.nombre_largo
    assert proceso.nombre_corto  # no vacío
    assert len(proceso.nombre_corto) <= 81  # 80 + posible "…"
    assert proceso.fecha_inicio == "2025-09-29"
    assert proceso.fecha_fin == "2025-11-15"
    assert proceso.entidad is not None
    assert proceso.descripcion_url == "https://example.org/processes/Homicidios"
    assert proceso.componentes is not None
    assert len(proceso.componentes) == 2
    assert proceso.formulario_url == proceso.componentes[0].url


def test_ficha_sin_hero_ni_fechas_usa_fallback_de_titulo():
    """~16% de las fichas reales no tienen el bloque hero-text ni el de fechas
    (plantilla distinta). El nombre debe salir de og:title y las fechas ser null.
    """
    html = _cargar_fixture("ficha_aditivos_alimentarios.html")
    proceso = parse_ficha(
        html, slug="aditivos-alimentarios", url="https://example.org/processes/aditivos-alimentarios"
    )

    assert proceso.nombre_largo  # se resolvió por el fallback, no quedó vacío
    assert "Plataforma de Participación Ciudadana Digital" not in proceso.nombre_largo
    assert "MERCOSUR" in proceso.nombre_largo
    assert proceso.fecha_inicio is None
    assert proceso.fecha_fin is None
    # esta ficha sí tiene "Grupo promotor" y componentes, a pesar de no tener hero
    assert proceso.entidad is not None
    assert proceso.componentes is not None


def test_ficha_sin_componentes():
    html = _cargar_fixture("ficha_consejo2025.html")
    proceso = parse_ficha(html, slug="consejo2025", url="https://example.org/processes/consejo2025")

    assert proceso.componentes is None
    assert proceso.formulario_url is None
    # el resto de los campos obligatorios sigue presente
    assert proceso.fecha_inicio is not None
    assert proceso.entidad is not None


def test_ficha_sin_entidad():
    html = _cargar_fixture("ficha_transporte_publico_montevideo.html")
    proceso = parse_ficha(
        html,
        slug="transporte-publico-montevideo",
        url="https://example.org/processes/transporte-publico-montevideo",
    )

    assert proceso.entidad is None
    assert proceso.fecha_inicio is not None
    assert proceso.componentes is not None


@pytest.mark.parametrize(
    ("raw", "esperado"),
    [
        ("29 sep 2025 / 15 nov 2025", ("2025-09-29", "2025-11-15")),
        ("01 ene 2026 / 31 dic 2026", ("2026-01-01", "2026-12-31")),
        (None, (None, None)),
        ("", (None, None)),
        ("formato totalmente inesperado", (None, None)),
    ],
)
def test_parse_rango_fechas(raw, esperado):
    assert parse_rango_fechas(raw) == esperado
