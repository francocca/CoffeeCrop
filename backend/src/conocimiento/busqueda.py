import psycopg

from conocimiento.config import cargar_config
from conocimiento.db import repositorio
from conocimiento.db.repositorio import Resultado
from conocimiento.embeddings.base import EmbeddingProvider
from conocimiento.errores import InvalidQueryError, NoEmbeddingsForModelError

K_POR_DEFECTO = 5
MAXIMO_CARACTERES_PREGUNTA = 1000
REGION_BOYACA = "boyaca"

__all__ = ["Resultado", "buscar"]


def buscar(
    conexion: psycopg.Connection,
    proveedor: EmbeddingProvider,
    pregunta: str,
    k: int = K_POR_DEFECTO,
    region: str | None = None,
    minimo_similitud: float | None = None,
    ventaja_boyaca: float | None = None,
) -> list[Resultado]:
    """Los `k` fragmentos más relevantes para la pregunta, de mayor a menor (US-002, US-003).

    El mínimo y la ventaja salen de la configuración salvo que se indiquen (Tarea 19 los calibra).
    """
    pregunta = _validar(pregunta, k, region)
    modelo = repositorio.leer_configuracion(conexion, repositorio.CLAVE_MODELO_ACTIVO)
    if modelo is None or repositorio.contar_embeddings(conexion, modelo) == 0:
        raise NoEmbeddingsForModelError(
            f"No hay vectores del modelo activo ({modelo or 'ninguno'}): "
            "ejecuta primero python -m conocimiento ingestar."
        )
    if proveedor.nombre_modelo != modelo:
        # BR-004: la pregunta se vectoriza con el mismo modelo que los fragmentos.
        raise ValueError(
            f"El proveedor usa {proveedor.nombre_modelo}, pero el modelo activo es {modelo}."
        )
    config = cargar_config()
    minimo = config.minimo_similitud if minimo_similitud is None else minimo_similitud
    ventaja = config.ventaja_boyaca if ventaja_boyaca is None else ventaja_boyaca
    return repositorio.buscar_similares(
        conexion,
        proveedor.embed_query(pregunta),
        modelo,
        k,
        minimo,
        ventaja_categoria_a=ventaja if region == REGION_BOYACA else 0.0,
    )


def _validar(pregunta: str, k: int, region: str | None) -> str:
    pregunta = (pregunta or "").strip()
    if not pregunta:
        raise InvalidQueryError("La pregunta está vacía.")
    if len(pregunta) > MAXIMO_CARACTERES_PREGUNTA:
        raise InvalidQueryError(
            f"La pregunta tiene {len(pregunta)} caracteres; "
            f"el máximo es {MAXIMO_CARACTERES_PREGUNTA}."
        )
    if k < 1:
        raise InvalidQueryError(f"k debe ser al menos 1 (se recibió {k}).")
    if region not in (None, REGION_BOYACA):
        raise InvalidQueryError(f"Región desconocida: {region!r}; la única admitida es 'boyaca'.")
    return pregunta
