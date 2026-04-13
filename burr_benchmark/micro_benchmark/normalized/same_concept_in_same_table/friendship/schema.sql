\c postgres
\set database_name normalized__same_concept_in_same_table__friendship
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE friendship (
    "person_id_a" VARCHAR(50),
    "name_a" VARCHAR(50),
    "address_a" VARCHAR(50),
    "person_id_b" VARCHAR(50),
    "name_b" VARCHAR(50),
    "address_b" VARCHAR(50)
);

ALTER TABLE ONLY friendship ADD CONSTRAINT "friendship_primary_key" PRIMARY KEY ("person_id_a", "person_id_b");
-- schema_end
\copy friendship("person_id_a", "name_a", "address_a", "person_id_b", "name_b", "address_b") FROM 'train_data/normalized/same_concept_in_same_table/friendship/friendship.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

