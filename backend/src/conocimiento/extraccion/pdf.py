import hashlib
import subprocess
from pathlib import Path

from conocimiento.config import cargar_config
from conocimiento.errores import PdfExtractionError

MINIMO_CARACTERES_LEGIBLES = 1500
SEGUNDOS_ESPERA_EXTRACCION = 120
TAMANO_BLOQUE_HUELLA = 1024 * 1024
SALTO_DE_PAGINA = "\f"


def extraer_paginas(ruta: Path, pdftotext_bin: str | None = None) -> list[str]:
    ejecutable = pdftotext_bin or cargar_config().pdftotext_bin
    if not Path(ruta).is_file():
        raise PdfExtractionError(f"No existe el archivo PDF: {ruta}")
    try:
        resultado = subprocess.run(
            [ejecutable, "-enc", "UTF-8", str(ruta), "-"],
            capture_output=True,
            timeout=SEGUNDOS_ESPERA_EXTRACCION,
        )
    except FileNotFoundError as error:
        raise PdfExtractionError(
            f"No se encontró pdftotext ('{ejecutable}'). Instálalo o indica "
            "la ruta del ejecutable en la variable PDFTOTEXT_BIN."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise PdfExtractionError(
            f"pdftotext tardó más de {SEGUNDOS_ESPERA_EXTRACCION} s con {Path(ruta).name} "
            "(revisa PDFTOTEXT_BIN y el archivo)."
        ) from error
    if resultado.returncode != 0:
        detalle = resultado.stderr.decode("utf-8", errors="replace").strip()
        raise PdfExtractionError(
            f"pdftotext ('{ejecutable}', configurable con PDFTOTEXT_BIN) falló con "
            f"{Path(ruta).name}: {detalle or 'sin detalle'}"
        )
    return _separar_paginas(resultado.stdout.decode("utf-8", errors="replace"))


def sha256_archivo(ruta: Path) -> str:
    huella = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        while bloque := archivo.read(TAMANO_BLOQUE_HUELLA):
            huella.update(bloque)
    return huella.hexdigest()


def tiene_texto_legible(paginas: list[str]) -> bool:
    return sum(len(pagina.strip()) for pagina in paginas) >= MINIMO_CARACTERES_LEGIBLES


def _separar_paginas(texto: str) -> list[str]:
    # En Windows pdftotext escribe \r\n; y cierra cada página con \f, incluida la última.
    paginas = texto.replace("\r\n", "\n").split(SALTO_DE_PAGINA)
    if paginas and paginas[-1] == "":
        paginas.pop()
    return paginas
