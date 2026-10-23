from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from psycopg.conninfo import conninfo_to_dict

from conocimiento.config import cargar_config
from conocimiento.errores import DatabaseUnavailableError

RUTA_ESQUEMA = Path(__file__).with_name("esquema.sql")
SEGUNDOS_ESPERA_CONEXION = 5


def conectar(database_url: str | None = None, registrar_vector: bool = True) -> psycopg.Connection:
    url = database_url or cargar_config().database_url
    try:
        conexion = psycopg.connect(url, connect_timeout=SEGUNDOS_ESPERA_CONEXION)
    except psycopg.Error as error:
        raise DatabaseUnavailableError(_mensaje_sin_conexion(url, error)) from error
    if registrar_vector:
        # Falla si la extensión aún no existe: inicializar_db conecta sin registrar.
        register_vector(conexion)
    return conexion


def inicializar_db(database_url: str | None = None) -> None:
    esquema = RUTA_ESQUEMA.read_text(encoding="utf-8")
    with conectar(database_url, registrar_vector=False) as conexion:
        conexion.execute(esquema)


def _mensaje_sin_conexion(url: str, error: psycopg.Error) -> str:
    try:
        datos = conninfo_to_dict(url)
        destino = f"{datos.get('host', 'localhost')}:{datos.get('port', 5432)}"
    except psycopg.Error:
        destino = "la dirección indicada en DATABASE_URL"
    motivo = str(error).strip().splitlines()[-1] if str(error).strip() else "sin detalle"
    return (
        f"No se pudo conectar a la base de datos en {destino} ({motivo}). "
        "Revisa que Docker esté encendido (docker compose up -d --wait en backend/) "
        "y que DATABASE_URL tenga el usuario, la clave y el puerto correctos."
    )
