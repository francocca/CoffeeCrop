# Progreso de Implementación — Gestión de la Finca Cafetera

## Resumen
- **Tareas completadas:** 13 / 15 — ✅ Capa de datos completa (Tareas 1-8) · ✅ Pantallas completas (Tareas 9-13)
- **Tarea actual:** Tarea 14 — pruebas de validadores de los modelos
- **Tiempo invertido:** ~7h 30m

## Registro de Tareas
- ✅ **Tarea 1 — Dependencias y base de datos:** ACEPTADA. `sqflite`, `path_provider`, `uuid` (+ `path` como dependencia directa, usada por `database_helper.dart`) agregadas; `DatabaseHelper.getDatabase()` creado con las sentencias `CREATE TABLE finca`/`CREATE TABLE actividad` de `plan.md` §4. Nota: la creación real del archivo `.db` se verifica end-to-end recién en la Tarea 6, cuando el repositorio lo invoque.
- ✅ **Tarea 2 — Excepciones tipadas:** ACEPTADA. `InvalidFarmDataException`, `InvalidActivityDataException`, `NoFincaException` creadas en `finca_exceptions.dart`.
- ✅ **Tarea 3 — Modelo `Finca`:** ACEPTADA. Valida BR-001 (nombre 1-100 chars, plantas > 0); `toMap`/`fromMap` coinciden con el esquema SQL.
- ✅ **Tarea 4 — Modelo `Actividad`:** ACEPTADA. Valida BR-003 (nombre 1-100 chars, monto ≥ 0, fecha no futura); `toMap`/`fromMap` coinciden con el esquema SQL.
- 🔧 **Fix fuera de alcance de las tareas:** `test/widget_test.dart` todavía probaba la app de ejemplo (`MyApp`/contador), que ya no existe desde que se construyó la pantalla de Inicio real. Se corrigió para probar `CoffeCropApp` — era necesario para que `flutter analyze` quedara limpio antes de seguir.

**Nota:** las pruebas unitarias de los validadores de `Finca`/`Actividad` quedan para la Tarea 14, según el orden ya aprobado en `tasks.md` (modelos → repositorio → pantallas → pruebas de validadores).
- ✅ **Tarea 5 — Interfaz `FincaRepository`:** ACEPTADA. Declara los 7 métodos del contrato de `spec.md` §5.
- ✅ **Tarea 6 — `SqfliteFincaRepository` (finca):** ACEPTADA. `obtenerFinca()`/`guardarFinca()` implementados con SQL de `plan.md` §5; 3 pruebas con base de datos en memoria (`sqflite_common_ffi`, dependencia de desarrollo agregada para esto), patrón AAA, todas en verde.
- ✅ **Tarea 7 — `SqfliteFincaRepository` (actividades: alta, listado, total):** ACEPTADA. `agregarActividad()` valida BR-005 (`NoFincaException`), `listarActividades()` pagina de a 20 (DEC-004), `calcularInversionTotal()` usa `COALESCE`. 5 pruebas nuevas, las 9 pruebas del proyecto pasan.
- ✅ **Tarea 8 — `SqfliteFincaRepository` (editar/eliminar):** ACEPTADA. `actualizarActividad()`/`eliminarActividad()` implementados; 4 pruebas nuevas confirman que la inversión total se recalcula tras editar y eliminar (BR-004). 13/13 pruebas del proyecto en verde.

### Checkpoint — Fundación completa (Tareas 1-8)
Toda la capa de datos (base de datos, modelos, repositorio) está implementada y probada. Falta la capa de pantallas (Tareas 9-13), que consume este repositorio.

- ✅ **Tarea 9 — `FincaFormScreen`:** ACEPTADA. Formulario de crear/editar finca (US-001), validación en vivo, maneja `InvalidFarmDataException`. **Gap señalado:** sin prueba de widget dedicada (no estaba en `tasks.md`, solo pruebas de validadores en la Tarea 14) — pendiente de decisión si se agrega.
- ✅ **Tarea 10 — `HomeScreen` con datos reales: ACEPTADA (2026-10-14).** El bloqueo del test se resolvió usando `FakeFincaRepository` (en memoria, sin I/O real, en `test/fakes/`) en vez de sqflite dentro de `testWidgets`; 2 pruebas de widget nuevas (estado vacío, y finca + actividades reales sin "Costo por planta"). 14/14 pruebas en verde, `flutter analyze` limpio. Historial del bloqueo:
  - Código escrito y `flutter analyze` pasa limpio: `main.dart` crea la base de datos real y el repositorio al arrancar; `home_shell.dart`/`home_screen.dart` reciben el repositorio inyectado; `FincaCard` ya no tiene "Costo por planta" (DEC-006); `ActividadFinca` se movió de `mock_finca_data.dart` (eliminado) a `actividades_card.dart`; Inicio ahora muestra estado vacío (si no hay finca) o los datos reales (finca + inversión total + actividades recientes).
  - **Bug pendiente sin resolver:** el `widget_test.dart` actualizado (que ahora necesita una base de datos real en memoria, porque `CoffeCropApp` requiere el repositorio) se queda colgado indefinidamente — probablemente porque el `CircularProgressIndicator` del estado de carga tiene una animación infinita que no deja asentar la prueba, combinado con que las operaciones async reales de sqflite no completan correctamente dentro de la zona "fake async" de `testWidgets`. Se probaron dos intentos con `tester.runAsync()` sin éxito; quedó colgado las dos veces (hubo que matar procesos `dart`/`flutter_tester` manualmente ambas veces).
  - **Las 12 pruebas del repositorio (Tareas 6-8) siguen pasando bien** cuando corren solas — el problema es específico de este nuevo widget test.
  - **Próximo paso sugerido:** en vez de seguir peleando con `runAsync`, probablemente lo más simple sea testear `HomeScreen` con un `FincaRepository` falso/en memoria (un fake de Dart puro, sin sqflite real) en vez de `SqfliteFincaRepository` + base de datos FFI — así no hay I/O real que choque con la zona fake-async de las pruebas de widgets.
  - **No se subió nada al repo** de este trabajo — queda como cambios locales sin commitear hasta resolver el bloqueo y confirmar que todo pasa.

- ✅ **Tarea 11 — `ActividadFormScreen`: ACEPTADA (2026-10-14).** Formulario crear/editar actividad (US-003, US-005): nombre, monto y fecha (por defecto hoy, con selector); sin finca bloquea el registro con mensaje y botón a `FincaFormScreen` (BR-005, DEC-003); modo edición precarga y actualiza; errores de validación por campo (BR-003). 5 pruebas de widget nuevas con `FakeFincaRepository`; 19/19 en verde, `flutter analyze` limpio. Rama: `feat/task-11-actividad-form`.
  - **Interpretación:** `tasks.md` dice "redirige a `FincaFormScreen`"; se implementó como mensaje bloqueante + botón (lo que dice DEC-003), no redirección automática.
  - **Pendiente de DoD:** verificación en dispositivo real diferida a la Tarea 13 (la pantalla aún no es alcanzable: el botón "+" se conecta ahí).

- ✅ **Tarea 12 — `ActividadesListScreen`: ACEPTADA (2026-10-14).** Listado "Ver todas" (US-004, US-005): paginado de a 20 con carga al acercarse al final (DEC-004), estado vacío, tocar abre `ActividadFormScreen` en edición, eliminar con diálogo de confirmación; tras editar/eliminar se recargan las páginas ya cargadas (conserva el scroll sin saltar ni repetir filas). 8 pruebas nuevas (5 de widget + 3 unitarias de `formatearHace`); 27/27 en verde, `flutter analyze` limpio. Rama: `feat/task-12-actividades-list`.
  - **Fuera de la lista de archivos de la tarea (justificado):** constante compartida `tamanoPaginaActividades` en `finca_repository.dart` (la pantalla necesita el tamaño de página para saber si hay más; antes era privada en el repositorio SQLite, también actualizado junto con el fake de pruebas); helper `formatearHace` en `utils/formatters.dart` ("Hoy" / "Ayer" / "Hace N días").
  - **Seguimiento para la Tarea 13:** `ActividadesCard` (Inicio) todavía muestra "Hace N días" sin los casos Hoy/Ayer — alinearlo con `formatearHace` al tocar ese widget.
  - **Pendiente de DoD:** verificación en dispositivo real diferida a la Tarea 13 (la pantalla aún no es alcanzable).

- ✅ **Tarea 13 — Inicio con actividades reales y navegación: ACEPTADA (2026-10-14).** El botón "+" abre `ActividadFormScreen`; "Ver todas las actividades" abre `ActividadesListScreen`; al volver de cualquiera de las dos Inicio se actualiza solo (BR-004) sin spinner de pantalla completa ni perder el scroll (señal `recargar` de `HomeShell` hacia `HomeScreen`, sin paquetes nuevos de manejo de estado, según `plan.md` §5). Inicio refresca siempre al volver (no solo al guardar) porque el formulario puede haber creado la finca (BR-005) sin registrar actividad. `ActividadesCard` ahora recibe `Actividad` reales (se eliminó `ActividadFinca`), usa `formatearHace` ("Hoy"/"Ayer"/"Hace N días") y tiene estado vacío (US-004). 5 pruebas de navegación nuevas; 32/32 en verde, `flutter analyze` limpio. Rama: `feat/task-13-home-navigation`.
  - **Verificado en la tablet Galaxy (SM X400) por el usuario:** flujo completo — crear finca, registrar/editar/eliminar actividades, "Ver todas", actualización de Inicio y persistencia al cerrar y reabrir. Esto cierra los pendientes de DoD de las Tareas 11 y 12 y confirma end-to-end la creación real de `coffecrop.db` (pendiente desde la Tarea 1).

## Registro de Rechazos
_(se completa solo si una tarea se rechaza en la auditoría)_
