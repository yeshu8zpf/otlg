\c postgres
\set database_name complex__scenario_c__component_supplier
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
-- schema_start
CREATE TABLE component(
    id int,
    name varchar(50)
);

CREATE TABLE supplier(
    id int,
    name varchar(50),
    address varchar(100)
);

CREATE TABLE component_supplier(
    component_id int,
    supplier_id int,
    relevant_for_automotive_industry boolean,
    relevant_for_electronics_industry boolean,
    relevant_for_food_industry boolean,
    relevant_for_construction_industry boolean,
    relevant_for_medical_industry boolean,
    relevant_for_aerospace_industry boolean
);

ALTER TABLE ONLY component ADD CONSTRAINT "component_primary_key" PRIMARY KEY (id);
ALTER TABLE ONLY supplier ADD CONSTRAINT "supplier_primary_key" PRIMARY KEY (id);
ALTER TABLE ONLY component_supplier ADD CONSTRAINT "component_supplier_primary_key" PRIMARY KEY (component_id, supplier_id);

ALTER TABLE ONLY component_supplier ADD CONSTRAINT FKcomponentSupplierComponent FOREIGN KEY (component_id) REFERENCES component(id) ON DELETE CASCADE;
ALTER TABLE ONLY component_supplier ADD CONSTRAINT FKcomponentSupplierSupplier FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE CASCADE;
-- schema_end
\copy component(id, name) FROM 'train_data/complex/scenario_c/component_supplier/component.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy supplier(id, name, address) FROM 'train_data/complex/scenario_c/component_supplier/supplier.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
\copy component_supplier(component_id, supplier_id, relevant_for_automotive_industry, relevant_for_electronics_industry, relevant_for_food_industry, relevant_for_construction_industry, relevant_for_medical_industry, relevant_for_aerospace_industry) FROM 'train_data/complex/scenario_c/component_supplier/component_supplier.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
