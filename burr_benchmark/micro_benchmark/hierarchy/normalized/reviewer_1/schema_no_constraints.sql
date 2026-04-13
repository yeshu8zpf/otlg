
DROP SCHEMA IF EXISTS reviewer_1_normalized_no_constraints CASCADE;
CREATE SCHEMA reviewer_1_normalized_no_constraints;
SET search_path = reviewer_1_normalized_no_constraints, pg_catalog;

SET default_tablespace = '';
SET default_with_oids = false;

CREATE TABLE person (
    pid SERIAL,
    name VARCHAR(50),
)

CREATE TABLE author (
    pid SERIAL,
    email VARCHAR(50),
)

CREATE TABLE reviewer (
    pid SERIAL,
    area VARCHAR(50),
)