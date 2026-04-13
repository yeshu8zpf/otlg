\c postgres
\set database_name nm_tables__general__course_requirement
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
-- schema_start
CREATE TABLE course (
    id int,
    name varchar(50)
);

CREATE TABLE requirement (
    id int,
    name varchar(50)
);

CREATE TABLE course_requirement (
    course_id int,
    requirement_id int
);

ALTER TABLE ONLY course
    ADD CONSTRAINT course_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY requirement
    ADD CONSTRAINT requirement_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY course_requirement
    ADD CONSTRAINT course_requirement_primary_key PRIMARY KEY (course_id, requirement_id);

ALTER TABLE ONLY course_requirement
    ADD CONSTRAINT "FKcourserequirementcourse" FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE;

ALTER TABLE ONLY course_requirement
    ADD CONSTRAINT "FKcourserequirementrequirement" FOREIGN KEY (requirement_id) REFERENCES requirement(id) ON DELETE CASCADE;
-- schema_end
\copy course(id, name) FROM 'train_data/nm_tables/general/course_requirement/course.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy requirement(id, name) FROM 'train_data/nm_tables/general/course_requirement/requirement.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy course_requirement(course_id, requirement_id) FROM 'train_data/nm_tables/general/course_requirement/course_requirement.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');


