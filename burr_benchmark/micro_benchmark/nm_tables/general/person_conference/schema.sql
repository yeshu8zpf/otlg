\c postgres
\set database_name nm_tables__general__person_conference
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE conference (
    id INT
);

CREATE TABLE person (
    id INT
);

CREATE TABLE enable_virtual_meeting (
    pid INT,
    cid INT
);

ALTER TABLE Only conference
    ADD CONSTRAINT conference_primary_key PRIMARY KEY (id);

ALTER TABLE Only person
    ADD CONSTRAINT person_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY enable_virtual_meeting
    ADD CONSTRAINT "enableVirtualMeetingPK" PRIMARY KEY (pid, cid);

ALTER TABLE ONLY enable_virtual_meeting
    ADD CONSTRAINT "FKenableVirtualMeetingPers" FOREIGN KEY (pid) REFERENCES person(id) ON DELETE CASCADE;

ALTER TABLE ONLY enable_virtual_meeting
    ADD CONSTRAINT "FKenableVirtualMeetingCon" FOREIGN KEY (cid) REFERENCES conference(id) ON DELETE CASCADE;
-- schema_end
\copy conference(id) FROM 'train_data/nm_tables/general/person_conference/conference.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy person(id) FROM 'train_data/nm_tables/general/person_conference/person.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy enable_virtual_meeting(pid, cid) FROM 'train_data/nm_tables/general/person_conference/enable_virtual_meeting.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');