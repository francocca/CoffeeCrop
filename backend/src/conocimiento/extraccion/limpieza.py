import re
from collections import Counter

TIPO_MANUAL = "manual"
TIPO_AVANCE = "avance"

MINIMO_PAGINAS_PARA_ENCABEZADOS = 4
PROPORCION_MINIMA_ENCABEZADO = 0.40
MAXIMO_CARACTERES_ENCABEZADO = 80
MAXIMO_CARACTERES_LINEA_SUELTA = 3
MAXIMO_CARACTERES_LINEA_DE_PORTADA = 220
MAXIMO_CARACTERES_LINEA_DE_CREDITOS = 120
MAXIMO_LINEAS_DE_NOMBRES_TRAS_ETIQUETA = 4
MINIMO_PALABRAS_DE_AUTORES = 2

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

_IGNORAR_MAYUSCULAS = re.IGNORECASE
_ENCABEZADO_DE_BIBLIOGRAFIA = re.compile(
    r"^literatura\s+(citada|consultada)\b\s*:?\s*(\d+\s*[.\-)].*)?$", _IGNORAR_MAYUSCULAS
)
# Cada patrón identifica una línea administrativa de la portada o del pie de los Avances.
_LINEAS_ADMINISTRATIVAS = tuple(
    re.compile(patron, _IGNORAR_MAYUSCULAS)
    for patron in (
        r"\bISSN\b",
        r"^I{1,2}S{2,4}N{1,2}\b",  # la portada de algunos Avances sale con cada letra duplicada
        r"orcid",
        r"\bDOI\b|doi\.org",
        r"Gerencia T[eé]cnica\s*(/|Fondo Nacional)",
        r"Centro Nacional de Investigaciones de Caf[eé]\s+\"Pedro Uribe",
        r"\bTel\.?\s*\(|\bFax\b",
        r"^A\.A\.\s*\d+",
        r"cenicafe@|www\.cenicafe\.org",
        r"^(Chinchin[aá]|Manizales)\b.*Colombia",
        r"^\N{COPYRIGHT SIGN}\s*FNC",
        r"Centro Nacional de Investigaciones de Caf[eé].*(Chinchin[aá]|Manizales|Caldas)",
    )
)
_ENLACE_ORCID = re.compile(r"orcid\.org", _IGNORAR_MAYUSCULAS)
# Se reconocen por su comienzo y valen con cualquier largo: pdftotext a veces junta varias
# líneas de la portada o del pie en una sola de más de 400 caracteres.
_COMIENZOS_ADMINISTRATIVOS = tuple(
    re.compile(patron, _IGNORAR_MAYUSCULAS)
    for patron in (
        r"^(Los trabajos suscritos|Licencia Creative Commons)",
        r"^(ISSN\b|https?://doi\.org|DOI\b)",
        r"^[*\N{ASTERISK OPERATOR}]{1,3}\s*\S.*(Investigador|Asistente|Auxiliar|Profesional"
        r"|Ingenier|Director|Especialista|Bi[oó]log|Bacteri[oó]log|Qu[ií]mic|Agr[oó]nom"
        r"|Entom[oó]log|M\.?Sc|Ph\.?D|Centro Nacional de Investigaciones)",
    )
)
# Los autores solo se buscan en la primera página: en el resto, un asterisco o una barra
# vertical suele ser una nota o una celda de tabla.
_AUTORES_CON_ASTERISCO = re.compile(r"[^\W\d_]\s?[*\N{ASTERISK OPERATOR}]{1,3}")
_AUTORES_CON_BARRAS = re.compile(r"[^\W\d_]\.?\s*\|\s*[A-ZÁÉÍÓÚÑ]")
_SEPARADORES_DE_AUTORES = re.compile(r"[*\N{ASTERISK OPERATOR};,|]")
_ETIQUETA_DE_CREDITOS = re.compile(
    r"^(edici[oó]n|fotograf[ií]as?|diagramaci[oó]n|impresi[oó]n|imprenta)\b",
    _IGNORAR_MAYUSCULAS,
)
_PALABRA_DE_ETIQUETA = re.compile(
    r"^(edici[oó]n|fotograf[ií]as?|diagramaci[oó]n|impresi[oó]n|imprenta)$",
    _IGNORAR_MAYUSCULAS,
)
_PARTICULAS_DE_NOMBRE = frozenset({"de", "del", "la", "las", "los", "y", "van", "von"})
_PALABRA_DE_NOMBRE = re.compile(r"^[A-ZÁÉÍÓÚÑ][A-Za-záéíóúñü\-]*\.?$")


def limpiar_paginas(paginas: list[str], tipo: str) -> list[str]:
    if tipo not in (TIPO_MANUAL, TIPO_AVANCE):
        raise ValueError(f"Tipo de documento desconocido: {tipo!r}")
    paginas = quitar_encabezados_repetidos(paginas)
    if tipo == TIPO_AVANCE:
        paginas = quitar_portada_administrativa(cortar_bibliografia(paginas))
    return normalizar_texto_corrido(paginas)


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


def cortar_bibliografia(paginas: list[str]) -> list[str]:
    for posicion, pagina in enumerate(paginas):
        lineas = pagina.split("\n")
        for indice, linea in enumerate(lineas):
            if _ENCABEZADO_DE_BIBLIOGRAFIA.match(_colapsar(linea)):
                antes = "\n".join(lineas[:indice])
                return paginas[:posicion] + [antes] + [""] * (len(paginas) - posicion - 1)
    return list(paginas)


def quitar_portada_administrativa(paginas: list[str]) -> list[str]:
    return [
        "\n".join(_sin_lineas_administrativas(pagina.split("\n"), es_primera=posicion == 0))
        for posicion, pagina in enumerate(paginas)
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


def _sin_lineas_administrativas(lineas: list[str], es_primera: bool) -> list[str]:
    conservadas: list[str] = []
    nombres_pendientes = 0
    for linea in lineas:
        colapsada = _colapsar(linea)
        if _es_linea_de_creditos(colapsada):
            nombres_pendientes = MAXIMO_LINEAS_DE_NOMBRES_TRAS_ETIQUETA
        elif _es_linea_administrativa(colapsada) or (es_primera and _es_linea_de_autores(colapsada)):
            nombres_pendientes = 0
        elif nombres_pendientes and _es_solo_nombres(colapsada):
            nombres_pendientes -= 1
        else:
            nombres_pendientes = 0
            conservadas.append(linea)
    return conservadas


def _es_linea_administrativa(linea: str) -> bool:
    if _ENLACE_ORCID.search(linea) or any(
        patron.match(linea) for patron in _COMIENZOS_ADMINISTRATIVOS
    ):
        return True
    if not linea or len(linea) > MAXIMO_CARACTERES_LINEA_DE_PORTADA:
        return False
    return any(patron.search(linea) for patron in _LINEAS_ADMINISTRATIVAS)


def _es_linea_de_autores(linea: str) -> bool:
    if not linea or len(linea) > MAXIMO_CARACTERES_LINEA_DE_PORTADA:
        return False
    if _AUTORES_CON_BARRAS.search(linea):
        return True
    if not _AUTORES_CON_ASTERISCO.search(linea):
        return False
    palabras = _SEPARADORES_DE_AUTORES.sub(" ", linea).split()
    return len(palabras) >= MINIMO_PALABRAS_DE_AUTORES and all(
        _es_palabra_de_nombre(palabra) or palabra == "y" or palabra.rstrip(".").isupper()
        for palabra in palabras
    )


def _es_linea_de_creditos(linea: str) -> bool:
    if not _ETIQUETA_DE_CREDITOS.match(linea):
        return False
    palabras = [palabra.rstrip(":") for palabra in linea.split()]
    return all(
        _PALABRA_DE_ETIQUETA.match(palabra) or _es_palabra_de_nombre(palabra) for palabra in palabras
    )


def _es_solo_nombres(linea: str) -> bool:
    if not linea or len(linea) > MAXIMO_CARACTERES_LINEA_DE_CREDITOS:
        return False
    return all(_es_palabra_de_nombre(palabra) for palabra in linea.split())


def _es_palabra_de_nombre(palabra: str) -> bool:
    return palabra.lower() in _PARTICULAS_DE_NOMBRE or bool(_PALABRA_DE_NOMBRE.match(palabra))
