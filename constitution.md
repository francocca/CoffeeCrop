# Project Constitution: CoffeCrop

## Alcance del proyecto
- CoffeCrop es una app de **administración de finca cafetera** (no finanzas generales del hogar) — decisión de alcance del 2026-08-06.
- Dos capacidades centrales:
  1. Registro y seguimiento de datos de la finca (actividades, inversión, costos, plantas) — offline-first.
  2. Asistente de IA que responde (a) consejos técnicos de café vía RAG sobre el Manual del Cafetero Colombiano y documentos de investigación de Cenicafé, y (b) preguntas sobre los datos propios del usuario (su finca, sus gastos, su cosecha).

## Tech Stack
- **App (Android/iOS):** Flutter (Dart) — Web descartado como plataforma objetivo (decisión 2026-09-30); se puede usar `flutter build web` solo como herramienta de previsualización en desarrollo
- **Almacenamiento local:** SQLite (`sqflite` / `drift`) — offline-first
- **Backend / Agente IA:** Python + FastAPI
- **Base vectorial:** PostgreSQL + pgvector (local: Docker · producción: AWS RDS)
- **LLM:** Claude API
- **Gráficos/reportes:** `fl_chart`
- **Voz a texto:** `speech_to_text`
- **OCR (escaneo de factura):** `google_mlkit_text_recognition` o backend
- **Biometría:** `local_auth`

## Principios de Arquitectura
- **Offline-first:** la app debe funcionar completamente sin conexión; la sincronización con el backend es un complemento, nunca un requisito para el uso básico.
- **Separación estricta frontend/backend:** se comunican únicamente vía API REST. El lenguaje de cada lado es independiente del otro (Flutter en la app, Python en el backend) — ver Decisiones Arquitectónicas.
- **Arquitectura por capas en el backend:** Routers (Controllers) → Services → Data Access.
- **Single Responsibility:** cada widget, servicio o módulo tiene una responsabilidad clara y acotada.
- **Local primero:** todo el desarrollo y las pruebas se hacen en local (SQLite + PostgreSQL/pgvector en Docker) antes de aprovisionar cualquier recurso pago en AWS.

## Decisiones Arquitectónicas (no se revisan sin discusión explícita)
- **Framework de la app:** Flutter — elegido por el usuario, coincide con el diseño de referencia ("Finanzas Inteligentes" / mockup Finca).
- **Backend:** Python, no Node.js — mejor ecosistema para RAG/embeddings (LangChain, LlamaIndex, pypdf); el lenguaje del backend no necesita coincidir con el del frontend porque solo se comunican por API HTTP.
- **Base vectorial:** PostgreSQL + pgvector, no un motor especializado (ej. OpenSearch) — alcanza y es más barato para el volumen esperado (manual + ~1000 documentos de Cenicafé ≈ 1-3 GB de vectores).
- **PDFs originales:** se descargan y guardan aparte de la base de datos (carpeta local en desarrollo, S3 en producción) — nunca como blobs en Postgres.
- **AWS:** descartado para desarrollo; solo se usa una vez la app esté validada en local.

## Límites (Boundaries)

### ✅ SIEMPRE HACER
- Escribir pruebas para toda la lógica de negocio (validaciones, reglas de la finca, recuperación RAG) antes de dar una tarea por terminada.
- Seguir convenciones RESTful en el backend (prefijo `/api/v1/`).
- Manejo explícito de errores con códigos HTTP estándar.
- Validar todas las entradas del usuario (formularios en Flutter y payloads de la API).
- Mantener los PDFs/documentos crudos fuera de la base de datos.
- Verificar visualmente cada cambio de interfaz (navegador o dispositivo real) antes de reportarlo como terminado.
- Actualizar `AGENTS.md` y los artefactos de este flujo (`spec.md`, `plan.md`, `tasks.md`, `progress.md`) cuando cambien decisiones de alcance o arquitectura.

### ⚠️ PREGUNTAR PRIMERO
- Antes de agregar nuevas dependencias/paquetes de terceros (pub.dev o pip).
- Antes de modificar el esquema de SQLite o de la base vectorial, o de agregar nuevas entidades/tablas.
- Antes de aprovisionar cualquier recurso en AWS, incluso para pruebas.
- Antes de cambiar una decisión arquitectónica ya tomada (ver sección anterior).
- Antes de descargar o scrapear los ~1000 documentos del servidor de Cenicafé (respetar límites de velocidad y términos de uso del sitio).

### 🚫 NUNCA HACER
- Nunca hardcodear secretos, API keys (Claude, credenciales de base de datos) en el código.
- Nunca incluir la API key de Claude ni credenciales de base de datos en el código de la app Flutter — la app nunca llama directamente a Claude ni a la base vectorial; siempre pasa por el backend, que es el único que guarda esos secretos (en variables de entorno, nunca en el repo).
- Nunca commitear datos financieros o personales reales del usuario.
- Nunca omitir pruebas para lógica de negocio crítica.
- Nunca guardar el corpus de PDFs como blobs dentro de PostgreSQL.
- Nunca agregar funcionalidades de finanzas generales del hogar (patrimonio, ingresos/gastos genéricos) — fuera de alcance.
- Nunca aprovisionar recursos de AWS con costo asociado sin confirmación explícita del usuario.
- Nunca hacer commit ni push directo a `main`, ni mergear PRs: todo va en una rama y el humano crea y mergea el PR (ver "Flujo de Git y Pull Requests").

## Estilo de Código
- **Dart/Flutter:** `lowerCamelCase` para variables/funciones, `PascalCase` para clases/widgets, archivos en `snake_case`.
- **Python:** PEP8, `snake_case` para funciones/variables, `PascalCase` para clases.
- Nombres descriptivos (mínimo 3 caracteres); evitar abreviaturas poco claras.
- Sin comentarios que expliquen "qué hace" el código — solo para decisiones no obvias (restricciones ocultas, workarounds).

## Estándar de Manejo de Errores
Todas las respuestas de error del backend deben seguir este formato:
```json
{
  "error": "Mensaje legible para humanos",
  "code": "CODIGO_ERROR",
  "timestamp": "ISO-8601"
}
```
Códigos de estado:
- `200`: Éxito con datos
- `201`: Recurso creado
- `400`: Errores de validación (mensajes específicos por campo)
- `404`: Recurso no encontrado
- `500`: Errores inesperados del servidor

## Requisitos de Pruebas
- Toda lógica de negocio (validaciones, reglas de la finca, recuperación RAG) debe tener pruebas antes de considerarse terminada.
- **Backend:** `pytest`, patrón AAA (Arrange, Act, Assert), mockear dependencias externas (Claude API, base de datos).
- **Flutter:** pruebas unitarias para validadores/formateadores y lógica de negocio; pruebas de widget para pantallas críticas.
- No se exige un porcentaje de cobertura rígido (proyecto individual), pero ninguna lógica de negocio nueva debe quedar sin prueba.
- **RAG:** las pruebas cubren las partes determinísticas (chunking, construcción de la consulta, conexión a la base vectorial, formato de la respuesta) — no se exige "probar" que la respuesta del LLM sea semánticamente correcta, eso se valida manualmente durante revisión.

## Estándares de API
- Todos los endpoints del backend con prefijo `/api/v1/`.
- Convenciones RESTful (GET/POST/PUT/DELETE).
- Formato de respuesta consistente (ver Estándar de Manejo de Errores).

## Flujo de trabajo (SDD)
Este proyecto sigue Spec-Driven Development. Jerarquía de artefactos:
1. **`constitution.md`** (este archivo) — leyes de alto nivel del proyecto.
2. **`spec.md`** — fuente única de verdad de features y reglas (qué y por qué, no cómo).
3. **`plan.md`** — plano arquitectónico de cada feature, generado por el agente y aprobado por el humano.
4. **`tasks.md`** — descomposición en tareas atómicas y secuenciales.
5. **`progress.md`** — registro de avance tarea por tarea.

`AGENTS.md` se mantiene como el resumen vivo de alto nivel (fases del producto completo, estado del entorno); los artefactos de SDD (`spec.md`, `plan.md`, `tasks.md`) se usan por feature/fase para el desarrollo guiado por especificación.

## Buenas prácticas de SDD
- **Spec primero:** ningún cambio de comportamiento se implementa sin estar en `spec.md`. Si aparece algo no especificado, se actualiza la spec (y el Decision Log) *antes* de escribir código; si ya se escribió código sin spec, se revierte o se especifica de inmediato (corregir el *drift*).
- **Trazabilidad:** cada tarea de `tasks.md` referencia las user stories (US-xxx), reglas de negocio (BR-xxx) y decisiones (DEC-xxx) que implementa; los commits y PRs las citan.
- **Una tarea a la vez:** se implementa solo lo que dice la tarea. Lo que surja fuera de alcance se anota en `progress.md` (o como nueva tarea), no se mezcla.
- **Definición de Hecho (DoD)** de una tarea — todas deben cumplirse:
  - [ ] Criterios de aceptación de la tarea cumplidos.
  - [ ] `flutter analyze` sin errores ni avisos.
  - [ ] Pruebas de la lógica nueva escritas y `flutter test` en verde.
  - [ ] Sin violaciones de los límites de esta constitución (secretos, dependencias sin aprobar, alcance).
  - [ ] Cambios de UI verificados en pantalla (dispositivo real).
  - [ ] `progress.md` actualizado (estado, decisiones, gaps); `spec.md`/`plan.md`/`tasks.md`/`AGENTS.md` sincronizados si algo cambió.
- **Auditoría antes de aceptar:** cumplimiento de spec → pruebas → calidad de código. Una tarea con una prueba fallida o colgada no se acepta ni se sube como terminada.
- **Decisiones y desviaciones visibles:** las decisiones del humano se registran en el Decision Log; las desviaciones del plan se declaran en `progress.md`, no se resuelven en silencio.
- **Los artefactos viven con el código:** documentación y código viajan en el mismo PR para que nunca queden desincronizados.

## Flujo de Git y Pull Requests
- **`main` es solo para código revisado.** Nunca se commitea ni se hace push directo a `main`; todo cambio entra por Pull Request. El humano crea y mergea el PR; el agente nunca mergea ni hace push a `main`.
- **Una rama por tarea** (o por grupo pequeño y coherente de tareas), creada desde un `main` actualizado:
  - Formato: `tipo/task-NN-descripcion-corta` (kebab-case), p. ej. `feat/task-11-actividad-form`.
  - Tipos: `feat` (funcionalidad), `fix` (corrección), `test`, `refactor`, `docs` (specs/documentación; sin número de tarea: `docs/descripcion`), `chore` (dependencias, configuración).
- **Commits** pequeños y atómicos, en imperativo y en inglés, con el formato `tipo(task-NN): resumen` (≤ 72 caracteres). El cuerpo explica el *porqué* y cita las referencias (US/BR/DEC). Cada commit deja el proyecto compilando.
  - Se commitea solo cuando el humano lo pide; no se suben cambios sin verificar (análisis limpio y pruebas en verde).
  - No se commitean secretos, `.env`, binarios pesados ni los PDFs de `docs/`. Se añade cada archivo explícitamente (nada de `git add -A` a ciegas).
- **Pull Requests** pequeños y enfocados (idealmente una tarea, < ~400 líneas de diff). La descripción incluye:
  1. Resumen y por qué (tarea, US/BR/DEC implementadas).
  2. Qué cambió / qué NO cambió (fuera de alcance).
  3. Cómo se probó (análisis, pruebas, verificación en dispositivo).
  4. Checklist de la Definición de Hecho.
  5. Gaps o decisiones pendientes para el revisor.
- **Antes de abrir el PR:** actualizar la rama con `main`, resolver conflictos, volver a correr `flutter analyze` y `flutter test`.
- **Después del merge:** se borra la rama y la siguiente tarea parte de un `main` actualizado (`git checkout main && git pull`).
- **Prohibido sin pedido explícito:** `push --force`, reescribir historia publicada, saltarse hooks (`--no-verify`).
