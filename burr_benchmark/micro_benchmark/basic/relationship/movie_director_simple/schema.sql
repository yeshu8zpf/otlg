\c postgres
\set database_name basic__relationship__movie_director_simple
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE movie (
    id int,
    director int
);

CREATE TABLE director (
    id int
);

ALTER TABLE Only movie
    ADD CONSTRAINT movie_primary_key PRIMARY KEY (id);

ALTER TABLE Only director
    ADD CONSTRAINT director_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY movie
    ADD CONSTRAINT "FKdirector" FOREIGN KEY (director) REFERENCES director(id) ON DELETE CASCADE;
-- schema_end
\copy director(id) FROM 'train_data/basic/relationship/movie_director_simple/director.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy movie(id, director) FROM 'train_data/basic/relationship/movie_director_simple/movie.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
