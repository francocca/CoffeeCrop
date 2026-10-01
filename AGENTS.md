# CoffeCrop — Agente Cafetero + Finanzas Inteligentes

## Resumen del proyecto
App móvil (Android, iOS) que combina:
1. **Gestión financiera y de finca cafetera** (movimientos, presupuestos, reportes) — offline-first.
2. **Asistente de IA (chat)** que responde dos tipos de preguntas:
   - Consejos técnicos de cultivo de café, basados en el *Manual del Cafetero Colombiano* (Cenicafé) y ~1000 documentos de investigación de Cenicafé, vía RAG (Retrieval-Augmented Generation).
   - Preguntas sobre los datos propios del usuario (saldos, gastos, cosecha, finca), consultando su base de datos.

**Diseño de referencia:** mockup "Finanzas Inteligentes" (Hogar y Finca) compartido por el usuario el 2026-08-04. Pantallas: Inicio, Registrar movimiento (voz/foto/manual/importar), Asistente IA, Movimientos, Categorías, Finca - Resumen, Reportes, Registro por voz, Confirmar movimiento, Presupuestos, Configuración. El propio diseño indica el stack: Flutter + SQLite + IA.

**Decisión de alcance (2026-08-06):** la app se enfoca únicamente en la **administración de la finca cafetera**, no en finanzas generales del hogar. Por eso la pantalla de Inicio usa el diseño de "Finca - Resumen" del mockup (tarjeta "Finca El Cafetal", plantas, inversión total, costo por planta, últimas actividades) en vez del dashboard genérico de patrimonio/ingresos-gastos del hogar. Los widgets del dashboard financiero genérico (`patrimonio_card`, `month_summary_card`, `proximos_pagos_card`, `ia_recommendation_card`) se eliminaron por quedar fuera de alcance.

## Estrategia de despliegue
- **Todo en local primero**: SQLite local + PostgreSQL/pgvector en Docker local + backend corriendo en localhost. Sin gastos de AWS durante desarrollo.
- Migrar a AWS (RDS PostgreSQL) recién cuando la app esté validada en local.
- Cotización AWS ya hecha (referencia, no aplicada aún): Amazon RDS for PostgreSQL, `db.t4g.micro`, Single-AZ, gp3 20GB, sin Multi-AZ/RDS Proxy/Database Insights → **~13.98 USD/mes**.

## Stack tecnológico

| Capa | Tecnología | Notas |
|---|---|---|
| App (Android/iOS) | **Flutter (Dart)** | Elegido por el usuario, coincide con el diseño de referencia. Web descartado como plataforma objetivo (2026-09-30) — solo se usa como herramienta rápida de previsualización en desarrollo |
| Almacenamiento local | SQLite (`sqflite` / `drift`) | Offline-first |
| Gráficos/reportes | `fl_chart` o `syncfusion_flutter_charts` | Pantallas de Reportes/Categorías |
| Voz a texto | `speech_to_text` | Registro por voz |
| OCR (escaneo de factura) | `google_mlkit_text_recognition` o backend | Escanear factura |
| Biometría | `local_auth` | Bloqueo con huella/Face ID |
| Backend / Agente IA | **Python (FastAPI)** | Independiente del lenguaje de la app — se comunican por API HTTP |
| Base vectorial | **PostgreSQL + pgvector** | Local: Docker. Prod: AWS RDS |
| LLM | **Claude API** | Genera respuestas del asistente |
| Fuente de conocimiento cafetero | Manual del Cafetero Colombiano (3 tomos, ~995 páginas, ya en el proyecto) + ~1000 documentos de investigación de Cenicafé (pendiente descargar) |

## Fases del proyecto

### Fase 1 — Base de la app (offline-first) — EN CURSO
- [ ] Modelo de datos: movimientos, categorías, presupuestos, cuentas, finca (plantas, costo, actividades)
- [x] Proyecto Flutter creado + corriendo en dispositivo Android real (web se usó solo como vista previa durante desarrollo, no es plataforma objetivo)
- [x] Pantalla Inicio (dashboard) construida con datos de ejemplo (mock), verificada en tablet física
- [ ] Pantallas: Movimientos, Reportes, Finca, Configuración
- [ ] Conectar Inicio a SQLite real (hoy usa `lib/data/mock_home_data.dart`)

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

## Estado del entorno (verificado 2026-08-06)
- Flutter: instalado en `C:\Flutter\flutter` (v3.44.9, channel stable), instalado por el usuario vía el asistente de VS Code. **No está en el PATH de las sesiones de terminal de este agente** — hay que anteponer `export PATH="/c/Flutter/flutter/bin:$PATH"` en Bash antes de correr comandos `flutter`.
- Android toolchain: SDK detectado en `C:\Android\Sdk`, pero faltan las cmdline-tools y aceptar licencias (`flutter doctor --android-licenses`). No bloquea el desarrollo actual (se usa Web/Chrome), se resuelve en la Fase 4 al probar en Android real.
- Visual Studio (Windows desktop): no instalado — no se necesita, fuera de alcance (solo Android/iOS).
- Docker: no instalado (necesario para PostgreSQL+pgvector local)
- Python: no instalado (necesario para el backend)
- Node.js: instalado (v24.18.0) — no se usa como backend principal, se eligió Python para el backend. Sí se usa `npx http-server` para servir el build web de Flutter en el navegador.
- Documentos: movidos a `docs/manual_cafetero/` (`ManualDelCafeteroColombianoTomo1.pdf`, `Tomo2.pdf`, `Tomo3.pdf`, ~995 páginas totales, texto extraíble, no escaneado)

## Estructura del proyecto
```
CoffeCrop/
  AGENTS.md
  .claude/launch.json       # config para previsualizar la app web en el navegador
  docs/manual_cafetero/     # PDFs del Manual del Cafetero Colombiano (fuente para RAG)
  app/                      # proyecto Flutter (org com.coffecrop, nombre coffecrop)
    app/serve_web.bat       # sirve el build web estático (flutter build web + npx http-server)
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

## Próximos pasos inmediatos
1. Terminar instalación de Flutter SDK.
2. Crear proyecto Flutter (`flutter create`).
3. Definir esquema SQLite inicial (movimientos, categorías, presupuestos, finca).
4. Construir pantalla de Inicio (dashboard) según el diseño de referencia.
