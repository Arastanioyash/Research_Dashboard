CREATE TYPE refresh_job_status AS ENUM ('pending', 'running', 'succeeded', 'failed');

CREATE TABLE refresh_job (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    status refresh_job_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ NULL,
    finished_at TIMESTAMPTZ NULL,
    message TEXT NULL,
    model_version VARCHAR(64) NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    raw_csv_path VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_refresh_job_project_source_model UNIQUE (project_id, source_hash, model_version)
);

CREATE INDEX ix_refresh_job_project_id ON refresh_job(project_id);
CREATE INDEX ix_refresh_job_source_hash ON refresh_job(source_hash);
