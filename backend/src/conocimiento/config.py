import os
from dataclasses import dataclass
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
ARCHIVO_ENV = RAIZ_PROYECTO / "backend" / ".env"

# La clave de la base no tiene valor por defecto: viene en DATABASE_URL (ver .env.example).
_DATABASE_URL = "postgresql://coffecrop@127.0.0.1:5433/coffecrop"
_PDFTOTEXT_BIN = "pdftotext"
_CARPETA_BASE_CONOCIMIENTO = RAIZ_PROYECTO / "docs" / "base_conocimiento"
_MODELO_EMBEDDINGS = "intfloat/multilingual-e5-base"
# Provisionales hasta calibrarlos con las preguntas de prueba (Tarea 19).
_MINIMO_SIMILITUD = 0.75
_VENTAJA_BOYACA = 0.05


@dataclass(frozen=True)
class Config:
    database_url: str
    pdftotext_bin: str
    carpeta_base_conocimiento: Path
    modelo_embeddings: str
    minimo_similitud: float
    ventaja_boyaca: float


def cargar_config() -> Config:
    entorno = os.environ
    return Config(
        database_url=entorno.get("DATABASE_URL", _DATABASE_URL),
        pdftotext_bin=entorno.get("PDFTOTEXT_BIN", _PDFTOTEXT_BIN),
        carpeta_base_conocimiento=Path(
            entorno.get("CARPETA_BASE_CONOCIMIENTO", _CARPETA_BASE_CONOCIMIENTO)
        ),
        modelo_embeddings=entorno.get("MODELO_EMBEDDINGS", _MODELO_EMBEDDINGS),
        minimo_similitud=float(entorno.get("MINIMO_SIMILITUD", _MINIMO_SIMILITUD)),
        ventaja_boyaca=float(entorno.get("VENTAJA_BOYACA", _VENTAJA_BOYACA)),
    )


def cargar_archivo_env(ruta: Path = ARCHIVO_ENV) -> None:
    """Lleva las líneas CLAVE=valor de backend/.env al entorno, sin pisar variables ya definidas."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())
