from collections.abc import Callable
from typing import Any

from sentence_transformers import SentenceTransformer

TAMANO_LOTE = 16
_PREFIJOS_E5 = ("passage: ", "query: ")
_SIN_PREFIJOS = ("", "")


class SentenceTransformersProvider:
    """Proveedor local para la familia e5 y BGE-M3 (`plan.md` §3.2)."""

    def __init__(
        self,
        nombre_modelo: str,
        tamano_lote: int = TAMANO_LOTE,
        cargar_modelo: Callable[[str], Any] = SentenceTransformer,
    ) -> None:
        if tamano_lote <= 0:
            raise ValueError(f"El tamaño de lote debe ser positivo; llegó {tamano_lote}.")
        self.nombre_modelo = nombre_modelo
        self.tamano_lote = tamano_lote
        self._modelo = cargar_modelo(nombre_modelo)
        self.dimension: int = self._modelo.get_embedding_dimension()
        self.max_tokens: int = self._modelo.get_max_seq_length()
        self._prefijo_pasaje, self._prefijo_pregunta = _prefijos(nombre_modelo)

    def contar_tokens(self, texto: str) -> int:
        # Sin tokens especiales ni prefijo: el margen de DEC-009 (60 tokens) los cubre.
        return len(self._modelo.tokenizer(texto, add_special_tokens=False)["input_ids"])

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        return self._vectorizar([f"{self._prefijo_pasaje}{texto}" for texto in textos])

    def embed_query(self, texto: str) -> list[float]:
        return self._vectorizar([f"{self._prefijo_pregunta}{texto}"])[0]

    def _vectorizar(self, textos: list[str]) -> list[list[float]]:
        vectores = self._modelo.encode(
            textos,
            batch_size=self.tamano_lote,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectores.tolist()


def _prefijos(nombre_modelo: str) -> tuple[str, str]:
    # Los modelos e5 se entrenaron con estos prefijos y rinden peor sin ellos; BGE-M3 no los usa.
    partes = nombre_modelo.lower().rsplit("/", 1)[-1].split("-")
    return _PREFIJOS_E5 if "e5" in partes else _SIN_PREFIJOS
