CREATE TABLE companies (
    company_id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ats_type VARCHAR(255) NOT NULL CHECK (ats_type IN ('greenhouse', 'comeet')),
    ats_id VARCHAR(100) NOT NULL,
    careers_url TEXT,
    city VARCHAR(200),
    is_active boolean DEFAULT true
);