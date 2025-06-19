-- Spotify Music Recommendation System v2 Database Initialization
-- This script sets up the PostgreSQL database with required extensions and optimizations

-- Set connection parameters
\set ON_ERROR_STOP on

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search and similarity
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For GIN indexes on btree types
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- For query performance monitoring

-- Create custom functions for audio feature similarity
CREATE OR REPLACE FUNCTION euclidean_distance(a REAL[], b REAL[])
RETURNS REAL AS $$
DECLARE
    result REAL := 0;
    i INTEGER;
BEGIN
    IF array_length(a, 1) != array_length(b, 1) THEN
        RAISE EXCEPTION 'Arrays must have the same length';
    END IF;
    
    FOR i IN 1..array_length(a, 1) LOOP
        result := result + POWER(a[i] - b[i], 2);
    END LOOP;
    
    RETURN SQRT(result);
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- Create function for cosine similarity
CREATE OR REPLACE FUNCTION cosine_similarity(a REAL[], b REAL[])
RETURNS REAL AS $$
DECLARE
    dot_product REAL := 0;
    norm_a REAL := 0;
    norm_b REAL := 0;
    i INTEGER;
BEGIN
    IF array_length(a, 1) != array_length(b, 1) THEN
        RAISE EXCEPTION 'Arrays must have the same length';
    END IF;
    
    FOR i IN 1..array_length(a, 1) LOOP
        dot_product := dot_product + (a[i] * b[i]);
        norm_a := norm_a + POWER(a[i], 2);
        norm_b := norm_b + POWER(b[i], 2);
    END LOOP;
    
    IF norm_a = 0 OR norm_b = 0 THEN
        RETURN 0;
    END IF;
    
    RETURN dot_product / (SQRT(norm_a) * SQRT(norm_b));
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- Create materialized view for audio feature statistics by cluster
CREATE OR REPLACE FUNCTION refresh_cluster_stats()
RETURNS void AS $$
BEGIN
    -- This will be called after cluster assignments are updated
    REFRESH MATERIALIZED VIEW CONCURRENTLY cluster_audio_stats;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance (will be applied after tables are created)
-- These will be handled by SQLAlchemy, but we can add some additional ones

-- Set up configuration for better performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Create role for application
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'spotify_app_role') THEN
        CREATE ROLE spotify_app_role;
    END IF;
END
$$;

-- Grant permissions
GRANT CONNECT, CREATE ON DATABASE spotify_recommendations TO spotify_user;
GRANT spotify_app_role TO spotify_user;

-- Create schema for ML models storage (optional)
CREATE SCHEMA IF NOT EXISTS ml_models;
GRANT USAGE ON SCHEMA ml_models TO spotify_user;
GRANT CREATE ON SCHEMA ml_models TO spotify_user;

-- Table for storing ML model metadata
CREATE TABLE IF NOT EXISTS ml_models.model_metadata (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL UNIQUE,
    model_type VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    parameters JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    file_path TEXT,
    file_size BIGINT,
    checksum VARCHAR(64)
);

-- Create index on model metadata
CREATE INDEX IF NOT EXISTS idx_model_metadata_name_version ON ml_models.model_metadata(model_name, version);
CREATE INDEX IF NOT EXISTS idx_model_metadata_active ON ml_models.model_metadata(is_active);

-- Set up logging for performance monitoring
CREATE TABLE IF NOT EXISTS public.query_performance_log (
    id SERIAL PRIMARY KEY,
    query_type VARCHAR(100),
    execution_time_ms REAL,
    row_count INTEGER,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create function to log query performance
CREATE OR REPLACE FUNCTION log_query_performance(
    p_query_type VARCHAR(100),
    p_execution_time_ms REAL,
    p_row_count INTEGER DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    INSERT INTO public.query_performance_log (query_type, execution_time_ms, row_count)
    VALUES (p_query_type, p_execution_time_ms, p_row_count);
END;
$$ LANGUAGE plpgsql;

-- Create function to clean old performance logs
CREATE OR REPLACE FUNCTION cleanup_performance_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.query_performance_log 
    WHERE logged_at < NOW() - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions on utility functions and tables
GRANT USAGE ON SCHEMA public TO spotify_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO spotify_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO spotify_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ml_models TO spotify_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ml_models TO spotify_user;

-- Print completion message
\echo 'Database initialization completed successfully!'
\echo 'Extensions created: uuid-ossp, pg_trgm, btree_gin, pg_stat_statements'
\echo 'Custom functions created: euclidean_distance, cosine_similarity'
\echo 'ML models schema created with metadata table'
\echo 'Performance monitoring tables and functions created' 