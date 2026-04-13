\c postgres
\set database_name attributes__boolean_relation__process
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE service (
    id int,
    name varchar(50),
    relevant_for_oil_and_gas boolean,
    relevant_for_automotive boolean,
    relevant_for_chemical boolean,
    relevant_for_pharma boolean,
    relevant_for_food boolean,
    relevant_for_retail boolean,
    relevant_for_logistics boolean,
    relevant_for_aviation boolean,
    relevant_for_energy boolean
);

ALTER TABLE ONLY service ADD CONSTRAINT "service_primary_key" PRIMARY KEY (id);
-- schema_end
\copy service(id,name,relevant_for_oil_and_gas,relevant_for_automotive,relevant_for_chemical,relevant_for_pharma,relevant_for_food,relevant_for_retail,relevant_for_logistics,relevant_for_aviation,relevant_for_energy) FROM 'train_data/attributes/boolean_relation/process/service_data.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');