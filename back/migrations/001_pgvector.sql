-- Run once on an existing PostgreSQL database before deploying the API.
-- Fresh databases also attempt to create the extension during API startup.
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE fragments
    ADD COLUMN IF NOT EXISTS embedding_vector vector(1536);

CREATE INDEX IF NOT EXISTS ix_fragments_embedding_vector_hnsw
    ON fragments USING hnsw (embedding_vector vector_cosine_ops)
    WHERE embedding_vector IS NOT NULL;
