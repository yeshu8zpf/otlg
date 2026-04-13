\c postgres
\set database_name nm_tables__ternary_relation__textbook_course_instructor
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE textbook (
    id integer,
    title VARCHAR(500)
);

CREATE TABLE instructor (
    id integer,
    name VARCHAR(50)
);

CREATE TABLE course (
    id integer,
    name VARCHAR(500),
    credits integer,
    max_students integer
);

CREATE TABLE textbook_course_instructor (
    tid integer,
    iid integer,
    cid integer
);

ALTER TABLE Only textbook
    ADD CONSTRAINT textbook_primary_key PRIMARY KEY (id);

ALTER TABLE Only instructor
    ADD CONSTRAINT instructor_primary_key PRIMARY KEY (id);

ALTER TABLE Only course
    ADD CONSTRAINT course_primary_key PRIMARY KEY (id);

ALTER TABLE Only textbook_course_instructor
    ADD CONSTRAINT textbook_course_instructor_primary_key PRIMARY KEY (tid, iid, cid);

ALTER TABLE ONLY textbook_course_instructor
    ADD CONSTRAINT "FKtextbook_course_instructorTextbook" FOREIGN KEY (tid) REFERENCES textbook(id) ON DELETE CASCADE;

ALTER TABLE ONLY textbook_course_instructor
    ADD CONSTRAINT "FKtextbook_course_instructorInstructor" FOREIGN KEY (iid) REFERENCES instructor(id) ON DELETE CASCADE;

ALTER TABLE ONLY textbook_course_instructor
    ADD CONSTRAINT "FKtextbook_course_instructorCourse" FOREIGN KEY (cid) REFERENCES course(id) ON DELETE CASCADE;
-- schema_end

-- data
\copy textbook(id, title) FROM 'train_data/nm_tables/ternary_relation/textbook_course_instructor/textbook.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy instructor(id, name) FROM 'train_data/nm_tables/ternary_relation/textbook_course_instructor/instructor.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy course(id, name, credits, max_students) FROM 'train_data/nm_tables/ternary_relation/textbook_course_instructor/course.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy textbook_course_instructor(tid, iid, cid) FROM 'train_data/nm_tables/ternary_relation/textbook_course_instructor/textbook_course_instructor.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

