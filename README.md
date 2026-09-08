# ETL — Procesos Participativos de Uruguay

Extrae los procesos participativos publicados en la [Plataforma de Participación Ciudadana Digital](https://plataformaparticipacionciudadana.gub.uy/processes) (Presidencia/AGESIC, sobre Decidim) y los vuelca a un JSON local, sin intervención manual.

## Cómo correr

```bash
pip install -r requirements.txt
python main.py --state all --limit 30
```

Genera `output.json` en la raíz del proyecto con la lista de procesos. `--state` filtra por `{all,active,past,upcoming}` (mapea a `filter[with_date]` del sitio) y `--limit` acota la cantidad de procesos procesados; sin `--limit` trae todos los que haya. `--output` permite cambiar la ruta del JSON de salida.

```bash
python main.py --state active           # solo procesos activos, sin límite
python main.py --state all --limit 30 --output tmp/procesos.json
```

Correr los tests (no requieren red, usan fixtures locales):

```bash
pytest tests/ -v
```

## Decisiones y supuestos

Esta sección resume las decisiones de mapeo más relevantes. El detalle completo — con los conteos exactos sobre las 86 fichas reales que sustentan cada una — está en [documentation.md](documentation.md).

- **`nombre_corto`:** el título no tiene un subtítulo corto y consistente que sirva como fuente alternativa (existe un elemento de "bajada" bajo el título, pero es texto libre que a veces es un hashtag de campaña o un eslogan genérico — no una versión corta del nombre; se documenta en `documentation.md` por qué se descartó como fuente). Se trunca `nombre_largo` a 80 caracteres, cortando en el último espacio completo (nunca a mitad de palabra) y agregando "…" cuando hubo corte. Validado con un caso real de 274 caracteres.
- **Fechas:** se parsean del string `"DD mon YYYY / DD mon YYYY"` (meses abreviados en español) con un diccionario manual, sin depender de `locale` del sistema. **~16% de los procesos reales (14 de 86) no tienen bloque de fechas en el HTML** — no es un caso teórico: son procesos con una plantilla distinta (fases con fechas propias en vez de un rango único). En esos casos `fecha_inicio`/`fecha_fin` quedan en `null`, nunca string vacío.
- **`entidad` (Grupo promotor):** fuente primaria es el bloque `"Grupo promotor"`, ausente en ~27% de los procesos reales (23 de 86). En esos casos hay fallback a la bajada del título (`hero-slogan`), donde la entidad promotora también se muestra en pantalla aunque no esté en el bloque estructurado — bug real encontrado por inspección manual y corregido (ver Fase 5.1 en `documentation.md`). Con el fallback, `entidad` queda en `null` solo si ninguna de las dos fuentes existe, algo que no se observó en ninguna de las 86 fichas reales.
- **`formulario_url` con múltiples componentes:** se toma el primer enlace `.participatory-space__nav-item` del DOM (60 de 86 procesos tienen más de uno, hasta 7 en un caso). Se asume que el orden del DOM refleja el orden de prioridad definido al armar el proceso — no hay forma de confirmar esto desde afuera del admin de Decidim, queda documentado como supuesto. El campo opcional `componentes` guarda la lista completa para no perder el resto.
- **Vía alternativa descartada — API/open data:** el sitio expone descarga de datos abiertos (`/open-data/download`), pero no se usó: la consigna pide explícitamente el flujo de scraping sobre las fichas HTML, y el dataset abierto no necesariamente expone los mismos 7 campos con el mismo criterio de mapeo (título corto, `formulario_url` por componente) que se pide acá.
- **Slugs con mayúscula:** el sitio real tiene slugs no-lowercase (`Homicidios`, `Consulta65`...`Consulta70`, `quinto-planGA`). No se normalizan en ningún punto del pipeline — lowercasearlos rompería la URL real y la deduplicación.

## Arquitectura

```
main.py               CLI: parsea args, orquesta crawler -> output. Sin lógica propia.
config.py              Constantes: URLs, selectores CSS, timeouts, límites, etiquetas.
crawler.py             Listado paginado, extracción de slugs, build_proceso() por slug.
parser.py               Extracción de campos desde HTML de una ficha. Sin I/O de red.
models.py                Proceso / Componente (pydantic) + serialización a dict/JSON.
output.py                 Escritura del JSON final.
utils/http_client.py       Sesión HTTP, reintentos con backoff exponencial, delay entre requests.
utils/dates.py               Parseo de fechas es-UY (diccionario manual de meses).
utils/text.py                 Extracción/normalización de texto (separador entre nodos) y truncado de nombre_corto.
utils/logging_config.py        Configuración centralizada del logger.
tests/                           Tests del parser contra fixtures HTML reales.
```

`parser.py` nunca hace requests — recibe HTML como string (más `slug` y `url`, que el crawler ya conoce) y devuelve un `Proceso`. Eso es lo que permite testear contra fixtures locales en `tests/fixtures/` sin depender de la red. Los reintentos y el delay entre requests viven en `utils/http_client.py`, separados de la orquestación en `crawler.py`; el manejo de errores por proceso individual está aislado en `crawler.build_proceso()`, así el único `try/except Exception` amplio del proyecto vive en un solo lugar bien delimitado y logueado (slug + URL + excepción), sin tumbar la corrida completa ante un fallo puntual.

## Pregunta de diseño — ETL incremental/idempotente

Ver sección "Fase 7" en [documentation.md](documentation.md).
