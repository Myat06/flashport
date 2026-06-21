CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE risk_level AS ENUM ('green', 'yellow', 'red');
CREATE TYPE jalur_type AS ENUM ('hijau', 'kuning', 'merah');
CREATE TYPE doc_type AS ENUM ('commercial_invoice', 'bill_of_lading', 'packing_list');

CREATE TABLE declarations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL UNIQUE,
    document_type doc_type NOT NULL,
    operator_id TEXT,
    device_id TEXT,
    scanned_at TIMESTAMPTZ NOT NULL,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    ml_kit_text TEXT,
    tesseract_text TEXT,
    confidence_badge confidence_level,
    risk_score SMALLINT CHECK (risk_score BETWEEN 0 AND 100),
    risk_badge risk_level,
    flagged_fields JSONB DEFAULT '[]',
    ceisa_ready BOOLEAN DEFAULT FALSE,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE declaration_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    declaration_id UUID NOT NULL REFERENCES declarations(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_value TEXT,
    is_edited BOOLEAN DEFAULT FALSE,
    edit_source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL,
    device_id TEXT,
    image_size_bytes INT,
    ml_kit_char_count INT,
    sync_duration_ms INT,
    status TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ceisa_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    declaration_id UUID NOT NULL REFERENCES declarations(id),
    submitted_by TEXT,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    jalur jalur_type,
    response_code TEXT,
    response_message TEXT,
    raw_response JSONB
);

CREATE INDEX idx_declarations_risk_badge ON declarations(risk_badge);
CREATE INDEX idx_declarations_confidence ON declarations(confidence_badge);
CREATE INDEX idx_declarations_created ON declarations(created_at DESC);
CREATE INDEX idx_decl_fields_declaration ON declaration_fields(declaration_id);
