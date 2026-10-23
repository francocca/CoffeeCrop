CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documento (
  id              UUID PRIMARY KEY,
  nombre_archivo  TEXT NOT NULL UNIQUE,
  categoria       CHAR(1) NOT NULL CHECK (categoria IN ('A','B','R','C')),
  tipo            TEXT NOT NULL CHECK (tipo IN ('manual','avance')),
  numero_avance   INTEGER,
  sha256          CHAR(64) NOT NULL,
  paginas         INTEGER NOT NULL,
  estado          TEXT NOT NULL CHECK (estado IN ('indexado','sin_texto','error')),
  fecha_ingesta   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fragmento (
  id            UUID PRIMARY KEY,
  documento_id  UUID NOT NULL REFERENCES documento(id) ON DELETE CASCADE,
  orden         INTEGER NOT NULL,
  texto         TEXT NOT NULL,
  pagina_inicio INTEGER NOT NULL,
  pagina_fin    INTEGER NOT NULL,
  tokens        INTEGER NOT NULL,
  es_tabla      BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE (documento_id, orden)
);

CREATE TABLE IF NOT EXISTS embedding (
  fragmento_id UUID NOT NULL REFERENCES fragmento(id) ON DELETE CASCADE,
  modelo       TEXT NOT NULL,
  dimension    INTEGER NOT NULL,
  vector       vector NOT NULL,
  PRIMARY KEY (fragmento_id, modelo)
);
CREATE INDEX IF NOT EXISTS embedding_modelo_idx ON embedding (modelo);

CREATE TABLE IF NOT EXISTS configuracion (
  clave TEXT PRIMARY KEY,
  valor TEXT NOT NULL
);
