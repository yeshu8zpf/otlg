\c postgres
\set database_name normalized__multiple_concepts_same_table__person_organization
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person_organization (
    person_id INTEGER,
    person_name VARCHAR(50),
    person_address VARCHAR(50),
    person_role VARCHAR(50),
    person_phone_number INTEGER,
    organization_id INTEGER,
    organization_name VARCHAR(50),
    organization_address VARCHAR(50),
    organization_phone_number INTEGER    
);

ALTER TABLE Only person_organization
    ADD CONSTRAINT person_organization_primary_key PRIMARY KEY (person_id, organization_id);
-- schema_end
\copy person_organization(person_id, person_name, person_address, person_role, person_phone_number, organization_id, organization_name, organization_address, organization_phone_number) FROM 'train_data/normalized/multiple_concepts_same_table/person_organization/person_organization.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

