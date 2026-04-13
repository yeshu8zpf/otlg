\c postgres
\set database_name one_to_one__binary_one_to_one_two_relations__marriage
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE person (
    id INT,
    name VARCHAR(50),
    sex VARCHAR(1)
);

CREATE TABLE marriage (
    pers_id INT,
    spouse_id INT
);

ALTER TABLE person ADD CONSTRAINT person_primary_key PRIMARY KEY (id);
ALTER TABLE marriage ADD CONSTRAINT marriage_primary_key PRIMARY KEY (pers_id);

ALTER TABLE marriage ADD CONSTRAINT FKmarriagePerson FOREIGN KEY (pers_id) REFERENCES person(id) ON DELETE CASCADE;
ALTER TABLE marriage ADD CONSTRAINT FKmarriageSpouse FOREIGN KEY (spouse_id) REFERENCES person(id) ON DELETE CASCADE;
ALTER TABLE marriage ADD UNIQUE (spouse_id);
-- schema_end
\copy person(id, name,sex ) FROM 'train_data/one_to_one/binary_one_to_one_two_relations/marriage/person.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy marriage(pers_id, spouse_id) FROM 'train_data/one_to_one/binary_one_to_one_two_relations/marriage/marriage.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

