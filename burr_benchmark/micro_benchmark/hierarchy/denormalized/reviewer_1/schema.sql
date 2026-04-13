\c postgres
\set database_name hierarchy__denormalized__reviewer_1
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    pid INT,
    name VARCHAR(50),
    email VARCHAR(50),
    area VARCHAR(50),
    type VARCHAR(50)
);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (pid);
-- schema_end
\copy person(pid, name, email, area, type) FROM 'train_data/hierarchy/denormalized/reviewer_1/person_denormalized.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
