-- PostgreSQL: additive migration; preserves documents, fragments and knowledge_edges.
-- SQLite development databases receive these tables through Base.metadata.create_all.
CREATE TABLE IF NOT EXISTS document_contents (
    version_id VARCHAR(36) PRIMARY KEY REFERENCES document_versions(id),
    kind VARCHAR(16) NOT NULL,
    text TEXT NOT NULL,
    pages JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS document_links (
    id VARCHAR(36) PRIMARY KEY,
    source_version_id VARCHAR(36) NOT NULL REFERENCES document_versions(id),
    target_version_id VARCHAR(36) NOT NULL REFERENCES document_versions(id),
    source_selection JSON NOT NULL,
    target_selection JSON NOT NULL,
    relation_type VARCHAR(64) NOT NULL,
    note TEXT,
    status VARCHAR(32) NOT NULL,
    created_by VARCHAR(128),
    approved_by VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS ix_document_links_source_version_id ON document_links(source_version_id);
CREATE INDEX IF NOT EXISTS ix_document_links_target_version_id ON document_links(target_version_id);
CREATE INDEX IF NOT EXISTS ix_document_links_status ON document_links(status);
