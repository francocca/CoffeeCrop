# CoffeCrop — Agente Cafetero + Finanzas Inteligentes

## Resumen del proyecto
App móvil (Android, iOS) que combina:
1. **Gestión financiera y de finca cafetera** (movimientos, presupuestos, reportes) — offline-first.
2. **Asistente de IA (chat)** que responde dos tipos de preguntas:
   - Consejos técnicos de cultivo de café, basados en el *Manual del Cafetero Colombiano* (Cenicafé) y ~1000 documentos de investigación de Cenicafé, vía RAG (Retrieval-Augmented Generation).
   - Preguntas sobre los datos propios del usuario (saldos, gastos, cosecha, finca), consultando su base de datos.

**Diseño de referencia:** mockup "Finanzas Inteligentes" (Hogar y Finca) compartido por el usuario el 2026-08-04. Pantallas: Inicio, Registrar movimiento (voz/foto/manual/importar), Asistente IA, Movimientos, Categorías, Finca - Resumen, Reportes, Registro por voz, Confirmar movimiento, Presupuestos, Configuración. El propio diseño indica el stack: Flutter + SQLite + IA.

**Decisión de alcance (2026-08-06):** la app se enfoca únicamente en la **administración de la finca cafetera**, no en finanzas generales del hogar. Por eso la pantalla de Inicio usa el diseño de "Finca - Resumen" del mockup (tarjeta de la finca con nombre, plantas e inversión total, y últimas actividades; el "costo por planta" del mockup se quitó por ahora, ver DEC-006 en `spec.md`) en vez del dashboard genérico de patrimonio/ingresos-gastos del hogar. Los widgets del dashboard financiero genérico (`patrimonio_card`, `month_summary_card`, `proximos_pagos_card`, `ia_recommendation_card`) se eliminaron por quedar fuera de alcance.

## Flujo de trabajo (leer antes de tocar código)
- El desarrollo sigue **Spec-Driven Development**: `constitution.md` → `spec.md` → `plan.md` → `tasks.md` → `progress.md`. Estado real del avance: `progress.md`.
- **Git:** nunca commitear ni hacer push a `main`. Cada tarea va en una rama `tipo/task-NN-descripcion-corta`; el humano crea y mergea el PR. Commits solo cuando el humano los pide. Convenciones completas y Definición de Hecho en `constitution.md`.

## Estrategia de despliegue
- **Todo en local primero**: SQLite local + PostgreSQL/pgvector en Docker local + backend corriendo en localhost. Sin gastos de AWS durante desarrollo.
- Migrar a AWS (RDS PostgreSQL) recién cuando la app esté validada en local.
- Cotización AWS ya hecha (referencia, no aplicada aún): Amazon RDS for PostgreSQL, `db.t4g.micro`, Single-AZ, gp3 20GB, sin Multi-AZ/RDS Proxy/Database Insights → **~13.98 USD/mes**.

## Stack tecnológico

| Capa | Tecnología | Notas |
|---|---|---|
| App (Android/iOS) | **Flutter (Dart)** | Elegido por el usuario, coincide con el diseño de referencia. Web descartado como plataforma objetivo (2026-09-30) — solo se usa como herramienta rápida de previsualización en desarrollo |
| Almacenamiento local | SQLite con **`sqflite`** (SQL escrito a mano; `drift` descartado) | Offline-first. Acceso detrás de la interfaz `FincaRepository` |
| Gráficos/reportes | `fl_chart` o `syncfusion_flutter_charts` | Pantallas de Reportes/Categorías |
| Voz a texto | `speech_to_text` | Registro por voz |
| OCR (escaneo de factura) | `google_mlkit_text_recognition` o backend | Escanear factura |
| Biometría | `local_auth` | Bloqueo con huella/Face ID |
| Backend / Agente IA | **Python (FastAPI)** | Independiente del lenguaje de la app — se comunican por API HTTP |
| Base vectorial | **PostgreSQL + pgvector** | Local: Docker. Prod: AWS RDS |
| LLM | **Claude API** | Genera respuestas del asistente |
| Fuente de conocimiento cafetero | Manual del Cafetero Colombiano (3 tomos, ~995 páginas, ya en el proyecto) + ~1000 documentos de investigación de Cenicafé (pendiente descargar) |

## Fases del proyecto

### Fase 1 — Base de la app (offline-first) — ✅ CERRADA (2026-10-14)
La feature **Gestión de la Finca** se especificó (`spec.md`), planificó (`plan.md`) y ejecutó (`tasks.md`, 15/15 tareas, ver `progress.md`):
- [x] Proyecto Flutter creado + corriendo en dispositivo Android real (web solo como vista previa de desarrollo)
- [x] Capa de datos: base SQLite (tablas `finca` y `actividad`), modelos con validación, excepciones tipadas y `FincaRepository` con 7 operaciones (alta/edición de finca, CRUD de actividades paginado de a 20, inversión total)
- [x] Pantallas: Inicio con datos reales y estado vacío, formulario de finca, formulario de actividad (crear/editar), listado "Ver todas" paginado con eliminar y confirmación, navegación con el botón "+"
- [x] 54 pruebas automáticas en verde (`flutter test`), `flutter analyze` limpio; flujo completo verificado en la tablet Galaxy
- [ ] **Pendiente, aplazado a propósito:** pestañas **Movimientos, Reportes y Configuración** siguen como placeholders (decisión 2026-10-14: las actividades ya cumplen el rol de "movimientos" con el alcance de solo administración de finca; se especifican más adelante cuando hagan falta, cada una con su propia spec)
- [ ] **Pendiente:** bloqueo biométrico y cifrado local (Fase 4, DEC-005)

### Fase 2 — Registro inteligente
- [ ] Registro por voz (voz → texto → LLM interpreta y llena formulario)
- [ ] Escaneo de factura (cámara + OCR)

### Fase 3 — Backend + Asistente IA
- [ ] Backend Python (FastAPI) con dos rutas: RAG (consejos) y consulta de datos propios (estadísticas)
- [ ] Base vectorial local (Docker + pgvector)
- [ ] Pipeline de ingesta: extracción de texto (`pdftotext`) → chunking → embeddings → guardado en base vectorial
- [ ] Ingesta del Manual del Cafetero Colombiano (3 tomos, ya descargados en el proyecto)
- [ ] Descarga y vectorización de los ~1000 documentos de Cenicafé (servidor externo, pendiente definir fuente/URL exacta)
- [ ] Integración del chat "Asistente IA" en la app, conectado al backend
- [ ] Sincronización/backup: SQLite local ↔ backend en la nube

### Fase 4 — Seguridad y publicación
- [ ] Bloqueo biométrico y cifrado local
- [ ] Pruebas en Android e iOS reales
- [ ] Migrar base de datos a AWS RDS (cuando esté validado en local)
- [ ] Publicación en Google Play y App Store

## Estado del entorno (verificado 2026-10-14)
- **Flutter** 3.44.9 (stable) en `C:\Flutter\flutter`. **No está en el PATH de las sesiones de terminal de este agente** — hay que anteponer `export PATH="/c/Flutter/flutter/bin:$PATH"` en Bash antes de correr comandos `flutter`.
- **Android:** toolchain completo (cmdline-tools instaladas, licencias aceptadas, NDK instalado); tablet Galaxy conectada por USB. Ver "Nota técnica: prueba en dispositivo Android real". Requiere el **Modo de programador de Windows** activado (symlinks para plugins nativos).
- **Docker** 29.7.2 y **Python** 3.14.7: instalados (para el backend y PostgreSQL+pgvector de la Fase 3). Aún sin usar en el proyecto.
- **Node.js** v24.18.0: solo se usa `npx http-server` para la vista previa web; el backend será Python.
- **Visual Studio (Windows desktop):** no instalado ni necesario (solo Android/iOS).
- **Disco:** una build de Android puede fallar con "Espacio en disco insuficiente" si `C:` se llena (ya pasó una vez); conviene mantener varios GB libres.
- **Documentos:** `docs/manual_cafetero/` (`ManualDelCafeteroColombianoTomo1.pdf`, `Tomo2.pdf`, `Tomo3.pdf`, ~995 páginas, texto extraíble, no escaneado). Ignorada por git (`.gitignore`).

## Estructura del proyecto
```
CoffeCrop/
  AGENTS.md  constitution.md  spec.md  plan.md  tasks.md  progress.md   # artefactos SDD
  .claude/launch.json       # config para previsualizar la app web en el navegador
  docs/manual_cafetero/     # PDFs del Manual del Cafetero Colombiano (fuente para RAG; no se versiona)
  app/                      # proyecto Flutter (org com.coffecrop, nombre coffecrop)
    serve_web.bat           # sirve el build web estático (flutter build web + npx http-server)
    lib/
      data/db/              # DatabaseHelper (abre/crea coffecrop.db)
      data/exceptions/      # excepciones tipadas de validación
      data/repositories/    # FincaRepository (interfaz) + SqfliteFincaRepository
      models/               # Finca, Actividad (con validación)
      screens/              # Inicio, formularios, listado, shell con navegación
      widgets/  theme/  utils/
    test/                   # pruebas: models/, data/, screens/, utils/, fakes/ (FakeFincaRepository)
```

## Nota técnica: previsualización web (solo herramienta de desarrollo)
**Web no es una plataforma objetivo del producto** (decisión 2026-09-30, solo Android/iOS) — pero se sigue usando `flutter build web` como atajo para verificar visualmente cambios de UI en el navegador durante el desarrollo, mucho más rápido que compilar para Android cada vez. Ningún dato persistido en SQLite funcionará ahí (ver `plan.md` de Gestión de la Finca — sqflite no soporta Web), así que esta vía solo sirve para revisar layout/estilos con datos de ejemplo, no funcionalidad real.

`flutter run -d web-server` falla al iniciar (el cliente de debug inyectado por DWDS tira un error de deserialización y la app nunca monta el `flt-glass-pane`). Workaround estable: `flutter build web` (build estático de release) servido con `npx http-server` en el puerto 8080.

## Nota técnica: prueba en dispositivo Android real
El usuario tiene una tablet Samsung Galaxy (SM X400, Android 16) conectada por USB, usada para ver los cambios en vivo mientras se construye la app. Detalles:
- Device id para `flutter run -d <id>`: `R52YA054V8H`
- Había dos instalaciones de Android SDK en la máquina; `ANDROID_HOME`/`ANDROID_SDK_ROOT` apuntan a `C:\Android\Sdk` (incompleto, sin cmdline-tools), pero la instalación completa está en `C:\Users\Cristian Franco\AppData\Local\Android\Sdk`. Se resolvió con `flutter config --android-sdk "C:\Users\Cristian Franco\AppData\Local\Android\Sdk"` (no se tocaron las variables de entorno del sistema).
- Licencias de Android SDK ya aceptadas (`flutter doctor --android-licenses`).
- El primer `flutter run` en un dispositivo nuevo puede tardar 10+ minutos (descarga el NDK). Los siguientes son rápidos (~40s de Gradle).
- Advertencia pendiente (no bloqueante aún): la ruta del SDK completo contiene un espacio ("Cristian Franco"), lo que puede dar problemas si se usan plugins con código nativo (NDK). Si aparece, la solución es mover el SDK a una ruta sin espacios.

## Decisiones tomadas
- **Framework de la app:** Flutter, elegido por el usuario tras comparar con React Native — coincide con el diseño de referencia.
- **Backend:** Python (no Node.js) — el lenguaje del backend es independiente del frontend (se comunican por API HTTP), y Python tiene mejor ecosistema para RAG/embeddings (LangChain, LlamaIndex, pypdf).
- **Base vectorial:** PostgreSQL + pgvector en vez de un motor especializado (ej. OpenSearch) — alcanza y es más barato para el volumen esperado (estimado 1-3 GB de vectores incluso con ~1000 documentos de Cenicafé sumados al manual).
- **PDFs originales:** se descargan y guardan aparte de la base de datos (local en desarrollo, S3 en producción), no como blobs en Postgres.
- **RDS descartado por ahora:** todo el desarrollo se hace en local (Docker) hasta validar la app; AWS solo para producción.
- **SQLite local con `sqflite`** (no `drift`), SQL explícito y sin generación de código; sin paquete de manejo de estado — las pantallas se refrescan volviendo a consultar el repositorio tras cada escritura.
- **Los datos de la finca viven en el dispositivo, no pasan por el backend** (offline-first). El backend de Python solo maneja el conocimiento cafetero (RAG con pgvector) y, más adelante, sincronización/backup y las consultas del asistente sobre los datos del usuario.
- **Pruebas de widgets con un repositorio falso** (`test/fakes/fake_finca_repository.dart`): usar sqflite real dentro de `testWidgets` cuelga la suite (animación infinita del `CircularProgressIndicator` + I/O real fuera de la zona fake-async). sqflite real solo se prueba en las pruebas del repositorio, con base de datos en memoria (`sqflite_common_ffi`).
- **Sin "costo por planta"** por ahora; "Inversión total" = suma de los montos de todas las actividades (DEC-006 en `spec.md`).

## Próximos pasos inmediatos
**Siguiente: Fase 3 — Backend + Asistente IA** (decisión del usuario, 2026-10-14). Se sigue el mismo flujo SDD, con una nueva spec por feature y una rama + PR por tarea:
1. Escribir la spec de la primera feature de la Fase 3: **base de conocimiento cafetero** (extracción de texto de los PDFs → chunking → embeddings → PostgreSQL + pgvector en Docker → búsqueda por similitud). Incluir su Clarify Loop (preguntas sobre embeddings/modelo, tamaño de chunk, formato de respuesta, etc.) antes de planificar.
2. `plan.md` y `tasks.md` para esa feature; luego ejecución tarea por tarea.
3. Después: endpoint del asistente (FastAPI + Claude API) y el chat dentro de la app.

Aplazado: Fase 2 (registro por voz y escaneo de factura), pestañas Movimientos/Reportes/Configuración, biometría (Fase 4).
