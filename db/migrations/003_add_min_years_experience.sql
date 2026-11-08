ALTER TABLE job_postings
    ADD COLUMN min_years_experience SMALLINT CHECK (min_years_experience >= 0);
