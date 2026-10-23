from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Contrato de un modelo de embeddings (US-004).

    Pasajes y preguntas van por métodos distintos porque algunos modelos (e5) les
    anteponen prefijos diferentes; esa diferencia queda dentro de cada proveedor.
    """

    nombre_modelo: str
    dimension: int
    max_tokens: int

    def contar_tokens(self, texto: str) -> int: ...

    def embed_documents(self, textos: list[str]) -> list[list[float]]: ...

    def embed_query(self, texto: str) -> list[float]: ...
