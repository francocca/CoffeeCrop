from pathlib import Path

import pytest

from conocimiento.config import cargar_config
from conocimiento.errores import (
    DatabaseUnavailableError,
    InvalidQueryError,
    NoEmbeddingsForModelError,
)

VARIABLES = (
    "DATABASE_URL",
    "PDFTOTEXT_BIN",
    "CARPETA_BASE_CONOCIMIENTO",
    "MODELO_EMBEDDINGS",
    "MINIMO_SIMILITUD",
    "VENTAJA_BOYACA",
)


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for variable in VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_valores_por_defecto_sin_variables_de_entorno():
    config = cargar_config()

    assert config.pdftotext_bin == "pdftotext"
    assert config.modelo_embeddings == "intfloat/multilingual-e5-base"
    assert config.carpeta_base_conocimiento.parts[-2:] == ("docs", "base_conocimiento")
    assert 0 < config.minimo_similitud < 1
    assert config.ventaja_boyaca >= 0


def test_la_url_por_defecto_no_trae_clave():
    config = cargar_config()

    assert "@" in config.database_url
    assert ":" not in config.database_url.split("//")[1].split("@")[0]


def test_variables_de_entorno_sobrescriben_los_valores_por_defecto(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://otro:clave@host:5432/base")
    monkeypatch.setenv("PDFTOTEXT_BIN", "C:/poppler/pdftotext.exe")
    monkeypatch.setenv("CARPETA_BASE_CONOCIMIENTO", "C:/otra/carpeta")
    monkeypatch.setenv("MODELO_EMBEDDINGS", "BAAI/bge-m3")
    monkeypatch.setenv("MINIMO_SIMILITUD", "0.6")
    monkeypatch.setenv("VENTAJA_BOYACA", "0.1")

    config = cargar_config()

    assert config.database_url == "postgresql://otro:clave@host:5432/base"
    assert config.pdftotext_bin == "C:/poppler/pdftotext.exe"
    assert config.carpeta_base_conocimiento == Path("C:/otra/carpeta")
    assert config.modelo_embeddings == "BAAI/bge-m3"
    assert config.minimo_similitud == 0.6
    assert config.ventaja_boyaca == 0.1


@pytest.mark.parametrize(
    ("clase", "codigo"),
    [
        (InvalidQueryError, "INVALID_QUERY"),
        (NoEmbeddingsForModelError, "NO_EMBEDDINGS_FOR_MODEL"),
        (DatabaseUnavailableError, "DB_UNAVAILABLE"),
    ],
)
def test_las_excepciones_tienen_su_codigo_y_mensaje(clase, codigo):
    error = clase("mensaje claro")

    assert error.code == codigo
    assert str(error) == "mensaje claro"
