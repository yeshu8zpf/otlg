\c postgres
\set database_name normalized__second_normal_form__person_address
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    id int,
    address_id int,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(50)
);

CREATE TABLE department (
    id int,
    name VARCHAR(50)
);

CREATE TABLE person_department (
    person_id int,
    department_id int
);

CREATE TABLE address (
    id int,
    street VARCHAR(50),
    house_number VARCHAR(50),
    zip VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50)
);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (id);

ALTER TABLE Only address
    ADD CONSTRAINT address_primary_key PRIMARY KEY (id);

ALTER TABLE Only department
    ADD CONSTRAINT department_primary_key PRIMARY KEY (id);

ALTER TABLE Only person_department
    ADD CONSTRAINT person_department_primary_key PRIMARY KEY (person_id, department_id);

ALTER TABLE ONLY person
    ADD CONSTRAINT "FKpersonAddress" FOREIGN KEY (address_id) REFERENCES address(id) ON DELETE CASCADE;

ALTER TABLE ONLY person_department
    ADD CONSTRAINT "FKpersonDepartmentPerson" FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE;

ALTER TABLE ONLY person_department
    ADD CONSTRAINT "FKpersonDepartmentDepartment" FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE;
-- schema_end
\copy address(id, street, house_number, zip, city, state) FROM 'train_data/normalized/second_normal_form/person_address/address.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy person(id, address_id, first_name, last_name, email) FROM 'train_data/normalized/second_normal_form/person_address/person.csv' WITH (FORMAT csv, HEADER true, DELIMITER ','); 
\copy department(id, name) FROM 'train_data/normalized/second_normal_form/person_address/department.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy person_department(person_id, department_id) FROM 'train_data/normalized/second_normal_form/person_address/person_department.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

