import pytest

from conocimiento.db import repositorio
from conocimiento.ingesta import ingestar_documento
from fakes import FakeEmbeddingProvider

pytestmark = pytest.mark.integration

NOMBRE = "Avance_465_Siembra_del_Café.pdf"
# Con max_tokens = 120 el tamaño objetivo es 60 palabras: varias páginas dan varios fragmentos.
MAX_TOKENS = 120

ORACIONES = [
    "La siembra del café en Boyacá se recomienda al comienzo de la temporada de lluvias.",
    "Las plántulas deben salir del almácigo con buen desarrollo de raíces y hojas sanas.",
    "El hoyo de siembra se prepara con anticipación y se mezcla el suelo con materia orgánica.",
    "La densidad de siembra depende de la variedad, la pendiente y el brillo solar de la zona.",
    "Durante el primer año conviene controlar las arvenses alrededor de cada planta joven.",
]
PAGINA = " ".join(ORACIONES)
PAGINAS = [PAGINA, PAGINA, PAGINA, PAGINA]
TABLA = (
    "Mes 1 2 3 4 5 6 7 8 9 10 11 12\n"
    "Lluvia 45,2 78,1 120,4 210,3 198,7 95,0 60,2 72,8 140,5 230,1 185,6 80,3"
)


class ExtractorSimulado:
    def __init__(self, paginas=None, error: Exception | None = None) -> None:
        self.paginas = PAGINAS if paginas is None else paginas
        self.error = error
        self.llamadas = 0

    def __call__(self, ruta):
        self.llamadas += 1
        if self.error:
            raise self.error
        return self.paginas


class ProveedorQueFalla(FakeEmbeddingProvider):
    def embed_documents(self, textos):
        raise RuntimeError("el modelo se quedó sin memoria")


@pytest.fixture
def pdf(tmp_path):
    ruta = tmp_path / NOMBRE
    ruta.write_bytes(b"%PDF contenido version 1")
    return ruta


@pytest.fixture
def proveedor():
    return FakeEmbeddingProvider(max_tokens=MAX_TOKENS)


def contar(conexion, tabla: str) -> int:
    return conexion.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]


def ingestar(conexion, pdf, proveedor, extractor=None, categoria="A", tipo="avance"):
    return ingestar_documento(
        conexion, pdf, categoria, tipo, proveedor, extractor or ExtractorSimulado()
    )


# --- Ingesta nueva ---


def test_un_documento_nuevo_queda_indexado_con_fragmentos_y_vectores(conexion, pdf, proveedor):
    # Act
    resultado = ingestar(conexion, pdf, proveedor)

    # Assert
    documento = repositorio.buscar_documento(conexion, NOMBRE)
    assert resultado.estado == "indexado"
    assert resultado.fragmentos_creados > 1
    assert resultado.fragmentos_descartados == 0
    assert resultado.motivo is None
    assert resultado.segundos > 0
    assert documento.estado == "indexado"
    assert (documento.categoria, documento.tipo, documento.paginas) == ("A", "avance", 4)
    assert documento.numero_avance == 465
    assert contar(conexion, "fragmento") == resultado.fragmentos_creados
    assert repositorio.contar_embeddings(conexion, proveedor.nombre_modelo) == resultado.fragmentos_creados


def test_los_fragmentos_guardan_paginas_validas(conexion, pdf, proveedor):
    ingestar(conexion, pdf, proveedor)

    paginas = conexion.execute("SELECT pagina_inicio, pagina_fin FROM fragmento").fetchall()
    assert all(1 <= inicio <= fin <= 4 for inicio, fin in paginas)


def test_un_documento_del_manual_no_lleva_numero_de_avance(conexion, tmp_path, proveedor):
    ruta = tmp_path / "ManualDelCafeteroColombianoTomo2.pdf"
    ruta.write_bytes(b"%PDF manual")

    ingestar(conexion, ruta, proveedor, categoria="B", tipo="manual")

    assert repositorio.buscar_documento(conexion, ruta.name).numero_avance is None


# --- Repetida, cambiada y con otro modelo (BR-003) ---


def test_repetir_la_ingesta_sin_cambios_no_duplica_nada(conexion, pdf, proveedor):
    # Arrange
    primera = ingestar(conexion, pdf, proveedor)
    extractor = ExtractorSimulado()

    # Act
    segunda = ingestar(conexion, pdf, proveedor, extractor)

    # Assert
    assert segunda.estado == "omitido"
    assert segunda.motivo == "ya indexado con el modelo activo"
    assert segunda.fragmentos_creados == 0
    assert extractor.llamadas == 0
    assert contar(conexion, "documento") == 1
    assert contar(conexion, "fragmento") == primera.fragmentos_creados
    assert contar(conexion, "embedding") == primera.fragmentos_creados


def test_un_documento_cambiado_reemplaza_al_anterior(conexion, pdf, proveedor):
    # Arrange
    ingestar(conexion, pdf, proveedor)
    anterior = repositorio.buscar_documento(conexion, NOMBRE)
    pdf.write_bytes(b"%PDF contenido version 2")
    paginas_nuevas = [PAGINA] * 5

    # Act
    resultado = ingestar(conexion, pdf, proveedor, ExtractorSimulado(paginas_nuevas))

    # Assert
    nuevo = repositorio.buscar_documento(conexion, NOMBRE)
    assert resultado.estado == "indexado"
    assert nuevo.id != anterior.id
    assert nuevo.sha256 != anterior.sha256
    assert nuevo.paginas == 5
    assert contar(conexion, "documento") == 1
    assert contar(conexion, "fragmento") == resultado.fragmentos_creados
    assert contar(conexion, "embedding") == resultado.fragmentos_creados


def test_mismo_documento_sin_vectores_del_modelo_activo_solo_se_vectoriza(conexion, pdf, proveedor):
    # Arrange
    primera = ingestar(conexion, pdf, proveedor)
    otro_modelo = FakeEmbeddingProvider(nombre_modelo="fake-bge-m3", dimension=128, max_tokens=MAX_TOKENS)
    extractor = ExtractorSimulado()

    # Act
    resultado = ingestar(conexion, pdf, otro_modelo, extractor)

    # Assert
    assert resultado.estado == "vectorizado"
    assert extractor.llamadas == 0
    assert contar(conexion, "fragmento") == primera.fragmentos_creados
    assert repositorio.contar_embeddings(conexion, "fake-bge-m3") == primera.fragmentos_creados
    assert repositorio.contar_embeddings(conexion, proveedor.nombre_modelo) == primera.fragmentos_creados


# --- Sin texto (BR-002) ---


def test_un_documento_sin_texto_legible_se_marca_y_no_crea_fragmentos(conexion, pdf, proveedor):
    resultado = ingestar(conexion, pdf, proveedor, ExtractorSimulado(["Portada", "", "  "]))

    assert resultado.estado == "sin_texto"
    assert repositorio.buscar_documento(conexion, NOMBRE).estado == "sin_texto"
    assert contar(conexion, "fragmento") == 0
    assert contar(conexion, "embedding") == 0


def test_un_documento_sin_texto_y_sin_cambios_se_omite_la_segunda_vez(conexion, pdf, proveedor):
    ingestar(conexion, pdf, proveedor, ExtractorSimulado(["Portada"]))
    extractor = ExtractorSimulado(["Portada"])

    resultado = ingestar(conexion, pdf, proveedor, extractor)

    assert resultado.estado == "omitido"
    assert extractor.llamadas == 0


# --- Errores ---


def test_un_error_al_extraer_se_marca_y_no_se_propaga(conexion, pdf, proveedor):
    # Act
    resultado = ingestar(conexion, pdf, proveedor, ExtractorSimulado(error=OSError("PDF dañado")))

    # Assert
    assert resultado.estado == "error"
    assert "PDF dañado" in resultado.motivo
    assert repositorio.buscar_documento(conexion, NOMBRE).estado == "error"
    assert contar(conexion, "fragmento") == 0


def test_un_error_al_vectorizar_no_deja_fragmentos_a_medias(conexion, pdf):
    resultado = ingestar(conexion, pdf, ProveedorQueFalla(max_tokens=MAX_TOKENS))

    assert resultado.estado == "error"
    assert "sin memoria" in resultado.motivo
    assert contar(conexion, "fragmento") == 0
    assert contar(conexion, "embedding") == 0


def test_un_reemplazo_que_falla_conserva_la_version_anterior_y_se_reintenta(conexion, pdf, proveedor):
    # Arrange
    primera = ingestar(conexion, pdf, proveedor)
    pdf.write_bytes(b"%PDF contenido version 2")

    # Act
    fallida = ingestar(conexion, pdf, ProveedorQueFalla(max_tokens=MAX_TOKENS))
    reintento = ingestar(conexion, pdf, proveedor)

    # Assert
    assert fallida.estado == "error"
    assert contar(conexion, "fragmento") == reintento.fragmentos_creados
    assert reintento.estado == "indexado"
    assert primera.fragmentos_creados == reintento.fragmentos_creados
    assert repositorio.buscar_documento(conexion, NOMBRE).estado == "indexado"


def test_un_archivo_que_no_existe_es_un_error_informado(conexion, tmp_path, proveedor):
    resultado = ingestar(conexion, tmp_path / "no_existe.pdf", proveedor)

    assert resultado.estado == "error"
    assert resultado.motivo


# --- Tablas por categoría (Tarea 8) ---


def test_las_tablas_se_descartan_fuera_de_la_categoria_a(conexion, pdf, proveedor):
    paginas = [*PAGINAS, TABLA]

    en_b = ingestar(conexion, pdf, proveedor, ExtractorSimulado(paginas), categoria="B")

    assert en_b.fragmentos_descartados >= 1
    assert contar(conexion, "fragmento") == en_b.fragmentos_creados
    assert conexion.execute("SELECT count(*) FROM fragmento WHERE es_tabla").fetchone()[0] == 0


def test_las_tablas_se_conservan_en_la_categoria_a(conexion, pdf, proveedor):
    paginas = [*PAGINAS, TABLA]

    en_a = ingestar(conexion, pdf, proveedor, ExtractorSimulado(paginas), categoria="A")

    assert en_a.fragmentos_descartados == 0
    assert conexion.execute("SELECT count(*) FROM fragmento WHERE es_tabla").fetchone()[0] >= 1
