\c postgres
\set database_name nm_tables__general__product_feature
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
-- schema_start
CREATE TABLE product (
    id int,
    name varchar(50)
);

CREATE TABLE feature (
    id int,
    name varchar(50)
);

CREATE TABLE product_feature (
    product_id int,
    feature_id int
);

ALTER TABLE ONLY product
    ADD CONSTRAINT product_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY feature
    ADD CONSTRAINT feature_primary_key PRIMARY KEY (id);

ALTER TABLE ONLY product_feature
    ADD CONSTRAINT product_feature_primary_key PRIMARY KEY (product_id, feature_id);

ALTER TABLE ONLY product_feature
    ADD CONSTRAINT "FKproductFeatureProduct" FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE;

ALTER TABLE ONLY product_feature
    ADD CONSTRAINT "FKproductFeatureFeature" FOREIGN KEY (feature_id) REFERENCES feature(id) ON DELETE CASCADE;
-- schema_end
\copy product(id, name) FROM 'train_data/nm_tables/general/product_feature/product.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy feature(id, name) FROM 'train_data/nm_tables/general/product_feature/feature.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy product_feature(product_id, feature_id) FROM 'train_data/nm_tables/general/product_feature/product_feature.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

