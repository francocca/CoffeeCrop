import math

import pytest

from conocimiento.embeddings.base import EmbeddingProvider
from fakes import FakeEmbeddingProvider

PREGUNTA_ROYA = "hongo de la hoja del cafeto"
PASAJE_ROYA = "La roya es un hongo que ataca la hoja del cafeto y causa defoliación."
PASAJE_SECADO = "El secado del grano en el silo reduce la humedad hasta el 11 por ciento."


def similitud(vector_a: list[float], vector_b: list[float]) -> float:
    return sum(a * b for a, b in zip(vector_a, vector_b))


def test_cumple_la_interfaz_embedding_provider():
    assert isinstance(FakeEmbeddingProvider(), EmbeddingProvider)


def test_el_mismo_texto_da_el_mismo_vector():
    # Arrange
    primero = FakeEmbeddingProvider()
    segundo = FakeEmbeddingProvider()

    # Act
    vector_primero = primero.embed_query(PASAJE_ROYA)
    vector_segundo = segundo.embed_documents([PASAJE_ROYA])[0]

    # Assert
    assert vector_primero == vector_segundo


def test_los_vectores_estan_normalizados_y_tienen_la_dimension_configurada():
    proveedor = FakeEmbeddingProvider(dimension=64)

    vectores = proveedor.embed_documents([PASAJE_ROYA, PASAJE_SECADO])

    for vector in vectores:
        assert len(vector) == 64
        assert math.isclose(math.sqrt(sum(valor * valor for valor in vector)), 1.0)


def test_textos_con_palabras_en_comun_quedan_mas_cerca():
    # Arrange
    proveedor = FakeEmbeddingProvider()

    # Act
    pregunta = proveedor.embed_query(PREGUNTA_ROYA)
    roya, secado = proveedor.embed_documents([PASAJE_ROYA, PASAJE_SECADO])

    # Assert
    assert similitud(pregunta, roya) > similitud(pregunta, secado)


def test_no_distingue_mayusculas():
    proveedor = FakeEmbeddingProvider()

    assert proveedor.embed_query("Roya del Cafeto") == proveedor.embed_query("roya del cafeto")


def test_permite_configurar_modelo_dimension_y_max_tokens():
    proveedor = FakeEmbeddingProvider(nombre_modelo="fake-bge-m3", dimension=1024, max_tokens=8192)

    assert proveedor.nombre_modelo == "fake-bge-m3"
    assert proveedor.dimension == 1024
    assert proveedor.max_tokens == 8192
    assert len(proveedor.embed_query(PASAJE_ROYA)) == 1024


def test_cuenta_tokens_por_palabra():
    assert FakeEmbeddingProvider().contar_tokens("La roya, del cafeto.") == 4


def test_un_texto_sin_palabras_es_un_error():
    with pytest.raises(ValueError):
        FakeEmbeddingProvider().embed_query("  ... ")
