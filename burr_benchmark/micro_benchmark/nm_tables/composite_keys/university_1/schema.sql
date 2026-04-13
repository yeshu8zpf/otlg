\c postgres
\set database_name nm_tables__composite_keys__university_1
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE student (
    planned_graduation_year INT,
    first_name VARCHAR(50),
    last_name VARCHAR(50)
);

CREATE TABLE course (
    semester VARCHAR(50),
    course_name VARCHAR(100),
    credits INT
);


CREATE TABLE enrollment (
    planned_graduation_year INT,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    semester VARCHAR(50),
    course_name VARCHAR(100)
);

ALTER TABLE Only student
    ADD CONSTRAINT student_primary_key PRIMARY KEY (planned_graduation_year, first_name, last_name);

ALTER TABLE Only course
    ADD CONSTRAINT course_primary_key PRIMARY KEY (semester, course_name);

ALTER TABLE ONLY enrollment
    ADD CONSTRAINT enrollment_primary_key PRIMARY KEY (planned_graduation_year, first_name, last_name, semester, course_name);

ALTER TABLE ONLY enrollment
    ADD CONSTRAINT "FKenrollmentStudent" FOREIGN KEY (planned_graduation_year, first_name, last_name) REFERENCES student(planned_graduation_year, first_name, last_name) ON DELETE CASCADE;

ALTER TABLE ONLY enrollment
    ADD CONSTRAINT "FKenrollmentCourse" FOREIGN KEY (semester, course_name) REFERENCES course(semester, course_name) ON DELETE CASCADE;
-- schema_end
\copy student(planned_graduation_year, first_name, last_name) FROM 'train_data/nm_tables/composite_keys/university_1/student.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy course(semester, course_name, credits) FROM 'train_data/nm_tables/composite_keys/university_1/course.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy enrollment(planned_graduation_year, first_name, last_name, semester, course_name) FROM 'train_data/nm_tables/composite_keys/university_1/enrollment.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

