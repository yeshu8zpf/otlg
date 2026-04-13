\c postgres
\set database_name one_to_n__binary_reflexive_n1__boss_employee
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE employee (
    id INT,
    name VARCHAR(50),
    boss_id INT
);

ALTER TABLE Only "employee" ADD CONSTRAINT "employee_primary_key" PRIMARY KEY (id);
ALTER TABLE ONLY "employee" ADD CONSTRAINT "FKemployeeBoss" FOREIGN KEY (boss_id) REFERENCES employee(id) ON DELETE CASCADE;
-- schema_end
\copy employee(id, name, boss_id) FROM 'train_data/one_to_n/binary_reflexive_n1/boss_employee/employee.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');  
