-- This script runs when PostgreSQL initializes
-- Ensure the nexusai user has proper permissions
ALTER USER nexusai WITH PASSWORD 'nexusai123';
GRANT ALL PRIVILEGES ON DATABASE nexusai_db TO nexusai;
