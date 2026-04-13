\c postgres
\set database_name normalized__same_concept_multiple_tables__library
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE book (
    "isbn" VARCHAR(50),
    "name" VARCHAR(50),
    "publication_year" INT,
    "copies_available" INT
);

CREATE TABLE book_2 (
    "isbn" VARCHAR(50),
    "name" VARCHAR(50),
    "publication_year" INT,
    "copies_available" INT
);

ALTER TABLE ONLY book ADD CONSTRAINT "book_primary_key" PRIMARY KEY (isbn);
ALTER TABLE ONLY book_2 ADD CONSTRAINT "book2_primary_key" PRIMARY KEY (isbn);
-- schema_end
\copy book("isbn", "name", "publication_year", "copies_available") FROM 'train_data/normalized/same_concept_multiple_tables/library/book.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy book_2("isbn", "name", "publication_year", "copies_available") FROM 'train_data/normalized/same_concept_multiple_tables/library/book_2.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

