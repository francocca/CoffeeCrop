import csv
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
from conocimiento.errores import ConocimientoError
from conocimiento.extraccion.limpieza import TIPO_AVANCE, TIPO_MANUAL, limpiar_paginas
from conocimiento.extraccion.pdf import extraer_paginas, sha256_archivo, tiene_texto_legible
from conocimiento.fragmentacion import CATEGORIAS, filtrar_tablas, fragmentar

LOTE_VECTORIZACION = 64
NOMBRE_MANIFIESTO = "_manifiesto.csv"

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


@dataclass(frozen=True)
class FilaManifiesto:
    archivo: str
    categoria: str
    carpeta_origen: str


@dataclass(frozen=True)
class InformeIngesta:
    resultados: list[ResultadoIngesta]
    segundos: float

    def con_estado(self, estado: str) -> list[ResultadoIngesta]:
        return [resultado for resultado in self.resultados if resultado.estado == estado]

    @property
    def fragmentos_creados(self) -> int:
        return sum(resultado.fragmentos_creados for resultado in self.resultados)

    @property
    def fragmentos_descartados(self) -> int:
        return sum(resultado.fragmentos_descartados for resultado in self.resultados)


def ingestar_carpeta(
    conexion: psycopg.Connection,
    carpeta: Path,
    proveedor: EmbeddingProvider,
    extractor: Callable[[Path], list[str]] = extraer_paginas,
) -> InformeIngesta:
    """Procesa cada PDF del manifiesto de la carpeta; un documento que falla no detiene a los demás."""
    inicio = time.perf_counter()
    filas = leer_manifiesto(Path(carpeta))
    _fijar_modelo_activo_si_falta(conexion, proveedor.nombre_modelo)
    resultados = []
    for numero, fila in enumerate(filas, start=1):
        resultado = _ingestar_fila(conexion, Path(carpeta), fila, proveedor, extractor)
        _registro.info(
            "[%d/%d] %s: %s%s", numero, len(filas), fila.archivo, resultado.estado,
            f" ({resultado.motivo})" if resultado.motivo else "",
        )
        resultados.append(resultado)
    return InformeIngesta(resultados, time.perf_counter() - inicio)


def leer_manifiesto(carpeta: Path) -> list[FilaManifiesto]:
    ruta = carpeta / NOMBRE_MANIFIESTO
    if not ruta.is_file():
        raise ConocimientoError(f"no existe el manifiesto {ruta}")
    # utf-8-sig: el manifiesto se generó en Windows y empieza con BOM.
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        return [
            FilaManifiesto(fila["archivo"], fila["categoria"], fila["carpeta_origen"])
            for fila in csv.DictReader(archivo)
        ]


def tipo_desde_nombre(nombre_archivo: str) -> str:
    return TIPO_MANUAL if nombre_archivo.lower().startswith("manual") else TIPO_AVANCE


def formatear_informe(informe: InformeIngesta) -> str:
    lineas = [
        "Informe de ingesta",
        f"  Documentos procesados: {len(informe.resultados)}",
        f"  Indexados: {len(informe.con_estado(ESTADO_INDEXADO))}",
        f"  Vectorizados con el modelo activo: {len(informe.con_estado(ESTADO_VECTORIZADO))}",
        f"  Omitidos: {len(informe.con_estado(ESTADO_OMITIDO))}",
        f"  Sin texto legible: {len(informe.con_estado(ESTADO_SIN_TEXTO))}",
        f"  Con error: {len(informe.con_estado(ESTADO_ERROR))}",
        f"  Fragmentos creados: {informe.fragmentos_creados}",
        f"  Fragmentos descartados (tablas): {informe.fragmentos_descartados}",
        f"  Tiempo total: {informe.segundos:.1f} s",
    ]
    for titulo, estados in (
        ("Omitidos", (ESTADO_OMITIDO, ESTADO_SIN_TEXTO)),
        ("Con error", (ESTADO_ERROR,)),
    ):
        detalle = [r for estado in estados for r in informe.con_estado(estado)]
        if detalle:
            lineas.append(f"{titulo}:")
            lineas += [f"  - {r.nombre_archivo}: {r.motivo}" for r in detalle]
    return "\n".join(lineas)


def _fijar_modelo_activo_si_falta(conexion: psycopg.Connection, nombre_modelo: str) -> None:
    # La primera ingesta deja activo su modelo; después solo lo cambia activar-modelo (Tarea 15).
    with conexion.transaction():
        if repositorio.leer_configuracion(conexion, repositorio.CLAVE_MODELO_ACTIVO) is None:
            repositorio.escribir_configuracion(conexion, repositorio.CLAVE_MODELO_ACTIVO, nombre_modelo)


def _ingestar_fila(
    conexion: psycopg.Connection,
    carpeta: Path,
    fila: FilaManifiesto,
    proveedor: EmbeddingProvider,
    extractor: Callable[[Path], list[str]],
) -> ResultadoIngesta:
    ruta = carpeta / fila.archivo
    # Estos dos casos se informan sin escribir en la base: no hay un documento real que registrar.
    if not ruta.is_file():
        return ResultadoIngesta(fila.archivo, ESTADO_ERROR, motivo="no existe en la carpeta")
    if fila.categoria not in CATEGORIAS:
        motivo = f"categoría desconocida en el manifiesto: {fila.categoria!r}"
        return ResultadoIngesta(fila.archivo, ESTADO_ERROR, motivo=motivo)
    tipo = tipo_desde_nombre(fila.archivo)
    return ingestar_documento(conexion, ruta, fila.categoria, tipo, proveedor, extractor)


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
