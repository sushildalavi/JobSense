-- =============================================================================
-- JobSense — PostgreSQL Initialization Script
-- Runs once on first container start. Sets up extensions and grants.
-- =============================================================================

-- ─── Required Extensions ─────────────────────────────────────────────────────
-- uuid-ossp: server-side UUID generation (uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- vector: pgvector for embedding similarity search
CREATE EXTENSION IF NOT EXISTS "vector";

-- pg_trgm: trigram-based fuzzy text search (used for job/company search)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- btree_gin: GIN indexes on scalar types (useful for compound JSON + status indexes)
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ─── Privileges ──────────────────────────────────────────────────────────────
GRANT ALL PRIVILEGES ON DATABASE jobsense TO jobsense;

-- ─── Performance Tuning ──────────────────────────────────────────────────────
-- These are safe defaults for a development instance.  Adjust for production.
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;          -- SSD-friendly
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload config so the changes take effect inside this container session.
SELECT pg_reload_conf();

-- ─── Development helpers ─────────────────────────────────────────────────────
-- Create a test database so CI migrations can run against an isolated DB.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'jobsense_test') THEN
        PERFORM dblink_exec('dbname=postgres', 'CREATE DATABASE jobsense_test OWNER jobsense');
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- dblink may not be available; test DB creation is optional
    NULL;
END
$$;
