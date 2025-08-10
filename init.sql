DO $$
BEGIN
   -- Create postgres superuser if it doesn't exist
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
      CREATE ROLE postgres WITH LOGIN PASSWORD 'postgres' SUPERUSER CREATEDB CREATEROLE REPLICATION;
      RAISE NOTICE 'Created postgres superuser';
   END IF;
   
   -- You can also create additional superusers here
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
      CREATE ROLE admin WITH LOGIN PASSWORD 'admin123' SUPERUSER CREATEDB CREATEROLE;
      RAISE NOTICE 'Created admin superuser';
   END IF;
END
$$;


CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

SELECT 'Current user: ' || current_user;
SELECT 'Current database: ' || current_database();
