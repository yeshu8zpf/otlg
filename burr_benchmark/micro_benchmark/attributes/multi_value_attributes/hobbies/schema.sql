\c postgres
\set database_name attributes__multi_value_attributes__hobbies
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    id INT,
    name VARCHAR(50)
);

CREATE TABLE hobbies (
    person_id INT,
    name VARCHAR(50),
    difficulty VARCHAR(50)
);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (id);

ALTER TABLE Only hobbies
    ADD CONSTRAINT hobbies_primary_key PRIMARY KEY (person_id, name);

ALTER TABLE ONLY hobbies
    ADD CONSTRAINT "FKpersonID" FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE;
-- schema_end
\copy person(id, name) FROM 'train_data/attributes/multi_value_attributes/hobbies/person.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy hobbies(person_id, name, difficulty) FROM 'train_data/attributes/multi_value_attributes/hobbies/hobbies.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

