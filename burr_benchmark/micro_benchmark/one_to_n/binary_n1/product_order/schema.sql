\c postgres
\set database_name one_to_n__binary_n1__product_order
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;

SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE client (
    id INT,
    name VARCHAR(50),
    address VARCHAR(100)
);

CREATE TABLE product (
    id INT,
    name VARCHAR(50),
    client_id INT,
    price INT
);

ALTER TABLE client ADD CONSTRAINT client_primary_key PRIMARY KEY (id);
ALTER TABLE product ADD CONSTRAINT order_primary_key PRIMARY KEY (id);

ALTER TABLE product ADD CONSTRAINT FKorderClient FOREIGN KEY (client_id) REFERENCES client(id) ON DELETE CASCADE;
-- schema_end
\copy client(id, name, address) FROM 'train_data/one_to_n/binary_n1/product_order/client.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy product(id, name, client_id, price) FROM 'train_data/one_to_n/binary_n1/product_order/product.csv' WITH (FORMAT csv, HEADER true, DELIMITER ','); 

