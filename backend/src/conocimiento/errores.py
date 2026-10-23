class ConocimientoError(Exception):
    code = "CONOCIMIENTO_ERROR"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class InvalidQueryError(ConocimientoError):
    code = "INVALID_QUERY"


class NoEmbeddingsForModelError(ConocimientoError):
    code = "NO_EMBEDDINGS_FOR_MODEL"


class DatabaseUnavailableError(ConocimientoError):
    code = "DB_UNAVAILABLE"
