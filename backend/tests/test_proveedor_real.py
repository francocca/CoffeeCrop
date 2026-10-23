import math

import numpy as np
import pytest

from conocimiento.embeddings.base import EmbeddingProvider
from conocimiento.embeddings.sentence_transformers import SentenceTransformersProvider

PREGUNTA_ROYA = "hongo de la hoja del cafeto"
PASAJE_ROYA = (
    "La roya del cafeto es causada por el hongo Hemileia vastatrix, que forma manchas "
    "anaranjadas en el envés de las hojas y provoca su caída."
)
PASAJE_SECADO = (
    "El secado del café pergamino al sol o en silos reduce la humedad del grano "
    "hasta el 10 o 12 por ciento antes de almacenarlo."
)


class ModeloSimulado:
    """Reemplaza a SentenceTransformer: anota lo que recibe y devuelve vectores fijos."""

    def __init__(self, dimension: int = 3, max_tokens: int = 512) -> None:
        self.dimension = dimension
        self.max_tokens = max_tokens
        self.llamadas_encode: list[dict] = []

    def tokenizer(self, texto: str, add_special_tokens: bool) -> dict:
        return {"input_ids": texto.split()}

    def get_embedding_dimension(self) -> int:
        return self.dimension

    def get_max_seq_length(self) -> int:
        return self.max_tokens

    def encode(self, textos, **opciones):
        self.llamadas_encode.append({"textos": list(textos), **opciones})
        return np.ones((len(textos), self.dimension)) / math.sqrt(self.dimension)


class CargadorSimulado:
    def __init__(self, modelo: ModeloSimulado) -> None:
        self.modelo = modelo
        self.nombres_cargados: list[str] = []

    def __call__(self, nombre_modelo: str) -> ModeloSimulado:
        self.nombres_cargados.append(nombre_modelo)
        return self.modelo


def proveedor_simulado(nombre_modelo: str = "intfloat/multilingual-e5-base", **opciones):
    modelo = ModeloSimulado()
    cargador = CargadorSimulado(modelo)
    proveedor = SentenceTransformersProvider(nombre_modelo, cargar_modelo=cargador, **opciones)
    return proveedor, modelo, cargador


# --- Con el modelo simulado (rápidas, sin descargas) ---


def test_cumple_la_interfaz_embedding_provider():
    proveedor, _, _ = proveedor_simulado()

    assert isinstance(proveedor, EmbeddingProvider)


def test_dimension_y_max_tokens_salen_del_modelo():
    # Arrange
    modelo = ModeloSimulado(dimension=1024, max_tokens=8192)

    # Act
    proveedor = SentenceTransformersProvider("BAAI/bge-m3", cargar_modelo=CargadorSimulado(modelo))

    # Assert
    assert proveedor.dimension == 1024
    assert proveedor.max_tokens == 8192


def test_e5_antepone_passage_a_los_documentos_y_query_a_las_preguntas():
    proveedor, modelo, _ = proveedor_simulado("intfloat/multilingual-e5-base")

    proveedor.embed_documents(["texto uno", "texto dos"])
    proveedor.embed_query("una pregunta")

    assert modelo.llamadas_encode[0]["textos"] == ["passage: texto uno", "passage: texto dos"]
    assert modelo.llamadas_encode[1]["textos"] == ["query: una pregunta"]


def test_e5_large_tambien_lleva_prefijos():
    proveedor, modelo, _ = proveedor_simulado("intfloat/multilingual-e5-large")

    proveedor.embed_query("una pregunta")

    assert modelo.llamadas_encode[0]["textos"] == ["query: una pregunta"]


def test_bge_m3_no_lleva_prefijos():
    proveedor, modelo, _ = proveedor_simulado("BAAI/bge-m3")

    proveedor.embed_documents(["texto uno"])
    proveedor.embed_query("una pregunta")

    assert modelo.llamadas_encode[0]["textos"] == ["texto uno"]
    assert modelo.llamadas_encode[1]["textos"] == ["una pregunta"]


def test_pide_vectores_normalizados_en_lotes_de_16_por_defecto():
    proveedor, modelo, _ = proveedor_simulado()

    vectores = proveedor.embed_documents(["texto"])

    assert modelo.llamadas_encode[0]["batch_size"] == 16
    assert modelo.llamadas_encode[0]["normalize_embeddings"] is True
    assert isinstance(vectores, list) and isinstance(vectores[0], list)


def test_el_tamano_de_lote_es_configurable():
    proveedor, modelo, _ = proveedor_simulado(tamano_lote=4)

    proveedor.embed_query("pregunta")

    assert modelo.llamadas_encode[0]["batch_size"] == 4


def test_un_tamano_de_lote_no_positivo_es_un_error():
    with pytest.raises(ValueError):
        proveedor_simulado(tamano_lote=0)


def test_carga_el_modelo_una_sola_vez():
    proveedor, _, cargador = proveedor_simulado()

    proveedor.embed_documents(["uno", "dos"])
    proveedor.embed_query("tres")
    proveedor.contar_tokens("cuatro")

    assert cargador.nombres_cargados == ["intfloat/multilingual-e5-base"]


def test_contar_tokens_usa_el_tokenizador_del_modelo():
    proveedor, _, _ = proveedor_simulado()

    assert proveedor.contar_tokens("roya del cafeto") == 3


# --- Con el modelo real (opcional: pytest -m modelo; descarga ~1 GB la primera vez) ---


# En Windows sin symlinks, huggingface_hub avisa y copia los archivos en vez de enlazarlos.
sin_aviso_de_symlinks = pytest.mark.filterwarnings("ignore:.*symlinks:UserWarning")


@pytest.fixture(scope="module")
def proveedor_e5():
    return SentenceTransformersProvider("intfloat/multilingual-e5-base")


@pytest.mark.modelo
@sin_aviso_de_symlinks
def test_e5_base_expone_dimension_768_y_lee_512_tokens(proveedor_e5):
    assert proveedor_e5.dimension == 768
    assert proveedor_e5.max_tokens == 512


@pytest.mark.modelo
@sin_aviso_de_symlinks
def test_la_pregunta_sobre_el_hongo_queda_mas_cerca_del_pasaje_de_roya(proveedor_e5):
    # Act
    pregunta = np.array(proveedor_e5.embed_query(PREGUNTA_ROYA))
    roya, secado = (np.array(v) for v in proveedor_e5.embed_documents([PASAJE_ROYA, PASAJE_SECADO]))

    # Assert
    assert math.isclose(np.linalg.norm(roya), 1.0, rel_tol=1e-5)
    assert pregunta @ roya > pregunta @ secado


@pytest.mark.modelo
@sin_aviso_de_symlinks
def test_contar_tokens_real_cuenta_al_menos_un_token_por_palabra(proveedor_e5):
    tokens = proveedor_e5.contar_tokens(PASAJE_ROYA)

    assert tokens >= len(PASAJE_ROYA.split())
