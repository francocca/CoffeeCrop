# CoffeCrop — Tareas: Gestión de la Finca Cafetera

> Descomposición atómica basada en `plan.md`. Orden: Infraestructura → Modelos → Repositorio → Pantallas (por vertical slice) → Pruebas → Cierre. Cada tarea se ejecuta, se audita contra `constitution.md`/`spec.md`, y se acepta o rechaza antes de pasar a la siguiente (Fase 4 del flujo SDD).

## Fase: Infraestructura

### Tarea 1: Dependencias y base de datos
**Descripción:** Agregar `sqflite`, `path_provider` y `uuid` al proyecto, y crear el helper que abre/crea la base de datos SQLite con las tablas `finca` y `actividad`.
**Archivos:** `app/pubspec.yaml`, `app/lib/data/db/database_helper.dart`
**Criterios de Aceptación:**
- [ ] Las 3 dependencias están en `pubspec.yaml` y resuelven sin conflicto.
- [ ] `database_helper.dart` expone una forma de obtener la instancia de la base de datos (abre el archivo o lo crea la primera vez).
- [ ] Ejecuta las sentencias `CREATE TABLE finca` y `CREATE TABLE actividad` exactamente como en `plan.md` §4.
- [ ] Prueba manual: la app arranca sin error y el archivo `.db` se crea en el dispositivo.
**Tiempo estimado:** 25 min
**Dependencias:** Ninguna

### Tarea 2: Excepciones tipadas
**Descripción:** Crear las excepciones `InvalidFarmDataException`, `InvalidActivityDataException` y `NoFincaException` usadas por las validaciones de negocio.
**Archivos:** `app/lib/data/exceptions/finca_exceptions.dart`
**Criterios de Aceptación:**
- [ ] Las 3 clases existen, extienden `Exception`, y guardan un mensaje legible.
- [ ] Cada una documenta brevemente a qué regla de negocio corresponde (BR-001/BR-003/BR-005).
**Tiempo estimado:** 15 min
**Dependencias:** Ninguna

## Fase: Modelos

### Tarea 3: Modelo `Finca`
**Descripción:** Clase `Finca` con los campos de `spec.md` §4, validación según BR-001, y conversión a/desde `Map` para SQLite.
**Archivos:** `app/lib/models/finca.dart`
**Criterios de Aceptación:**
- [ ] Campos: `id`, `nombre`, `numeroPlantas`, `fechaCreacion`.
- [ ] El constructor valida nombre (1-100 chars) y número de plantas (entero > 0); lanza `InvalidFarmDataException` si falla.
- [ ] Métodos `toMap()` y `Finca.fromMap()` compatibles con el esquema SQL.
**Tiempo estimado:** 25 min
**Dependencias:** Tarea 2

### Tarea 4: Modelo `Actividad`
**Descripción:** Clase `Actividad` con los campos de `spec.md` §4, validación según BR-003, y conversión a/desde `Map`.
**Archivos:** `app/lib/models/actividad.dart`
**Criterios de Aceptación:**
- [ ] Campos: `id`, `fincaId`, `nombre`, `monto`, `fecha`, `fechaCreacion`.
- [ ] El constructor valida nombre (1-100 chars), monto (≥ 0) y fecha (no futura); lanza `InvalidActivityDataException` si falla.
- [ ] Métodos `toMap()` y `Actividad.fromMap()` compatibles con el esquema SQL.
**Tiempo estimado:** 25 min
**Dependencias:** Tarea 2

## Fase: Repositorio (capa de datos)

### Tarea 5: Interfaz `FincaRepository`
**Descripción:** Definir el contrato abstracto exacto de `spec.md` §5.
**Archivos:** `app/lib/data/repositories/finca_repository.dart`
**Criterios de Aceptación:**
- [ ] Declara los 7 métodos del contrato (`obtenerFinca`, `guardarFinca`, `listarActividades`, `agregarActividad`, `actualizarActividad`, `eliminarActividad`, `calcularInversionTotal`).
- [ ] Firma de `listarActividades` recibe `pagina` (paginación DEC-004).
**Tiempo estimado:** 15 min
**Dependencias:** Tareas 3, 4

### Tarea 6: `SqfliteFincaRepository` — finca
**Descripción:** Implementar `obtenerFinca()` y `guardarFinca()` con el SQL de `plan.md` §5.
**Archivos:** `app/lib/data/repositories/sqflite_finca_repository.dart`, `app/test/data/sqflite_finca_repository_test.dart`
**Criterios de Aceptación:**
- [ ] `obtenerFinca()` ejecuta `SELECT * FROM finca LIMIT 1` y devuelve `null` si no hay fila.
- [ ] `guardarFinca()` ejecuta `INSERT OR REPLACE` con los datos del modelo.
- [ ] Prueba unitaria con base de datos sqflite en memoria: crear finca → `obtenerFinca()` la devuelve con los mismos datos.
**Tiempo estimado:** 35 min
**Dependencias:** Tarea 5, Tarea 1

### Tarea 7: `SqfliteFincaRepository` — actividades (alta, listado, total)
**Descripción:** Implementar `agregarActividad()` (con chequeo BR-005), `listarActividades()` paginado y `calcularInversionTotal()`.
**Archivos:** `app/lib/data/repositories/sqflite_finca_repository.dart`, `app/test/data/sqflite_finca_repository_test.dart`
**Criterios de Aceptación:**
- [ ] `agregarActividad()` lanza `NoFincaException` si `SELECT COUNT(*) FROM finca` es 0 (BR-005).
- [ ] `listarActividades(pagina: 0)` trae máximo 20 filas ordenadas por fecha descendente; `pagina: 1` trae las siguientes.
- [ ] `calcularInversionTotal()` devuelve `0` con la tabla vacía (prueba el `COALESCE`) y la suma correcta con varias actividades.
- [ ] Pruebas unitarias para los 3 casos anteriores, patrón AAA.
**Tiempo estimado:** 45 min
**Dependencias:** Tarea 6

### Tarea 8: `SqfliteFincaRepository` — editar/eliminar
**Descripción:** Implementar `actualizarActividad()` y `eliminarActividad()`.
**Archivos:** `app/lib/data/repositories/sqflite_finca_repository.dart`, `app/test/data/sqflite_finca_repository_test.dart`
**Criterios de Aceptación:**
- [ ] `actualizarActividad()` ejecuta el `UPDATE` y los cambios se reflejan al volver a leer.
- [ ] `eliminarActividad()` ejecuta el `DELETE` y la fila deja de aparecer en `listarActividades()`.
- [ ] Prueba que confirma que `calcularInversionTotal()` cambia correctamente tras editar y tras eliminar (BR-004).
**Tiempo estimado:** 25 min
**Dependencias:** Tarea 7

## Fase: Pantallas (UI)

### Tarea 9: `FincaFormScreen` (crear/editar finca)
**Descripción:** Formulario para registrar o editar nombre y número de plantas (US-001).
**Archivos:** `app/lib/screens/finca_form_screen.dart`
**Criterios de Aceptación:**
- [ ] Campos nombre y número de plantas con validación en vivo (mensajes de error específicos por campo).
- [ ] Al guardar, llama a `guardarFinca()`; si lanza `InvalidFarmDataException`, muestra el mensaje sin cerrar el formulario.
- [ ] Al guardar con éxito, vuelve a la pantalla de Inicio.
**Tiempo estimado:** 35 min
**Dependencias:** Tarea 6

### Tarea 10: `HomeScreen` con datos reales
**Descripción:** Reemplazar los datos de ejemplo (`mock_finca_data.dart`) por datos reales del repositorio; quitar "Costo por planta" de `FincaCard` (DEC-006).
**Archivos:** `app/lib/screens/home_screen.dart`, `app/lib/widgets/finca_card.dart`
**Criterios de Aceptación:**
- [ ] Si `obtenerFinca()` devuelve `null`, muestra estado vacío con botón que lleva a `FincaFormScreen`.
- [ ] Si hay finca, muestra nombre, número de plantas e inversión total reales (sin costo por planta, ver US-002/DEC-006).
- [ ] `mock_finca_data.dart` deja de usarse en esta pantalla (puede quedar como fixture de pruebas si hace falta, no como fuente de datos de producción).
**Tiempo estimado:** 30 min
**Dependencias:** Tarea 9, Tarea 7

### Tarea 11: `ActividadFormScreen` (crear/editar actividad)
**Descripción:** Formulario para registrar una actividad nueva o editar una existente (US-003, US-005).
**Archivos:** `app/lib/screens/actividad_form_screen.dart`
**Criterios de Aceptación:**
- [ ] Campos nombre, monto y fecha (fecha por defecto hoy, editable).
- [ ] Si no existe finca, la pantalla no se alcanza — muestra mensaje y redirige a `FincaFormScreen` (BR-005, DEC-003).
- [ ] Modo edición precarga los valores de la actividad seleccionada.
- [ ] Errores de validación (`InvalidActivityDataException`) se muestran por campo sin cerrar el formulario.
**Tiempo estimado:** 40 min
**Dependencias:** Tarea 8

### Tarea 12: `ActividadesListScreen` (listado paginado + eliminar)
**Descripción:** Vista "Ver todas las actividades" con scroll paginado y opción de eliminar con confirmación (US-004, US-005).
**Archivos:** `app/lib/screens/actividades_list_screen.dart`
**Criterios de Aceptación:**
- [ ] Carga la página 0 al entrar; pide la siguiente página al llegar al final del scroll.
- [ ] Estado vacío si no hay actividades.
- [ ] Tocar una actividad abre `ActividadFormScreen` en modo edición.
- [ ] Eliminar pide confirmación (diálogo) antes de llamar a `eliminarActividad()`.
**Tiempo estimado:** 40 min
**Dependencias:** Tarea 11

### Tarea 13: Conectar Inicio con actividades reales y navegación
**Descripción:** La tarjeta de "Últimas actividades" en Inicio muestra datos reales; el botón "+" central y "Ver todas" navegan a las pantallas correspondientes.
**Archivos:** `app/lib/screens/home_screen.dart`, `app/lib/screens/home_shell.dart`, `app/lib/widgets/actividades_card.dart`
**Criterios de Aceptación:**
- [ ] Inicio muestra las actividades más recientes (primeras de la página 0) usando datos reales.
- [ ] El botón "+" de la barra inferior abre `ActividadFormScreen` (modo crear).
- [ ] "Ver todas las actividades" navega a `ActividadesListScreen`.
- [ ] Al volver de cualquiera de las dos pantallas tras un cambio, Inicio refleja los datos actualizados (BR-004).
**Tiempo estimado:** 30 min
**Dependencias:** Tarea 10, Tarea 12

## Fase: Pruebas y Cierre

### Tarea 14: Pruebas de validadores
**Descripción:** Pruebas unitarias de los modelos `Finca` y `Actividad` cubriendo casos válidos e inválidos.
**Archivos:** `app/test/models/finca_test.dart`, `app/test/models/actividad_test.dart`
**Criterios de Aceptación:**
- [ ] Casos válidos no lanzan excepción.
- [ ] Nombre vacío y nombre > 100 caracteres lanzan `InvalidFarmDataException`/`InvalidActivityDataException` según corresponda.
- [ ] Número de plantas ≤ 0, monto negativo y fecha futura lanzan la excepción correspondiente.
- [ ] Todas las pruebas siguen el patrón AAA.
**Tiempo estimado:** 30 min
**Dependencias:** Tareas 3, 4

### Tarea 15: Cierre de Fase 1
**Descripción:** Actualizar `progress.md` y `AGENTS.md` reflejando que la Fase 1 quedó completa.
**Archivos:** `progress.md`, `AGENTS.md`
**Criterios de Aceptación:**
- [ ] `progress.md` lista las 15 tareas como aceptadas.
- [ ] `AGENTS.md` marca la Fase 1 como completa y actualiza "Próximos pasos inmediatos" hacia la Fase 2 (Registro inteligente) o Fase 3 (Backend + IA), según lo que el usuario priorice.
**Tiempo estimado:** 15 min
**Dependencias:** Tareas 1-14

---
**Total estimado:** ~7 horas (15 tareas). Se ejecutan una por una, cada una se audita contra `constitution.md` y `spec.md` antes de pasar a la siguiente.
