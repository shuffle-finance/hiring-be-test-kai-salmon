-- Database initialization script for Backend Developer Coding Test
-- This creates an empty database that candidates can use to design their own schema

-- Create database and user (already done by Docker environment variables)
-- POSTGRES_DB=transactions, POSTGRES_USER=postgres, POSTGRES_PASSWORD=password

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a basic logging table to track candidate API activity (optional)
CREATE TABLE IF NOT EXISTS candidate_api_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    user_agent TEXT,
    ip_address INET,
    request_data JSONB,
    response_data JSONB
);

-- Create an index on timestamp for performance
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON candidate_api_logs(timestamp);

-- Insert welcome message
INSERT INTO candidate_api_logs (endpoint, method, status_code, response_time_ms, request_data, response_data)
VALUES (
    '/welcome',
    'INFO',
    200,
    0,
    '{"message": "database_initialized"}',
    '{"message": "Welcome to the Backend Developer Coding Test! This PostgreSQL database is ready for your schema design. Good luck!"}'
)
ON CONFLICT DO NOTHING;

-- Grant permissions to ensure candidates can create tables
GRANT ALL PRIVILEGES ON DATABASE transactions TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Add some helpful comments
COMMENT ON DATABASE transactions IS 'Backend Developer Coding Test - Design your own schema here!';
COMMENT ON TABLE candidate_api_logs IS 'Optional logging table - feel free to use or ignore';

-- Show successful initialization
SELECT 'Database initialized successfully for Backend Developer Coding Test!' AS status; 