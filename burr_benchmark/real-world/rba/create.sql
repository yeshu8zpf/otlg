--
-- PostgreSQL database dump
--

-- Dumped from database version 14.11 (Homebrew)
-- Dumped by pg_dump version 14.11 (Homebrew)

\c postgres
\set database_name real_world__rba__original
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
SET default_tablespace = '';
SET default_with_oids = false;


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bar; Type: TABLE; Schema: public; Owner: lukaslaskowski
--

CREATE TABLE public.bar (
    enterprise_domain character varying,
    business_activity character varying,
    business_activity_code character varying,
    apqc_reference character varying,
    business_activity_description character varying,
    annotation character varying
);




--
-- Name: bc_to_sc; Type: TABLE; Schema: public; Owner: lukaslaskowski
--

CREATE TABLE public.bc_to_sc (
    object_id_sc character varying,
    master_id_bc character varying,
    solution_capability character varying,
    reference_architecture_hybrid character varying,
    reference_architecture_cloud character varying,
    type character varying,
    ppms_product_id character varying,
    line_item_type character varying,
    reference_architecture_hybrid_1 character varying,
    reference_architecture_cloud_1 character varying,
    ppms_product_name character varying,
    deployment_type character varying,
    platform character varying,
    alternative_hybrid character varying,
    alternative_cloud character varying
);




--
-- Name: bcm; Type: TABLE; Schema: public; Owner: lukaslaskowski
--

CREATE TABLE public.bcm (
    hierarchy_id character varying,
    enterprise_domain character varying,
    enterprise_domain_seq_id character varying,
    master_id_domain character varying,
    business_domain character varying,
    object_type character varying,
    business_domain_seq_id character varying,
    master_id_bd character varying,
    business_area character varying,
    object_type_2 character varying,
    barea_seq_id character varying,
    master_id_barea character varying,
    business_capability character varying,
    object_type_3 character varying,
    master_id_bc character varying,
    business_capability_description character varying,
    bc_relevant_for_cross_industry character varying,
    bc_relevant_for_retail_industry character varying,
    bc_relevant_for_autmotive_industry character varying,
    bc_relevant_for_professional_services_industry character varying,
    bc_relevant_for_industrial_machinery_and_components character varying,
    bc_relevant_for_oil_and_gas character varying,
    bc_relevant_for_utilities character varying,
    bc_seq_id character varying
);




--
-- Name: bpm; Type: TABLE; Schema: public; Owner: lukaslaskowski
--

CREATE TABLE public.bpm (
    business_process_id character varying,
    based_on character varying,
    business_process character varying,
    bp_relevant_for_cross_industry character varying,
    bp_relevant_for_retail_industry character varying,
    bp_relevant_for_automotive character varying,
    bp_relevant_for_professional_services character varying,
    bp_relevant_for_industrial_machinery_and_components character varying,
    bp_relevant_for_oil_and_gas character varying,
    bp_relevant_for_utilities character varying,
    business_process_type character varying,
    type character varying,
    enterprise_domain character varying,
    bp_description character varying,
    business_process_id_1 character varying,
    based_on_1 character varying,
    business_process_1 character varying,
    business_process_type_1 character varying,
    type_1 character varying,
    enterprise_domain_1 character varying,
    business_process_sequence_1 character varying,
    business_process_description_1 character varying,
    business_process_id_2 character varying,
    based_on_2 character varying,
    business_process_2 character varying,
    business_process_type_2 character varying,
    type_2 character varying,
    enterprise_domain_2 character varying,
    business_process_sequence_2 character varying,
    object_id_business_activity character varying,
    based_on_3 character varying,
    reference_to_bar_id character varying,
    business_activity character varying,
    ba_sequence character varying,
    description character varying,
    apqc_reference character varying,
    object_id_fp character varying,
    forward_pointer character varying,
    fp_object_type character varying,
    master_id_bc character varying,
    business_capability character varying,
    bc_type character varying,
    business_capability_description character varying
);




--
-- Name: ind; Type: TABLE; Schema: public; Owner: lukaslaskowski
--

CREATE TABLE public.ind (
    industry_id character varying,
    industry_name character varying
);




--
-- Name: scm; Type: TABLE; Schema: public; Owner: lukaslaskowski
--

CREATE TABLE public.scm (
    id character varying,
    hierarchy_id character varying,
    enterprise_domain character varying,
    master_id_domain character varying,
    business_domain character varying,
    business_domain_seq_id character varying,
    master_id_bd character varying,
    business_area character varying,
    barea_seq_id character varying,
    master_id_barea character varying,
    business_capability character varying,
    master_id_bc character varying,
    business_capability_description character varying,
    bc_relevant_for_cross_industry character varying,
    bc_relevant_for_retail_industry character varying,
    bc_relevant_for_autmotive_industry character varying,
    bc_relevant_for_professional_services_industry character varying,
    bc_relevant_for_industrial_machinery_and_components character varying,
    bc_relevant_for_oil_and_gas character varying,
    bc_relevant_for_utilities character varying,
    object_id_sc character varying,
    solution_capability character varying,
    solution_capability_reference_architecture_hybrid character varying,
    solution_capability_reference_architecture_cloud character varying,
    type character varying,
    ppms_product_id character varying,
    line_item_type character varying,
    ppms_product_name character varying,
    solution_component_reference_architecture_hybrid character varying,
    solution_component_reference_architecture_cloud character varying,
    deployment_type character varying,
    platform character varying,
    "unnamed:_32" character varying
);




--
-- Name: spm; Type: TABLE; Schema: public; Owner: lukaslaskowski
--

CREATE TABLE public.spm (
    solution_process_id character varying,
    based_on character varying,
    business_process_id character varying,
    solution_process character varying,
    sp_relevant_for_cross_industry character varying,
    sp_relevant_for_retail_industry character varying,
    sp_relevant_for_automotive character varying,
    sp_relevant_for_professional_services character varying,
    sp_relevant_for_industrial_machinery_and_components character varying,
    sp_relevant_for_oil_and_gas character varying,
    sp_relevant_for_utilities character varying,
    type character varying,
    enterprise_domain character varying,
    sp_description character varying,
    reference_architecture_type character varying,
    solution_process_id_1 character varying,
    based_on_1 character varying,
    business_process_id_1 character varying,
    solution_process_1 character varying,
    type_1 character varying,
    solution_process_sequence_1 character varying,
    enterprise_domain_1 character varying,
    solution_process_description_1 character varying,
    solution_process_id_2 character varying,
    based_on_2 character varying,
    business_process_id_2 character varying,
    solution_process_2 character varying,
    type_2 character varying,
    solution_process_sequence_2 character varying,
    enterprise_domain_2 character varying,
    object_id_business_activity_in_solution_process character varying,
    ba_in_sp_reference_to_rba character varying,
    business_activity_in_solution_process character varying,
    ba_in_sp_sequence character varying,
    description character varying,
    apqc_reference character varying,
    object_id_fp character varying,
    forward_pointer character varying,
    fp_object_type character varying,
    object_id_sc character varying,
    solution_capability character varying,
    ppms_product_id character varying,
    line_item_type character varying,
    ppms_product_name character varying,
    deployment_type character varying,
    platform character varying
);