\c postgres
\set database_name attributes__boolean_relation__software
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE software (
    id int,
    name varchar(50),
    supports_windows boolean,
    supports_mac boolean,
    supports_linux boolean
);

ALTER TABLE ONLY software ADD CONSTRAINT "software_primary_key" PRIMARY KEY (id);
-- schema_end
\copy software(id,name,supports_windows,supports_mac,supports_linux) FROM 'train_data/attributes/boolean_relation/software/software_data.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');