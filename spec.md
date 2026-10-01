# CoffeCrop — Especificación: Gestión de la Finca Cafetera

> Primera feature a especificar (Fase 1 de `AGENTS.md`). Cubre el modelo de datos y las reglas de negocio detrás de la pantalla "Finca - Resumen" ya construida con datos de ejemplo — el objetivo de esta spec es reemplazar esos datos mock por SQLite real.

## 1. Overview
**Problem Statement:** El caficultor necesita registrar los datos básicos de su finca (plantas, inversión) y las actividades que realiza (fertilización, control de plagas, etc.) para llevar un control de costos, sin depender de internet.

**Target Users:** Caficultores individuales administrando su propia finca desde el celular.

**Success Metrics:**
- El usuario puede registrar una actividad en menos de 15 segundos.
- La pantalla de Inicio (Finca - Resumen) siempre refleja los datos reales guardados, sin pérdida al cerrar la app.
- Cero necesidad de conexión a internet para registrar o consultar datos de la finca.

## 2. User Stories

### US-001: Registrar la Finca
**Como** caficultor
**Quiero** registrar el nombre de mi finca y el número de plantas de café
**Para** tener una base sobre la cual calcular mis costos

**Criterios de Aceptación:**
- Nombre es obligatorio (1-100 caracteres).
- Número de plantas es obligatorio, entero positivo (> 0).
- Solo existe una finca por instalación de la app (ver DEC-001).
- El sistema asigna fecha de creación automáticamente.

### US-002: Ver Resumen de la Finca
**Como** caficultor
**Quiero** ver en la pantalla de Inicio el nombre de mi finca, número de plantas e inversión total
**Para** entender de un vistazo el estado financiero de mi finca

**Criterios de Aceptación:**
- Inversión total = suma de los montos de todas las actividades registradas (incluye tanto mano de obra como elementos comprados: fungicidas, elementos de aseo, careta, gafas, rastrillo, secador solar, etc. — cada compra o gasto es una actividad, ver US-003).
- Por ahora no se calcula un costo por planta (ver DEC-006) — solo se muestra la inversión total.
- Si no hay finca registrada aún, se muestra un estado vacío invitando a crearla (no la pantalla en blanco).

### US-003: Registrar Actividad
**Como** caficultor
**Quiero** registrar una actividad (ej. fertilización, control de plagas, compra de fertilizante, pago de obreros) con su nombre, monto y fecha
**Para** llevar un historial de en qué invierto en mi finca

**Criterios de Aceptación:**
- Nombre/descripción es obligatorio (1-100 caracteres).
- Monto es obligatorio, numérico, no negativo.
- Fecha es obligatoria; por defecto la fecha actual, editable.
- El sistema asigna un ID único y queda asociada a la finca.
- Si no existe una finca registrada todavía, el sistema bloquea el registro y muestra un mensaje que lleva a crear la finca primero (ver DEC-003).

### US-004: Ver Últimas Actividades
**Como** caficultor
**Quiero** ver un listado de mis actividades más recientes
**Para** revisar rápidamente en qué gasté últimamente

**Criterios de Aceptación:**
- Ordenadas por fecha descendente (más reciente primero).
- La pantalla de Inicio muestra las más recientes (ver US-002); existe una vista "Ver todas" con el listado completo.
- La vista "Ver todas" pagina de a 20 actividades (scroll incremental), no carga todo de una vez (ver DEC-004).
- Muestra nombre, fecha relativa ("Hace X días") y monto.
- Estado vacío si no hay actividades.

### US-005: Editar/Eliminar Actividad
**Como** caficultor
**Quiero** poder corregir o eliminar una actividad que registré mal
**Para** mantener mis datos precisos

**Criterios de Aceptación:**
- Editar permite cambiar nombre, monto y fecha.
- Eliminar pide confirmación antes de borrar.
- La inversión total se recalcula automáticamente tras editar/eliminar (ver BR-004).

## 3. Business Rules

### BR-001: Validación de la Finca
**Given** un usuario completa el formulario de registro de finca
**When** envía el nombre y número de plantas
**Then** el sistema valida que el nombre tenga 1-100 caracteres y el número de plantas sea un entero > 0
**And** valores inválidos retornan error `INVALID_FARM_DATA` con mensaje específico por campo.

### BR-003: Validación de Actividad
**Given** un usuario registra una actividad
**When** envía nombre, monto y fecha
**Then** el sistema valida nombre (1-100 caracteres), monto (numérico ≥ 0) y fecha (no puede ser futura)
**And** valores inválidos retornan error `INVALID_ACTIVITY_DATA`.

### BR-004: Recalculo de Totales
**Given** una actividad es editada o eliminada
**When** el cambio se guarda
**Then** la inversión total mostrada en Inicio se recalcula inmediatamente (no requiere reiniciar la app).

### BR-005: Actividad Requiere Finca Existente
**Given** no existe una finca registrada en la instalación
**When** el usuario intenta registrar una actividad
**Then** el sistema rechaza la operación con error `NO_FARM_REGISTERED`
**And** la UI redirige al formulario de creación de finca (US-001).

## 4. Data Model (SQLite)

### Tabla `finca`
| Campo | Tipo | Restricciones |
|---|---|---|
| id | TEXT (UUID) | PK |
| nombre | TEXT | NOT NULL, 1-100 chars |
| numero_plantas | INTEGER | NOT NULL, > 0 |
| fecha_creacion | TEXT (ISO-8601) | NOT NULL, autogenerado |

### Tabla `actividad`
| Campo | Tipo | Restricciones |
|---|---|---|
| id | TEXT (UUID) | PK |
| finca_id | TEXT | FK → finca.id, NOT NULL |
| nombre | TEXT | NOT NULL, 1-100 chars |
| monto | REAL | NOT NULL, ≥ 0 |
| fecha | TEXT (ISO-8601) | NOT NULL, no futura |
| fecha_creacion | TEXT (ISO-8601) | NOT NULL, autogenerado |

## 5. Contrato de Acceso a Datos (capa local — sin backend todavía)

Esta feature vive enteramente en el dispositivo (Fase 1, sin backend aún). El contrato es la interfaz del repositorio Dart que las pantallas van a consumir:

```dart
abstract class FincaRepository {
  Future<Finca?> obtenerFinca();
  Future<void> guardarFinca(Finca finca);

  /// Paginado: [pagina] empieza en 0, tamaño de página fijo de 20 (ver DEC-004).
  Future<List<Actividad>> listarActividades({required int pagina});
  Future<void> agregarActividad(Actividad actividad); // lanza NoFincaException si no hay finca (BR-005)
  Future<void> actualizarActividad(Actividad actividad);
  Future<void> eliminarActividad(String id);

  Future<double> calcularInversionTotal();
}
```

**Errores esperados:** validaciones (BR-001, BR-003) lanzan excepciones tipadas (`InvalidFarmDataException`, `InvalidActivityDataException`); la ausencia de finca (BR-005) lanza `NoFincaException`. La UI traduce estas excepciones a mensajes de formulario o navegación — no hay códigos HTTP porque no hay HTTP en esta feature.

## 6. Out of Scope (esta spec)
- ❌ Sincronización con backend/nube (Fase 3 de `AGENTS.md`).
- ❌ Múltiples fincas por usuario (pendiente de confirmar, ver Clarify Loop).
- ❌ Adjuntar fotos/comprobantes a una actividad.
- ❌ Categorías de actividad (fertilización, plagas, etc. como catálogo) — por ahora el nombre es texto libre.
- ❌ Reportes/gráficos de tendencia (eso corresponde a la pantalla "Reportes", spec aparte).
- ❌ Pantallas "Movimientos", "Configuración" (specs aparte, fuera de esta feature).

## 7. Decision Log

### DEC-001: Una sola finca por instalación
**Fecha:** 2026-09-30
**Decisión:** El modelo asume una sola finca por instalación de la app; no hay selector de finca.
**Razonamiento:** Más simple y encaja con el alcance actual (un caficultor, una finca). Extensible más adelante si hace falta soporte multi-finca.

### DEC-002: Comportamiento ante cambio de número de plantas — ⚠️ SUPERADA por DEC-006
**Fecha:** 2026-09-30
**Decisión:** Solo se recalcula hacia adelante — se usa siempre el número de plantas actual para el costo por planta, sin mantener historial de cambios.
**Razonamiento:** Mantiene el modelo simple (un solo valor vigente); no hay evidencia aún de que el usuario necesite comparar costos históricos por cambios en el tamaño de la finca.
**Nota:** Esta decisión queda sin efecto práctico — ver DEC-006, el costo por planta se quitó del alcance de esta spec. Se conserva en el log para no perder el rastro de la discusión.

### DEC-003: Bloqueo de actividad sin finca registrada
**Fecha:** 2026-09-30
**Decisión:** Si no existe una finca registrada, el sistema bloquea el registro de actividades y dirige al usuario a crear la finca primero (BR-005).
**Razonamiento:** Evita datos huérfanos (actividades sin finca asociada) y da un flujo de onboarding claro para usuarios nuevos.

### DEC-004: Paginación desde el inicio
**Fecha:** 2026-09-30
**Decisión:** El listado "Ver todas las actividades" pagina de a 20 registros (scroll incremental) desde esta primera versión.
**Razonamiento:** Decisión del usuario — preferencia por robustez a futuro aunque el volumen inicial sea bajo, evitando una migración posterior cuando el historial crezca.

### DEC-005: Bloqueo biométrico diferido a Fase 4
**Fecha:** 2026-09-30
**Decisión:** Esta feature no implementa bloqueo biométrico; se mantiene en el roadmap de `AGENTS.md` (Fase 4 — Seguridad y publicación).
**Razonamiento:** Consistencia con el plan de fases ya acordado; evita mezclar alcance de seguridad con la primera feature de datos.

### DEC-006: Se quita el "costo por planta", la inversión se basa solo en actividades
**Fecha:** 2026-09-30
**Decisión:** Se elimina el cálculo de costo por planta (BR-002 removida) de esta spec. La "Inversión total" es simplemente la suma de los montos de todas las actividades registradas. Cada actividad representa tanto mano de obra como compras de insumos/herramientas (fungicidas, elementos de aseo, careta, gafas, rastrillo, secador solar, etc.) — no hay una entidad separada de "elementos" por ahora, todo se registra como actividad.
**Razonamiento:** El costo por planta no aporta valor todavía sin más contexto de uso; simplifica el modelo para esta primera versión. `numero_plantas` se conserva en la Finca como dato descriptivo, pero no participa en ningún cálculo por el momento.
**Impacto pendiente:** La pantalla de Inicio ya construida (`FincaCard` en `app/lib/widgets/finca_card.dart`) todavía muestra "Costo por planta" en la UI con datos de ejemplo — hay que actualizarla para que coincida con esta spec cuando se implemente (Fase 4 del flujo SDD).
