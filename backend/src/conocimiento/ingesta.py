import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

import psycopg

from conocimiento.db import repositorio
from conocimiento.db.repositorio import DatosDocumento, Documento
from conocimiento.embeddings.base import EmbeddingProvider
from conocimiento.extraccion.limpieza import limpiar_paginas
from conocimiento.extraccion.pdf import extraer_paginas, sha256_archivo, tiene_texto_legible
from conocimiento.fragmentacion import filtrar_tablas, fragmentar

LOTE_VECTORIZACION = 64

ESTADO_INDEXADO = "indexado"
ESTADO_SIN_TEXTO = "sin_texto"
ESTADO_ERROR = "error"
# Estados del resultado que no se guardan en la base.
ESTADO_OMITIDO = "omitido"
ESTADO_VECTORIZADO = "vectorizado"

_NUMERO_AVANCE = re.compile(r"^Avance_(\d+)_", re.IGNORECASE)

_registro = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoIngesta:
    nombre_archivo: str
    estado: str
    fragmentos_creados: int = 0
    fragmentos_descartados: int = 0
    segundos: float = 0.0
    motivo: str | None = None


def ingestar_documento(
    conexion: psycopg.Connection,
    ruta: Path,
    categoria: str,
    tipo: str,
    proveedor: EmbeddingProvider,
    extractor: Callable[[Path], list[str]] = extraer_paginas,
) -> ResultadoIngesta:
    """Procesa un PDF de punta a punta; un fallo se informa en el resultado, nunca se propaga."""
    inicio = time.perf_counter()
    nombre = Path(ruta).name
    try:
        resultado = _ingestar(conexion, Path(ruta), categoria, tipo, proveedor, extractor)
    except Exception as error:
        motivo = f"{type(error).__name__}: {error}"
        _registro.warning("No se pudo ingerir %s: %s", nombre, motivo)
        _marcar_error(conexion, Path(ruta), categoria, tipo)
        resultado = ResultadoIngesta(nombre, ESTADO_ERROR, motivo=motivo)
    return replace(resultado, segundos=time.perf_counter() - inicio)


def _ingestar(
    conexion: psycopg.Connection,
    ruta: Path,
    categoria: str,
    tipo: str,
    proveedor: EmbeddingProvider,
    extractor: Callable[[Path], list[str]],
) -> ResultadoIngesta:
    nombre = ruta.name
    sha256 = sha256_archivo(ruta)
    existente = repositorio.buscar_documento(conexion, nombre)
    if existente is not None and existente.sha256 == sha256:
        if existente.estado == ESTADO_SIN_TEXTO:
            return ResultadoIngesta(nombre, ESTADO_OMITIDO, motivo="sin texto legible (sin cambios)")
        if existente.estado == ESTADO_INDEXADO:
            return _vectorizar_si_falta(conexion, existente, proveedor)

    paginas = extractor(ruta)
    datos = DatosDocumento(
        nombre_archivo=nombre,
        categoria=categoria,
        tipo=tipo,
        sha256=sha256,
        paginas=len(paginas),
        estado=ESTADO_INDEXADO,
        numero_avance=_numero_avance(nombre),
    )
    if not tiene_texto_legible(paginas):
        with repositorio.transaccion(conexion):
            repositorio.reemplazar_documento(conexion, replace(datos, estado=ESTADO_SIN_TEXTO))
        return ResultadoIngesta(nombre, ESTADO_SIN_TEXTO, motivo="sin texto legible (BR-002)")

    paginas_limpias = limpiar_paginas(paginas, tipo)
    fragmentos = fragmentar(paginas_limpias, proveedor.contar_tokens, proveedor.max_tokens)
    filtrado = filtrar_tablas(fragmentos, categoria)
    with repositorio.transaccion(conexion):
        documento = repositorio.reemplazar_documento(conexion, datos)
        ids = repositorio.guardar_fragmentos(conexion, documento, filtrado.conservados)
        _guardar_vectores(conexion, proveedor, ids, [f.texto for f in filtrado.conservados])
    return ResultadoIngesta(
        nombre,
        ESTADO_INDEXADO,
        fragmentos_creados=len(ids),
        fragmentos_descartados=filtrado.descartados,
    )


def _vectorizar_si_falta(
    conexion: psycopg.Connection, documento: Documento, proveedor: EmbeddingProvider
) -> ResultadoIngesta:
    nombre = documento.nombre_archivo
    if repositorio.contar_embeddings(conexion, proveedor.nombre_modelo, documento.id) > 0:
        return ResultadoIngesta(nombre, ESTADO_OMITIDO, motivo="ya indexado con el modelo activo")
    fragmentos = repositorio.leer_fragmentos(conexion, documento.id)
    with repositorio.transaccion(conexion):
        _guardar_vectores(
            conexion, proveedor, [fid for fid, _ in fragmentos], [texto for _, texto in fragmentos]
        )
    return ResultadoIngesta(
        nombre, ESTADO_VECTORIZADO, motivo=f"vectores nuevos de {proveedor.nombre_modelo}"
    )


def _guardar_vectores(
    conexion: psycopg.Connection, proveedor: EmbeddingProvider, ids: list, textos: list[str]
) -> None:
    for desde in range(0, len(textos), LOTE_VECTORIZACION):
        hasta = desde + LOTE_VECTORIZACION
        vectores = proveedor.embed_documents(textos[desde:hasta])
        pares = list(zip(ids[desde:hasta], vectores))
        repositorio.guardar_embeddings(conexion, proveedor.nombre_modelo, pares)


def _marcar_error(conexion: psycopg.Connection, ruta: Path, categoria: str, tipo: str) -> None:
    # Si ya había una versión indexada se conserva y solo cambia su estado: la próxima corrida
    # la vuelve a procesar. Si no la había, queda registrado el intento fallido.
    try:
        existente = repositorio.buscar_documento(conexion, ruta.name)
        if existente is not None:
            repositorio.actualizar_estado(conexion, existente.id, ESTADO_ERROR)
            return
        datos = DatosDocumento(
            nombre_archivo=ruta.name,
            categoria=categoria,
            tipo=tipo,
            sha256=sha256_archivo(ruta) if ruta.is_file() else "0" * 64,
            paginas=0,
            estado=ESTADO_ERROR,
            numero_avance=_numero_avance(ruta.name),
        )
        repositorio.reemplazar_documento(conexion, datos)
    except Exception as error:
        _registro.warning("Tampoco se pudo marcar %s como error: %s", ruta.name, error)


def _numero_avance(nombre_archivo: str) -> int | None:
    coincidencia = _NUMERO_AVANCE.match(nombre_archivo)
    return int(coincidencia.group(1)) if coincidencia else None
