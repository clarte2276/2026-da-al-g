-- Add character-level provenance for manually selected text ranges.
ALTER TABLE knowledge_edges
    ADD COLUMN IF NOT EXISTS source_anchor_json JSONB;

ALTER TABLE knowledge_edges
    ADD COLUMN IF NOT EXISTS target_anchor_json JSONB;
