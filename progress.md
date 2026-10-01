# Progreso de Implementación — Gestión de la Finca Cafetera

## Resumen
- **Tareas completadas:** 4 / 15
- **Tarea actual:** Tarea 5 — Interfaz `FincaRepository`
- **Tiempo invertido:** ~1h 30m

## Registro de Tareas
- ✅ **Tarea 1 — Dependencias y base de datos:** ACEPTADA. `sqflite`, `path_provider`, `uuid` (+ `path` como dependencia directa, usada por `database_helper.dart`) agregadas; `DatabaseHelper.getDatabase()` creado con las sentencias `CREATE TABLE finca`/`CREATE TABLE actividad` de `plan.md` §4. Nota: la creación real del archivo `.db` se verifica end-to-end recién en la Tarea 6, cuando el repositorio lo invoque.
- ✅ **Tarea 2 — Excepciones tipadas:** ACEPTADA. `InvalidFarmDataException`, `InvalidActivityDataException`, `NoFincaException` creadas en `finca_exceptions.dart`.
- ✅ **Tarea 3 — Modelo `Finca`:** ACEPTADA. Valida BR-001 (nombre 1-100 chars, plantas > 0); `toMap`/`fromMap` coinciden con el esquema SQL.
- ✅ **Tarea 4 — Modelo `Actividad`:** ACEPTADA. Valida BR-003 (nombre 1-100 chars, monto ≥ 0, fecha no futura); `toMap`/`fromMap` coinciden con el esquema SQL.
- 🔧 **Fix fuera de alcance de las tareas:** `test/widget_test.dart` todavía probaba la app de ejemplo (`MyApp`/contador), que ya no existe desde que se construyó la pantalla de Inicio real. Se corrigió para probar `CoffeCropApp` — era necesario para que `flutter analyze` quedara limpio antes de seguir.

**Nota:** las pruebas unitarias de los validadores de `Finca`/`Actividad` quedan para la Tarea 14, según el orden ya aprobado en `tasks.md` (modelos → repositorio → pantallas → pruebas de validadores).

## Registro de Rechazos
_(se completa solo si una tarea se rechaza en la auditoría)_
