# CoffeCrop — Tareas: Base de Conocimiento Cafetero

> Descomposición atómica basada en `plan.md` y `spec.md` (en esta carpeta). Orden: Infraestructura → Texto (código puro, sin base ni modelo) → Embeddings → Base de datos y casos de uso → Corrida real y calibración → Cierre. Cada tarea se ejecuta, se audita contra `constitution.md` y `spec.md`, y se acepta o rechaza antes de pasar a la siguiente.

## Convenciones de ejecución
- **Rama y PR por tarea:** `tipo/task-NN-descripcion-corta` desde un `main` actualizado; el humano crea y mergea el PR (ver "Flujo de Git y Pull Requests" en `constitution.md`).
- **Código en `backend/`** (Python). Entorno virtual en `backend/.venv` (ya ignorado por git). Comandos desde `backend/`: `pytest` (unitarias), `pytest -m integration` (necesitan el PostgreSQL de Docker encendido), `pytest -m modelo` (descargan el modelo real; no corren por defecto).
- **Definición de Hecho** de `constitution.md`, adaptada a Python: criterios de la tarea cumplidos, `pytest` en verde sin avisos, pruebas de la lógica nueva, sin secretos ni dependencias no aprobadas (las aprobadas están en `plan.md` §2), `progress.md` actualizado. Verificación visual no aplica (no hay UI).
- **Trazabilidad:** cada tarea cita las US/BR/DEC de `spec.md` que implementa.
- **Tareas hechas por el humano:** la Tarea 18 (preguntas de prueba) la redacta el usuario; se puede hacer en paralelo desde ya.

## Fase: Infraestructura

### Tarea 1: Proyecto Python, configuración y errores
**Descripción:** Crear el proyecto `backend/` con `pyproject.toml` (dependencias aprobadas y configuración de pytest con los marcadores `integration` y `modelo`), el paquete `conocimiento`, la lectura de configuración por variables de entorno y las excepciones tipadas. Crear además `specs/base-conocimiento/progress.md`.
**Archivos:** `backend/pyproject.toml`, `backend/src/conocimiento/__init__.py`, `backend/src/conocimiento/config.py`, `backend/src/conocimiento/errores.py`, `backend/tests/test_config.py` (+ `specs/base-conocimiento/progress.md`)
**Criterios de Aceptación:**
- [ ] `python -m venv .venv` + `pip install -e ".[dev]"` funciona en Python 3.14 y `pytest` corre.
- [ ] `config.py` expone (con valores por defecto salvo secretos): `DATABASE_URL`, `PDFTOTEXT_BIN`, `CARPETA_BASE_CONOCIMIENTO`, `MODELO_EMBEDDINGS`, `MINIMO_SIMILITUD`, `VENTAJA_BOYACA`; nada con secretos reales en el código.
- [ ] `errores.py` define `InvalidQueryError`, `NoEmbeddingsForModelError`, `DatabaseUnavailableError` con los códigos `INVALID_QUERY`, `NO_EMBEDDINGS_FOR_MODEL`, `DB_UNAVAILABLE`.
- [ ] Prueba: variables de entorno sobrescriben los valores por defecto.
**Tiempo estimado:** 40 min
**Dependencias:** Ninguna

### Tarea 2: PostgreSQL + pgvector local con Docker
**Descripción:** Levantar la base de datos local según `plan.md` §6.8.
**Archivos:** `backend/docker-compose.yml`, `backend/.env.example`, `.gitignore` (agregar `backend/.env`)
**Criterios de Aceptación:**
- [ ] `docker compose up -d` deja el servicio `db` sano (healthcheck) con la imagen `pgvector/pgvector:pg16`, publicado solo en `127.0.0.1:5433`.
- [ ] Usuario, clave y base salen de `backend/.env`; `.env.example` trae solo valores de ejemplo y `backend/.env` queda ignorado por git.
- [ ] Los datos sobreviven a `docker compose down` + `up` (volumen con nombre).
- [ ] Se puede ejecutar `CREATE EXTENSION vector;` y `SELECT '[1,2,3]'::vector;` con `psql` dentro del contenedor.
**Tiempo estimado:** 25 min
**Dependencias:** Ninguna

### Tarea 3: Esquema de base de datos y conexión
**Descripción:** Crear el esquema de `plan.md` §5 y el módulo de conexión, con la función de inicialización y la infraestructura de pruebas de integración.
**Archivos:** `backend/src/conocimiento/db/esquema.sql`, `backend/src/conocimiento/db/conexion.py`, `backend/tests/conftest.py`, `backend/tests/test_esquema.py`
**Criterios de Aceptación:**
- [ ] `inicializar_db()` crea la extensión y las tablas `documento`, `fragmento`, `embedding`, `configuracion` y es idempotente (se puede correr dos veces).
- [ ] Si la base no responde, la conexión lanza `DatabaseUnavailableError` (`DB_UNAVAILABLE`) con mensaje claro.
- [ ] `conftest.py` ofrece una base de datos de prueba aislada (se crea y se borra por sesión de pruebas) para las pruebas `integration`.
- [ ] Pruebas de integración: tablas creadas; `ON DELETE CASCADE` borra fragmentos y vectores al borrar un documento; la restricción de categoría rechaza valores distintos de A/B/R/C.
**Tiempo estimado:** 45 min
**Dependencias:** Tareas 1, 2

## Fase: Texto (código puro)

### Tarea 4: Extracción de texto de PDFs
**Descripción:** Llamar a `pdftotext` como proceso aparte y devolver el texto por página, más utilidades de huella y texto legible (`plan.md` §6.1).
**Archivos:** `backend/src/conocimiento/extraccion/pdf.py`, `backend/tests/test_extraccion_pdf.py`
**Criterios de Aceptación:**
- [ ] `extraer_paginas(ruta)` devuelve una lista de textos, uno por página, con el número de página = posición + 1.
- [ ] `sha256_archivo(ruta)` devuelve la huella del contenido.
- [ ] `tiene_texto_legible(paginas)` es falso con menos de 1.500 caracteres en total (BR-002).
- [ ] Si `pdftotext` no existe o falla, lanza un error claro que menciona `PDFTOTEXT_BIN`.
- [ ] Pruebas con la salida de `pdftotext` simulada (sin depender de PDFs reales) y una prueba opcional con un PDF real marcada `docs`, que se omite si la carpeta no está.
**Tiempo estimado:** 35 min
**Dependencias:** Tarea 1
**Referencias:** US-001, BR-002

### Tarea 5: Limpieza — encabezados repetidos y texto corrido
**Descripción:** Primera parte de `limpieza.py` (`plan.md` §6.2, puntos 1 y 4).
**Archivos:** `backend/src/conocimiento/extraccion/limpieza.py`, `backend/tests/test_limpieza.py`
**Criterios de Aceptación:**
- [ ] Elimina las líneas de ≤ 80 caracteres que se repiten en ≥ 40 % de las páginas, solo en documentos de ≥ 4 páginas (ej. "cafetero colombiano").
- [ ] No toca documentos de menos de 4 páginas ni líneas de contenido que aparecen una o dos veces.
- [ ] Une las líneas de un mismo párrafo, normaliza espacios y ligaduras, y descarta líneas sueltas de ≤ 3 caracteres.
- [ ] Conserva los números de página (la salida sigue siendo una lista por página).
- [ ] Pruebas con textos de ejemplo (AAA), incluyendo un caso con encabezado repetido y otro con texto que no debe tocarse.
**Tiempo estimado:** 40 min
**Dependencias:** Tarea 4
**Referencias:** US-001

### Tarea 6: Limpieza — portada administrativa y bibliografía
**Descripción:** Segunda parte de `limpieza.py` (`plan.md` §6.2, puntos 2 y 3), solo para Avances.
**Archivos:** `backend/src/conocimiento/extraccion/limpieza.py`, `backend/tests/test_limpieza.py`
**Criterios de Aceptación:**
- [ ] Elimina por patrones las líneas de autores/ORCID, DOI, ISSN, "Los trabajos suscritos…", edición, fotografías, diagramación, imprenta, dirección y teléfono; conserva el título y el cuerpo.
- [ ] Descarta el texto desde el encabezado "Literatura citada" (en cualquier combinación de mayúsculas) hasta el final, solo en Avances.
- [ ] En el Manual (tipo `manual`) no se aplica ninguna de las dos reglas.
- [ ] Pruebas con un extracto real de portada (texto público de un Avance) y un caso de bibliografía.
**Tiempo estimado:** 35 min
**Dependencias:** Tarea 5
**Referencias:** US-001

### Tarea 7: Fragmentación (núcleo)
**Descripción:** Dividir el texto limpio en fragmentos según BR-001 y DEC-009.
**Archivos:** `backend/src/conocimiento/fragmentacion.py`, `backend/tests/test_fragmentacion.py`
**Criterios de Aceptación:**
- [ ] `fragmentar(paginas, contar_tokens, max_tokens_modelo)` calcula el tamaño objetivo `min(600, max_tokens_modelo − 60)` y un solape ≈ 1/6 de ese tamaño.
- [ ] Corta solo en límites de oración (o de página); ningún fragmento supera el tamaño objetivo salvo que una sola oración ya lo supere (se registra una advertencia en ese caso).
- [ ] Cada fragmento trae `pagina_inicio` y `pagina_fin` correctas, `orden` consecutivo y `tokens`.
- [ ] Aplica el solape con las últimas oraciones del fragmento anterior; nunca mezcla textos de dos documentos (una llamada = un documento).
- [ ] Pruebas con un contador de tokens simulado (palabras): tamaño, solape, páginas, oraciones largas y documento de una sola página.
**Tiempo estimado:** 45 min
**Dependencias:** Tarea 5
**Referencias:** US-001, BR-001, DEC-009

### Tarea 8: Marcado de tablas y política por categoría
**Descripción:** Detectar fragmentos que son casi solo números y decidir cuáles conservar (`plan.md` §6.3).
**Archivos:** `backend/src/conocimiento/fragmentacion.py`, `backend/tests/test_fragmentacion.py`
**Criterios de Aceptación:**
- [ ] `es_tabla(texto)` es verdadero si menos del 45 % de los caracteres no-espacio son letras.
- [ ] La función de filtrado conserva los fragmentos `es_tabla` solo de documentos de categoría A y descarta los de B, R y C; los fragmentos de prosa se conservan siempre.
- [ ] El filtrado informa cuántos fragmentos descartó (para el informe de ingesta).
- [ ] Pruebas con una tabla de calendario de siembra, un párrafo normal y el mismo contenido en categorías A y B.
**Tiempo estimado:** 25 min
**Dependencias:** Tarea 7
**Referencias:** BR-001, DEC-004

## Fase: Embeddings

### Tarea 9: Interfaz EmbeddingProvider y proveedor falso
**Descripción:** Definir el contrato del modelo (US-004) y un proveedor falso determinista para las pruebas (`plan.md` §3.1 y §7).
**Archivos:** `backend/src/conocimiento/embeddings/base.py`, `backend/tests/fakes.py`, `backend/tests/test_fakes.py`
**Criterios de Aceptación:**
- [ ] `EmbeddingProvider` (Protocol) declara `nombre_modelo`, `dimension`, `max_tokens`, `contar_tokens`, `embed_documents`, `embed_query`.
- [ ] `FakeEmbeddingProvider` genera vectores normalizados por bolsa de palabras con hashing: mismo texto → mismo vector; textos con palabras en común quedan más cerca que textos sin palabras en común.
- [ ] El proveedor falso permite configurar `nombre_modelo`, `dimension` y `max_tokens` (para probar el cambio de modelo y DEC-009).
- [ ] Pruebas que verifican determinismo y cercanía relativa.
**Tiempo estimado:** 30 min
**Dependencias:** Tarea 1
**Referencias:** US-004, BR-004

### Tarea 10: Proveedor local con sentence-transformers
**Descripción:** Implementar el proveedor real para la familia e5 y BGE-M3 (`plan.md` §3.2).
**Archivos:** `backend/src/conocimiento/embeddings/sentence_transformers.py`, `backend/tests/test_proveedor_real.py`
**Criterios de Aceptación:**
- [ ] Carga `intfloat/multilingual-e5-base`; expone `dimension` = 768 y `max_tokens` = 512 leídos del modelo (no escritos a mano).
- [ ] Añade el prefijo `passage: ` en `embed_documents` y `query: ` en `embed_query` para modelos e5, y ninguno para BGE-M3.
- [ ] `contar_tokens` usa el tokenizador del modelo; los vectores salen normalizados.
- [ ] Procesa en lotes configurables (por defecto 16) y no recarga el modelo en cada llamada.
- [ ] Prueba `modelo` (opcional, descarga ~1 GB la primera vez): "hongo de la hoja del cafeto" queda más cerca de un pasaje sobre roya que de uno sobre secado del grano.
- [ ] Se anota en `progress.md` cuánto tardó la descarga y el tamaño en disco.
**Tiempo estimado:** 45 min (más la descarga)
**Dependencias:** Tarea 9
**Referencias:** US-004, DEC-002

## Fase: Base de datos y casos de uso

### Tarea 11: Repositorio — escritura
**Descripción:** Capa única con SQL para guardar y reemplazar documentos, fragmentos y vectores (`plan.md` §4 y §6.4).
**Archivos:** `backend/src/conocimiento/db/repositorio.py`, `backend/tests/test_repositorio.py`
**Criterios de Aceptación:**
- [ ] Operaciones: buscar documento por nombre, crear/reemplazar documento (borra el anterior en cascada), guardar fragmentos, guardar embeddings por modelo, leer/escribir `configuracion` (`modelo_activo`), contar embeddings por modelo.
- [ ] Guardar un fragmento sin documento, página o categoría falla antes de llegar a la base (BR-006).
- [ ] Todo el trabajo de un documento ocurre dentro de una transacción: si falla a mitad, no queda nada a medias.
- [ ] Pruebas de integración de cada operación, incluida la transacción que se revierte.
**Tiempo estimado:** 45 min
**Dependencias:** Tarea 3
**Referencias:** US-001, BR-003, BR-006

### Tarea 12: Ingesta de un documento
**Descripción:** Caso de uso que procesa un PDF de punta a punta (`plan.md` §6.4, pasos 1–4).
**Archivos:** `backend/src/conocimiento/ingesta.py`, `backend/tests/test_ingesta.py`
**Criterios de Aceptación:**
- [ ] `ingestar_documento(ruta, categoria, tipo, proveedor, extractor)` extrae → limpia → fragmenta → filtra tablas → vectoriza en lotes → guarda; el extractor se inyecta para poder probar sin PDFs reales.
- [ ] Un documento sin texto legible se guarda como `sin_texto` y no crea fragmentos (BR-002).
- [ ] Mismo hash y ya indexado con el modelo activo → omite; mismo hash sin vectores del modelo activo → solo vectoriza; hash distinto → reemplaza (BR-003).
- [ ] Si algo falla se marca `error`, se informa el motivo y no se propaga al resto.
- [ ] Devuelve un resultado con estado, fragmentos creados, fragmentos descartados y tiempo.
- [ ] Pruebas de integración con el proveedor falso: ingesta nueva, repetida (no duplica), cambiada (reemplaza), sin texto y con error simulado.
**Tiempo estimado:** 45 min
**Dependencias:** Tareas 6, 8, 9, 11
**Referencias:** US-001, BR-002, BR-003, BR-006

### Tarea 13: Ingesta de la carpeta y comandos de CLI
**Descripción:** Leer `_manifiesto.csv`, procesar todos los documentos, imprimir el informe y exponer los primeros comandos.
**Archivos:** `backend/src/conocimiento/ingesta.py`, `backend/src/conocimiento/cli.py`, `backend/src/conocimiento/__main__.py`, `backend/tests/test_ingesta_carpeta.py`
**Criterios de Aceptación:**
- [ ] `ingestar_carpeta(carpeta, proveedor)` lee el manifiesto (archivo, categoría, carpeta de origen), deduce `tipo` y `numero_avance` del nombre y procesa cada PDF; un fallo no detiene a los demás.
- [ ] Un archivo listado en el manifiesto que no existe en disco se informa como error, no rompe la ejecución.
- [ ] El informe final lista documentos indexados, omitidos (con motivo), con error, fragmentos creados y descartados, y tiempo total.
- [ ] Comandos: `python -m conocimiento inicializar-db` y `python -m conocimiento ingestar [--carpeta RUTA]`.
- [ ] Pruebas de integración con una carpeta temporal, un manifiesto de 3 filas, el extractor simulado y el proveedor falso (incluye re-ejecución sin duplicados).
**Tiempo estimado:** 45 min
**Dependencias:** Tarea 12
**Referencias:** US-001, BR-003

### Tarea 14: Búsqueda por significado
**Descripción:** Caso de uso `buscar` con puntaje mínimo y ventaja de Boyacá (`plan.md` §6.5).
**Archivos:** `backend/src/conocimiento/busqueda.py`, `backend/src/conocimiento/db/repositorio.py`, `backend/tests/test_busqueda.py`
**Criterios de Aceptación:**
- [ ] `buscar(pregunta, k=5, region=None)` vectoriza con el modelo activo, consulta con la SQL de `plan.md` §6.5 y devuelve `Resultado(texto, documento, pagina_inicio, pagina_fin, categoria, puntaje)` de mayor a menor relevancia.
- [ ] Pregunta vacía o de más de 1.000 caracteres → `InvalidQueryError`.
- [ ] Sin vectores del modelo activo → `NoEmbeddingsForModelError`; nunca se comparan vectores de modelos distintos (BR-004).
- [ ] El puntaje mínimo se aplica a la similitud real; con nada por encima devuelve lista vacía (BR-007).
- [ ] La ventaja de Boyacá solo se aplica con `region="boyaca"` y solo a categoría A, y solo para ordenar (BR-005).
- [ ] Pruebas de integración con proveedor falso y vectores armados a mano: orden, `k`, mínimo, ventaja con y sin región, modelos mezclados.
**Tiempo estimado:** 45 min
**Dependencias:** Tareas 9, 11
**Referencias:** US-002, US-003, BR-004, BR-005, BR-007

### Tarea 15: Reindexar y cambiar el modelo activo
**Descripción:** Permitir migrar a otro modelo sin rehacer nada (US-004).
**Archivos:** `backend/src/conocimiento/ingesta.py`, `backend/src/conocimiento/cli.py`, `backend/tests/test_reindexar.py`
**Criterios de Aceptación:**
- [ ] `reindexar(proveedor)` vectoriza todos los fragmentos existentes con el modelo nuevo y guarda un vector adicional por fragmento, sin tocar los del modelo anterior.
- [ ] `activar_modelo(nombre)` cambia `modelo_activo` solo si ya existen vectores de ese modelo; si no, lanza `NoEmbeddingsForModelError`.
- [ ] Entre `reindexar` y `activar_modelo`, `buscar` sigue usando el modelo anterior; después, el nuevo.
- [ ] Comandos `reindexar --modelo X` y `activar-modelo X`.
- [ ] Pruebas de integración con dos proveedores falsos de distinta dimensión (768 y 1024 simulados con valores pequeños).
**Tiempo estimado:** 40 min
**Dependencias:** Tareas 13, 14
**Referencias:** US-004, BR-004

### Tarea 16: Evaluación de calidad y comandos de búsqueda
**Descripción:** Medir la recuperación con las preguntas de prueba y exponer `buscar` y `evaluar` por línea de comandos.
**Archivos:** `backend/src/conocimiento/evaluacion.py`, `backend/src/conocimiento/cli.py`, `backend/tests/test_evaluacion.py`
**Criterios de Aceptación:**
- [ ] `evaluar(archivo_csv, k=5)` lee `pregunta` y `documentos_esperados` (separados por `;`), y calcula el porcentaje de preguntas con algún documento esperado entre los `k` primeros resultados.
- [ ] El informe lista las preguntas que fallaron con lo que se esperaba y lo que se obtuvo; un documento esperado que no existe en la base se avisa como error del archivo de preguntas.
- [ ] Comandos `buscar "pregunta" [--region boyaca] [-k 5]` (muestra texto, documento, páginas, categoría, puntaje) y `evaluar [--archivo RUTA]`.
- [ ] Pruebas con proveedor falso y un CSV de ejemplo (aciertos, fallos y documento inexistente).
**Tiempo estimado:** 40 min
**Dependencias:** Tarea 14
**Referencias:** US-002, US-005

## Fase: Corrida real y calibración

### Tarea 17: Primera ingesta real
**Descripción:** Indexar los 322 PDFs reales con `multilingual-e5-base` y revisar la calidad de lo que quedó guardado.
**Archivos:** `specs/base-conocimiento/progress.md` (y ajustes puntuales a `limpieza.py`/`fragmentacion.py` con sus pruebas si la revisión los exige)
**Criterios de Aceptación:**
- [ ] La ingesta termina sin detenerse; el informe muestra los 322 documentos como indexados, `sin_texto` o con error, ninguno perdido sin aviso.
- [ ] Se registra en `progress.md`: tiempo total, fragmentos creados, fragmentos de tabla descartados y documentos omitidos con motivo.
- [ ] Revisión manual de 15 fragmentos tomados al azar (con el usuario): sin portadas ni encabezados repetidos, páginas correctas, oraciones completas.
- [ ] Una segunda ejecución inmediata no crea nada nuevo y termina en segundos (BR-003).
- [ ] Todo problema de limpieza encontrado se corrige con una prueba nueva o se anota como pendiente.
**Tiempo estimado:** 45 min de trabajo (más el tiempo de proceso de la máquina, a medir)
**Dependencias:** Tareas 10, 13
**Referencias:** US-001, métricas de éxito de `spec.md`

### Tarea 18: Preguntas de prueba (las escribe el usuario)
**Descripción:** Armar el conjunto de preguntas con el que se medirá la calidad. El agente ayuda a redactarlas y a localizar el documento esperado.
**Archivos:** `backend/evaluacion/preguntas.csv`
**Criterios de Aceptación:**
- [ ] Al menos 20 preguntas en español, escritas como las haría un caficultor (ej. "¿cómo controlo la broca a 1.600 metros?").
- [ ] Cada pregunta indica uno o más documentos donde está la respuesta (`documentos_esperados`), y todos existen en la base.
- [ ] Al menos 5 preguntas son específicas de Boyacá o de clima frío (para medir DEC-004) y al menos 3 tratan temas que **no** están en la base (para calibrar BR-007; el resultado esperado es lista vacía).
- [ ] Cubre varios temas: plagas, enfermedades, fertilización, suelos, beneficio/secado, siembra y renovación, variedades.
**Tiempo estimado:** 45 min (del usuario)
**Dependencias:** ninguna para redactar; Tarea 16 para validarlas contra la base. Se puede empezar ya.
**Referencias:** US-005

### Tarea 19: Evaluación comparativa y calibración
**Descripción:** Elegir el modelo y fijar los valores de puntaje mínimo y ventaja de Boyacá con datos, no a ojo.
**Archivos:** `specs/base-conocimiento/progress.md` y, según el resultado, `backend/.env.example` / `backend/src/conocimiento/config.py` (valores por defecto)
**Criterios de Aceptación:**
- [ ] Se ejecuta `evaluar` con `multilingual-e5-base`, `multilingual-e5-large` y `BAAI/bge-m3` (con `reindexar` + `activar-modelo` para cada uno) y se anota el porcentaje de aciertos y el tiempo de indexación de cada uno.
- [ ] Se elige el modelo activo con la mejor calidad que el equipo soporte; la decisión y los números quedan en `progress.md` y en el Decision Log de `spec.md`.
- [ ] Se fijan `MINIMO_SIMILITUD` (que las preguntas fuera de tema devuelvan lista vacía sin perder aciertos) y `VENTAJA_BOYACA` (que mejore las preguntas de Boyacá sin desplazar a las demás).
- [ ] Se prueba una variación del tamaño de fragmento y/o de la limpieza de bibliografía si los resultados lo sugieren, y se anota el efecto.
- [ ] Se compara contra la meta de ≥ 80 % de `spec.md`; si no se alcanza, se documentan los fallos y las causas probables como siguientes pasos.
**Tiempo estimado:** 45 min de trabajo (más descargas y re-indexaciones, a medir)
**Dependencias:** Tareas 15, 16, 17, 18
**Referencias:** US-003, US-005, BR-005, BR-007, DEC-002, DEC-004

## Fase: Cierre

### Tarea 20: Cierre de la feature
**Descripción:** Dejar la feature documentada, con las decisiones pendientes resueltas.
**Archivos:** `specs/base-conocimiento/progress.md`, `specs/base-conocimiento/spec.md`, `AGENTS.md`, `backend/README.md`
**Criterios de Aceptación:**
- [ ] `backend/README.md` explica en pocos pasos cómo levantar Docker, instalar, inicializar, ingerir, buscar y evaluar.
- [ ] Se confirman o ajustan con el usuario DEC-007 (citas) y DEC-008 (lista vacía) y quedan registradas en `spec.md`.
- [ ] `AGENTS.md`: Fase 3 actualizada (qué queda hecho, modelo elegido, estado del entorno con la base de conocimiento) y próximos pasos hacia el endpoint del asistente.
- [ ] `progress.md` lista todas las tareas como aceptadas, con un resumen de la feature, lecciones y gaps abiertos.
**Tiempo estimado:** 30 min
**Dependencias:** Tareas 1–19

---
**Total estimado:** ~13 horas de trabajo (20 tareas), más el tiempo de proceso de la máquina en las Tareas 10, 17 y 19 (descarga de modelos e indexación), que se mide en la primera corrida real. Las Tareas 4–8 (texto) y 9 (proveedor falso) no dependen de la base de datos y pueden avanzar mientras se prepara Docker; la Tarea 18 (preguntas) puede hacerse en paralelo desde ya.
