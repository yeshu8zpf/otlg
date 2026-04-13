\c postgres
\set database_name normalized__multiple_concepts_same_table__library
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
    "copies_available" INT,
    "author" VARCHAR(50),
    "birth_year" INT,
    "nationality" VARCHAR(50),
    "address" VARCHAR(200)
);

ALTER TABLE ONLY book ADD CONSTRAINT "book_primary_key" PRIMARY KEY (isbn);
-- schema_end
\copy book("isbn", "name", "publication_year", "copies_available", "author", "birth_year", "nationality", "address") FROM 'train_data/normalized/multiple_concepts_same_table/library/book.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
