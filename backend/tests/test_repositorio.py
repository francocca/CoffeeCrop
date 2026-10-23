from dataclasses import replace

import pytest

from conocimiento.db import repositorio
from conocimiento.db.repositorio import CLAVE_MODELO_ACTIVO, DatosDocumento
from conocimiento.fragmentacion import Fragmento

pytestmark = pytest.mark.integration

MODELO = "intfloat/multilingual-e5-base"
OTRO_MODELO = "BAAI/bge-m3"


def datos_documento(nombre="Avance_465_Siembra_del_Café.pdf", sha256="a" * 64, **cambios):
    datos = DatosDocumento(
        nombre_archivo=nombre,
        categoria="A",
        tipo="avance",
        sha256=sha256,
        paginas=8,
        estado="indexado",
        numero_avance=465,
    )
    return replace(datos, **cambios)


def fragmento(orden: int, pagina_inicio: int = 1, pagina_fin: int = 1) -> Fragmento:
    return Fragmento(
        orden=orden,
        texto=f"Texto del fragmento {orden}.",
        pagina_inicio=pagina_inicio,
        pagina_fin=pagina_fin,
        tokens=4,
        es_tabla=False,
    )


def contar(conexion, tabla: str) -> int:
    return conexion.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]


def documento_con_fragmentos(conexion, cantidad: int = 2, **cambios):
    documento = repositorio.reemplazar_documento(conexion, datos_documento(**cambios))
    ids = repositorio.guardar_fragmentos(conexion, documento, [fragmento(n) for n in range(cantidad)])
    return documento, ids


# --- Documentos ---


def test_crear_un_documento_y_buscarlo_por_nombre(conexion):
    # Act
    creado = repositorio.reemplazar_documento(conexion, datos_documento())
    encontrado = repositorio.buscar_documento(conexion, "Avance_465_Siembra_del_Café.pdf")

    # Assert
    assert encontrado == creado
    assert encontrado.categoria == "A"
    assert encontrado.numero_avance == 465
    assert encontrado.fecha_ingesta is not None


def test_buscar_un_documento_que_no_existe_devuelve_none(conexion):
    assert repositorio.buscar_documento(conexion, "no_existe.pdf") is None


def test_reemplazar_un_documento_borra_el_anterior_con_sus_fragmentos_y_vectores(conexion):
    # Arrange
    anterior, ids = documento_con_fragmentos(conexion)
    repositorio.guardar_embeddings(conexion, MODELO, [(ids[0], [0.1, 0.2, 0.3])])

    # Act
    nuevo = repositorio.reemplazar_documento(conexion, datos_documento(sha256="b" * 64))

    # Assert
    assert nuevo.id != anterior.id
    assert repositorio.buscar_documento(conexion, anterior.nombre_archivo).sha256 == "b" * 64
    assert contar(conexion, "documento") == 1
    assert contar(conexion, "fragmento") == 0
    assert contar(conexion, "embedding") == 0


def test_reemplazar_no_toca_otros_documentos(conexion):
    documento_con_fragmentos(conexion, nombre="otro.pdf")

    repositorio.reemplazar_documento(conexion, datos_documento())

    assert contar(conexion, "documento") == 2
    assert contar(conexion, "fragmento") == 2


# --- Fragmentos ---


def test_guardar_fragmentos_devuelve_sus_ids_en_orden(conexion):
    # Arrange
    documento = repositorio.reemplazar_documento(conexion, datos_documento())
    fragmentos = [fragmento(0, 1, 1), fragmento(1, 1, 2)]

    # Act
    ids = repositorio.guardar_fragmentos(conexion, documento, fragmentos)

    # Assert
    guardados = conexion.execute(
        "SELECT id, orden, pagina_inicio, pagina_fin FROM fragmento ORDER BY orden"
    ).fetchall()
    assert guardados == [(ids[0], 0, 1, 1), (ids[1], 1, 1, 2)]


def test_un_fragmento_sin_documento_no_se_guarda(conexion):
    with pytest.raises(ValueError, match="BR-006"):
        repositorio.guardar_fragmentos(conexion, None, [fragmento(0)])


@pytest.mark.parametrize("paginas", [(0, 1), (3, 2), (None, 1), (1, None)])
def test_un_fragmento_sin_paginas_validas_no_se_guarda_ni_deja_los_demas(conexion, paginas):
    # Arrange
    documento = repositorio.reemplazar_documento(conexion, datos_documento())
    invalido = replace(fragmento(1), pagina_inicio=paginas[0], pagina_fin=paginas[1])

    # Act / Assert
    with pytest.raises(ValueError, match="BR-006"):
        repositorio.guardar_fragmentos(conexion, documento, [fragmento(0), invalido])
    assert contar(conexion, "fragmento") == 0


@pytest.mark.parametrize("categoria", [None, "", "H"])
def test_un_fragmento_sin_categoria_valida_no_se_guarda(conexion, categoria):
    documento = repositorio.reemplazar_documento(conexion, datos_documento())

    with pytest.raises(ValueError, match="BR-006"):
        repositorio.guardar_fragmentos(conexion, replace(documento, categoria=categoria), [fragmento(0)])
    assert contar(conexion, "fragmento") == 0


# --- Embeddings ---


def test_guardar_embeddings_por_modelo_y_contarlos(conexion):
    # Arrange
    _, ids = documento_con_fragmentos(conexion)

    # Act
    repositorio.guardar_embeddings(conexion, MODELO, [(ids[0], [0.1, 0.2, 0.3]), (ids[1], [0.3, 0.2, 0.1])])
    repositorio.guardar_embeddings(conexion, OTRO_MODELO, [(ids[0], [0.5, 0.5])])

    # Assert
    assert repositorio.contar_embeddings(conexion, MODELO) == 2
    assert repositorio.contar_embeddings(conexion, OTRO_MODELO) == 1
    assert repositorio.contar_embeddings(conexion, "modelo-sin-vectores") == 0
    vector, dimension = conexion.execute(
        "SELECT vector, dimension FROM embedding WHERE fragmento_id = %s AND modelo = %s", (ids[0], MODELO)
    ).fetchone()
    assert dimension == 3
    assert vector.to_list() == pytest.approx([0.1, 0.2, 0.3])


def test_contar_embeddings_de_un_solo_documento(conexion):
    documento, ids = documento_con_fragmentos(conexion)
    _, otros_ids = documento_con_fragmentos(conexion, nombre="otro.pdf", cantidad=3)
    repositorio.guardar_embeddings(conexion, MODELO, [(i, [1.0, 0.0]) for i in ids + otros_ids])

    assert repositorio.contar_embeddings(conexion, MODELO, documento.id) == 2
    assert repositorio.contar_embeddings(conexion, MODELO) == 5


def test_vectores_de_dimensiones_distintas_en_un_mismo_lote_son_un_error(conexion):
    _, ids = documento_con_fragmentos(conexion)

    with pytest.raises(ValueError):
        repositorio.guardar_embeddings(conexion, MODELO, [(ids[0], [0.1, 0.2]), (ids[1], [0.1, 0.2, 0.3])])
    assert contar(conexion, "embedding") == 0


# --- Configuración ---


def test_leer_una_clave_que_no_existe_devuelve_none(conexion):
    assert repositorio.leer_configuracion(conexion, CLAVE_MODELO_ACTIVO) is None


def test_escribir_y_cambiar_el_modelo_activo(conexion):
    # Act
    repositorio.escribir_configuracion(conexion, CLAVE_MODELO_ACTIVO, MODELO)
    repositorio.escribir_configuracion(conexion, CLAVE_MODELO_ACTIVO, OTRO_MODELO)

    # Assert
    assert repositorio.leer_configuracion(conexion, CLAVE_MODELO_ACTIVO) == OTRO_MODELO
    assert contar(conexion, "configuracion") == 1


# --- Transacción por documento ---


def test_si_algo_falla_a_mitad_del_documento_no_queda_nada(conexion):
    # Arrange
    class FalloSimulado(Exception):
        pass

    # Act
    with pytest.raises(FalloSimulado):
        with repositorio.transaccion(conexion):
            documento, ids = documento_con_fragmentos(conexion)
            repositorio.guardar_embeddings(conexion, MODELO, [(ids[0], [0.1, 0.2])])
            raise FalloSimulado("el modelo falló al vectorizar")

    # Assert
    assert repositorio.buscar_documento(conexion, documento.nombre_archivo) is None
    assert contar(conexion, "fragmento") == 0
    assert contar(conexion, "embedding") == 0


def test_un_reemplazo_que_falla_conserva_el_documento_anterior(conexion):
    # Arrange
    anterior, _ = documento_con_fragmentos(conexion)

    # Act
    with pytest.raises(ValueError):
        with repositorio.transaccion(conexion):
            nuevo = repositorio.reemplazar_documento(conexion, datos_documento(sha256="b" * 64))
            repositorio.guardar_fragmentos(conexion, nuevo, [fragmento(0, 0, 0)])

    # Assert
    assert repositorio.buscar_documento(conexion, anterior.nombre_archivo) == anterior
    assert contar(conexion, "fragmento") == 2


def test_una_transaccion_que_termina_bien_conserva_todo(conexion):
    with repositorio.transaccion(conexion):
        documento_con_fragmentos(conexion)

    assert contar(conexion, "documento") == 1
    assert contar(conexion, "fragmento") == 2
