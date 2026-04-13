\c postgres
\set database_name complex__scenario_d__hotel
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE hotel (
    id INT,
    name VARCHAR(50),
    address VARCHAR(500)
);

CREATE TABLE room (
    bed_number INT,
    room_number INT,
    location VARCHAR(100),
    hotel_id INT
);

ALTER TABLE hotel ADD CONSTRAINT hotel_primary_key PRIMARY KEY (id);
ALTER TABLE room ADD CONSTRAINT room_primary_key PRIMARY KEY (room_number, hotel_id);

ALTER TABLE room ADD CONSTRAINT FKroomHotel FOREIGN KEY (hotel_id) REFERENCES hotel(id) ON DELETE CASCADE;
-- schema_end
-- generated with gpt-o4-mini-high
\copy hotel(id, name, address) FROM 'train_data/complex/scenario_d/hotel/hotels.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy room(bed_number, room_number, location, hotel_id) FROM 'train_data/complex/scenario_d/hotel/rooms.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

