import hashlib
import subprocess

import pytest

from conocimiento.config import cargar_config
from conocimiento.errores import PdfExtractionError
from conocimiento.extraccion import pdf
from conocimiento.extraccion.pdf import extraer_paginas, sha256_archivo, tiene_texto_legible

CARPETA_DOCS = cargar_config().carpeta_base_conocimiento


@pytest.fixture
def pdf_falso(tmp_path):
    ruta = tmp_path / "Avance_999_Prueba.pdf"
    ruta.write_bytes(b"%PDF-1.4 contenido de prueba")
    return ruta


def simular_pdftotext(monkeypatch, stdout=b"", stderr=b"", returncode=0):
    llamadas = []

    def falso_run(comando, **opciones):
        llamadas.append(comando)
        return subprocess.CompletedProcess(comando, returncode, stdout, stderr)

    monkeypatch.setattr(pdf.subprocess, "run", falso_run)
    return llamadas


def test_extraer_paginas_devuelve_un_texto_por_pagina(monkeypatch, pdf_falso):
    simular_pdftotext(monkeypatch, stdout="Roya del café\n\fBroca\n\fCosecha\n\f".encode())

    paginas = extraer_paginas(pdf_falso, pdftotext_bin="pdftotext")

    assert paginas == ["Roya del café\n", "Broca\n", "Cosecha\n"]


def test_extraer_paginas_normaliza_saltos_de_linea_de_windows(monkeypatch, pdf_falso):
    simular_pdftotext(monkeypatch, stdout=b"Linea uno\r\nLinea dos\r\n\f")

    paginas = extraer_paginas(pdf_falso, pdftotext_bin="pdftotext")

    assert paginas == ["Linea uno\nLinea dos\n"]


def test_extraer_paginas_conserva_las_paginas_vacias_del_medio(monkeypatch, pdf_falso):
    simular_pdftotext(monkeypatch, stdout=b"Uno\n\f\fTres\n\f")

    paginas = extraer_paginas(pdf_falso, pdftotext_bin="pdftotext")

    assert paginas == ["Uno\n", "", "Tres\n"]


def test_extraer_paginas_llama_a_pdftotext_con_utf8_y_salida_estandar(monkeypatch, pdf_falso):
    llamadas = simular_pdftotext(monkeypatch, stdout=b"Texto\n\f")

    extraer_paginas(pdf_falso, pdftotext_bin="mi-pdftotext")

    assert llamadas == [["mi-pdftotext", "-enc", "UTF-8", str(pdf_falso), "-"]]


def test_extraer_paginas_usa_pdftotext_bin_de_la_configuracion(monkeypatch, pdf_falso):
    llamadas = simular_pdftotext(monkeypatch, stdout=b"Texto\n\f")
    monkeypatch.setenv("PDFTOTEXT_BIN", "C:/poppler/pdftotext.exe")

    extraer_paginas(pdf_falso)

    assert llamadas[0][0] == "C:/poppler/pdftotext.exe"


def test_pdftotext_inexistente_menciona_pdftotext_bin(pdf_falso):
    with pytest.raises(PdfExtractionError) as excepcion:
        extraer_paginas(pdf_falso, pdftotext_bin="no-existe-pdftotext-xyz")

    assert "PDFTOTEXT_BIN" in excepcion.value.mensaje
    assert excepcion.value.code == "PDF_EXTRACTION_ERROR"


def test_pdftotext_que_falla_menciona_pdftotext_bin_y_el_detalle(monkeypatch, pdf_falso):
    simular_pdftotext(monkeypatch, stderr=b"Syntax Error: archivo danado", returncode=1)

    with pytest.raises(PdfExtractionError) as excepcion:
        extraer_paginas(pdf_falso, pdftotext_bin="pdftotext")

    assert "PDFTOTEXT_BIN" in excepcion.value.mensaje
    assert "archivo danado" in excepcion.value.mensaje
    assert pdf_falso.name in excepcion.value.mensaje


def test_pdftotext_que_se_cuelga_lanza_error_claro(monkeypatch, pdf_falso):
    def falso_run(comando, **opciones):
        raise subprocess.TimeoutExpired(comando, opciones["timeout"])

    monkeypatch.setattr(pdf.subprocess, "run", falso_run)

    with pytest.raises(PdfExtractionError) as excepcion:
        extraer_paginas(pdf_falso, pdftotext_bin="pdftotext")

    assert "PDFTOTEXT_BIN" in excepcion.value.mensaje


def test_pdf_inexistente_lanza_error_claro(tmp_path):
    with pytest.raises(PdfExtractionError) as excepcion:
        extraer_paginas(tmp_path / "no_esta.pdf", pdftotext_bin="pdftotext")

    assert "no_esta.pdf" in excepcion.value.mensaje


def test_sha256_archivo_devuelve_la_huella_del_contenido(tmp_path):
    ruta = tmp_path / "datos.bin"
    ruta.write_bytes(b"abc")

    huella = sha256_archivo(ruta)

    assert huella == hashlib.sha256(b"abc").hexdigest()
    assert len(huella) == 64


def test_sha256_cambia_si_cambia_el_contenido(tmp_path):
    ruta = tmp_path / "datos.bin"
    ruta.write_bytes(b"version uno")
    antes = sha256_archivo(ruta)

    ruta.write_bytes(b"version dos")

    assert sha256_archivo(ruta) != antes


@pytest.mark.parametrize(
    ("cantidad", "esperado"),
    [(0, False), (1499, False), (1500, True), (5000, True)],
)
def test_tiene_texto_legible_usa_el_minimo_de_1500_caracteres(cantidad, esperado):
    paginas = ["a" * cantidad]

    assert tiene_texto_legible(paginas) is esperado


def test_tiene_texto_legible_suma_todas_las_paginas():
    paginas = ["a" * 700, "b" * 700, "c" * 100]

    assert tiene_texto_legible(paginas) is True


def test_tiene_texto_legible_no_cuenta_espacios_ni_saltos_de_linea():
    paginas = ["a" * 1000 + "\n" * 800 + " " * 800]

    assert tiene_texto_legible(paginas) is False


def test_tiene_texto_legible_con_lista_vacia_es_falso():
    assert tiene_texto_legible([]) is False


@pytest.mark.docs
@pytest.mark.skipif(not CARPETA_DOCS.is_dir(), reason="docs/base_conocimiento no está en este equipo")
def test_extraccion_real_de_un_avance():
    ruta = sorted(CARPETA_DOCS.glob("Avance_*.pdf"))[0]

    paginas = extraer_paginas(ruta)

    assert len(paginas) >= 1
    assert all(isinstance(pagina, str) for pagina in paginas)
    assert "\r" not in "".join(paginas)
    assert len(sha256_archivo(ruta)) == 64
