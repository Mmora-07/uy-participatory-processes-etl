"""Tests de la parte pura de crawler.py (extracción de slugs desde el HTML
del listado). No requiere red: usa el fixture del listado guardado en
tests/fixtures/. Ver documentation.md (Fase 0) para el origen del fixture.
"""

from pathlib import Path

from crawler import _extraer_slugs

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_extraer_slugs_del_listado_completo():
    html = (FIXTURES_DIR / "listado_per_page_100.html").read_text(encoding="utf-8")
    slugs = _extraer_slugs(html)

    assert len(slugs) == 86
    assert len(set(slugs)) == 86  # sin duplicados dentro de una misma página
    # slugs con mayúscula reales -- confirma que no se lowercasea acá
    assert "Homicidios" in slugs
    assert "homicidios" not in slugs
