\c postgres
\set database_name one_to_n__binary_n1_with_extra_table__extra_attribute
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
    price INT
);

CREATE TABLE orders (
    client_id INT,
    product_id INT,
    date DATE
);

ALTER TABLE client ADD CONSTRAINT client_primary_key PRIMARY KEY (id);
ALTER TABLE product ADD CONSTRAINT product_primary_key PRIMARY KEY (id);
ALTER TABLE orders ADD CONSTRAINT orders_primary_key PRIMARY KEY (client_id, product_id);

ALTER TABLE orders ADD CONSTRAINT FKclient_orderClient FOREIGN KEY (client_id) REFERENCES client(id) ON DELETE CASCADE;
ALTER TABLE orders ADD CONSTRAINT FKclient_orderOrder FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE;
-- schema_end
\copy client(id, name, address) FROM 'train_data/one_to_n/binary_n1_with_extra_table/extra_attribute/client.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy product(id, name, price) FROM 'train_data/one_to_n/binary_n1_with_extra_table/extra_attribute/product.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy orders(client_id, product_id, date) FROM 'train_data/one_to_n/binary_n1_with_extra_table/extra_attribute/orders.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
