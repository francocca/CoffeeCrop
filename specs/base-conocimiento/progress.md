# Progreso de Implementación — Base de Conocimiento Cafetero

## Resumen
- **Tareas completadas:** 0 / 20 (Tarea 1 en revisión)
- **Tarea actual:** Tarea 1 — Proyecto Python, configuración y errores
- **Tiempo invertido:** —

## Registro de Tareas
- 🔄 **Tarea 1 — Proyecto Python, configuración y errores:** lista para auditoría (2026-10-21). Rama: `feat/task-01-proyecto-python`.
  - `backend/pyproject.toml` (dependencias aprobadas de `plan.md` §2; `pytest` con marcadores `integration` y `modelo`, `modelo` excluido por defecto, avisos tratados como error), paquete `conocimiento`, `config.py` (`cargar_config()` lee el entorno en cada llamada) y `errores.py` (`ConocimientoError` base + las tres excepciones con su `code`).
  - Verificado: `python -m venv .venv` + `pip install -e ".[dev]"` en Python 3.14.7 instala sin problemas (torch 2.14.1, sentence-transformers 6.2.0, psycopg 3.3.6, pgvector 0.5.1); `pytest` → 6 pruebas en verde, sin avisos.
  - **Decisiones menores:** la URL por defecto de la base no incluye clave (`postgresql://coffecrop@127.0.0.1:5433/coffecrop`), la clave llega por `DATABASE_URL` (Tarea 2 crea `.env.example`); `MINIMO_SIMILITUD=0.75` y `VENTAJA_BOYACA=0.05` son valores provisionales hasta la Tarea 19; se agregó `backend/src/*.egg-info/` y `backend/.pytest_cache/` a `.gitignore`.
  - **Aviso para la Tarea 2:** `.gitignore` ignora `.env.*`, lo que también ignoraría `backend/.env.example`; hará falta una excepción `!.env.example`.

## Registro de Rechazos
(ninguno)
