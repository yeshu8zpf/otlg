\c postgres
\set database_name hierarchy__each_combination__reviewer_1
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    pid INT,
    name VARCHAR(50)
);

CREATE TABLE author (
    pid INT,
    email VARCHAR(50)
);

CREATE TABLE reviewer (
    pid INT,
    area VARCHAR(50)
);

CREATE TABLE author_reviewer (
    pid INT,
    email VARCHAR(50),
    area VARCHAR(50)
);


ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (pid);

ALTER TABLE Only author
    ADD CONSTRAINT author_primary_key PRIMARY KEY (pid);

ALTER TABLE Only reviewer
    ADD CONSTRAINT reviewer_primary_key PRIMARY KEY (pid);

ALTER TABLE Only author_reviewer
    ADD CONSTRAINT author_reviewer_primary_key PRIMARY KEY (pid);

ALTER TABLE ONLY author
    ADD CONSTRAINT "FKpID" FOREIGN KEY (pid) REFERENCES person(pid) ON DELETE CASCADE;

ALTER TABLE ONLY reviewer
    ADD CONSTRAINT "FKpID" FOREIGN KEY (pid) REFERENCES person(pid) ON DELETE CASCADE;

ALTER TABLE ONLY author_reviewer
    ADD CONSTRAINT "FKpID" FOREIGN KEY (pid) REFERENCES person(pid) ON DELETE CASCADE;
-- schema_end
\copy person(pid, name) FROM 'train_data/hierarchy/each_combination/reviewer_1/person.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy author(pid, email) FROM 'train_data/hierarchy/each_combination/reviewer_1/author.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy reviewer(pid, area) FROM 'train_data/hierarchy/each_combination/reviewer_1/reviewer.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy author_reviewer(pid, email, area) FROM 'train_data/hierarchy/each_combination/reviewer_1/author_reviewer.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
