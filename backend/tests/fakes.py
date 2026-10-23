import hashlib
import math
import re

_PALABRAS = re.compile(r"\w+")


class FakeEmbeddingProvider:
    """Proveedor determinista por bolsa de palabras con hashing, para no cargar el modelo real."""

    def __init__(
        self,
        nombre_modelo: str = "fake-bolsa-de-palabras",
        dimension: int = 256,
        max_tokens: int = 512,
    ) -> None:
        self.nombre_modelo = nombre_modelo
        self.dimension = dimension
        self.max_tokens = max_tokens

    def contar_tokens(self, texto: str) -> int:
        return len(_PALABRAS.findall(texto))

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        return [self._vectorizar(texto) for texto in textos]

    def embed_query(self, texto: str) -> list[float]:
        return self._vectorizar(texto)

    def _vectorizar(self, texto: str) -> list[float]:
        vector = [0.0] * self.dimension
        for palabra in _PALABRAS.findall(texto.lower()):
            # hashlib y no hash(): hash() cambia entre ejecuciones de Python.
            huella = int.from_bytes(hashlib.sha256(palabra.encode("utf-8")).digest()[:8], "big")
            vector[huella % self.dimension] += 1.0
        norma = math.sqrt(sum(valor * valor for valor in vector))
        if norma == 0:
            raise ValueError("El texto no tiene palabras; no se puede vectorizar.")
        return [valor / norma for valor in vector]
