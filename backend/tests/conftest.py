import os
import uuid

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from conocimiento.config import cargar_archivo_env
from conocimiento.db.conexion import conectar, inicializar_db

cargar_archivo_env()


@pytest.fixture(scope="session")
def url_db_prueba():
    url_admin = os.environ.get("DATABASE_URL")
    if not url_admin:
        pytest.fail(
            "Las pruebas de integración necesitan DATABASE_URL (backend/.env) "
            "y el PostgreSQL de Docker encendido: docker compose up -d --wait"
        )
    nombre = f"coffecrop_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(url_admin, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nombre)))
    try:
        yield make_conninfo(url_admin, dbname=nombre)
    finally:
        with psycopg.connect(url_admin, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(nombre))
            )


@pytest.fixture
def conexion(url_db_prueba):
    inicializar_db(url_db_prueba)
    with conectar(url_db_prueba) as conexion_prueba:
        yield conexion_prueba
        # La conexión es autocommit (lo escrito ya está confirmado): se limpia vaciando las tablas.
        conexion_prueba.execute("TRUNCATE documento, configuracion CASCADE")
