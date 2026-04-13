\c postgres
\set database_name complex__scenario_f__reviewer
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE author (
    aid INT,
    name VARCHAR(50),
    email VARCHAR(50)
);

CREATE TABLE reviewer (
    rid INT,
    name VARCHAR(50),
    area VARCHAR(50),
    type VARCHAR(50) NOT NULL,
    editorial_role VARCHAR(50),
    institution_affiliation VARCHAR(100),
    reputation_score INT
);

CREATE TABLE person (
    pid INT,
    name VARCHAR(50) NOT NULL
);


ALTER TABLE Only author
    ADD CONSTRAINT author_primary_key PRIMARY KEY (aid);

ALTER TABLE Only reviewer
    ADD CONSTRAINT reviewer_primary_key PRIMARY KEY (rid);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (pid);
-- schema_end
\copy author(aid, name, email) FROM 'train_data/complex/scenario_f/reviewer/author.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy reviewer(rid, name, area, type, editorial_role, institution_affiliation, reputation_score) FROM 'train_data/complex/scenario_f/reviewer/reviewer.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy person(pid, name) FROM 'train_data/complex/scenario_f/reviewer/person.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
