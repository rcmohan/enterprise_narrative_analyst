CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company       TEXT NOT NULL,
  doc_type      TEXT NOT NULL,
  fiscal_period TEXT NOT NULL,
  source_url    TEXT,
  file_hash     TEXT UNIQUE NOT NULL,
  ingested_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE chunks (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  company       TEXT NOT NULL,
  doc_type      TEXT NOT NULL,
  fiscal_period TEXT NOT NULL,
  chunk_index   INT NOT NULL,
  text          TEXT NOT NULL,
  token_count   INT,
  embedding     vector(1536),
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX chunks_embedding_idx ON chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX chunks_company_idx ON chunks (company);
CREATE INDEX chunks_doc_type_idx ON chunks (doc_type);
CREATE INDEX chunks_fiscal_period_idx ON chunks (fiscal_period);
