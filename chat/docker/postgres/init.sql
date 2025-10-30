-- Initialize PostgreSQL database for triage chat system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema if needed
-- CREATE SCHEMA IF NOT EXISTS triage;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE triage_chat TO postgres;

-- The actual tables will be created by Alembic migrations
