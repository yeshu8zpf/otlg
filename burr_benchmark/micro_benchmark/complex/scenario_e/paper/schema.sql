\c postgres
\set database_name complex__scenario_e__paper
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    pid INT,
    name VARCHAR(50),
    email VARCHAR(50),
    area VARCHAR(50),
    type VARCHAR(50)
);

CREATE TABLE paper (
    paper_id INT,
    title VARCHAR(100),
    abstract TEXT,
    year INT,
    reviewer_id INT,
    author_id INT
);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (pid);
ALTER TABLE Only paper
    ADD CONSTRAINT paper_primary_key PRIMARY KEY (paper_id);

ALTER TABLE paper ADD CONSTRAINT FKpaperReviewer FOREIGN KEY (reviewer_id) REFERENCES person(pid) ON DELETE CASCADE;
ALTER TABLE paper ADD CONSTRAINT FKpaperAuthor FOREIGN KEY (author_id) REFERENCES person(pid) ON DELETE CASCADE;
-- schema_end
\copy person(pid, name, email, area, type) FROM 'train_data/complex/scenario_e/paper/person.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy paper(paper_id, title, abstract, year, reviewer_id, author_id) FROM 'train_data/complex/scenario_e/paper/paper.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
