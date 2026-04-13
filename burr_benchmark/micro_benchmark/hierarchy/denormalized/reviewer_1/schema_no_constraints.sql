DROP DATABASE IF EXISTS reviewer_1_hierarchy_denormalized_no_constraints;
CREATE DATABASE reviewer_1_hierarchy_denormalized_no_constraints;
\c reviewer_1_hierarchy_denormalized_no_constraints;


SET default_tablespace = '';
SET default_with_oids = false;

CREATE TABLE person (
    pid SERIAL,
    name VARCHAR(50),
    email VARCHAR(50),
    area VARCHAR(50),
    type VARCHAR(50),
)

