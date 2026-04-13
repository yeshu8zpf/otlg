\c postgres
\set database_name complex__scenario_c__beverage_supplier
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;


SET default_tablespace = '';
SET default_with_oids = false;
-- schema_start
CREATE TABLE beverage (
    id int,
    name varchar(50),
    contains_caffeine boolean,
    contains_sugar boolean,
    contains_alcohol boolean,
    contains_dairy boolean,
    contains_gluten boolean,
    contains_nuts boolean
);

CREATE TABLE supplier (
    id int,
    name varchar(50),
    address varchar(100)
);

CREATE TABLE beverage_supplier (
    beverage_id int,
    supplier_id int
);

ALTER TABLE ONLY beverage ADD CONSTRAINT "beverage_primary_key" PRIMARY KEY (id);
ALTER TABLE ONLY supplier ADD CONSTRAINT "supplier_primary_key" PRIMARY KEY (id);
ALTER TABLE ONLY beverage_supplier ADD CONSTRAINT "beverage_supplier_primary_key" PRIMARY KEY (beverage_id, supplier_id);

ALTER TABLE ONLY beverage_supplier ADD CONSTRAINT FKbeverageSupplierBeverage FOREIGN KEY (beverage_id) REFERENCES beverage(id) ON DELETE CASCADE;
ALTER TABLE ONLY beverage_supplier ADD CONSTRAINT FKbeverageSupplierSupplier FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE CASCADE;

\copy beverage(id, name, contains_caffeine, contains_sugar, contains_alcohol, contains_dairy, contains_gluten, contains_nuts) FROM 'train_data/complex/scenario_c/beverage_supplier/beverage.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy supplier(id, name, address) FROM 'train_data/complex/scenario_c/beverage_supplier/supplier.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy beverage_supplier(beverage_id, supplier_id) FROM 'train_data/complex/scenario_c/beverage_supplier/beverage_supplier.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
