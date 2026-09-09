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

- **Selector primario:** `h1` dentro de `.participatory-space__hero-text`. Es el título visible en pantalla.
- **Corrección (ver Fase 5.1):** el hallazgo original de esta fase ("no existe un subtítulo real") era incompleto — sí existe un elemento `<p class="participatory-space__hero-slogan">` justo debajo del `h1` en la mayoría de las fichas. No se usa para `nombre_corto` de todas formas, y el enunciado formal de la prueba confirma este criterio ("si el sitio muestra un subtítulo/resumen... usalo; si no, truncá"): el contenido de `hero-slogan` es texto libre inconsistente (a veces el nombre de la entidad promotora, a veces un hashtag de campaña, a veces un eslogan genérico como "Cuidamos el mañana") — no es un subtítulo/resumen fiable del título, así que no califica como la excepción que el enunciado permite.
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

- **Selector primario:** mismo patrón que fechas — `div.participatory-space__metadata-item` con `.participatory-space__metadata-item-title span` == `"Grupo promotor"`; valor en el `span` hermano.
- **Hallazgo no anticipado (contrario al borrador de 0.4, que no había encontrado ningún caso):** con la muestra completa de 86 fichas, **23 de 86 (~27%) no tienen el bloque "Grupo promotor"**. Es un caso real y frecuente, no un caso borde teórico.
- **Decisión final (ver Fase 5.1/5.2):** `entidad` sale **únicamente** del bloque estructurado `"Grupo promotor"`; `null` explícito cuando no está presente. Se evaluó (e implementó, y luego se revirtió) un fallback a `hero-slogan` para esos 23 casos — la página sí muestra ahí el nombre de la entidad en la mayoría de ellos — pero el enunciado formal de la prueba es explícito: "es un campo estructurado real, no texto libre... null si falta". `hero-slogan` es exactamente lo que el enunciado descarta (texto libre), así que se revirtió el fallback para cumplir el contrato tal cual está pedido.

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
| `ficha_transporte_publico_montevideo.html` | `Grupo promotor` ausente → `entidad: null` (ver Fase 5.1/5.2). |
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
- Toda extracción de texto pasa por `utils.text.extract_text()` (separador `" "` entre nodos + normalización), no por `tag.get_text(strip=True)` directo — evita pegar palabras de nodos hijos distintos sin espacio real entre ellos (bug real encontrado en Fase 5.1).
- 9 tests iniciales contra los 4 fixtures + casos de `utils/dates.py` (fecha completa, ausente, string vacío, formato inesperado) — todos verdes en el primer intento, gracias a haber confirmado los selectores contra HTML real en Fase 0 antes de escribir el parser (no se escribió a ciegas). Se agregó 1 test más en Fase 5.1 (regresión del separador de texto) → 10 tests en total.

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

### Fase 5.1 — Auditoría de nulos por campo, un fallback tentador y un bug real de texto

Tabla resumen de `null` por campo sobre los 86 procesos reales (`output.json` completo, `--state all` sin `--limit`):

| Campo | `null` | % | Motivo |
|---|---:|---:|---|
| `slug` | 0 | 0% | — |
| `nombre_largo` | 0 | 0% | — |
| `nombre_corto` | 0 | 0% | — |
| `fecha_inicio` / `fecha_fin` | 14 | 16% | Plantilla sin bloque de fechas (ver Fase 0) — `null` real confirmado. |
| `entidad` | 23 | 27% | Bloque `"Grupo promotor"` ausente en el HTML — `null` real y esperado por contrato (ver Fase 5.2). |
| `descripcion_url` | 0 | 0% | — |
| `formulario_url` / `componentes` | 3 | 3% | Ficha real sin sección "Salta a:" (verificado a mano en Fase 5). |

**Caso investigado (y descartado — ver Fase 5.2):** revisando manualmente el registro de `evaluacion-trastorno-espectro-autista` ("Consulta sobre terapias alternativas para el Trastorno del Espectro Autista (TEA)") en `output.json`, se detectó `entidad: null` a pesar de que la ficha real muestra "Agencia de Evaluación de Tecnologías Sanitarias de Uruguay (AETSU)" debajo del título. Esa entidad vive en `<p class="participatory-space__hero-slogan">`, un elemento que el parser no consulta para `entidad` (solo mira `Grupo promotor`, ausente en esta ficha).

Se re-analizaron las 86 fichas cacheadas de Fase 0 cruzando `Grupo promotor` contra `hero-slogan`, para evaluar si convenía usar este último como fallback:

| Combinación | Cantidad | Qué implica |
|---|---:|---|
| Ambos presentes | 49 | La mayoría **no coincide textualmente** (`hero-slogan` es más corto/informal — sigla vs. nombre completo, a veces un hashtag de campaña) → `hero-slogan` es un campo de "bajada" de texto libre, no un duplicado estructurado de `Grupo promotor`. |
| Solo `hero-slogan` (Grupo promotor ausente) | 23 | Los 23 casos "entidad null". Revisados a mano, los 23 *leen* como una entidad real (ministerios, agencias, institutos) — un fallback ahí habría sido técnicamente plausible. |
| Solo `Grupo promotor` (slogan ausente) | 14 | Sin relevancia para esta decisión. |
| Ninguno de los dos | 0 | No hay evidencia real de este caso. |

Se implementó el fallback, se probó contra fixtures y contra el sitio real (`entidad` en `null` bajó de 23/86 a 0/86), y **se revirtió al día siguiente al recibir el enunciado formal de la prueba** — ver Fase 5.2 para el motivo exacto. Queda documentado acá como parte del proceso real de trabajo, no como un error a esconder: es un buen ejemplo de una mejora de calidad de datos técnicamente razonable que había que descartar por no ajustarse al contrato pedido.

**Bug real (este sí se mantiene corregido), encontrado en el mismo repaso:** `_extraer_metadata_item` y compañía usaban `tag.get_text(strip=True)` sin separador. En fichas donde el valor mezcla un `<a>` (ej. un hashtag) con texto plano sin espacio real entre ambos en el HTML fuente, esto pegaba las palabras (`"...instaladoreseléctricosURSEA"`, ficha `Consulta67`). **Fix:** `utils/text.extract_text()` centraliza `tag.get_text(" ")` + `normalize_whitespace()`, usado en todos los puntos de extracción de texto del parser (título, metadata, componentes). Este fix no depende de la discusión de `entidad` — mejora la limpieza de cualquier campo de texto y no viola ningún contrato del enunciado. Cubierto por `test_extract_text_no_pega_nodos_sin_espacio`.

### Fase 5.2 — Confirmación contra el enunciado formal y reversión del fallback

El 2026-09-08, ya con el fallback de `entidad` implementado, se recibió el enunciado formal de la prueba (`prueba_uruguay_consultas_publicas.pdf`). La tabla de campos ahí es explícita sobre `entidad`:

> "Valor del bloque de metadata **'Grupo promotor'** en la ficha... **Es un campo estructurado real, no texto libre** — pero no todos los procesos lo traen completo; **null si falta**."

Esto contradice directamente el fallback a `hero-slogan` (que es, por definición, texto libre) implementado en Fase 5.1. **Se revirtió** (`parser.py`, vuelta a `entidad = _extraer_metadata_item(soup, METADATA_LABEL_ENTIDAD)` sin fallback; se sacó `HERO_SLOGAN_SELECTOR` de `config.py` por quedar sin uso) para cumplir el contrato tal cual está escrito, en vez de "mejorar" un dato que el enunciado pide explícitamente dejar en `null` cuando el campo estructurado no está completo. `output.json` se regeneró: `entidad` en `null` vuelve a **23/86**, que es el número correcto según el enunciado formal.

El resto del enunciado formal se contrastó campo por campo contra lo ya implementado y **coincide sin cambios**, lo cual valida las decisiones tomadas por exploración empírica en Fase 0 antes de tener el PDF en mano:

- `nombre_largo`: el enunciado pide explícitamente `<h1>` con fallback a `og:title` — exactamente el fallback que ya se había implementado al encontrar el 16% de fichas sin `hero-text`.
- `formulario_url`/`componentes`: el enunciado da el selector exacto `.participatory-space__nav-item` y el criterio "primer enlace" — coincide con lo implementado.
- `nombre_corto`: el enunciado permite usar un subtítulo/resumen del sitio "si el sitio lo muestra", y confirma que en esta instancia lo más común es que no exista tal subtítulo utilizable — coherente con la decisión de truncar y con haber descartado `hero-slogan` como esa fuente (ver Fase 5.1).
- Alternativas de datos abiertos/API: el enunciado confirma exactamente lo que se documentó como vía descartada — `/open-data/download` no trae título/fechas/entidad a nivel de proceso, y `/api` no está habilitado en esta instancia.
- Filtro y paginación: el enunciado reporta 4 procesos activos por defecto y "paginación de 24 por página" — el conteo de activos coincide exacto (4/4); la paginación medida automáticamente dio 25 por página por defecto y hasta 100 con `per_page=100` (ver Fase 0), una diferencia menor que no afecta el resultado ya que ambos enfoques llegan a los mismos 86 procesos.

**Alternativa considerada y descartada — flag de CLI para reactivar el fallback:** en vez de eliminar el fallback, se evaluó dejarlo detrás de un flag opcional (ej. `--entidad-incluir-texto-libre`, apagado por defecto) para no "perder" el hallazgo de Fase 5.1. Se descartó por dos razones: (1) el enunciado no dice "preferí estructurado, pero texto libre sirve como respaldo" — dice explícitamente "no texto libre", así que un flag que habilita justo eso sigue siendo una vía para no cumplir el contrato pedido, aunque esté apagada por defecto; tener esa puerta en el código es una señal peor que no tenerla, incluso si nunca se activa en la corrida evaluada. (2) Es una rama de código, un selector CSS y una CLI adicional mantenidos para un caso de uso que nunca se ejercita en la entrega real — exactamente el tipo de complejidad "por las dudas" que este proyecto evita en otros lados (ver criterio de "ausencia de valores mágicos" y la arquitectura de Fase 1). El hallazgo ya queda preservado íntegro como evidencia escrita acá arriba, que es donde pesa para la evaluación ("criterio de mapeo"), sin necesidad de que viva como código ejecutable.

**Alternativa considerada y descartada — rama de Git aparte para el fallback:** también se evaluó, en vez de un flag, mover el fallback a una rama (`feature/entidad-fallback` o similar) y dejar `main` limpia según el enunciado, mostrando así manejo de Git. Se descartó por el mismo motivo de fondo que el flag: el problema nunca fue *dónde* vive el código que viola "no texto libre", sino que el enunciado ya definió esa fuente como inválida para este campo — tenerla en otra rama documentada no cambia esa evaluación, solo cambia dónde se guarda. Además agrega una rama sin un propósito real de desarrollo (no es work-in-progress ni una función que vaya a integrarse después) — se puede demostrar manejo de ramas de Git con cualquier otra tarea real del proyecto, no hace falta forzar una para un caso que ya se decidió no usar. El razonamiento y la implementación siguen preservados en el historial de commits (`c5046f3`, `e26ea72`) y en esta sección — alcanza como evidencia sin mantener una rama viva.

### Fase 5.3 — Resumen de nulos automático y script de validación

Dos agregados opcionales, sin tocar el comando de referencia (`python main.py --state all --limit 30` sigue siendo exactamente ese comando, sin flags nuevos):

- **Resumen de nulos al final del run:** `output.loguear_resumen_nulos()` cuenta, sobre la lista de `Proceso` ya construida, cuántos son `null` en cada campo nulleable (`fecha_inicio`, `fecha_fin`, `entidad`, `formulario_url`) y lo loguea en una sola línea INFO. Se llama automáticamente desde `main.py` después de `escribir_json()`, así que aparece sin pedir nada extra en la corrida evaluada. Automatiza lo que antes se calculaba a mano para la tabla de Fase 5.1.
- **`validar_output.py`:** script aparte (no lo importa `main.py`) que corre los mismos checks manuales de la Fase 5 sobre un `output.json` ya generado. Reconstruye cada registro como `Proceso` (pydantic) antes de validar nada más — si a un registro le faltara un campo o tuviera el tipo equivocado, el script ya falla ahí, con el error puntual de pydantic señalando qué registro y qué campo. A partir de ahí corre 5 checks explícitos, cada uno logueado por separado (para que corriendo el script se vea exactamente qué se evaluó, no solo un "OK" genérico al final):

  | # | Chequeo | Qué detecta | Qué NO detecta |
  |---|---|---|---|
  | 0 | Estructura y tipos (vía `Proceso(**item)`) | Falta algún campo de los 7 + `componentes`, o tiene un tipo incompatible (ej. un número donde va texto). | Que el *valor* sea correcto semánticamente — solo la forma. |
  | 1 | Cantidad ≥ 30 | Menos procesos que el piso pedido por el enunciado. | — |
  | 2 | Slugs únicos | Slugs duplicados en el archivo. | — |
  | 3 | Sin strings vacíos | `""` en cualquier campo — tanto en los que **nunca** deben ser null (`slug`, `nombre_largo`, `nombre_corto`, `descripcion_url`) como en los que si faltan deben ser `null`, no `""` (`fecha_inicio`, `fecha_fin`, `entidad`, `formulario_url`). | Que un `null` en un campo nulleable sea un caso real y no un bug de parseo — eso se revisó a mano en Fase 5. |
  | 4 | Formato de fecha | `fecha_inicio`/`fecha_fin` no nulos que no matchean `YYYY-MM-DD`. | Que la fecha sea *correcta* (ej. un 31 de febrero pasaría). |
  | 5 | Forma de URL | `descripcion_url`/`formulario_url` no nulos sin scheme `http(s)` o sin dominio. | Que la URL responda 200 — **a propósito no hace requests de red** (mismo principio que el resto del proyecto: no depender de la red donde no hace falta). Esa verificación puntual ya se hizo a mano en Fase 5 sobre una muestra y quedó documentada ahí, no se repite automáticamente acá. |

  El check 3 (sin strings vacíos) originalmente solo cubría los 4 campos nulleables — al hacer explícitos los chequeos para esta sección se notó que los 4 campos que *nunca* deben ser `null` tampoco estaban protegidos contra terminar en `""` (ej. si `_extraer_nombre_largo` cae en su rama de fallo total, ver `parser.py`). Se agregó esa cobertura (`CAMPOS_SIEMPRE_REQUERIDOS`) al mismo tiempo que se explicitaron los logs — un buen ejemplo de que documentar/loguear con más detalle también hace más fácil encontrar huecos de cobertura.

  Probado deliberadamente con un `output.json` corrompido a propósito (slug duplicado, fecha en formato crudo, `nombre_largo`/`nombre_corto` vacíos) para confirmar que detecta cada problema por separado y sale con código de salida 1.

Uso: `python validar_output.py` (usa `output.json` por defecto) o `python validar_output.py ruta/al/archivo.json`.

---

## Fase 7 — Pregunta de diseño

**¿Cómo harías que esta ETL corra de forma incremental/idempotente en vez de recrear todo desde cero cada vez?**

El `slug` es la clave natural de upsert: es estable, único en el sitio real (confirmado sobre los 86 procesos) y no se normaliza, así que sirve directo como clave primaria en destino (`INSERT ... ON CONFLICT (slug) DO UPDATE` en Postgres, o el equivalente `MERGE` en otros motores). Para evitar reescribir un registro que no cambió, se calcularía un hash (ej. SHA-256) sobre los campos extraídos de cada proceso y se compararía contra el hash guardado en destino antes de hacer el UPDATE — el sitio no expone algo como `updated_at` ni `sort=updated_at` en el listado, así que no hay forma de pedir "solo lo que cambió desde la última corrida": igual hay que traer el listado completo y las 86 fichas, y es en destino donde se decide qué de eso realmente cambió. La idempotencia ante fallos a mitad de corrida sale gratis de este mismo diseño: si el proceso se corta después de procesar 40 de 86 slugs, correrlo de nuevo desde el principio no duplica nada — cada upsert por `slug` simplemente vuelve a escribir (o no, si el hash no cambió) el mismo registro, en vez de insertar una fila nueva.
