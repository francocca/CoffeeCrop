import re
from collections import Counter

MINIMO_PAGINAS_PARA_ENCABEZADOS = 4
PROPORCION_MINIMA_ENCABEZADO = 0.40
MAXIMO_CARACTERES_ENCABEZADO = 80
MAXIMO_CARACTERES_LINEA_SUELTA = 3

_LIGADURAS_Y_ESPACIOS = str.maketrans(
    {
        "\N{LATIN SMALL LIGATURE FF}": "ff",
        "\N{LATIN SMALL LIGATURE FI}": "fi",
        "\N{LATIN SMALL LIGATURE FL}": "fl",
        "\N{LATIN SMALL LIGATURE FFI}": "ffi",
        "\N{LATIN SMALL LIGATURE FFL}": "ffl",
        "\N{NO-BREAK SPACE}": " ",
        "\N{THIN SPACE}": " ",
        "\N{ZERO WIDTH SPACE}": "",
        "\N{SOFT HYPHEN}": "",
    }
)
# Las viñetas del Manual llegan como caracteres de control C1 (p. ej. "\x83\x83").
_VINETA_AL_INICIO = re.compile(r"^[\x80-\x9f\N{BULLET}]+\s*")
_CONTROL_C1 = re.compile(r"[\x80-\x9f]")
_BLOQUES = re.compile(r"\n\s*\n")
_ESPACIOS = re.compile(r"[ \t]+")
_NUMERO_DE_PAGINA = re.compile(r"\d{1,3}")


def limpiar_paginas(paginas: list[str]) -> list[str]:
    return normalizar_texto_corrido(quitar_encabezados_repetidos(paginas))


def quitar_encabezados_repetidos(paginas: list[str]) -> list[str]:
    if len(paginas) < MINIMO_PAGINAS_PARA_ENCABEZADOS:
        return list(paginas)
    paginas_con_la_linea = Counter()
    for pagina in paginas:
        paginas_con_la_linea.update(_lineas_cortas_distintas(pagina))
    minimo_de_paginas = PROPORCION_MINIMA_ENCABEZADO * len(paginas)
    repetidas = {
        linea for linea, cantidad in paginas_con_la_linea.items() if cantidad >= minimo_de_paginas
    }
    if not repetidas:
        return list(paginas)
    return [
        "\n".join(linea for linea in pagina.split("\n") if _colapsar(linea) not in repetidas)
        for pagina in paginas
    ]


def normalizar_texto_corrido(paginas: list[str]) -> list[str]:
    return [_normalizar_pagina(pagina) for pagina in paginas]


def _lineas_cortas_distintas(pagina: str) -> set[str]:
    lineas = {_colapsar(linea) for linea in pagina.split("\n")}
    return {linea for linea in lineas if 0 < len(linea) <= MAXIMO_CARACTERES_ENCABEZADO}


def _colapsar(linea: str) -> str:
    return _ESPACIOS.sub(" ", linea.translate(_LIGADURAS_Y_ESPACIOS)).strip()


def _normalizar_pagina(pagina: str) -> str:
    parrafos: list[str] = []
    numero_de_pagina_pendiente = True
    for bloque in _BLOQUES.split(pagina):
        lineas = [_con_vineta_visible(_colapsar(linea)) for linea in bloque.split("\n")]
        lineas = [linea for linea in lineas if linea]
        if lineas and numero_de_pagina_pendiente:
            # El Manual pega el número de página arriba, sin línea en blanco antes del texto.
            numero_de_pagina_pendiente = False
            if _NUMERO_DE_PAGINA.fullmatch(lineas[0]):
                lineas = lineas[1:]
        if len(lineas) == 1 and len(lineas[0]) <= MAXIMO_CARACTERES_LINEA_SUELTA:
            continue
        parrafos.extend(_agrupar_en_parrafos(lineas))
    return "\n\n".join(_CONTROL_C1.sub("", parrafo) for parrafo in parrafos)


def _con_vineta_visible(linea: str) -> str:
    coincidencia = _VINETA_AL_INICIO.match(linea)
    if coincidencia is None:
        return linea
    resto = linea[coincidencia.end():]
    return f"\N{BULLET} {resto}" if resto else "\N{BULLET}"


def _agrupar_en_parrafos(lineas: list[str]) -> list[str]:
    parrafos: list[str] = []
    for linea in lineas:
        if linea.startswith("\N{BULLET}") or not parrafos:
            parrafos.append(linea)
        else:
            parrafos[-1] = f"{parrafos[-1]} {linea}"
    return parrafos
