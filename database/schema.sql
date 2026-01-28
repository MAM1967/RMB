 -- Base schema for Recruiter Market Brief

 CREATE TABLE IF NOT EXISTS companies (
   id TEXT PRIMARY KEY,
   name TEXT NOT NULL,
   ats TEXT NOT NULL,
   careers_url TEXT,
   created_at TIMESTAMPTZ DEFAULT timezone('utc', now())
 );

 CREATE TABLE IF NOT EXISTS job_postings (
   id BIGSERIAL PRIMARY KEY,
   source_job_id TEXT NOT NULL,
   company_id TEXT NOT NULL REFERENCES companies (id),
   title TEXT NOT NULL,
   url TEXT NOT NULL,
   first_seen TIMESTAMPTZ NOT NULL,
   function TEXT,
   level TEXT,
   location_city TEXT,
   location_state TEXT,
   is_remote BOOLEAN DEFAULT FALSE,
   source_url TEXT NOT NULL,
   scraped_at TIMESTAMPTZ NOT NULL,
   CONSTRAINT job_postings_source_company_unique UNIQUE (source_job_id, company_id)
 );

 CREATE INDEX IF NOT EXISTS idx_job_postings_company_id
   ON job_postings (company_id);

 CREATE INDEX IF NOT EXISTS idx_job_postings_location
   ON job_postings (location_state, is_remote);

 CREATE INDEX IF NOT EXISTS idx_job_postings_first_seen
   ON job_postings (first_seen DESC);

 CREATE TABLE IF NOT EXISTS weekly_metrics (
   id BIGSERIAL PRIMARY KEY,
   week_start_date DATE NOT NULL,
   company_id TEXT NOT NULL REFERENCES companies (id),
   function TEXT,
   level TEXT,
   job_count INTEGER NOT NULL,
   created_at TIMESTAMPTZ DEFAULT timezone('utc', now()),
   CONSTRAINT weekly_metrics_unique UNIQUE (week_start_date, company_id, function, level)
 );

