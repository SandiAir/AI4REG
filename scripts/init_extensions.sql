-- PostgreSQL Extensions fuer ngdai
-- Wird automatisch beim ersten Start von Docker Compose ausgefuehrt

CREATE EXTENSION IF NOT EXISTS age;
-- pgvector wird spaeter hinzugefuegt wenn das Docker-Image es unterstuetzt
-- CREATE EXTENSION IF NOT EXISTS vector;

LOAD 'age';
SET search_path = ag_catalog, "$user", public;
SELECT create_graph('ngdai_graph');
