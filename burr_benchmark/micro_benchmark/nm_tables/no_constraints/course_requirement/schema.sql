\c postgres
\set database_name nm_tables__no_constraints__course_requirement
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
-- schema_end
-- data
\copy course(id, name) FROM 'train_data/nm_tables/no_constraints/course_requirement/course_nc.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy requirement(id, name) FROM 'train_data/nm_tables/no_constraints/course_requirement/requirement_nc.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy course_requirement(course_id, requirement_id) FROM 'train_data/nm_tables/no_constraints/course_requirement/course_requirement_nc.csv' WITH (FORMAT csv, HEADER true, DELIMITER ','); 

