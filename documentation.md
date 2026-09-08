# Documentación de decisiones y hallazgos

> Este archivo registra, en orden cronológico por fase, las decisiones de diseño tomadas y la evidencia empírica que las sustenta. Sirve como bitácora de trabajo, como base para la sustentación del proyecto y como borrador de la sección "Decisiones y supuestos" del README final.

---

## Fase 0 — Reconocimiento

**Sitio real:** `https://plataformaparticipacionciudadana.gub.uy/processes` (Decidim, Presidencia/AGESIC — Uruguay).

**Metodología:** se descargó el listado completo (`?filter[with_date]=all&per_page=100`) y las 86 fichas de proceso individuales que contiene, con un script Python ad hoc (`httpx`, delay 0.4s entre requests) para inspeccionar la estructura real del HTML de forma programática — no solo visual — antes de fijar ninguna regla de mapeo. Esto permitió confirmar o refutar con conteos exactos (no solo "no se observó en la muestra") cada uno de los supuestos que dejaba abiertos el enunciado.

### Volumen y paginación

- El listado con `filter[with_date]=all` trae **86 procesos** en total (por encima del piso de 30 pedido).
- `per_page` acepta hasta **100**, por lo que con un solo request (`per_page=100`) se obtienen los 86 en una única página — no hace falta paginar en la práctica actual, pero el crawler igual implementa el loop de `page=N` de forma genérica (ver Fase 3) para no asumir que el volumen se va a mantener por debajo de 100 en el futuro.
- El "24 por página" que menciona la consigna no se corresponde con el comportamiento real observado (se vieron 25 por página con el valor por defecto, y hasta 100 con `per_page=100`).

### `nombre_largo` / `nombre_corto`

- **No existe un subtítulo real distinto del título principal** en ninguna de las 86 fichas. La regla de truncado aplica al 100% de los casos.
- **Selector primario:** `h1` dentro de `.participatory-space__hero-text`. Es el título visible en pantalla.
- **Hallazgo no anticipado — 14 de 86 procesos (~16%) no tienen ese bloque `hero-text` en absoluto** (ver sección de fechas más abajo, es el mismo grupo de procesos). En esos casos el `<h1>` de la página es el logo del sitio ("Plataforma de Participación Ciudadana Digital"), no el título del proceso.
  - **Decisión:** fallback a `<meta property="og:title">` (o `<title>` si faltara también), quitando el sufijo fijo `" - Plataforma de Participación Ciudadana Digital"` (constante en `config.py`). Confirmado que ese meta tag está presente y correcto en los 14 casos.
- **Regla de truncado para `nombre_corto`:** máx. 80 caracteres, normalizando espacios múltiples antes de truncar, cortando en el último espacio completo (nunca a mitad de palabra) y agregando `"…"` cuando hubo corte. Se validó con un caso real de 274 caracteres (`consulta72`, sobre el Precio Máximo Intermedio de GLP), que hace evidente por qué el truncado es necesario y no un caso de laboratorio.

### Fechas

- Formato confirmado en el HTML: `"DD mon YYYY / DD mon YYYY"` (ej. `"29 sep 2025 / 15 nov 2025"`), meses abreviados en español, minúsculas, sin punto.
- **Selector:** `div.participatory-space__metadata-item` cuyo `.participatory-space__metadata-item-title span` dice exactamente `"Fecha de inicio / Fecha de finalización"`; el valor está en el `span` hermano siguiente.
- **Hallazgo no anticipado y contrario al borrador de 0.4 — el caso de fecha ausente sí existe y es frecuente:** los mismos **14 de 86 procesos (~16%)** que no tienen `hero-text` tampoco tienen este bloque de metadata de fechas en absoluto (no es que venga vacío o parcial: el bloque entero no se renderiza). Son procesos con plantilla distinta — muestran "Fases del proceso" con fechas por fase dentro de un modal de ayuda, en vez del rango de fecha único en el encabezado.
  - **Decisión:** `fecha_inicio` y `fecha_fin` → `null` explícito cuando no se encuentra el bloque, nunca string vacío. `utils/dates.py` no debe asumir que el string siempre existe.
- No se encontró ningún caso de fecha *parcial* (con inicio pero sin fin, o viceversa) entre los 86 — el contrato de "una sola fecha presente" queda como red de seguridad defensiva, sin evidencia empírica de que ocurra en este sitio.

### `entidad` (Grupo promotor)

- **Selector:** mismo patrón que fechas — `div.participatory-space__metadata-item` con `.participatory-space__metadata-item-title span` == `"Grupo promotor"`; valor en el `span` hermano.
- **Hallazgo no anticipado (contrario al borrador de 0.4, que no había encontrado ningún caso):** con la muestra completa de 86 fichas, **23 de 86 (~27%) no tienen el bloque "Grupo promotor"**. Es un caso real y frecuente, no un caso borde teórico.
  - **Decisión:** `entidad` → `null` explícito cuando el bloque no está presente.

### `formulario_url` / `componentes`

- **Selector:** `a.participatory-space__nav-item` (los enlaces bajo "Salta a:" en la ficha). Los `href` son siempre relativos (ej. `/processes/Homicidios/f/640/proposals`) — se resuelven a absolutos con `urljoin` contra la URL base, nunca se concatenan a mano.
- **Los 3 escenarios se confirmaron con conteo exacto sobre las 86 fichas:**
  - **Cero componentes:** 3 casos (`consejo2025`, `pencti-publica`, `plan-nacional-seguridad-publica`) → `formulario_url` y `componentes` → `null`.
  - **Un componente:** varios casos (ej. `plan-juventudes-2025-2030`).
  - **Múltiples componentes:** 60 de 86 (mayoría). Máximo observado: 7 (`plan-nacional-genero`).
- **Decisión:** `formulario_url` = primer `.participatory-space__nav-item` en orden de aparición en el DOM (se asume que el orden del DOM refleja el orden de prioridad definido por quien armó el proceso en Decidim — no hay forma de confirmar esto sin acceso al admin, se documenta como supuesto).
- `componentes` (campo opcional) = lista completa de esos enlaces (URL absoluta + texto visible), útil para no perder información cuando hay más de uno.

### `slug` y `descripcion_url`

- **No se parsean desde el HTML.** El crawler ya conoce el slug (viene del listado) y la URL completa (la que usó para hacer el request), así que `parser.py` los recibe como parámetros junto con el HTML en vez de re-derivarlos — evita depender de un `<link rel="canonical">` que, se confirmó, **no está presente** en ninguna ficha (solo hay `og:url`, pero es redundante con dato que el crawler ya tiene).
- **Hallazgo no anticipado — slugs con mayúsculas:** confirmado con la lista completa de 86 (`Homicidios`, `Violencia-genero`, `Consulta65`…`Consulta70`, `quinto-planGA`, `sexto-planGA`). **Decisión: el slug nunca se normaliza a minúsculas** en ningún punto del pipeline — hacerlo rompería la URL real y la deduplicación tendría que ser case-sensitive de todos modos.

### Fixtures guardados

En `tests/fixtures/`, HTML real sin modificar, elegidos para cubrir los casos borde confirmados arriba:

| Archivo | Caso que cubre |
|---|---|
| `ficha_homicidios.html` | Caso "feliz": título, fechas y entidad presentes, 2 componentes, slug con mayúscula. |
| `ficha_aditivos_alimentarios.html` | Plantilla sin `hero-text`: sin título en `h1`, sin bloque de fechas → fallback a `og:title`, fechas `null`. |
| `ficha_consejo2025.html` | Cero componentes (`formulario_url` y `componentes` → `null`). |
| `ficha_transporte_publico_montevideo.html` | `entidad` ausente (`Grupo promotor` no presente) con fechas y componentes normales. |
| `listado_per_page_100.html` | Listado completo (86 procesos) con `per_page=100`, para probar la extracción de slugs del crawler. |

---

## Fase 1 — Arquitectura

Se adopta el árbol extendido de `plan.md` §1.4 (config.py, utils/http_client.py, output.py, utils/text.py, utils/logging_config.py separados) en vez del árbol mínimo de §1.1, porque la evaluación pondera explícitamente "organización, nombres claros, ausencia de valores mágicos" — separar cliente HTTP / parseo / orquestación / salida permite explicar cada pieza de forma aislada en la sustentación.

- **Modelo de datos:** `pydantic.BaseModel` en vez de `dataclass` — valida tipos en el borde (parser → modelo) sin código manual, y da serialización a dict/JSON (`model_dump`) gratis, coherente con el punto de "serialización propia" del checklist de 1.4.
- **HTTP:** `httpx` (API moderna, tipada, soporta `Client` reutilizable con `timeout`/`headers` centralizados).
- **Parseo HTML:** `beautifulsoup4` + `lxml` como parser — selectors CSS suficientes para los patrones confirmados en Fase 0 (`div.participatory-space__metadata-item`, `a.participatory-space__nav-item`), sin necesitar XPath.

---

## Fase 2 — Parser

- `parser.py` no hace ningún request: recibe `(html, slug, url)` como datos simples. `slug` y `url` los provee el crawler (que ya los conoce por construcción), en vez de re-derivarlos del HTML — evita depender de un `<link rel="canonical">` que se confirmó ausente en todas las fichas.
- **Sobre "7 campos obligatorios":** el enunciado original (fuera de este repo) los cuenta como 7, pero `plan.md` §2.1 lista 8 nombres de campo. Se resuelve tratando `fecha_inicio`/`fecha_fin` como un único concepto ("fecha", con dos valores) — así quedan exactamente 7: `slug`, `nombre_largo`, `nombre_corto`, `fecha` (inicio+fin), `entidad`, `descripcion_url`, `formulario_url`. `componentes` es el campo opcional adicional. Se documenta acá para no tener que reconstruir el razonamiento en la sustentación.
- Extracción de `entidad` y de las fechas comparten el mismo patrón HTML (`div.participatory-space__metadata-item`), así que `parser._extraer_metadata_item()` es una sola función genérica parametrizada por la etiqueta buscada ("Grupo promotor" / "Fecha de inicio / Fecha de finalización"), en vez de dos funciones casi idénticas.
- 9 tests contra los 4 fixtures + casos de `utils/dates.py` (fecha completa, ausente, string vacío, formato inesperado) — todos verdes en el primer intento, gracias a haber confirmado los selectores contra HTML real en Fase 0 antes de escribir el parser (no se escribió a ciegas).

## Fase 3 — Crawler

- Deduplicación de slugs: se hace **al armar la lista de slugs** (`listar_slugs`, con un `dict` que preserva orden de inserción), no sobre el resultado final. Con un único request (`per_page=100`) alcanza para los 86 procesos reales, pero el loop de paginación (`page=N`) queda genérico por si el volumen crece por encima de 100 en el futuro.
- Reintentos: 3 reintentos (4 intentos totales) con backoff exponencial `0.5 * 2^intento` segundos (0.5s, 1s, 2s), solo ante timeout o 5xx — un 4xx no se reintenta porque no es un error transitorio. Después de una respuesta exitosa se aplica el delay fijo de `REQUEST_DELAY_SECONDS` (0.4s) como buena práctica de scraping, no como medida anti-bot.
- `build_proceso(client, slug)` aísla fetch + parse + `try/except Exception` amplio para un solo proceso: loguea slug + URL + excepción (`logger.exception`, con traceback) y devuelve `None` sin tumbar la corrida. `crawl()` simplemente descarta los `None`.
- Validado en vivo contra el sitio real con `--limit 6` y luego el comando de referencia completo (`--state all --limit 30`): trae los 30 procesos, con `entidad`/`formulario_url` en `null` exactamente en los slugs identificados en Fase 0 (`pencti-publica`, `consejo2025`, etc.) — el comportamiento en producción coincide con lo previsto a partir del análisis offline.

## Fase 4 — CLI

- `main.py` solo parsea argumentos (`--limit`, `--state`, `--output`) y llama a `crawl()` + `escribir_json()` — cero lógica de negocio.
- `--state` usa `choices=VALID_STATES` (de `config.py`) para fallar rápido con un estado inválido en vez de silenciosamente no filtrar nada.
- Comando de referencia ejecutado tal cual: `python main.py --state all --limit 30` → `output.json` con 30 procesos reales, 0 slugs duplicados, 0 campos faltantes, 0 strings vacíos donde debía haber `null`. Se verificaron a mano 2 pares `descripcion_url`/`formulario_url` (HTTP 200 reales).

---

## Fase 5 — Validación de calidad de datos

Corrida completa (`python main.py --state all`, sin `--limit`) contra el sitio real, sin errores logueados (ningún `WARNING`/`ERROR`, ningún reintento disparado):

- **86 procesos**, 0 slugs duplicados.
- Los 7 campos obligatorios presentes en los 86 registros; 0 strings vacíos (`""`) donde debía haber `null`.
- Fechas siempre en `YYYY-MM-DD` o `null` (verificado con regex sobre los 86 registros) — nunca el string crudo.
- `entidad` en `null`: **23/86**, `fecha_inicio` en `null`: **14/86**, `formulario_url` en `null`: **3/86** — coinciden exactamente con los conteos de la Fase 0, confirmando que el análisis offline sobre el HTML predijo correctamente el comportamiento del pipeline completo en producción.
- Verificación manual: 3 URLs (`descripcion_url` y `formulario_url` de 2 procesos distintos) devolvieron HTTP 200 reales al navegarlas.
- Revisión manual de `pencti-publica` y `consejo2025` (candidatos a `formulario_url: null`): confirmado que son casos reales sin sección "Salta a:" en la ficha, no bugs de parseo.

---

## Fase 7 — Pregunta de diseño

**¿Cómo harías que esta ETL corra de forma incremental/idempotente en vez de recrear todo desde cero cada vez?**

El `slug` es la clave natural de upsert: es estable, único en el sitio real (confirmado sobre los 86 procesos) y no se normaliza, así que sirve directo como clave primaria en destino (`INSERT ... ON CONFLICT (slug) DO UPDATE` en Postgres, o el equivalente `MERGE` en otros motores). Para evitar reescribir un registro que no cambió, se calcularía un hash (ej. SHA-256) sobre los campos extraídos de cada proceso y se compararía contra el hash guardado en destino antes de hacer el UPDATE — el sitio no expone algo como `updated_at` ni `sort=updated_at` en el listado, así que no hay forma de pedir "solo lo que cambió desde la última corrida": igual hay que traer el listado completo y las 86 fichas, y es en destino donde se decide qué de eso realmente cambió. La idempotencia ante fallos a mitad de corrida sale gratis de este mismo diseño: si el proceso se corta después de procesar 40 de 86 slugs, correrlo de nuevo desde el principio no duplica nada — cada upsert por `slug` simplemente vuelve a escribir (o no, si el hash no cambió) el mismo registro, en vez de insertar una fila nueva.
