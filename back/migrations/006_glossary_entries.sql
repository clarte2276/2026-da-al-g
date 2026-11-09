CREATE TABLE glossary_entries (
    id varchar(36) PRIMARY KEY,
    category varchar(32) NOT NULL DEFAULT '부품',
    title varchar(200) NOT NULL,
    code varchar(100),
    aliases text NOT NULL DEFAULT '',
    scope text NOT NULL DEFAULT '',
    location text NOT NULL DEFAULT '',
    photo_path varchar(2000),
    photo_media_type varchar(100),
    photo_caption text NOT NULL DEFAULT '',
    definition text NOT NULL DEFAULT '',
    symptoms text NOT NULL DEFAULT '',
    actions text NOT NULL DEFAULT '',
    regulations text NOT NULL DEFAULT '',
    status varchar(16) NOT NULL DEFAULT 'draft',
    document_id varchar(36) REFERENCES documents(id) ON DELETE SET NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
