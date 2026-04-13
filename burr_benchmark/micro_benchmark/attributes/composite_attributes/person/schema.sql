\c postgres
\set database_name attributes__composite_attributes__person
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    id INTEGER,
    name VARCHAR(50),
    address VARCHAR(500)
);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (id);
-- schema_end
\copy person(id, name, address) FROM 'train_data/attributes/composite_attributes/person/person_data.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';');
