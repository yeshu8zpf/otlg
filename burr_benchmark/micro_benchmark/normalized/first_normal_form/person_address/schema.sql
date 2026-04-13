\c postgres
\set database_name normalized__first_normal_form__person_address
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    id int,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(50),
    department VARCHAR(50),
    department_id int,
    address_id int,
    street VARCHAR(50),
    house_number VARCHAR(50),
    zip VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50)
);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (id);
-- schema_end
\copy person(id, first_name, last_name, email, department, department_id, address_id, street, house_number, zip, city, state) FROM 'train_data/normalized/first_normal_form/person_address/person_fnf.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');