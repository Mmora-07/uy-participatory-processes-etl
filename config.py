"""Constantes centralizadas: URLs, selectores CSS, límites y parámetros de red.

Ver documentation.md (Fase 0) para el detalle de cómo se confirmó cada selector
contra el HTML real del sitio.
"""

# --- Sitio ---
BASE_URL = "https://plataformaparticipacionciudadana.gub.uy"
PROCESSES_PATH = "/processes"
SITE_TITLE_SUFFIX = " - Plataforma de Participación Ciudadana Digital"

# Estados válidos para --state, mapeados 1:1 a filter[with_date]
# (confirmado contra el sitio real: active=4, past=82, upcoming=0, all=86)
VALID_STATES = ("all", "active", "past", "upcoming")

# --- Listado / paginación ---
# El sitio acepta per_page hasta 100 (no 24 como sugiere el enunciado);
# con 86 procesos totales, un único request alcanza para traerlos todos.
LISTING_PER_PAGE = 100

# --- Red ---
HTTP_TIMEOUT_SECONDS = 15.0
HTTP_MAX_RETRIES = 3
HTTP_BACKOFF_FACTOR = 0.5  # segundos: 0.5, 1, 2 (exponencial) entre reintentos
REQUEST_DELAY_SECONDS = 0.4  # delay entre requests sucesivos (buena práctica, no anti-bot)
USER_AGENT = "uy-participatory-processes-etl/1.0"

# --- Selectores CSS (confirmados contra 86 fichas reales, ver documentation.md) ---
HERO_TITLE_SELECTOR = ".participatory-space__hero-text h1"
METADATA_ITEM_SELECTOR = ".participatory-space__metadata-item"
METADATA_ITEM_TITLE_SELECTOR = ".participatory-space__metadata-item-title span"
NAV_ITEM_SELECTOR = "a.participatory-space__nav-item"

METADATA_LABEL_FECHAS = "Fecha de inicio / Fecha de finalización"
METADATA_LABEL_ENTIDAD = "Grupo promotor"

# --- Reglas de texto ---
NOMBRE_CORTO_MAX_LEN = 80
