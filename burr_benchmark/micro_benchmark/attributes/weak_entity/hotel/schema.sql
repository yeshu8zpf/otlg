\c postgres
\set database_name attributes__weak_entity__hotel
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE hotel (
    id INT,
    name VARCHAR(50)
);

CREATE TABLE room (
    bed_number INT,
    room_number INT,
    hotel_id INT
);

ALTER TABLE hotel ADD CONSTRAINT hotel_primary_key PRIMARY KEY (id);
ALTER TABLE room ADD CONSTRAINT room_primary_key PRIMARY KEY (room_number, hotel_id);

ALTER TABLE room ADD CONSTRAINT FKroomHotel FOREIGN KEY (hotel_id) REFERENCES hotel(id) ON DELETE CASCADE;
-- schema_end
-- generated with gpt-o4-mini-high
\copy hotel(id, name) FROM 'train_data/attributes/weak_entity/hotel/hotels.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy room(bed_number, room_number, hotel_id) FROM 'train_data/attributes/weak_entity/hotel/rooms.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

