\c postgres
\set database_name basic__table__stadium
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE stadium (
    id int
);

ALTER TABLE Only stadium
    ADD CONSTRAINT stadium_primary_key PRIMARY KEY (id);
-- schema_end
\copy stadium(id) FROM 'train_data/basic/table/stadium/stadium.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

