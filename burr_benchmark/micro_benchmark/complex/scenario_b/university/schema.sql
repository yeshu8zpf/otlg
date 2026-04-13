\c postgres
\set database_name complex__scenario_b__university
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

CREATE TABLE department (
    department_name VARCHAR(100),
    building VARCHAR(100)
);

CREATE TABLE instructor (
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    department_name VARCHAR(100)
);

CREATE TABLE teaching_assignment (
    semester VARCHAR(50),
    course_name VARCHAR(100),
    instructor_first_name VARCHAR(50),
    instructor_last_name VARCHAR(50),
    assigned_date DATE
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

ALTER TABLE Only department
    ADD CONSTRAINT department_primary_key PRIMARY KEY (department_name);

ALTER TABLE Only instructor
    ADD CONSTRAINT instructor_primary_key PRIMARY KEY (first_name, last_name);

ALTER TABLE Only instructor
    ADD CONSTRAINT "FKinstructorDepartment" FOREIGN KEY (department_name) REFERENCES department(department_name) ON DELETE CASCADE;

ALTER TABLE Only teaching_assignment
    ADD CONSTRAINT teaching_assignment_primary_key PRIMARY KEY (instructor_first_name, instructor_last_name, semester, course_name);

ALTER TABLE Only teaching_assignment
    ADD CONSTRAINT "FKteachingAssignmentInstructor" FOREIGN KEY (instructor_first_name, instructor_last_name) REFERENCES instructor(first_name, last_name) ON DELETE CASCADE;

ALTER TABLE Only teaching_assignment
    ADD CONSTRAINT "FKteachingAssignmentCourse" FOREIGN KEY (semester, course_name) REFERENCES course(semester, course_name) ON DELETE CASCADE;
-- schema_end
\copy student(planned_graduation_year, first_name, last_name) FROM 'train_data/complex/scenario_b/university/student.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy course(semester, course_name, credits) FROM 'train_data/complex/scenario_b/university/course.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy enrollment(planned_graduation_year, first_name, last_name, semester, course_name) FROM 'train_data/complex/scenario_b/university/enrollment.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy department(department_name, building) FROM 'train_data/complex/scenario_b/university/department.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy instructor(first_name, last_name, department_name) FROM 'train_data/complex/scenario_b/university/instructor.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

