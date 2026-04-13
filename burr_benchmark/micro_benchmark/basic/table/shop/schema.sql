\c postgres
\set database_name basic__table__shop
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE shop (
    id int
);

ALTER TABLE Only shop
    ADD CONSTRAINT shop_primary_key PRIMARY KEY (id);
-- schema_end
\copy shop(id) FROM 'train_data/basic/table/shop/shop.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
