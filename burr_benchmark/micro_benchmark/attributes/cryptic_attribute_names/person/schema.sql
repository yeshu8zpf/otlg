-- Start by connecting to the 'postgres' database
\c postgres

\set database_name attributes__cryptic_attribute_names__person
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;

-- schema_start
CREATE TABLE person (
    "NFSA" int,
    "NZQW2ZI" VARCHAR(50),
    "MFSGI4TFONZQ" VARCHAR(100),
    "MVWWC2LM" VARCHAR(50),
    "OBUG63TFL5XHK3LCMVZA" VARCHAR(50)
);

ALTER TABLE person ADD CONSTRAINT person_primary_key PRIMARY KEY ("NFSA");
-- schema_end
\copy person("NFSA", "NZQW2ZI", "MFSGI4TFONZQ", "MVWWC2LM", "OBUG63TFL5XHK3LCMVZA") FROM 'train_data/attributes/cryptic_attribute_names/person/person_cryptic_data.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
