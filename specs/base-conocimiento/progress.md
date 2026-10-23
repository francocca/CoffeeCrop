# Progreso de Implementación — Base de Conocimiento Cafetero

## Resumen
- **Tareas completadas:** 2 / 20 (Tarea 3 en revisión)
- **Tarea actual:** Tarea 3 — Esquema de base de datos y conexión
- **Tiempo invertido:** —

## Registro de Tareas
- ✅ **Tarea 1 — Proyecto Python, configuración y errores:** ACEPTADA (2026-10-22, mergeada en el PR #12). Rama: `feat/task-01-proyecto-python`.
  - `backend/pyproject.toml` (dependencias aprobadas de `plan.md` §2; `pytest` con marcadores `integration` y `modelo`, `modelo` excluido por defecto, avisos tratados como error), paquete `conocimiento`, `config.py` (`cargar_config()` lee el entorno en cada llamada) y `errores.py` (`ConocimientoError` base + las tres excepciones con su `code`).
  - Verificado: `python -m venv .venv` + `pip install -e ".[dev]"` en Python 3.14.7 instala sin problemas (torch 2.14.1, sentence-transformers 6.2.0, psycopg 3.3.6, pgvector 0.5.1); `pytest` → 6 pruebas en verde, sin avisos.
  - **Decisiones menores:** la URL por defecto de la base no incluye clave (`postgresql://coffecrop@127.0.0.1:5433/coffecrop`), la clave llega por `DATABASE_URL` (Tarea 2 crea `.env.example`); `MINIMO_SIMILITUD=0.75` y `VENTAJA_BOYACA=0.05` son valores provisionales hasta la Tarea 19; se agregó `backend/src/*.egg-info/` y `backend/.pytest_cache/` a `.gitignore`.
  - **Aviso para la Tarea 2:** `.gitignore` ignora `.env.*`, lo que también ignoraría `backend/.env.example`; hará falta una excepción `!.env.example`.
- ✅ **Tarea 2 — PostgreSQL + pgvector local con Docker:** ACEPTADA (2026-10-22, mergeada en el PR #13). Rama: `feat/task-02-docker-postgres`.
  - `backend/docker-compose.yml` (servicio `db`, imagen `pgvector/pgvector:pg16`, publicado solo en `127.0.0.1:5433`, volumen con nombre `conocimiento_datos`, healthcheck con `pg_isready`; usuario, clave y base obligatorios desde `backend/.env`), `backend/.env.example` (solo valores de ejemplo) y `.gitignore` (`backend/.env` ignorado, excepción `!.env.example` porque `.env.*` también lo ignoraba).
  - Verificado en este equipo: `docker compose up -d --wait` deja `db` en estado *healthy*; `CREATE EXTENSION vector` y `SELECT '[1,2,3]'::vector` funcionan con `psql` dentro del contenedor; un dato escrito sobrevivió a `docker compose down` + `up`; `git check-ignore` confirma que `backend/.env` se ignora y `.env.example` no.
  - `backend/.env` local creado con una clave generada al azar (no se versiona ni se muestra). Quien clone el repo debe copiar `.env.example` a `.env` y cambiar la clave, igual en `POSTGRES_PASSWORD` y `DATABASE_URL`.
  - **Nota:** el volumen quedó con la extensión `vector` ya creada en la base `coffecrop`; `inicializar_db()` (Tarea 3) usa `CREATE EXTENSION IF NOT EXISTS`, así que no choca. El contenedor queda encendido para la Tarea 3.
- 🔄 **Tarea 3 — Esquema de base de datos y conexión:** lista para auditoría (2026-10-22). Rama: `feat/task-03-esquema-conexion`.
  - `db/esquema.sql` (`plan.md` §5, todo con `IF NOT EXISTS`), `db/conexion.py` (`conectar()` y `inicializar_db()`), `tests/conftest.py` (base de prueba aislada `coffecrop_test_<id>`, creada y borrada por sesión; fixture `conexion` con rollback por prueba) y `tests/test_esquema.py`.
  - Verificado: `pytest` → 8 en verde (unitarias); `pytest -m integration` → 12 en verde contra el PostgreSQL de Docker (tablas y extensión creadas, idempotencia, `ON DELETE CASCADE` hasta los vectores, categorías A/B/R/C aceptadas y D/H/E/a rechazadas, tipo `vector` registrado). Tras la corrida no queda ninguna base `coffecrop_test_*`.
  - `DB_UNAVAILABLE`: si la conexión falla, el mensaje dice host y puerto, el motivo de libpq y qué revisar, **sin incluir la clave** (hay una prueba que lo comprueba). También cubre una URL mal formada.
  - **Desvíos declarados:** (1) `addopts` ahora excluye `integration` y `modelo` por defecto (`pytest` = unitarias, `pytest -m integration` = las de base de datos, como dice `tasks.md`); en la Tarea 1 solo excluía `modelo`. (2) `package-data` en `pyproject.toml` para que `esquema.sql` viaje con el paquete. (3) `db/__init__.py`, necesario para el paquete.
  - **Decisión:** `conectar(registrar_vector=True)` registra el tipo `vector` de pgvector; `inicializar_db` lo desactiva porque la extensión aún puede no existir. `Vector` de pgvector 0.5.1 se lee con `.to_list()`.
  - **Pendiente para la Tarea 13 (CLI):** `cargar_config()` lee solo variables de entorno, no `backend/.env`; hoy solo `conftest.py` lo carga (para las pruebas). El CLI deberá cargar `.env` o documentar cómo exportar `DATABASE_URL`.
  - Las pruebas de integración fallan con un mensaje claro si falta `DATABASE_URL` o Docker está apagado (no se omiten en silencio).

## Registro de Rechazos
(ninguno)
