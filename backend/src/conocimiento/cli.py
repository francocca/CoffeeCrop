import argparse
import logging
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from conocimiento.config import cargar_config
from conocimiento.db.conexion import conectar, inicializar_db
from conocimiento.embeddings.base import EmbeddingProvider
from conocimiento.errores import ConocimientoError
from conocimiento.extraccion.pdf import extraer_paginas
from conocimiento.ingesta import ESTADO_ERROR, formatear_informe, ingestar_carpeta

SALIDA_CORRECTA = 0
SALIDA_CON_ERRORES = 1
SALIDA_FALLO = 2


def crear_proveedor(nombre_modelo: str) -> EmbeddingProvider:
    # Importación diferida: cargar torch tarda ~30 s y comandos como inicializar-db no lo necesitan.
    from conocimiento.embeddings.sentence_transformers import SentenceTransformersProvider

    return SentenceTransformersProvider(nombre_modelo)


def main(
    argumentos: Sequence[str] | None = None,
    fabrica_proveedor: Callable[[str], EmbeddingProvider] = crear_proveedor,
    extractor: Callable[[Path], list[str]] = extraer_paginas,
) -> int:
    opciones = _analizador().parse_args(argumentos)
    # Solo el avance propio en INFO; las librerías (Hugging Face, httpx) quedan en WARNING.
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logging.getLogger("conocimiento").setLevel(logging.INFO)
    try:
        if opciones.comando == "inicializar-db":
            return _inicializar_db()
        return _ingestar(opciones.carpeta, fabrica_proveedor, extractor)
    except ConocimientoError as error:
        print(f"Error: {error.mensaje}", file=sys.stderr)
        return SALIDA_FALLO


def _analizador() -> argparse.ArgumentParser:
    analizador = argparse.ArgumentParser(
        prog="python -m conocimiento",
        description="Base de conocimiento cafetero de CoffeCrop.",
    )
    comandos = analizador.add_subparsers(dest="comando", required=True)
    comandos.add_parser("inicializar-db", help="Crea la extensión vector y las tablas.")
    ingestar = comandos.add_parser("ingestar", help="Ingiere los PDFs del manifiesto de la carpeta.")
    ingestar.add_argument(
        "--carpeta",
        type=Path,
        default=None,
        help="Carpeta con los PDFs y _manifiesto.csv (por defecto, CARPETA_BASE_CONOCIMIENTO).",
    )
    return analizador


def _inicializar_db() -> int:
    inicializar_db(cargar_config().database_url)
    print("Base de datos lista: extensión vector y tablas creadas.")
    return SALIDA_CORRECTA


def _ingestar(
    carpeta: Path | None,
    fabrica_proveedor: Callable[[str], EmbeddingProvider],
    extractor: Callable[[Path], list[str]],
) -> int:
    config = cargar_config()
    carpeta = carpeta or config.carpeta_base_conocimiento
    if not carpeta.is_dir():
        print(f"Error: no existe la carpeta {carpeta}", file=sys.stderr)
        return SALIDA_FALLO
    with conectar(config.database_url) as conexion:
        proveedor = fabrica_proveedor(config.modelo_embeddings)
        informe = ingestar_carpeta(conexion, carpeta, proveedor, extractor)
    print(formatear_informe(informe))
    return SALIDA_CON_ERRORES if informe.con_estado(ESTADO_ERROR) else SALIDA_CORRECTA
