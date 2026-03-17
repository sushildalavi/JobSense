-- =============================================================================
-- ApplyFlow — PostgreSQL Initialization Script
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE applyflow TO applyflow;
