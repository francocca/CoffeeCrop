import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import psycopg
from pgvector import Vector
from psycopg.rows import class_row

from conocimiento.fragmentacion import CATEGORIAS, Fragmento

CLAVE_MODELO_ACTIVO = "modelo_activo"


@dataclass(frozen=True)
class DatosDocumento:
    nombre_archivo: str
    categoria: str
    tipo: str
    sha256: str
    paginas: int
    estado: str
    numero_avance: int | None = None


@dataclass(frozen=True)
class Documento:
    id: uuid.UUID
    nombre_archivo: str
    categoria: str
    tipo: str
    numero_avance: int | None
    sha256: str
    paginas: int
    estado: str
    fecha_ingesta: datetime


def transaccion(conexion: psycopg.Connection):
    """Agrupa el trabajo de un documento: si algo falla dentro, no queda nada a medias."""
    return conexion.transaction()


def buscar_documento(conexion: psycopg.Connection, nombre_archivo: str) -> Documento | None:
    with conexion.cursor(row_factory=class_row(Documento)) as cursor:
        return cursor.execute(
            "SELECT id, nombre_archivo, categoria, tipo, numero_avance, sha256, paginas, estado,"
            " fecha_ingesta FROM documento WHERE nombre_archivo = %s",
            (nombre_archivo,),
        ).fetchone()


def reemplazar_documento(conexion: psycopg.Connection, datos: DatosDocumento) -> Documento:
    """Crea el documento; si ya había uno con el mismo nombre, lo borra antes (con sus
    fragmentos y vectores, en cascada)."""
    with conexion.transaction(), conexion.cursor(row_factory=class_row(Documento)) as cursor:
        cursor.execute("DELETE FROM documento WHERE nombre_archivo = %s", (datos.nombre_archivo,))
        return cursor.execute(
            "INSERT INTO documento"
            " (id, nombre_archivo, categoria, tipo, numero_avance, sha256, paginas, estado)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            " RETURNING id, nombre_archivo, categoria, tipo, numero_avance, sha256, paginas,"
            " estado, fecha_ingesta",
            (
                uuid.uuid4(),
                datos.nombre_archivo,
                datos.categoria,
                datos.tipo,
                datos.numero_avance,
                datos.sha256,
                datos.paginas,
                datos.estado,
            ),
        ).fetchone()


def guardar_fragmentos(
    conexion: psycopg.Connection, documento: Documento | None, fragmentos: Sequence[Fragmento]
) -> list[uuid.UUID]:
    """Guarda los fragmentos de un documento y devuelve sus ids, en el mismo orden."""
    # BR-006: se valida todo antes de escribir, así un fragmento inválido no deja otros guardados.
    _validar_trazabilidad(documento, fragmentos)
    ids = [uuid.uuid4() for _ in fragmentos]
    with conexion.transaction(), conexion.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO fragmento"
            " (id, documento_id, orden, texto, pagina_inicio, pagina_fin, tokens, es_tabla)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    fragmento_id,
                    documento.id,
                    fragmento.orden,
                    fragmento.texto,
                    fragmento.pagina_inicio,
                    fragmento.pagina_fin,
                    fragmento.tokens,
                    fragmento.es_tabla,
                )
                for fragmento_id, fragmento in zip(ids, fragmentos)
            ],
        )
    return ids


def guardar_embeddings(
    conexion: psycopg.Connection,
    modelo: str,
    vectores_por_fragmento: Sequence[tuple[uuid.UUID, Sequence[float]]],
) -> None:
    dimensiones = {len(vector) for _, vector in vectores_por_fragmento}
    if len(dimensiones) > 1:
        raise ValueError(
            f"Los vectores del modelo {modelo} tienen dimensiones distintas: {dimensiones}."
        )
    with conexion.transaction(), conexion.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO embedding (fragmento_id, modelo, dimension, vector)"
            " VALUES (%s, %s, %s, %s)",
            [
                (fragmento_id, modelo, len(vector), Vector(list(vector)))
                for fragmento_id, vector in vectores_por_fragmento
            ],
        )


def contar_embeddings(
    conexion: psycopg.Connection, modelo: str, documento_id: uuid.UUID | None = None
) -> int:
    if documento_id is None:
        consulta = "SELECT count(*) FROM embedding WHERE modelo = %s"
        parametros: tuple = (modelo,)
    else:
        consulta = (
            "SELECT count(*) FROM embedding e JOIN fragmento f ON f.id = e.fragmento_id"
            " WHERE e.modelo = %s AND f.documento_id = %s"
        )
        parametros = (modelo, documento_id)
    return conexion.execute(consulta, parametros).fetchone()[0]


def leer_configuracion(conexion: psycopg.Connection, clave: str) -> str | None:
    fila = conexion.execute("SELECT valor FROM configuracion WHERE clave = %s", (clave,)).fetchone()
    return fila[0] if fila else None


def escribir_configuracion(conexion: psycopg.Connection, clave: str, valor: str) -> None:
    conexion.execute(
        "INSERT INTO configuracion (clave, valor) VALUES (%s, %s)"
        " ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor",
        (clave, valor),
    )


def _validar_trazabilidad(documento: Documento | None, fragmentos: Sequence[Fragmento]) -> None:
    if documento is None or documento.id is None:
        raise ValueError("Un fragmento no se guarda sin su documento (BR-006).")
    if documento.categoria not in CATEGORIAS:
        raise ValueError(
            "Un fragmento no se guarda sin categoría válida (BR-006);"
            f" llegó {documento.categoria!r}."
        )
    for fragmento in fragmentos:
        inicio, fin = fragmento.pagina_inicio, fragmento.pagina_fin
        if inicio is None or fin is None or inicio < 1 or fin < inicio:
            raise ValueError(
                f"El fragmento {fragmento.orden} no tiene páginas válidas (BR-006):"
                f" {inicio}–{fin}."
            )
