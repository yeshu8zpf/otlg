\c postgres
\set database_name nm_tables__general__customer_preference
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
-- schema_start
CREATE TABLE customer (
    id int,
    name varchar(50)
);

CREATE TABLE preference (
    id int,
    name varchar(50)
);

CREATE TABLE customer_preference (
    customer_id int,
    preference_id int
);

ALTER TABLE ONLY customer
    ADD CONSTRAINT customer_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY preference
    ADD CONSTRAINT preference_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY customer_preference
    ADD CONSTRAINT customer_preference_primary_key PRIMARY KEY (customer_id, preference_id);

ALTER TABLE ONLY customer_preference
    ADD CONSTRAINT "FKcustomerpreferencecustomer" FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE;

ALTER TABLE ONLY customer_preference
    ADD CONSTRAINT "FKcustomerpreferencepreference" FOREIGN KEY (preference_id) REFERENCES preference(id) ON DELETE CASCADE;
-- schema_end
\copy customer(id, name) FROM 'train_data/nm_tables/general/customer_preference/customer.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy preference(id, name) FROM 'train_data/nm_tables/general/customer_preference/preference.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy customer_preference(customer_id, preference_id) FROM 'train_data/nm_tables/general/customer_preference/customer_preference.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

