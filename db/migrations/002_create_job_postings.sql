CREATE TABLE job_postings (
    job_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies (company_id),
    ats_type VARCHAR(255) NOT NULL CHECK (ats_type IN ('greenhouse', 'comeet')),
    external_id VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    level VARCHAR(100),
    role_family VARCHAR(100),
    city VARCHAR(200),
    work_mode VARCHAR(100),
    url TEXT,
    description TEXT,
    content_hash TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    UNIQUE (ats_type, company_id, external_id)
);
