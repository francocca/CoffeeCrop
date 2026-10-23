import uuid

import psycopg
import pytest

from conocimiento.db.conexion import conectar, inicializar_db
from conocimiento.errores import DatabaseUnavailableError

TABLAS = ("documento", "fragmento", "embedding", "configuracion")
HUELLA = "a" * 64


def insertar_documento(conexion, categoria="A") -> uuid.UUID:
    documento_id = uuid.uuid4()
    conexion.execute(
        "INSERT INTO documento (id, nombre_archivo, categoria, tipo, sha256, paginas, estado)"
        " VALUES (%s, %s, %s, 'avance', %s, 3, 'indexado')",
        (documento_id, f"{documento_id}.pdf", categoria, HUELLA),
    )
    return documento_id


def contar(conexion, tabla: str) -> int:
    return conexion.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]


@pytest.mark.integration
def test_inicializar_db_crea_la_extension_y_las_tablas(url_db_prueba):
    inicializar_db(url_db_prueba)

    with conectar(url_db_prueba) as conexion:
        existentes = {
            fila[0]
            for fila in conexion.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
        }
        extension = conexion.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()
    assert set(TABLAS) <= existentes
    assert extension is not None


@pytest.mark.integration
def test_inicializar_db_es_idempotente(url_db_prueba):
    inicializar_db(url_db_prueba)

    inicializar_db(url_db_prueba)

    with conectar(url_db_prueba) as conexion:
        assert contar(conexion, "documento") >= 0


@pytest.mark.integration
def test_conectar_registra_el_tipo_vector(conexion):
    resultado = conexion.execute("SELECT '[1,2,3]'::vector").fetchone()[0]

    assert resultado.to_list() == [1.0, 2.0, 3.0]


@pytest.mark.integration
def test_borrar_un_documento_borra_sus_fragmentos_y_vectores(conexion):
    documento_id = insertar_documento(conexion)
    fragmento_id = uuid.uuid4()
    conexion.execute(
        "INSERT INTO fragmento (id, documento_id, orden, texto, pagina_inicio, pagina_fin, tokens)"
        " VALUES (%s, %s, 0, 'texto', 1, 1, 5)",
        (fragmento_id, documento_id),
    )
    conexion.execute(
        "INSERT INTO embedding (fragmento_id, modelo, dimension, vector)"
        " VALUES (%s, 'modelo-prueba', 3, '[1,2,3]')",
        (fragmento_id,),
    )

    conexion.execute("DELETE FROM documento WHERE id = %s", (documento_id,))

    assert contar(conexion, "fragmento") == 0
    assert contar(conexion, "embedding") == 0


@pytest.mark.integration
@pytest.mark.parametrize("categoria", ["A", "B", "R", "C"])
def test_categorias_validas_se_aceptan(conexion, categoria):
    insertar_documento(conexion, categoria)

    assert contar(conexion, "documento") == 1


@pytest.mark.integration
@pytest.mark.parametrize("categoria", ["D", "H", "E", "a"])
def test_categoria_distinta_de_a_b_r_c_se_rechaza(conexion, categoria):
    with pytest.raises(psycopg.errors.CheckViolation):
        insertar_documento(conexion, categoria)


def test_sin_base_disponible_lanza_db_unavailable(monkeypatch):
    # Windows reintenta las conexiones rechazadas hasta agotar la espera.
    monkeypatch.setattr("conocimiento.db.conexion.SEGUNDOS_ESPERA_CONEXION", 1)
    url_sin_servidor = "postgresql://nadie:secreto@127.0.0.1:1/ninguna"

    with pytest.raises(DatabaseUnavailableError) as excepcion:
        conectar(url_sin_servidor)

    assert excepcion.value.code == "DB_UNAVAILABLE"
    assert "127.0.0.1:1" in excepcion.value.mensaje
    assert "secreto" not in excepcion.value.mensaje


def test_url_mal_formada_tambien_lanza_db_unavailable():
    with pytest.raises(DatabaseUnavailableError):
        conectar("esto no es una url")
