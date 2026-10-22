# CoffeCrop — Especificación: Base de Conocimiento Cafetero

> Primera feature de la Fase 3 (`AGENTS.md`). Convierte los documentos de Cenicafé ya descargados en una base **consultable por significado**: extrae su texto, lo divide en fragmentos, los vectoriza con un modelo local y los guarda en PostgreSQL + pgvector. Es la pieza que más adelante usará el asistente de IA (otra feature) para responder con información confiable y citable.

## 1. Overview
**Problem Statement:** El caficultor necesita consejos técnicos (roya, broca, fertilización, beneficio, etc.) pero la información está repartida en cientos de PDFs. Un asistente no puede "leerlos todos" en cada pregunta ni inventar respuestas: necesita encontrar rápidamente los pasajes relevantes y saber de qué documento y página salieron.

**Target Users:**
- **El asistente de IA / backend** (consumidor directo): pide los pasajes más relevantes para una pregunta en español.
- **El operador (el desarrollador)**: ejecuta la ingesta, cambia el modelo de vectorización y mide la calidad de las búsquedas.
- **El caficultor** (indirecto): recibe respuestas respaldadas por documentos de Cenicafé, con foco inicial en Boyacá.

**Success Metrics:**
- Los 322 PDFs de `docs/base_conocimiento/` quedan procesados: cada uno termina como indexado, o reportado como "sin texto" o "con error" — ninguno se pierde sin aviso.
- El 100 % de los fragmentos guardados conserva su documento, página y categoría.
- Calidad de recuperación medida: con un conjunto de preguntas de prueba escritas por el usuario (≥ 20), el documento esperado aparece entre los 5 primeros resultados en al menos el **80 %** de los casos (meta propuesta, a confirmar al ver los primeros resultados reales).
- Volver a correr la ingesta sin cambios en los PDFs no duplica nada y termina en segundos.
- Cambiar de modelo de vectorización no obliga a rediseñar nada, solo a re-indexar.

## 2. User Stories

### US-001: Ingerir los documentos
**Como** operador
**Quiero** ejecutar una ingesta sobre `docs/base_conocimiento/`
**Para** que todo el texto de los PDFs quede guardado como fragmentos buscables

**Criterios de Aceptación:**
- Lee la categoría de cada archivo (A, B, R, C) del manifiesto `_manifiesto.csv` de esa carpeta.
- Extrae el texto conservando el número de página de cada pasaje.
- Un PDF sin texto legible (BR-002) o que falla al leerse se reporta y se omite; no detiene al resto.
- Al terminar entrega un informe: documentos indexados, omitidos (con motivo), fragmentos creados y tiempo total.
- Volver a ejecutarla no duplica datos (BR-003).

### US-002: Buscar por significado
**Como** asistente de IA (backend)
**Quiero** enviar una pregunta en español y recibir los fragmentos más relevantes
**Para** responder basándome en los documentos y poder citarlos

**Criterios de Aceptación:**
- Devuelve los `k` fragmentos más similares (por defecto 5), ordenados de mayor a menor relevancia.
- Cada resultado incluye: texto, documento, página(s), categoría y puntaje de similitud.
- Encuentra pasajes por significado aunque no compartan palabras exactas con la pregunta (p. ej. "hongo de la hoja" → roya).
- Una pregunta vacía o excesivamente larga se rechaza con un error claro.
- Si ningún fragmento supera el mínimo de relevancia, devuelve una lista vacía (BR-007).

### US-003: Priorizar Boyacá
**Como** asistente de IA (backend)
**Quiero** indicar que la consulta es sobre Boyacá
**Para** que los documentos con información específica de Boyacá aparezcan primero

**Criterios de Aceptación:**
- Sin indicar región, el orden depende solo de la similitud.
- Indicando Boyacá, los fragmentos de categoría A suben de posición (BR-005).
- Cada resultado informa su categoría, para que se pueda explicar de dónde viene.

### US-004: Cambiar el modelo de vectorización
**Como** mantenedor
**Quiero** poder reemplazar el modelo local por otro (por ejemplo uno de pago)
**Para** mejorar la calidad en el futuro sin rehacer el resto del sistema

**Criterios de Aceptación:**
- El modelo se usa a través de una interfaz única; el resto del código no depende de uno en particular.
- Cada vector guardado registra con qué modelo y dimensión se generó (BR-004).
- Existe un comando para re-indexar todo con el modelo nuevo; mientras tanto la búsqueda sigue funcionando con el modelo anterior.
- La búsqueda nunca compara vectores de modelos distintos.

### US-005: Medir la calidad de la recuperación
**Como** operador
**Quiero** correr un conjunto de preguntas de prueba con sus documentos esperados
**Para** saber si la base responde bien y si un cambio (de modelo, de tamaño de fragmento) mejora o empeora

**Criterios de Aceptación:**
- El conjunto es un archivo editable de al menos 20 preguntas, cada una con el/los documento(s) esperado(s); las preguntas las redacta el usuario (conoce el dominio).
- El comando informa el porcentaje de preguntas cuyo documento esperado aparece entre los 5 primeros resultados, y lista las que fallaron.
- Se puede ejecutar antes y después de un cambio para comparar.

## 3. Business Rules

### BR-001: Tamaño y límites de los fragmentos
**Given** el texto de un documento
**When** se divide en fragmentos
**Then** cada fragmento tiene como máximo unos 600 tokens, y nunca más de lo que el modelo activo puede leer (menos un margen): el tamaño objetivo es el menor de los dos (DEC-009), con un solape de aproximadamente una sexta parte del tamaño con el fragmento anterior
**And** los tokens se cuentan con el tokenizador del propio modelo
**And** se corta en límites de párrafo o de página y nunca a mitad de una oración
**And** ningún fragmento mezcla texto de dos documentos
**And** cada fragmento guarda la página donde empieza y la página donde termina.

### BR-002: Solo documentos con texto legible
**Given** un PDF cuyo texto extraído tiene menos de 1.500 caracteres (escaneado o vacío)
**When** se intenta ingerir
**Then** se marca como `sin_texto` y se informa
**And** no se crean fragmentos para él.

### BR-003: Ingesta repetible (idempotente)
**Given** un documento ya indexado
**When** se vuelve a ejecutar la ingesta y su contenido no cambió (misma huella SHA-256)
**Then** no se crea nada nuevo
**And** si su contenido cambió, sus fragmentos anteriores se reemplazan por los nuevos.

### BR-004: Consistencia del modelo
**Given** fragmentos vectorizados con un modelo determinado
**When** se hace una búsqueda
**Then** la pregunta se vectoriza con ese mismo modelo y se compara solo contra vectores de ese modelo y dimensión
**And** si no hay vectores del modelo activo, la búsqueda falla con un error claro en vez de devolver resultados sin sentido.

### BR-005: Prioridad de Boyacá
**Given** una búsqueda que indica la región Boyacá
**When** se ordenan los resultados
**Then** los fragmentos de categoría A reciben una ventaja sobre los demás
**And** esa ventaja es configurable (el valor se define en el plan con las preguntas de prueba)
**And** sin región indicada no se aplica ninguna ventaja.

### BR-006: Trazabilidad obligatoria
**Given** un fragmento nuevo
**When** se guarda
**Then** debe tener documento, página(s) y categoría
**And** un fragmento sin alguno de esos datos nunca se guarda.

### BR-007: Respuestas fuera del conocimiento
**Given** una pregunta sobre un tema que la base no cubre
**When** ningún fragmento supera el puntaje mínimo de relevancia
**Then** la búsqueda devuelve una lista vacía
**And** el puntaje mínimo es configurable (su valor se calibra en el plan con las preguntas de prueba)
**And** así el asistente puede decir "no tengo información" en lugar de inventar.

## 4. Data Model (conceptual — PostgreSQL + pgvector)

### Documento
- `id` (UUID), `nombre_archivo` (único), `categoria` (A | B | R | C), `tipo` (manual | avance), `numero_avance` (nulo para el manual), `sha256`, `paginas`, `estado` (indexado | sin_texto | error), `fecha_ingesta`.

### Fragmento
- `id`, `documento_id` (→ Documento), `orden` dentro del documento, `texto`, `pagina_inicio`, `pagina_fin`, `tokens`.

### Embedding
- `fragmento_id` (→ Fragmento), `modelo` (identificador del modelo), `dimension`, `vector`.
- Un fragmento puede tener un embedding por modelo (permite re-indexar sin borrar el anterior).

> Los PDFs originales **no** se guardan en la base (siguen en disco, `docs/` no se versiona); solo el texto, los metadatos y los vectores.

## 5. Contratos (internos — no hay API HTTP en esta feature)

Esta feature es una librería/comandos de Python dentro de `backend/`. El endpoint del asistente (FastAPI) es otra feature y consumirá estos contratos.

```python
class EmbeddingProvider(Protocol):
    nombre_modelo: str          # p. ej. "multilingual-e5-base"
    dimension: int
    def embed_documents(self, textos: list[str]) -> list[list[float]]: ...
    def embed_query(self, texto: str) -> list[float]: ...

def ingestar(carpeta: Path, proveedor: EmbeddingProvider) -> InformeIngesta: ...

def buscar(pregunta: str, k: int = 5, region: str | None = None) -> list[Resultado]: ...
# Resultado: texto, documento, pagina_inicio, pagina_fin, categoria, puntaje

def evaluar(archivo_preguntas: Path, k: int = 5) -> InformeCalidad: ...
```

**Errores esperados:** pregunta vacía o demasiado larga (`INVALID_QUERY`), no hay vectores del modelo activo (`NO_EMBEDDINGS_FOR_MODEL`), base de datos no disponible (`DB_UNAVAILABLE`). Al ser librería, se lanzan como excepciones tipadas; el futuro endpoint las traducirá al formato de error de `constitution.md`.

## 6. Out of Scope (esta spec)
- ❌ El endpoint del asistente y la llamada a Claude (feature siguiente).
- ❌ El chat y cualquier pantalla de la app.
- ❌ Los 122 avances anteriores al 2000 (categoría H) y los 120 escaneados sin texto (categoría E): quedan fuera por ahora (DEC-005 y DEC-006); incluir los escaneados exigiría OCR.
- ❌ Descargar nuevos avances de Cenicafé (el script existe, pero los avances nuevos hay que clasificarlos antes de ingerirlos).
- ❌ Búsqueda híbrida (palabras clave + significado) y re-ranking: posibles mejoras futuras si las preguntas de prueba muestran que hacen falta.
- ❌ Despliegue en AWS (todo local en Docker, según `AGENTS.md`).
- ❌ Actualizaciones automáticas de la base.

## 7. Riesgos y puntos abiertos (se resuelven en `plan.md`, no bloquean esta spec)
- **Qué modelo local concreto usar** (hay varias opciones multilingües): se decide comparándolos con las preguntas de prueba (US-005).
- **Calidad de la extracción de texto:** los PDFs tienen columnas, tablas y figuras; `pdftotext` puede mezclar el orden o dejar ruido (encabezados, números de página, guiones de fin de línea). El plan define la limpieza.
- **Tiempo de indexación:** se estiman 8.000–12.000 fragmentos; el tiempo real en CPU se mide en la primera corrida.
- **Quién redacta las preguntas de prueba:** el usuario (dominio cafetero); sin ellas la meta del 80 % no se puede medir.
- **Dependencias nuevas de Python** (modelo, cliente de PostgreSQL, lector de PDF): se listan en el plan para aprobación, como exige `constitution.md`.

## 8. Decision Log

### DEC-001: Alcance — manual + avances seleccionados, sin etapa de descarga
**Fecha:** 2026-10-20
**Decisión:** La base se construye con los 322 PDFs de `docs/base_conocimiento/` (Manual del Cafetero en 3 tomos + 319 Avances Técnicos de categorías A, B, R y C). Los avances ya están descargados y clasificados.
**Razonamiento:** El usuario descargó los Avances Técnicos y se clasificaron por relevancia para Boyacá (`docs/reporte_relevancia_boyaca.txt`); no hace falta una etapa de descarga dentro de esta feature.

### DEC-002: Vectorización con un modelo local multilingüe, detrás de una interfaz
**Fecha:** 2026-10-20
**Decisión:** Se usa un modelo local, gratuito y multilingüe para vectorizar, accedido siempre a través de `EmbeddingProvider`; cada vector guarda el modelo y la dimensión con que se generó.
**Razonamiento:** Es gratis, funciona sin conexión y los textos no salen del equipo; el usuario quiere poder migrar luego a un modelo de pago para mejorar el rendimiento, así que el modelo no puede estar acoplado al resto del código (US-004, BR-004). Cambiar de modelo implica re-indexar.

### DEC-003: Fragmentos de ~600 tokens con solape
**Fecha:** 2026-10-20
**Decisión:** Fragmentos de unos 600 tokens, solape de unos 100, cortados en límites de párrafo/página (BR-001). *Ajustada por DEC-009: el tamaño real depende de cuánto puede leer el modelo.*
**Razonamiento:** Decisión del usuario (opción recomendada). Da contexto suficiente para respuestas agronómicas (una dosis sin la etapa del cultivo pierde sentido); el tamaño se puede ajustar con las preguntas de prueba.

### DEC-004: Prioridad de Boyacá por categoría
**Fecha:** 2026-10-20
**Decisión:** Cada fragmento guarda su categoría (A/B/R/C); al consultar con región Boyacá, los de categoría A suben de posición (BR-005).
**Razonamiento:** Decisión del usuario (opción recomendada). Solo existe un documento dedicado a Boyacá y unos pocos con datos específicos; ordenar solo por similitud los dejaría enterrados entre el conocimiento general. No requiere datos nuevos: el manifiesto ya tiene la categoría.

### DEC-005: Documentos anteriores al 2000 (categoría H) quedan fuera por ahora
**Fecha:** 2026-10-20
**Decisión:** No se ingieren los 122 avances publicados antes del 2000.
**Razonamiento:** Decisión del usuario (opción recomendada). Sus recomendaciones de agroquímicos pueden estar desactualizadas; si faltara cobertura en algún tema, se agregan documentos puntuales después.

### DEC-006: Documentos escaneados (categoría E) quedan fuera por ahora
**Fecha:** 2026-10-20
**Decisión:** No se ingieren los 120 PDFs sin texto ni se agrega OCR en esta feature.
**Razonamiento:** Decisión del usuario (opción recomendada). Son páginas antiguas, muchas fuera de tema; el OCR sumaría una herramienta, tiempo de proceso y errores de lectura para poco valor.

### DEC-009: El tamaño del fragmento depende del modelo (ajusta DEC-003)
**Fecha:** 2026-10-20
**Decisión:** El tamaño objetivo de los fragmentos es el menor entre 600 tokens y lo que el modelo activo puede leer menos un margen de 60 (con e5, que lee 512, ≈ 450 tokens y solape ≈ 75; con BGE-M3, que lee 8.192, ≈ 600 y solape 100). Los tokens se cuentan con el tokenizador del modelo.
**Razonamiento:** Aceptada por el usuario. DEC-003 pedía ~600 tokens, pero los modelos multilingües e5 solo leen 512 y cortarían el final del fragmento sin avisar, perdiendo texto. Se mantiene la intención de DEC-003 (fragmentos de contexto suficiente, con solape) respetando el límite real de cada modelo. Descubierta al preparar el plan, al comparar las características de los modelos candidatos.

### DEC-007: Cada resultado debe poder citarse — *propuesta del agente, por confirmar*
**Fecha:** 2026-10-20
**Decisión:** Cada resultado de búsqueda trae documento y página(s) (BR-006), para que el asistente pueda citar la fuente en su respuesta.
**Razonamiento:** Los consejos agronómicos deben ser verificables y el caficultor puede querer consultar el documento; además evita respuestas inventadas. Cómo se muestra la cita al usuario lo define la feature del asistente.

### DEC-008: Sin resultados relevantes, no se inventa — *propuesta del agente, por confirmar*
**Fecha:** 2026-10-20
**Decisión:** Si nada supera el puntaje mínimo, la búsqueda devuelve una lista vacía (BR-007).
**Razonamiento:** Permite al asistente responder "no tengo información sobre eso" en vez de improvisar con fragmentos poco relacionados.
