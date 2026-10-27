import pytest

from conocimiento import cli
from conocimiento.db import repositorio
from conocimiento.ingesta import (
    formatear_informe,
    ingestar_carpeta,
    leer_manifiesto,
    tipo_desde_nombre,
)
from fakes import FakeEmbeddingProvider

AVANCE = "Avance_465_Siembra_del_Café.pdf"
MANUAL = "ManualDelCafeteroColombianoTomo2.pdf"
FALTANTE = "Avance_999_No_Descargado.pdf"
MANIFIESTO = (
    "﻿archivo,categoria,carpeta_origen\n"
    f"{AVANCE},A,.\n"
    f"{MANUAL},B,manual_cafetero\n"
    f"{FALTANTE},C,.\n"
)
PAGINA = " ".join(
    [
        "La siembra del café en Boyacá se recomienda al comienzo de la temporada de lluvias.",
        "Las plántulas deben salir del almácigo con buen desarrollo de raíces y hojas sanas.",
        "El hoyo de siembra se prepara con anticipación y se mezcla con materia orgánica.",
        "La densidad de siembra depende de la variedad, la pendiente y el brillo solar.",
        "Durante el primer año conviene controlar las arvenses alrededor de cada planta.",
    ]
)
MAX_TOKENS = 120


class ExtractorSimulado:
    def __init__(self) -> None:
        self.rutas = []

    def __call__(self, ruta):
        self.rutas.append(ruta.name)
        return [PAGINA] * 4


@pytest.fixture
def carpeta(tmp_path):
    (tmp_path / "_manifiesto.csv").write_text(MANIFIESTO, encoding="utf-8")
    (tmp_path / AVANCE).write_bytes(b"%PDF avance")
    (tmp_path / MANUAL).write_bytes(b"%PDF manual")
    return tmp_path


@pytest.fixture
def proveedor():
    return FakeEmbeddingProvider(max_tokens=MAX_TOKENS)


def contar(conexion, tabla: str) -> int:
    return conexion.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]


# --- Manifiesto y tipo (sin base de datos) ---


def test_leer_manifiesto_ignora_el_bom_y_lee_las_tres_columnas(carpeta):
    filas = leer_manifiesto(carpeta)

    assert [(f.archivo, f.categoria, f.carpeta_origen) for f in filas] == [
        (AVANCE, "A", "."),
        (MANUAL, "B", "manual_cafetero"),
        (FALTANTE, "C", "."),
    ]


def test_leer_manifiesto_admite_nombres_con_comas(tmp_path):
    (tmp_path / "_manifiesto.csv").write_text(
        'archivo,categoria,carpeta_origen\n"Avance_520_Nitrógeno,_Fósforo_y_Potasio.pdf",B,.\n',
        encoding="utf-8",
    )

    filas = leer_manifiesto(tmp_path)

    assert filas[0].archivo == "Avance_520_Nitrógeno,_Fósforo_y_Potasio.pdf"


def test_el_tipo_se_deduce_del_nombre():
    assert tipo_desde_nombre(MANUAL) == "manual"
    assert tipo_desde_nombre(AVANCE) == "avance"


# --- Ingesta de la carpeta ---


@pytest.mark.integration
def test_ingestar_carpeta_procesa_cada_fila_y_un_faltante_no_detiene_a_los_demas(
    conexion, carpeta, proveedor
):
    # Arrange
    extractor = ExtractorSimulado()

    # Act
    informe = ingestar_carpeta(conexion, carpeta, proveedor, extractor)

    # Assert
    estados = {r.nombre_archivo: r.estado for r in informe.resultados}
    assert estados == {AVANCE: "indexado", MANUAL: "indexado", FALTANTE: "error"}
    assert extractor.rutas == [AVANCE, MANUAL]
    assert informe.con_estado("error")[0].motivo == "no existe en la carpeta"
    assert informe.fragmentos_creados == contar(conexion, "fragmento") > 0
    assert informe.segundos > 0


@pytest.mark.integration
def test_el_tipo_y_el_numero_de_avance_salen_del_nombre(conexion, carpeta, proveedor):
    ingestar_carpeta(conexion, carpeta, proveedor, ExtractorSimulado())

    avance = repositorio.buscar_documento(conexion, AVANCE)
    manual = repositorio.buscar_documento(conexion, MANUAL)
    assert (avance.tipo, avance.numero_avance, avance.categoria) == ("avance", 465, "A")
    assert (manual.tipo, manual.numero_avance, manual.categoria) == ("manual", None, "B")


@pytest.mark.integration
def test_la_primera_ingesta_deja_activo_su_modelo_y_no_lo_cambia_despues(
    conexion, carpeta, proveedor
):
    # Arrange
    ingestar_carpeta(conexion, carpeta, proveedor, ExtractorSimulado())
    otro = FakeEmbeddingProvider(nombre_modelo="otro-modelo", max_tokens=MAX_TOKENS)

    # Act
    ingestar_carpeta(conexion, carpeta, otro, ExtractorSimulado())

    # Assert
    activo = repositorio.leer_configuracion(conexion, repositorio.CLAVE_MODELO_ACTIVO)
    assert activo == proveedor.nombre_modelo


@pytest.mark.integration
def test_un_archivo_faltante_no_se_registra_en_la_base(conexion, carpeta, proveedor):
    ingestar_carpeta(conexion, carpeta, proveedor, ExtractorSimulado())

    assert repositorio.buscar_documento(conexion, FALTANTE) is None
    assert contar(conexion, "documento") == 2


@pytest.mark.integration
def test_volver_a_ejecutar_no_duplica_nada(conexion, carpeta, proveedor):
    # Arrange
    primera = ingestar_carpeta(conexion, carpeta, proveedor, ExtractorSimulado())
    extractor = ExtractorSimulado()

    # Act
    segunda = ingestar_carpeta(conexion, carpeta, proveedor, extractor)

    # Assert
    assert [r.estado for r in segunda.resultados] == ["omitido", "omitido", "error"]
    assert extractor.rutas == []
    assert segunda.fragmentos_creados == 0
    assert contar(conexion, "documento") == 2
    assert contar(conexion, "fragmento") == primera.fragmentos_creados
    assert contar(conexion, "embedding") == primera.fragmentos_creados


@pytest.mark.integration
def test_una_categoria_desconocida_en_el_manifiesto_es_un_error_informado(
    conexion, tmp_path, proveedor
):
    (tmp_path / "_manifiesto.csv").write_text(
        f"archivo,categoria,carpeta_origen\n{AVANCE},H,.\n", encoding="utf-8"
    )
    (tmp_path / AVANCE).write_bytes(b"%PDF avance")

    informe = ingestar_carpeta(conexion, tmp_path, proveedor, ExtractorSimulado())

    assert informe.resultados[0].estado == "error"
    assert "'H'" in informe.resultados[0].motivo
    assert contar(conexion, "documento") == 0


@pytest.mark.integration
def test_el_informe_lista_totales_omitidos_con_motivo_y_errores(conexion, carpeta, proveedor):
    # Arrange
    primera = ingestar_carpeta(conexion, carpeta, proveedor, ExtractorSimulado())
    segunda = ingestar_carpeta(conexion, carpeta, proveedor, ExtractorSimulado())

    # Act
    texto_primera = formatear_informe(primera)
    texto_segunda = formatear_informe(segunda)

    # Assert
    assert "Indexados: 2" in texto_primera
    assert "Con error: 1" in texto_primera
    assert f"Fragmentos creados: {primera.fragmentos_creados}" in texto_primera
    assert "Fragmentos descartados (tablas): 0" in texto_primera
    assert "Tiempo total:" in texto_primera
    assert f"  - {FALTANTE}: no existe en la carpeta" in texto_primera
    assert "Omitidos: 2" in texto_segunda
    assert f"  - {AVANCE}: ya indexado con el modelo activo" in texto_segunda


# --- Comandos ---


@pytest.fixture
def entorno_de_prueba(monkeypatch, url_db_prueba, carpeta):
    monkeypatch.setenv("DATABASE_URL", url_db_prueba)
    monkeypatch.setenv("CARPETA_BASE_CONOCIMIENTO", str(carpeta))
    return carpeta


def proveedor_falso(nombre_modelo: str) -> FakeEmbeddingProvider:
    return FakeEmbeddingProvider(nombre_modelo=nombre_modelo, max_tokens=MAX_TOKENS)


@pytest.mark.integration
def test_comando_inicializar_db(entorno_de_prueba, capsys):
    salida = cli.main(["inicializar-db"])

    assert salida == 0
    assert "Base de datos lista" in capsys.readouterr().out


@pytest.mark.integration
def test_comando_ingestar_usa_la_carpeta_por_defecto_e_imprime_el_informe(
    entorno_de_prueba, conexion, capsys
):
    # Act
    salida = cli.main(["ingestar"], fabrica_proveedor=proveedor_falso, extractor=ExtractorSimulado())

    # Assert
    texto = capsys.readouterr().out
    assert salida == 1
    assert "Indexados: 2" in texto
    assert "Con error: 1" in texto


@pytest.mark.integration
def test_comando_ingestar_con_otra_carpeta(entorno_de_prueba, conexion, tmp_path_factory, capsys):
    otra = tmp_path_factory.mktemp("vacia")
    (otra / "_manifiesto.csv").write_text("archivo,categoria,carpeta_origen\n", encoding="utf-8")

    salida = cli.main(
        ["ingestar", "--carpeta", str(otra)],
        fabrica_proveedor=proveedor_falso,
        extractor=ExtractorSimulado(),
    )

    assert salida == 0
    assert "Documentos procesados: 0" in capsys.readouterr().out


def test_comando_ingestar_con_una_carpeta_que_no_existe(tmp_path, capsys):
    salida = cli.main(["ingestar", "--carpeta", str(tmp_path / "no_existe")])

    assert salida == 2
    assert "no existe la carpeta" in capsys.readouterr().err


@pytest.mark.integration
def test_comando_ingestar_sin_manifiesto_termina_con_un_error_claro(
    entorno_de_prueba, conexion, tmp_path_factory, capsys
):
    sin_manifiesto = tmp_path_factory.mktemp("sin_manifiesto")

    salida = cli.main(
        ["ingestar", "--carpeta", str(sin_manifiesto)],
        fabrica_proveedor=proveedor_falso,
        extractor=ExtractorSimulado(),
    )

    assert salida == 2
    assert "no existe el manifiesto" in capsys.readouterr().err


def test_comando_desconocido_termina_con_error():
    with pytest.raises(SystemExit):
        cli.main(["borrar-todo"])
