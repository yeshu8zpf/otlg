\c postgres
\set database_name nm_tables__additional_attributes__group_1
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE user_ (
    "id" int
);

CREATE TABLE group_ (
    "id" INT
);

CREATE TABLE user_group (
    uid INT,
    gid INT,
    registration_date INT,
    expiration_duration INT,
    access_rights VARCHAR(50)
);

ALTER TABLE Only "user_" ADD CONSTRAINT "user_primary_key" PRIMARY KEY (id);

ALTER TABLE Only "group_" ADD CONSTRAINT "group_primary_key" PRIMARY KEY (id);

ALTER TABLE ONLY "user_group" ADD CONSTRAINT "enableUserGroupPK" PRIMARY KEY (uid, gid);

ALTER TABLE ONLY "user_group" ADD CONSTRAINT "FKusergroupUser" FOREIGN KEY (uid) REFERENCES user_(id) ON DELETE CASCADE;

ALTER TABLE ONLY "user_group" ADD CONSTRAINT "FKusergroupGroup" FOREIGN KEY (gid) REFERENCES group_(id) ON DELETE CASCADE;
-- schema_end
\copy "user_"(id) FROM 'train_data/nm_tables/additional_attributes/group_1/user_.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy "group_"(id) FROM 'train_data/nm_tables/additional_attributes/group_1/group_.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy "user_group"(uid, gid, registration_date, expiration_duration, access_rights) FROM 'train_data/nm_tables/additional_attributes/group_1/user_group.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');