import math

import pytest

from conocimiento.busqueda import buscar
from conocimiento.db import repositorio
from conocimiento.db.repositorio import CLAVE_MODELO_ACTIVO, DatosDocumento
from conocimiento.errores import InvalidQueryError, NoEmbeddingsForModelError
from conocimiento.fragmentacion import Fragmento
from conocimiento.ingesta import ingestar_documento
from fakes import FakeEmbeddingProvider

MODELO = "modelo-768"
OTRO_MODELO = "modelo-1024"
PREGUNTA = "¿Cuándo sembrar café en Boyacá?"
SIN_MINIMO = -1.0


class ProveedorFijo:
    """Devuelve siempre el mismo vector de pregunta; los de los fragmentos se arman a mano."""

    def __init__(self, nombre_modelo: str = MODELO, vector=(1.0, 0.0)) -> None:
        self.nombre_modelo = nombre_modelo
        self.dimension = len(vector)
        self.max_tokens = 512
        self._vector = list(vector)

    def contar_tokens(self, texto: str) -> int:
        return len(texto.split())

    def embed_documents(self, textos):
        raise AssertionError("buscar no debe vectorizar fragmentos")

    def embed_query(self, texto: str):
        return self._vector


def con_similitud(similitud: float) -> list[float]:
    # Con la pregunta en [1, 0], la similitud coseno de [c, √(1 − c²)] es exactamente c.
    return [similitud, math.sqrt(1 - similitud**2)]


def guardar(conexion, nombre: str, categoria: str, similitudes, modelo=MODELO, vectores=None):
    """Un documento con un fragmento por similitud; el texto de cada uno dice su puntaje."""
    documento = repositorio.reemplazar_documento(
        conexion,
        DatosDocumento(
            nombre_archivo=nombre,
            categoria=categoria,
            tipo="avance",
            sha256=nombre.ljust(64, "0")[:64],
            paginas=len(similitudes),
            estado="indexado",
        ),
    )
    fragmentos = [
        Fragmento(
            orden=n,
            texto=f"{nombre} {similitud}",
            pagina_inicio=n + 1,
            pagina_fin=n + 1,
            tokens=2,
            es_tabla=False,
        )
        for n, similitud in enumerate(similitudes)
    ]
    ids = repositorio.guardar_fragmentos(conexion, documento, fragmentos)
    vectores = vectores or [con_similitud(similitud) for similitud in similitudes]
    repositorio.guardar_embeddings(conexion, modelo, list(zip(ids, vectores)))
    return ids


def activar(conexion, modelo=MODELO):
    repositorio.escribir_configuracion(conexion, CLAVE_MODELO_ACTIVO, modelo)


def textos(resultados) -> list[str]:
    return [resultado.texto for resultado in resultados]


# --- Validación de la pregunta (sin base de datos: se rechaza antes de consultar) ---


@pytest.mark.parametrize("pregunta", ["", "   \n ", None])
def test_una_pregunta_vacia_se_rechaza(pregunta):
    with pytest.raises(InvalidQueryError, match="vacía"):
        buscar(None, ProveedorFijo(), pregunta)


def test_una_pregunta_de_mas_de_mil_caracteres_se_rechaza():
    with pytest.raises(InvalidQueryError, match="1001 caracteres"):
        buscar(None, ProveedorFijo(), "a" * 1001)


def test_k_menor_que_uno_se_rechaza():
    with pytest.raises(InvalidQueryError, match="k debe ser"):
        buscar(None, ProveedorFijo(), PREGUNTA, k=0)


def test_una_region_desconocida_se_rechaza():
    with pytest.raises(InvalidQueryError, match="Región desconocida"):
        buscar(None, ProveedorFijo(), PREGUNTA, region="huila")


# --- Búsqueda ---


@pytest.mark.integration
def test_devuelve_los_resultados_de_mayor_a_menor_con_sus_datos(conexion):
    # Arrange
    guardar(conexion, "Avance_1.pdf", "B", [0.80, 0.95])
    guardar(conexion, "Avance_2.pdf", "C", [0.90])
    activar(conexion)

    # Act
    resultados = buscar(conexion, ProveedorFijo(), PREGUNTA, minimo_similitud=SIN_MINIMO)

    # Assert
    assert textos(resultados) == ["Avance_1.pdf 0.95", "Avance_2.pdf 0.9", "Avance_1.pdf 0.8"]
    primero = resultados[0]
    assert (primero.documento, primero.pagina_inicio, primero.pagina_fin, primero.categoria) == (
        "Avance_1.pdf", 2, 2, "B",
    )
    assert primero.puntaje == pytest.approx(0.95)


@pytest.mark.integration
def test_k_limita_la_cantidad_de_resultados(conexion):
    guardar(conexion, "Avance_1.pdf", "B", [0.99, 0.98, 0.97, 0.96, 0.95, 0.94, 0.93])
    activar(conexion)

    por_defecto = buscar(conexion, ProveedorFijo(), PREGUNTA, minimo_similitud=SIN_MINIMO)
    dos = buscar(conexion, ProveedorFijo(), PREGUNTA, k=2, minimo_similitud=SIN_MINIMO)

    assert len(por_defecto) == 5
    assert textos(dos) == ["Avance_1.pdf 0.99", "Avance_1.pdf 0.98"]


@pytest.mark.integration
def test_el_minimo_deja_fuera_lo_poco_relacionado(conexion):
    guardar(conexion, "Avance_1.pdf", "B", [0.90, 0.75, 0.60])
    activar(conexion)

    resultados = buscar(conexion, ProveedorFijo(), PREGUNTA, minimo_similitud=0.75)

    assert textos(resultados) == ["Avance_1.pdf 0.9", "Avance_1.pdf 0.75"]


@pytest.mark.integration
def test_si_nada_supera_el_minimo_devuelve_una_lista_vacia(conexion):
    # BR-007
    guardar(conexion, "Avance_1.pdf", "A", [0.60, 0.50])
    activar(conexion)

    resultados = buscar(
        conexion, ProveedorFijo(), PREGUNTA, region="boyaca", minimo_similitud=0.75
    )

    assert resultados == []


@pytest.mark.integration
def test_el_minimo_por_defecto_sale_de_la_configuracion(conexion, monkeypatch):
    guardar(conexion, "Avance_1.pdf", "B", [0.90, 0.70])
    activar(conexion)
    monkeypatch.setenv("MINIMO_SIMILITUD", "0.8")

    resultados = buscar(conexion, ProveedorFijo(), PREGUNTA)

    assert textos(resultados) == ["Avance_1.pdf 0.9"]


# --- Ventaja de Boyacá (BR-005) ---


@pytest.fixture
def boyaca_y_general(conexion):
    guardar(conexion, "Avance_General.pdf", "B", [0.90])
    guardar(conexion, "Avance_Boyaca.pdf", "A", [0.87])
    guardar(conexion, "Avance_Vecino.pdf", "R", [0.89])
    activar(conexion)
    return conexion


@pytest.mark.integration
def test_sin_region_se_ordena_solo_por_similitud(boyaca_y_general):
    resultados = buscar(
        boyaca_y_general, ProveedorFijo(), PREGUNTA, minimo_similitud=SIN_MINIMO, ventaja_boyaca=0.05
    )

    assert textos(resultados) == [
        "Avance_General.pdf 0.9", "Avance_Vecino.pdf 0.89", "Avance_Boyaca.pdf 0.87",
    ]


@pytest.mark.integration
def test_con_region_boyaca_la_categoria_a_sube_pero_conserva_su_puntaje_real(boyaca_y_general):
    # Act
    resultados = buscar(
        boyaca_y_general,
        ProveedorFijo(),
        PREGUNTA,
        region="boyaca",
        minimo_similitud=SIN_MINIMO,
        ventaja_boyaca=0.05,
    )

    # Assert: 0,87 + 0,05 supera a 0,90; la R no recibe ventaja.
    assert textos(resultados) == [
        "Avance_Boyaca.pdf 0.87", "Avance_General.pdf 0.9", "Avance_Vecino.pdf 0.89",
    ]
    assert resultados[0].puntaje == pytest.approx(0.87)
    assert resultados[0].categoria == "A"


@pytest.mark.integration
def test_la_ventaja_no_rescata_un_fragmento_por_debajo_del_minimo(conexion):
    guardar(conexion, "Avance_Boyaca.pdf", "A", [0.72])
    guardar(conexion, "Avance_General.pdf", "B", [0.80])
    activar(conexion)

    resultados = buscar(
        conexion, ProveedorFijo(), PREGUNTA, region="boyaca", minimo_similitud=0.75, ventaja_boyaca=0.05
    )

    assert textos(resultados) == ["Avance_General.pdf 0.8"]


# --- Modelos (BR-004) ---


@pytest.mark.integration
def test_solo_compara_contra_vectores_del_modelo_activo(conexion):
    # Arrange: el otro modelo tiene otra dimensión y un fragmento idéntico a su pregunta.
    guardar(conexion, "Avance_1.pdf", "B", [0.80])
    guardar(conexion, "Avance_2.pdf", "B", [1.0], modelo=OTRO_MODELO, vectores=[[1.0, 0.0, 0.0]])
    activar(conexion, MODELO)

    # Act
    del_activo = buscar(conexion, ProveedorFijo(), PREGUNTA, minimo_similitud=SIN_MINIMO)
    activar(conexion, OTRO_MODELO)
    del_otro = buscar(
        conexion,
        ProveedorFijo(OTRO_MODELO, vector=(1.0, 0.0, 0.0)),
        PREGUNTA,
        minimo_similitud=SIN_MINIMO,
    )

    # Assert
    assert textos(del_activo) == ["Avance_1.pdf 0.8"]
    assert textos(del_otro) == ["Avance_2.pdf 1.0"]


@pytest.mark.integration
def test_sin_modelo_activo_no_hay_vectores_que_buscar(conexion):
    guardar(conexion, "Avance_1.pdf", "B", [0.80])

    with pytest.raises(NoEmbeddingsForModelError, match="ninguno"):
        buscar(conexion, ProveedorFijo(), PREGUNTA)


@pytest.mark.integration
def test_un_modelo_activo_sin_vectores_es_un_error(conexion):
    guardar(conexion, "Avance_1.pdf", "B", [0.80], modelo=OTRO_MODELO, vectores=[[1.0, 0.0, 0.0]])
    activar(conexion, MODELO)

    with pytest.raises(NoEmbeddingsForModelError, match=MODELO):
        buscar(conexion, ProveedorFijo(), PREGUNTA)


@pytest.mark.integration
def test_un_proveedor_de_otro_modelo_no_puede_buscar(conexion):
    guardar(conexion, "Avance_1.pdf", "B", [0.80])
    activar(conexion, MODELO)

    with pytest.raises(ValueError, match="modelo activo es modelo-768"):
        buscar(conexion, ProveedorFijo(OTRO_MODELO), PREGUNTA)


# --- De punta a punta con la ingesta ---


@pytest.mark.integration
def test_encuentra_el_pasaje_de_un_documento_ingerido(conexion, tmp_path):
    # Arrange
    proveedor = FakeEmbeddingProvider()
    paginas = {
        "Avance_100_Roya.pdf": "La roya del cafeto es un hongo que ataca la hoja y causa defoliación.",
        "Avance_200_Secado.pdf": "El secado del grano en silos requiere controlar la humedad final.",
    }
    for nombre, texto in paginas.items():
        ruta = tmp_path / nombre
        ruta.write_bytes(b"%PDF")
        ingestar_documento(
            conexion, ruta, "B", "avance", proveedor, extractor=lambda _ruta, t=texto: [t * 40]
        )
    activar(conexion, proveedor.nombre_modelo)

    # Act
    resultados = buscar(conexion, proveedor, "hongo en la hoja del cafeto", minimo_similitud=SIN_MINIMO)

    # Assert
    assert resultados[0].documento == "Avance_100_Roya.pdf"
    assert resultados[0].pagina_inicio == 1
