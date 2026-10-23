import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, replace

TAMANO_MAXIMO_FRAGMENTO = 600
MARGEN_TOKENS_MODELO = 60
DIVISOR_SOLAPE = 6
PROPORCION_MINIMA_LETRAS = 0.45
CATEGORIAS = frozenset({"A", "B", "R", "C"})
# Los calendarios y datos de Boyacá vienen en tablas; en las demás categorías son casi solo números.
CATEGORIAS_QUE_CONSERVAN_TABLAS = frozenset({"A"})

_PARRAFOS = re.compile(r"\n\s*\n")
# Una oración termina en . ! ? o … seguidos de espacio y de algo que puede abrir otra oración.
_FIN_DE_ORACION = re.compile(r"(?<=[.!?\N{HORIZONTAL ELLIPSIS}])\s+(?=[\"'(\N{BULLET}¿¡\dA-ZÁÉÍÓÚÑ])")
_TERMINA_ORACION = re.compile(r"[.!?:\N{HORIZONTAL ELLIPSIS}][\"')\]]*$")
# Abreviaturas tras las que un punto no cierra la oración ("Dr. Gómez", "Fig. 3").
_ABREVIATURAS = frozenset(
    {"sr", "sra", "dr", "dra", "ing", "lic", "nro", "fig", "figs", "tab", "pág", "págs",
     "cap", "vol", "aprox", "cía", "ej", "p", "pp", "cv", "var", "spp", "sp"}
)

_registro = logging.getLogger(__name__)


@dataclass(frozen=True)
class Fragmento:
    orden: int
    texto: str
    pagina_inicio: int
    pagina_fin: int
    tokens: int
    es_tabla: bool


@dataclass(frozen=True)
class ResultadoFiltro:
    conservados: list[Fragmento]
    descartados: int


@dataclass(frozen=True)
class _Oracion:
    texto: str
    pagina: int
    abre_parrafo: bool
    tokens: int


def tamano_objetivo(max_tokens_modelo: int) -> int:
    objetivo = min(TAMANO_MAXIMO_FRAGMENTO, max_tokens_modelo - MARGEN_TOKENS_MODELO)
    if objetivo <= 0:
        raise ValueError(
            f"El modelo lee {max_tokens_modelo} tokens; hacen falta más de {MARGEN_TOKENS_MODELO}."
        )
    return objetivo


def tamano_solape(objetivo: int) -> int:
    return objetivo // DIVISOR_SOLAPE


def es_tabla(texto: str) -> bool:
    caracteres = [caracter for caracter in texto if not caracter.isspace()]
    if not caracteres:
        return False
    letras = sum(caracter.isalpha() for caracter in caracteres)
    return letras / len(caracteres) < PROPORCION_MINIMA_LETRAS


def filtrar_tablas(fragmentos: list[Fragmento], categoria: str) -> ResultadoFiltro:
    """Descarta los fragmentos de tabla salvo en categoría A; renumera `orden` sin huecos."""
    if categoria not in CATEGORIAS:
        raise ValueError(f"Categoría desconocida: {categoria!r}; se esperaba A, B, R o C.")
    if categoria in CATEGORIAS_QUE_CONSERVAN_TABLAS:
        seleccionados = list(fragmentos)
    else:
        seleccionados = [fragmento for fragmento in fragmentos if not fragmento.es_tabla]
    conservados = [replace(fragmento, orden=orden) for orden, fragmento in enumerate(seleccionados)]
    return ResultadoFiltro(conservados, len(fragmentos) - len(conservados))


def fragmentar(
    paginas: list[str], contar_tokens: Callable[[str], int], max_tokens_modelo: int
) -> list[Fragmento]:
    """Divide un documento (una lista de páginas limpias, la primera es la 1) en fragmentos."""
    objetivo = tamano_objetivo(max_tokens_modelo)
    solape = tamano_solape(objetivo)
    fragmentos: list[Fragmento] = []
    actual: list[_Oracion] = []

    def cerrar(oraciones: list[_Oracion]) -> None:
        texto = _unir(oraciones)
        fragmentos.append(
            Fragmento(
                orden=len(fragmentos),
                texto=texto,
                pagina_inicio=oraciones[0].pagina,
                pagina_fin=oraciones[-1].pagina,
                tokens=contar_tokens(texto),
                es_tabla=es_tabla(texto),
            )
        )

    for oracion in _oraciones(paginas, contar_tokens):
        if oracion.tokens > objetivo:
            _registro.warning(
                "Una oración de %d tokens supera el tamaño objetivo (%d), página %d: %.60s…",
                oracion.tokens, objetivo, oracion.pagina, oracion.texto,
            )
            if actual:
                cerrar(actual)
            cerrar([oracion])
            actual = []
            continue
        if actual and contar_tokens(_unir([*actual, oracion])) > objetivo:
            cerrar(actual)
            actual = _ultimas_oraciones(actual, solape)
            while actual and contar_tokens(_unir([*actual, oracion])) > objetivo:
                actual = actual[1:]
        actual.append(oracion)
    if actual:
        cerrar(actual)
    return fragmentos


def _oraciones(paginas: list[str], contar_tokens: Callable[[str], int]) -> list[_Oracion]:
    oraciones: list[_Oracion] = []
    for numero, pagina in enumerate(paginas, start=1):
        for parrafo in _PARRAFOS.split(pagina):
            partes = _partir_en_oraciones(parrafo.strip())
            for posicion, texto in enumerate(partes):
                oraciones.append(_Oracion(texto, numero, posicion == 0, contar_tokens(texto)))
    return oraciones


def _partir_en_oraciones(parrafo: str) -> list[str]:
    if not parrafo:
        return []
    oraciones: list[str] = []
    for parte in _FIN_DE_ORACION.split(parrafo):
        if oraciones and _termina_en_abreviatura(oraciones[-1]):
            oraciones[-1] = f"{oraciones[-1]} {parte}"
        else:
            oraciones.append(parte)
    return oraciones


def _termina_en_abreviatura(oracion: str) -> bool:
    if not oracion.endswith("."):
        return False
    ultima_palabra = oracion.rsplit(maxsplit=1)[-1].rstrip(".").lstrip("(")
    # Una sola letra es una inicial ("Jorge E. Botero") o un género abreviado ("H. vastatrix").
    return len(ultima_palabra) == 1 or ultima_palabra.lower() in _ABREVIATURAS


def _unir(oraciones: list[_Oracion]) -> str:
    texto = oraciones[0].texto
    for anterior, oracion in zip(oraciones, oraciones[1:]):
        # Una oración partida por un salto de página se vuelve a unir con un espacio.
        continua_en_otra_pagina = oracion.pagina != anterior.pagina and not _TERMINA_ORACION.search(
            anterior.texto
        )
        separador = "\n\n" if oracion.abre_parrafo and not continua_en_otra_pagina else " "
        texto = f"{texto}{separador}{oracion.texto}"
    return texto


def _ultimas_oraciones(oraciones: list[_Oracion], maximo_tokens: int) -> list[_Oracion]:
    seleccionadas: list[_Oracion] = []
    total = 0
    for oracion in reversed(oraciones):
        if total + oracion.tokens > maximo_tokens:
            break
        seleccionadas.insert(0, oracion)
        total += oracion.tokens
    return seleccionadas
