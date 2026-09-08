# Plan de ejecución — ETL Procesos Participativos de Uruguay

> Guía de trabajo para no perder el foco durante el desarrollo. Cada fase tiene objetivos, subobjetivos y criterios de "hecho". No avanzar a la siguiente fase hasta cerrar los checks de la actual, salvo que se indique lo contrario.

---

## Fase 0 — Reconocimiento (sin escribir código)

**Objetivo:** entender el sitio real antes de asumir nada, y fijar las decisiones de mapeo que la consigna deja abiertas.

### 0.1 Explorar el sitio a mano
- [ ] Abrir `/processes?filter[with_date]=all` y `&page=2` en el navegador.
- [ ] Confirmar que hay >30 procesos entre las dos páginas (ya lo dice la consigna, pero verificarlo con los propios ojos evita sorpresas).
- [ ] Entrar a 4-5 fichas de proceso distintas, buscando variedad de casos borde:
  - [ ] Una con fecha de inicio y fin completas.
  - [ ] Una con fecha `null` o incompleta.
  - [ ] Una con `entidad` (Grupo promotor) presente.
  - [ ] Una con `entidad` ausente.
  - [ ] Una con varios componentes en el nav (`.participatory-space__nav-item`).
  - [ ] Una con cero componentes (si existe).

### 0.2 Fijar reglas de mapeo (documentar ya, no al final)
- [ ] `nombre_corto`: confirmar si el sitio muestra subtítulo real en alguna ficha. Si no, fijar la regla de truncado (largo máx., si corta en palabra completa, si agrega "…").
- [ ] Formato exacto del string de fechas (`"01 feb 2026 / 30 sep 2026"`) y armar el diccionario de meses es-UY abreviados (ene…dic) — no depender de `locale`.
- [ ] Definir output de `fecha_inicio`/`fecha_fin` cuando el string viene parcial o ausente (siempre `null`, nunca string vacío).
- [ ] `formulario_url`: confirmar que se toma el primer `.participatory-space__nav-item` del DOM; documentar el supuesto de que el orden del DOM = orden de prioridad.
- [ ] `entidad` ausente → `null` explícito.

### 0.3 Guardar fixture
- [ ] Guardar el HTML de al menos una ficha real como fixture local (para parser.py y el test unitario, sin depender de red).

**Criterio de cierre de Fase 0:** tener las 5 reglas de mapeo escritas en un borrador (van a ir al README luego) y el fixture guardado.

### 0.4 Hallazgos preliminares (referencia — verificar igual antes de dar por cerrada la Fase 0)

> Ya se hizo una exploración inicial del sitio (7 fichas + el listado general) que arrojó estos datos. Se dejan acá como punto de partida y sugerencia, **no como sustituto** de los checks de 0.1/0.2 — conviene confirmarlos con la propia exploración antes de fijarlos como reglas definitivas, sobre todo los que dicen "no observado".

- **Volumen real:** el listado con `filter[with_date]=all` trae **86 procesos** en total, muy por encima del piso de 30. El selector "Resultados por página" ofrece 25/50/100 vía `&per_page=N` — no 24 como decía la consigna. Sugerencia: usar `per_page=100` y paginar con `&page=N` hasta agotar resultados o alcanzar `--limit`, en vez de asumir un tamaño de página fijo.
- **`nombre_corto`:** en las 7 fichas revisadas no apareció ningún subtítulo distinto del `<h1>` — la regla de truncado a ~80 caracteres aplicaría en el 100% de los casos vistos. Sugerencia de detalle: normalizar espacios múltiples antes de truncar (se vio un título con doble espacio) y cortar en el último espacio completo, no a mitad de palabra.
- **Formato de fechas confirmado:** `"DD mon YYYY / DD mon YYYY"` (ej. `"01 feb 2026 / 30 sep 2026"`, `"29 sep 2025 / 15 nov 2025"`), meses abreviados en español, minúsculas, sin punto. Estable en las 7 fichas. No se observó ningún caso de fecha ausente o parcial en la muestra — el manejo de `null` para ese caso queda como red de seguridad sin validar empíricamente todavía.
- **`entidad` (Grupo promotor):** presente en las 7 fichas revisadas, incluyendo organismos muy distintos (ministerio, unidad reguladora, instituto). No se encontró ningún caso real de `entidad` ausente — sigue siendo un caso a contemplar por contrato de nulos, pero sin evidencia empírica todavía. Vale la pena seguir buscando este caso específico durante la Fase 0.
- **`formulario_url` / `componentes` — los 3 escenarios sí se confirmaron:**
  - Cero componentes: ficha "Elecciones de representantes... Consejo Asesor Honorario de Discapacidad" no tiene sección "Salta a:" → sugiere `null`.
  - Un componente: ficha del Plan de Acción de Juventudes.
  - Múltiples componentes: Homicidios (2 enlaces), AtuServicio.uy (2 enlaces), Plan Nacional de Género (7 enlaces).
- **Hallazgo no anticipado — slugs con mayúsculas:** varios slugs no son lowercase (`Homicidios`, `Consulta67`, `Consulta70`). Sugerencia: no normalizar/lowercasear el slug en ningún punto del pipeline, o se rompe la deduplicación y los links dejan de ser válidos.
- **Hallazgo no anticipado — texto de "banner" entre el título y la descripción:** al menos una ficha (AtuServicio.uy) mostraba un aviso tipo "Extensión de plazo..." entre el `<h1>` y el bloque "Acerca de este proceso". No afecta directamente a los 7 campos obligatorios, pero es una trampa a tener en cuenta si en algún momento se decide extraer texto "del primer párrafo después del título" para algo.

---

## Fase 1 — Estructura del proyecto

**Objetivo:** dejar el esqueleto de carpetas/archivos antes de meter lógica.

- [ ] Crear estructura:
  ```
  proyecto/
  ├── main.py
  ├── crawler.py
  ├── parser.py
  ├── models.py
  ├── utils/
  │   └── dates.py
  ├── tests/
  │   ├── fixtures/
  │   └── test_parser.py
  ├── output.json          (se genera, no se escribe a mano)
  └── README.md
  ```
- [ ] Definir `models.py`: dataclass o pydantic model con los 7 campos obligatorios + `componentes` opcional. Decidir y poder justificar la elección.
- [ ] Elegir librería HTTP (`httpx` o `requests`) y librería de parseo HTML (`beautifulsoup4` o `lxml` / `selectolax`).

**Criterio de cierre:** carpetas creadas, dependencias decididas, `models.py` con los tipos definidos (aunque el resto esté vacío).

### 1.4 Auditoría de arquitectura (modularidad, robustez, escalabilidad, legibilidad)

> Revisión hecha sobre la estructura de 1.1-1.3: cumple con los requisitos literales de la consigna (main.py + módulos separados), pero se detectaron puntos de mejora para que el proyecto sea más fácil de explicar en la sustentación y menos propenso a archivos que "hacen de todo un poco". Se deja como **extensión** de la estructura base, no como reemplazo — el árbol de 1.1 sigue siendo válido, esto lo detalla más.

**Árbol de carpetas extendido (sugerido):**
```
proyecto/
├── main.py                    # CLI: parsea args, orquesta, sin lógica de negocio propia
├── config.py                  # Constantes centralizadas (URLs, timeouts, límites, selectores CSS)
├── crawler.py                 # Orquestación: listado, paginación, iteración de slugs
├── parser.py                  # Extracción de campos desde HTML de una ficha (sin I/O de red)
├── models.py                  # Dataclass/Pydantic + serialización a dict/JSON
├── output.py                  # Escritura del JSON final (aísla el "sink" de datos)
├── utils/
│   ├── http_client.py         # Sesión HTTP, reintentos, backoff, delay (reutilizable)
│   ├── dates.py                # Parseo de fechas es-UY
│   ├── text.py                  # Truncado de nombre_corto, normalización de espacios
│   └── logging_config.py         # Configuración centralizada del logger
├── tests/
│   ├── fixtures/
│   └── test_parser.py
├── output.json
└── README.md
```

**Checklist de refinamiento (no obligatorio por la letra de la consigna, pero recomendado):**
- [ ] `config.py`: mover ahí todos los valores "mágicos" — `per_page=100`, cantidad de reintentos, factor de backoff, delay entre requests, el límite de 80 chars de `nombre_corto`, el selector `.participatory-space__nav-item`, el texto "Grupo promotor". Responde directamente al criterio de evaluación "ausencia de valores mágicos sin explicación".
- [ ] `utils/http_client.py`: extraer ahí la sesión HTTP con reintentos/backoff/delay, separada de la orquestación. `crawler.py` debería *llamar* a este cliente, no implementar reintentos inline.
- [ ] `parser.py` sin I/O: la función de parseo recibe un string de HTML y devuelve un dict/modelo — nunca hace un request por su cuenta. Esto es justamente lo que permite testear contra el fixture local sin red (Fase 2); conviene dejarlo como regla explícita de diseño, no solo como consecuencia accidental.
- [ ] `utils/text.py`: extraer la lógica de truncado de `nombre_corto` (corte en palabra completa, normalización de espacios múltiples, agregado de "…") como función pura y testeable, en vez de dejarla inline dentro de `parser.py`.
- [ ] Patrón "un registro a la vez": en `crawler.py`, aislar una función tipo `build_proceso(slug: str) -> Proceso | None` que hace fetch + parse + manejo de excepción para un solo proceso. El loop principal solo itera sobre slugs y llama a esa función — así el `try/except` amplio vive en un único lugar bien delimitado, no disperso por el archivo.
- [ ] `output.py` (o una función equivalente en `main.py`): aislar la escritura del JSON final en una función propia, para que sea trivial cambiar el destino en el futuro (ej. a una base de datos, según la pregunta de diseño de la Fase 7) sin tocar el resto del pipeline.
- [ ] Logging centralizado: configurar el logger una sola vez (ej. al arrancar `main.py`, o en `utils/logging_config.py`), y que cada módulo solo haga `logging.getLogger(__name__)` — evitar múltiples `logging.basicConfig()` dispersos.
- [ ] `models.py`: agregar un método de serialización propio (ej. `to_dict()`, o `dataclasses.asdict()` con manejo explícito de `None`) para que la conversión a JSON no dependa de lógica ad hoc en `main.py`.

**Por qué importa esto para la sustentación:** la consigna evalúa explícitamente "organización, nombres claros, ausencia de valores mágicos sin explicación". Esta separación adicional no es obligatoria por la letra de la consigna, pero permite explicar cada pieza de forma aislada ("esto es el cliente HTTP", "esto es el parser", "esto es la orquestación") en vez de tener que justificar un `crawler.py` que mezcla red, reintentos y lógica de negocio.

**Criterio de cierre de 1.4:** cada punto de la checklist tiene un lugar claro en el árbol de archivos antes de empezar a escribir lógica real (Fase 2 en adelante).

---

## Fase 2 — Parser (contra el fixture local, sin red)

**Objetivo:** que toda la lógica de extracción de una ficha funcione de forma aislada y testeable, antes de tocar red.

> Nota de arquitectura (ver 1.4): al implementar esta fase, `parser.py` no debe hacer ningún request — solo recibe HTML como string. La lógica de truncado de `nombre_corto` conviene extraerla a `utils/text.py` en vez de dejarla inline acá.

### 2.1 Extracción de campos
- [ ] `slug` desde la URL.
- [ ] `nombre_largo` desde `<h1>` / `og:title`.
- [ ] `nombre_corto` aplicando la regla fijada en 0.2.
- [ ] `fecha_inicio` / `fecha_fin`: parseo del string combinado usando `utils/dates.py`.
- [ ] `entidad` desde el bloque "Grupo promotor".
- [ ] `descripcion_url` = URL de la ficha.
- [ ] `formulario_url` = primer `.participatory-space__nav-item`.
- [ ] (Opcional) `componentes` = lista completa de esos enlaces.

### 2.2 utils/dates.py
- [ ] Diccionario manual de meses es-UY abreviados.
- [ ] Función que reciba el string crudo y devuelva `(fecha_inicio, fecha_fin)` en formato `YYYY-MM-DD` o `None`.
- [ ] Manejar casos: string ausente, solo una fecha, formato inesperado (no debe romper, debe loguear y devolver `None`).

### 2.3 Test unitario
- [ ] 1-2 tests sobre el fixture HTML guardado en 0.3, verificando los 7 campos obligatorios.
- [ ] Al menos un test de `utils/dates.py` con casos borde (fecha completa, fecha ausente, formato raro).

**Criterio de cierre:** `pytest` corre en verde contra el fixture local, sin necesidad de red.

---

## Fase 3 — Crawler (listado + red)

**Objetivo:** recorrer el listado paginado y obtener el HTML de cada ficha, con resiliencia.

> Nota de arquitectura (ver 1.4): conviene que los reintentos/backoff/delay vivan en `utils/http_client.py`, no inline en `crawler.py`. El manejo de errores por proceso individual encaja bien en una función `build_proceso(slug)` separada del loop principal, y todos los valores de configuración (per_page, cantidad de reintentos, delay) deberían salir de `config.py`, no quedar como números sueltos.

- [ ] Función para pedir `/processes?filter[with_date]={state}&page=N` y extraer los slugs listados.
- [ ] Paginación: seguir incrementando `page` hasta juntar el `--limit` pedido o hasta que la página no devuelva más resultados.
- [ ] Deduplicación por `slug` (definir en qué punto exacto: ¿al armar la lista de slugs, o sobre el resultado final? — elegir uno y ser consistente).
- [ ] Fetch de cada ficha individual (`/processes/{slug}`).
- [ ] Reintentos con backoff ante timeout/5xx (definir cantidad de intentos y estrategia: exponencial recomendado).
- [ ] Delay entre requests (valor razonable, ej. 0.3-0.5s, justificable como buena práctica, no por anti-bot).
- [ ] Manejo de errores por comportamiento: `try/except Exception` amplio *dentro del loop por proceso*, logueando slug + URL + excepción, sin tumbar la corrida completa.
- [ ] Logging configurado (INFO para progreso, WARNING/ERROR para fallos individuales).

**Criterio de cierre:** correr el crawler contra el sitio real trae ≥30 slugs únicos y sus HTMLs sin que un fallo puntual rompa la corrida.

---

## Fase 4 — CLI (main.py)

**Objetivo:** exponer todo lo anterior de forma ejecutable y evaluable sin intervención manual.

> Nota de arquitectura (ver 1.4): `main.py` debería quedar delgado — parsea argumentos y orquesta llamadas a `crawler`, `parser` y `output.py`, sin lógica de negocio propia. La escritura del JSON final conviene aislarla en `output.py` (o una función dedicada) en vez de mezclarla con el parseo de argumentos.

- [ ] `--limit N` (tope de procesos procesados).
- [ ] `--state {all,active,past,upcoming}` mapeado a `filter[with_date]`.
- [ ] Modo que solo imprima/guarde el JSON localmente (esta es la única forma de ejecución que van a correr).
- [ ] Comando de referencia a documentar: `python main.py --state all --limit 30`.
- [ ] Type hints en las funciones públicas de `main.py`, `crawler.py`, `parser.py`.
- [ ] Uso de `pathlib.Path` para cualquier ruta de archivo (fixture, output.json, etc.).

**Criterio de cierre:** correr el comando documentado desde cero genera `output.json` con ≥30 procesos reales, sin tocar nada a mano.

---

## Fase 5 — Validación de calidad de datos

**Objetivo:** revisar el `output.json` generado con ojo de evaluador, no de desarrollador.

- [ ] ≥30 procesos en total.
- [ ] Sin slugs duplicados.
- [ ] Los 7 campos obligatorios presentes en cada registro (con `null` donde corresponde, nunca `""` ni ausentes del dict).
- [ ] Fechas en formato `YYYY-MM-DD` o `null`, nunca el string crudo original.
- [ ] `descripcion_url` y `formulario_url` son URLs reales y navegables (probar 2-3 al azar abriéndolas).
- [ ] Revisar manualmente 2-3 registros con `entidad: null` o `fecha_inicio: null` para confirmar que son casos reales y no bugs de parseo.

**Criterio de cierre:** `output.json` pasa todos los checks de arriba.

---

## Fase 6 — README.md

**Objetivo:** documentar de forma que se note el criterio de mapeo, que es lo que más pesa en la evaluación.

- [ ] Instrucciones de cómo correr el CLI (3-4 líneas de prosa + comandos de ejemplo).
- [ ] Sección **"Decisiones y supuestos"** (3-5 bullets, la parte que más importa):
  - [ ] Qué se hizo con `nombre_corto` y por qué.
  - [ ] Cómo se parsean las fechas y qué pasa en los casos ausentes/parciales.
  - [ ] Cómo se maneja `entidad` ausente.
  - [ ] Criterio para `formulario_url` cuando hay múltiples componentes.
  - [ ] (Opcional) Cualquier vía alternativa evaluada y descartada (open data, API GraphQL) con la razón concreta.
- [ ] Sección breve de arquitectura (qué hace cada módulo).

**Criterio de cierre:** alguien que no vio el código puede correr el CLI y entender las decisiones de mapeo solo leyendo el README.

---

## Fase 7 — Pregunta de diseño (incremental/idempotente)

**Objetivo:** respuesta escrita de 5-8 líneas, preparada con tiempo, no al final corriendo con el reloj.

- [ ] Mencionar `slug` como clave natural de upsert (INSERT ... ON CONFLICT / MERGE).
- [ ] Mencionar detección de cambios (hash de contenido o `updated_at`) para no reprocesar si no cambió nada.
- [ ] Mencionar que el sitio no expone `sort=updated_at`, así que sin eso hay que traer el listado completo igual y comparar en destino.
- [ ] Mencionar idempotencia ante fallos a mitad de corrida (reintentar sin duplicar).

**Criterio de cierre:** párrafo de 5-8 líneas listo, sin necesidad de improvisar en la sustentación.

---

## Fase 8 — Repaso pre-sustentación

**Objetivo:** poder defender cada decisión sin mirar el código.

- [ ] Explicar por qué scraping y no API/open data (el descarte, no solo "porque lo decía la consigna").
- [ ] Explicar dónde y cómo se hace la deduplicación por slug.
- [ ] Explicar la regla de truncado de `nombre_corto` y sus límites.
- [ ] Explicar el diseño de retries/backoff (cuántos intentos, estrategia, timeout).
- [ ] Explicar por qué el `except Exception` amplio dentro del loop es aceptable acá y en qué otro contexto no lo sería.
- [ ] Tener clara la respuesta de la Fase 7 sin leerla.

---

## Prioridad relativa (si el tiempo aprieta)

1. **Innegociable:** CLI funcional que genere ≥30 procesos con los 7 campos obligatorios y su contrato de nulos correcto.
2. **Muy importante:** sección "Decisiones y supuestos" del README — es lo que la consigna dice explícitamente que más pesa.
3. **Importante:** manejo de errores por comportamiento + logging + retries.
4. **Importante:** tests unitarios del parser (aunque sean solo 1-2).
5. **Deseable:** campo opcional `componentes`.
6. **Deseable pero preparado igual:** respuesta a la pregunta de diseño.
