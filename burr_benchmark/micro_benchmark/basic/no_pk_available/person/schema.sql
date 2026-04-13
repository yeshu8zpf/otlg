\c postgres
\set database_name basic__no_pk_available__person
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    id int
);
-- schema_end
\copy person(id) FROM 'train_data/basic/no_pk_available/person/person_nopk.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

