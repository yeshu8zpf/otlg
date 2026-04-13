\c postgres
\set database_name nm_tables__general__employee_skill
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
-- schema_start
CREATE TABLE employee (
    id int,
    name varchar(50)
);

CREATE TABLE skill (
    id int,
    name varchar(50)
);

CREATE TABLE employee_skill (
    employee_id int,
    skill_id int
);

ALTER TABLE ONLY employee
    ADD CONSTRAINT employee_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY skill
    ADD CONSTRAINT skill_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY employee_skill
    ADD CONSTRAINT employee_skill_primary_key PRIMARY KEY (employee_id, skill_id);

ALTER TABLE ONLY employee_skill
    ADD CONSTRAINT "FKemployeeskillemployee" FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE;

ALTER TABLE ONLY employee_skill
    ADD CONSTRAINT "FKemployeeskillskill" FOREIGN KEY (skill_id) REFERENCES skill(id) ON DELETE CASCADE;
-- schema_end
\copy employee(id, name) FROM 'train_data/nm_tables/general/employee_skill/employee.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy skill(id, name) FROM 'train_data/nm_tables/general/employee_skill/skill.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy employee_skill(employee_id, skill_id) FROM 'train_data/nm_tables/general/employee_skill/employee_skill.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');


