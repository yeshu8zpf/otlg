You are given a relational database scenario.

## Scenario path
/root/ontology/burr_benchmark/real-world/npd_factpages

## Compact schema SQL
SET session_replication_role = replica;

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

--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;

--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';

--
--

CREATE TABLE public.apaareagross (
    apamap_no bigint NOT NULL,
    apaareageometryewkt text NOT NULL,
    apaareageometry_kml_wgs84 text NOT NULL,
    apaareagross_id bigint NOT NULL
);

--
--

CREATE SEQUENCE public.apaareagross_apaareagross_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.apaareagross_apaareagross_id_seq OWNED BY public.apaareagross.apaareagross_id;

--
--

CREATE TABLE public.apaareanet (
    blkid bigint NOT NULL,
    blklabel character varying(40) NOT NULL,
    qdrname character varying(40) NOT NULL,
    blkname character varying(40) NOT NULL,
    prvname character varying(2) NOT NULL,
    apaareatype character varying(40),
    urlnpd character varying(200) NOT NULL,
    apaareanet_id bigint NOT NULL,
    apaareanetgeometrywkt public.geometry(Polygon,4326)
);

--
--

CREATE SEQUENCE public.apaareanet_apaareanet_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.apaareanet_apaareanet_id_seq OWNED BY public.apaareanet.apaareanet_id;

--
--

CREATE TABLE public.baaarea (
    baanpdidbsnsarrarea bigint NOT NULL,
    baanpdidbsnsarrareapoly bigint NOT NULL,
    baaname character varying(40) NOT NULL,
    baakind character varying(40) NOT NULL,
    baaareapolydatevalidfrom date NOT NULL,
    baaareapolydatevalidto date,
    baaareapolyactive character varying(40) NOT NULL,
    baadateapproved date NOT NULL,
    baadatevalidfrom date NOT NULL,
    baadatevalidto date,
    baaactive character varying(20) NOT NULL,
    baafactpageurl character varying(200) NOT NULL,
    baafactmapurl character varying(200),
    baaareageometrywkt text NOT NULL
);

--
--

COMMENT ON COLUMN public.baaarea.baanpdidbsnsarrarea IS 'NPDID Bsns. Arr. Area';

--
--

COMMENT ON COLUMN public.baaarea.baaname IS 'Name';

--
--

COMMENT ON COLUMN public.baaarea.baakind IS 'Kind';

--
--

COMMENT ON COLUMN public.baaarea.baaareapolydatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.baaarea.baaareapolydatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.baaarea.baadateapproved IS 'Date approved';

--
--

COMMENT ON COLUMN public.baaarea.baadatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.baaarea.baadatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.baaarea.baaactive IS 'Active';

--
--

COMMENT ON COLUMN public.baaarea.baafactpageurl IS 'Fact page';

--
--

COMMENT ON COLUMN public.baaarea.baafactmapurl IS 'Fact map';

--
--

CREATE TABLE public.bsns_arr_area (
    baaname character varying(40) NOT NULL,
    baakind character varying(40) NOT NULL,
    baadateapproved date NOT NULL,
    baadatevalidfrom date NOT NULL,
    baadatevalidto date,
    baafactpageurl character varying(200) NOT NULL,
    baafactmapurl character varying(200),
    baanpdidbsnsarrarea bigint NOT NULL,
    baadateupdated date,
    baadateupdatedmax date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.bsns_arr_area.baaname IS 'Name';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baakind IS 'Kind';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baadateapproved IS 'Date approved';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baadatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baadatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baafactpageurl IS 'Fact page';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baafactmapurl IS 'Fact map';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baanpdidbsnsarrarea IS 'NPDID Bsns. Arr. Area';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baadateupdated IS 'Date main level updated';

--
--

COMMENT ON COLUMN public.bsns_arr_area.baadateupdatedmax IS 'Date all updated';

--
--

CREATE TABLE public.bsns_arr_area_area_poly_hst (
    baaname character varying(40) NOT NULL,
    baaareapolydatevalidfrom date NOT NULL,
    baaareapolydatevalidto date NOT NULL,
    baaareapolynationcode2 character varying(2) NOT NULL,
    baaareapolyblockname character varying(40) DEFAULT ''::character varying NOT NULL,
    baaareapolyno bigint NOT NULL,
    baaareapolyarea numeric(13,6) NOT NULL,
    baanpdidbsnsarrarea bigint NOT NULL,
    baaareapolydateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baaname IS 'Name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baaareapolydatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baaareapolydatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baaareapolynationcode2 IS 'Nation code';

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baaareapolyblockname IS 'Block name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baaareapolyarea IS 'Polygon area [km2]';

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baanpdidbsnsarrarea IS 'NPDID Bsns. Arr. Area';

--
--

COMMENT ON COLUMN public.bsns_arr_area_area_poly_hst.baaareapolydateupdated IS 'Date updated';

--
--

CREATE TABLE public.bsns_arr_area_licensee_hst (
    baaname character varying(40) NOT NULL,
    baalicenseedatevalidfrom date NOT NULL,
    baalicenseedatevalidto date NOT NULL,
    cmplongname character varying(200) NOT NULL,
    baalicenseeinterest numeric(13,6) NOT NULL,
    baalicenseesdfi numeric(13,6),
    baanpdidbsnsarrarea bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    baalicenseedateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.baaname IS 'Name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.baalicenseedatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.baalicenseedatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.baalicenseeinterest IS 'Interest [%]';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.baalicenseesdfi IS 'SDFI [%]';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.baanpdidbsnsarrarea IS 'NPDID Bsns. Arr. Area';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.bsns_arr_area_licensee_hst.baalicenseedateupdated IS 'Date updated';

--
--

CREATE TABLE public.bsns_arr_area_operator (
    baaname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    baanpdidbsnsarrarea bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    baaoperatordateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.bsns_arr_area_operator.baaname IS 'Name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_operator.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_operator.baanpdidbsnsarrarea IS 'NPDID Bsns. Arr. Area';

--
--

COMMENT ON COLUMN public.bsns_arr_area_operator.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.bsns_arr_area_operator.baaoperatordateupdated IS 'Date updated';

--
--

CREATE TABLE public.bsns_arr_area_transfer_hst (
    baaname character varying(40) NOT NULL,
    baatransferdatevalidfrom date NOT NULL,
    baatransferdirection character varying(4) NOT NULL,
    baatransferkind character varying(40),
    cmplongname character varying(200) NOT NULL,
    baatransferredinterest numeric(13,6) NOT NULL,
    baatransfersdfi numeric(13,6),
    baanpdidbsnsarrarea bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    baatransferdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baaname IS 'Name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baatransferdatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baatransferdirection IS 'Transfer direction';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baatransferkind IS 'Transfer kind';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baatransferredinterest IS 'Transferred interest [%]';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baatransfersdfi IS 'SDFI [%]';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baanpdidbsnsarrarea IS 'NPDID Bsns. Arr. Area';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.bsns_arr_area_transfer_hst.baatransferdateupdated IS 'Date updated';

--
--

CREATE TABLE public.company (
    cmplongname character varying(200) NOT NULL,
    cmporgnumberbrreg character varying(100),
    cmpgroup character varying(100),
    cmpshortname character varying(40) NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    cmplicenceopercurrent character varying(1) NOT NULL,
    cmplicenceoperformer character varying(1) NOT NULL,
    cmplicencelicenseecurrent character varying(1) NOT NULL,
    cmplicencelicenseeformer character varying(1) NOT NULL,
    datesyncnpd date NOT NULL,
    UNIQUE (cmplongname),
    UNIQUE (cmpshortname)
);

--
--

COMMENT ON COLUMN public.company.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.company.cmporgnumberbrreg IS 'Organisation number';

--
--

COMMENT ON COLUMN public.company.cmpgroup IS 'Group';

--
--

COMMENT ON COLUMN public.company.cmpshortname IS 'Company shortname';

--
--

COMMENT ON COLUMN public.company.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.company.cmplicenceopercurrent IS 'Currently licence operator';

--
--

COMMENT ON COLUMN public.company.cmplicenceoperformer IS 'Former licence operator';

--
--

COMMENT ON COLUMN public.company.cmplicencelicenseecurrent IS 'Currently licence licensee';

--
--

COMMENT ON COLUMN public.company.cmplicencelicenseeformer IS 'Former licence licensee';

--
--

CREATE TABLE public.company_reserves (
    cmplongname character varying(200) NOT NULL,
    fldname character varying(40) NOT NULL,
    cmprecoverableoil numeric(13,6) NOT NULL,
    cmprecoverablegas numeric(13,6) NOT NULL,
    cmprecoverablengl numeric(13,6) NOT NULL,
    cmprecoverablecondensate numeric(13,6) NOT NULL,
    cmprecoverableoe numeric(13,6) NOT NULL,
    cmpremainingoil numeric(13,6) NOT NULL,
    cmpremaininggas numeric(13,6) NOT NULL,
    cmpremainingngl numeric(13,6) NOT NULL,
    cmpremainingcondensate numeric(13,6) NOT NULL,
    cmpremainingoe numeric(13,6) NOT NULL,
    cmpdateoffresestdisplay date NOT NULL,
    cmpshare numeric(13,6) NOT NULL,
    fldnpdidfield bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.company_reserves.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.company_reserves.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.company_reserves.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.company_reserves.cmpnpdidcompany IS 'NPDID company';

--
--

CREATE TABLE public.discovery (
    dscname character varying(40) NOT NULL,
    cmplongname character varying(200),
    dsccurrentactivitystatus character varying(40) NOT NULL,
    dschctype character varying(40),
    wlbname character varying(60),
    nmaname character varying(40),
    fldname character varying(40),
    dscdatefrominclinfield date,
    dscdiscoveryyear bigint NOT NULL,
    dscresinclindiscoveryname character varying(40),
    dscownerkind character varying(40),
    dscownername character varying(40),
    dscnpdiddiscovery bigint NOT NULL,
    fldnpdidfield bigint,
    wlbnpdidwellbore bigint NOT NULL,
    dscfactpageurl character varying(200) NOT NULL,
    dscfactmapurl character varying(200) NOT NULL,
    dscdateupdated date,
    dscdateupdatedmax date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.discovery.dscname IS 'Discovery name';

--
--

COMMENT ON COLUMN public.discovery.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.discovery.dsccurrentactivitystatus IS 'Current activity status';

--
--

COMMENT ON COLUMN public.discovery.dschctype IS 'HC type';

--
--

COMMENT ON COLUMN public.discovery.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.discovery.nmaname IS 'Main NCS area';

--
--

COMMENT ON COLUMN public.discovery.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.discovery.dscdatefrominclinfield IS 'Included in field from date';

--
--

COMMENT ON COLUMN public.discovery.dscdiscoveryyear IS 'Discovery year';

--
--

COMMENT ON COLUMN public.discovery.dscresinclindiscoveryname IS 'Resources incl. in';

--
--

COMMENT ON COLUMN public.discovery.dscownerkind IS 'Owner kind';

--
--

COMMENT ON COLUMN public.discovery.dscownername IS 'Owner name';

--
--

COMMENT ON COLUMN public.discovery.dscnpdiddiscovery IS 'NPDID discovery';

--
--

COMMENT ON COLUMN public.discovery.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.discovery.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.discovery.dscfactpageurl IS 'Fact page';

--
--

COMMENT ON COLUMN public.discovery.dscfactmapurl IS 'Fact map';

--
--

COMMENT ON COLUMN public.discovery.dscdateupdated IS 'Date main level updated';

--
--

COMMENT ON COLUMN public.discovery.dscdateupdatedmax IS 'Date all updated';

--
--

CREATE TABLE public.discovery_reserves (
    dscname character varying(40) NOT NULL,
    dscreservesrc character varying(40) NOT NULL,
    dscrecoverableoil numeric(13,6) NOT NULL,
    dscrecoverablegas numeric(13,6) NOT NULL,
    dscrecoverablengl numeric(13,6) NOT NULL,
    dscrecoverablecondensate numeric(13,6) NOT NULL,
    dscdateoffresestdisplay date NOT NULL,
    dscnpdiddiscovery bigint NOT NULL,
    dscreservesdateupdated date NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.discovery_reserves.dscname IS 'Discovery name';

--
--

COMMENT ON COLUMN public.discovery_reserves.dscreservesrc IS 'Resource class';

--
--

COMMENT ON COLUMN public.discovery_reserves.dscrecoverableoil IS 'Rec. oil [mill Sm3]';

--
--

COMMENT ON COLUMN public.discovery_reserves.dscrecoverablegas IS 'Rec. gas [bill Sm3]';

--
--

COMMENT ON COLUMN public.discovery_reserves.dscrecoverablengl IS 'Rec. NGL [mill tonn]';

--
--

COMMENT ON COLUMN public.discovery_reserves.dscrecoverablecondensate IS 'Rec. cond. [mill Sm3]';

--
--

COMMENT ON COLUMN public.discovery_reserves.dscdateoffresestdisplay IS 'Resource updated date';

--
--

COMMENT ON COLUMN public.discovery_reserves.dscnpdiddiscovery IS 'NPDID discovery';

--
--

CREATE TABLE public.dscarea (
    fldnpdidfield bigint,
    fldname character varying(40),
    dscnpdiddiscovery bigint NOT NULL,
    dscname character varying(40) NOT NULL,
    dscresinclindiscoveryname character varying(40),
    dscnpdidresinclindiscovery bigint,
    dscincludedinfld character varying(3) NOT NULL,
    dschctype character varying(40) NOT NULL,
    fldhctype character varying(40),
    dsccurrentactivitystatus character varying(40) NOT NULL,
    fldcurrentactivitystatus character varying(40),
    flddsclabel character varying(40) NOT NULL,
    dscfacturl character varying(200) NOT NULL,
    fldfacturl character varying(200),
    flddscareageometrywkt_ed50 text NOT NULL
);

--
--

COMMENT ON COLUMN public.dscarea.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.dscarea.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.dscarea.dscnpdiddiscovery IS 'NPDID discovery';

--
--

COMMENT ON COLUMN public.dscarea.dscname IS 'Discovery name';

--
--

COMMENT ON COLUMN public.dscarea.dscresinclindiscoveryname IS 'Resources incl. in';

--
--

COMMENT ON COLUMN public.dscarea.dschctype IS 'HC type';

--
--

COMMENT ON COLUMN public.dscarea.dsccurrentactivitystatus IS 'Current activity status';

--
--

CREATE TABLE public.facility_fixed (
    fclname character varying(40) NOT NULL,
    fclphase character varying(40) NOT NULL,
    fclsurface character varying(1) NOT NULL,
    fclcurrentoperatorname character varying(100),
    fclkind character varying(40) NOT NULL,
    fclbelongstoname character varying(41),
    fclbelongstokind character varying(40),
    fclbelongstos bigint,
    fclstartupdate date,
    fclgeodeticdatum character varying(10),
    fclnsdeg bigint,
    fclnsmin bigint,
    fclnssec numeric(13,6),
    fclnscode character varying(1) NOT NULL,
    fclewdeg bigint,
    fclewmin bigint,
    fclewsec numeric(13,6),
    fclewcode character varying(1) NOT NULL,
    fclwaterdepth numeric(13,6) NOT NULL,
    fclfunctions character varying(400),
    fcldesignlifetime bigint,
    fclfactpageurl character varying(200) NOT NULL,
    fclfactmapurl character varying(200) NOT NULL,
    fclnpdidfacility bigint NOT NULL,
    fcldateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.facility_fixed.fclname IS 'Name';

--
--

COMMENT ON COLUMN public.facility_fixed.fclphase IS 'Phase';

--
--

COMMENT ON COLUMN public.facility_fixed.fclsurface IS 'Surface facility';

--
--

COMMENT ON COLUMN public.facility_fixed.fclcurrentoperatorname IS 'Current operator';

--
--

COMMENT ON COLUMN public.facility_fixed.fclkind IS 'Kind';

--
--

COMMENT ON COLUMN public.facility_fixed.fclbelongstoname IS 'Belongs to, name';

--
--

COMMENT ON COLUMN public.facility_fixed.fclbelongstokind IS 'Belongs to, kind';

--
--

COMMENT ON COLUMN public.facility_fixed.fclstartupdate IS 'Startup date';

--
--

COMMENT ON COLUMN public.facility_fixed.fclgeodeticdatum IS 'Geodetic datum';

--
--

COMMENT ON COLUMN public.facility_fixed.fclnsdeg IS 'NS degrees';

--
--

COMMENT ON COLUMN public.facility_fixed.fclnsmin IS 'NS minutes';

--
--

COMMENT ON COLUMN public.facility_fixed.fclnssec IS 'NS seconds';

--
--

COMMENT ON COLUMN public.facility_fixed.fclnscode IS 'NS code';

--
--

COMMENT ON COLUMN public.facility_fixed.fclewdeg IS 'EW degrees';

--
--

COMMENT ON COLUMN public.facility_fixed.fclewmin IS 'EW minutes';

--
--

COMMENT ON COLUMN public.facility_fixed.fclewsec IS 'EW seconds';

--
--

COMMENT ON COLUMN public.facility_fixed.fclewcode IS 'EW code';

--
--

COMMENT ON COLUMN public.facility_fixed.fclwaterdepth IS 'Water depth [m]';

--
--

COMMENT ON COLUMN public.facility_fixed.fclfunctions IS 'Functions';

--
--

COMMENT ON COLUMN public.facility_fixed.fcldesignlifetime IS 'Design lifetime [year]';

--
--

COMMENT ON COLUMN public.facility_fixed.fclfactpageurl IS 'Fact page';

--
--

COMMENT ON COLUMN public.facility_fixed.fclfactmapurl IS 'Fact map';

--
--

COMMENT ON COLUMN public.facility_fixed.fclnpdidfacility IS 'NPDID facility';

--
--

COMMENT ON COLUMN public.facility_fixed.fcldateupdated IS 'Date updated';

--
--

CREATE TABLE public.facility_moveable (
    fclname character varying(40) NOT NULL,
    fclcurrentrespcompanyname character varying(100),
    fclkind character varying(40) NOT NULL,
    fclfunctions character varying(400),
    fclnationname character varying(40) NOT NULL,
    fclfactpageurl character varying(200) NOT NULL,
    fclnpdidfacility bigint NOT NULL,
    fclnpdidcurrentrespcompany bigint,
    fcldateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.facility_moveable.fclname IS 'Name';

--
--

COMMENT ON COLUMN public.facility_moveable.fclcurrentrespcompanyname IS 'Current responsible company';

--
--

COMMENT ON COLUMN public.facility_moveable.fclkind IS 'Kind';

--
--

COMMENT ON COLUMN public.facility_moveable.fclfunctions IS 'Functions';

--
--

COMMENT ON COLUMN public.facility_moveable.fclnationname IS 'Nation';

--
--

COMMENT ON COLUMN public.facility_moveable.fclfactpageurl IS 'Fact page';

--
--

COMMENT ON COLUMN public.facility_moveable.fclnpdidfacility IS 'NPDID facility';

--
--

COMMENT ON COLUMN public.facility_moveable.fclnpdidcurrentrespcompany IS 'NPDID responsible company';

--
--

COMMENT ON COLUMN public.facility_moveable.fcldateupdated IS 'Date updated';

--
--

CREATE TABLE public.fclpoint (
    fclnpdidfacility bigint NOT NULL,
    fclsurface character varying(1) NOT NULL,
    fclcurrentoperatorname character varying(100),
    fclname character varying(40) NOT NULL,
    fclkind character varying(40) NOT NULL,
    fclbelongstoname character varying(41),
    fclbelongstokind character varying(40),
    fclbelongstos bigint,
    fclstartupdate date NOT NULL,
    fclwaterdepth numeric(13,6) NOT NULL,
    fclfunctions character varying(400),
    fcldesignlifetime bigint NOT NULL,
    fclfactpageurl character varying(200) NOT NULL,
    fclfactmapurl character varying(200) NOT NULL,
    fclpointgeometrywkt point NOT NULL
);

--
--

COMMENT ON COLUMN public.fclpoint.fclnpdidfacility IS 'NPDID facility';

--
--

COMMENT ON COLUMN public.fclpoint.fclsurface IS 'Surface facility';

--
--

COMMENT ON COLUMN public.fclpoint.fclcurrentoperatorname IS 'Current operator';

--
--

COMMENT ON COLUMN public.fclpoint.fclname IS 'Name';

--
--

COMMENT ON COLUMN public.fclpoint.fclkind IS 'Kind';

--
--

COMMENT ON COLUMN public.fclpoint.fclbelongstoname IS 'Belongs to, name';

--
--

COMMENT ON COLUMN public.fclpoint.fclbelongstokind IS 'Belongs to, kind';

--
--

COMMENT ON COLUMN public.fclpoint.fclstartupdate IS 'Startup date';

--
--

COMMENT ON COLUMN public.fclpoint.fclwaterdepth IS 'Water depth [m]';

--
--

COMMENT ON COLUMN public.fclpoint.fclfunctions IS 'Functions';

--
--

COMMENT ON COLUMN public.fclpoint.fcldesignlifetime IS 'Design lifetime [year]';

--
--

COMMENT ON COLUMN public.fclpoint.fclfactpageurl IS 'Fact page';

--
--

COMMENT ON COLUMN public.fclpoint.fclfactmapurl IS 'Fact map';

--
--

CREATE TABLE public.field (
    fldname character varying(40) NOT NULL,
    cmplongname character varying(200),
    fldcurrentactivitysatus character varying(40) NOT NULL,
    wlbname character varying(60),
    wlbcompletiondate date,
    fldownerkind character varying(40),
    fldownername character varying(40),
    fldnpdidowner bigint,
    fldnpdidfield bigint NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    cmpnpdidcompany bigint,
    fldfactpageurl character varying(200) NOT NULL,
    fldfactmapurl character varying(200) NOT NULL,
    flddateupdated date,
    flddateupdatedmax date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.field.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.field.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.field.fldcurrentactivitysatus IS 'Current activity status';

--
--

COMMENT ON COLUMN public.field.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.field.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.field.fldownerkind IS 'Owner kind';

--
--

COMMENT ON COLUMN public.field.fldownername IS 'Owner name';

--
--

COMMENT ON COLUMN public.field.fldnpdidowner IS 'NPDID owner';

--
--

COMMENT ON COLUMN public.field.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.field.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.field.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.field.fldfactpageurl IS 'Field fact page';

--
--

COMMENT ON COLUMN public.field.flddateupdated IS 'Date main level updated';

--
--

COMMENT ON COLUMN public.field.flddateupdatedmax IS 'Date all updated';

--
--

CREATE TABLE public.field_activity_status_hst (
    fldname character varying(40) NOT NULL,
    fldstatusfromdate date NOT NULL,
    fldstatustodate date NOT NULL,
    fldstatus character varying(40) NOT NULL,
    fldnpdidfield bigint NOT NULL,
    fldstatusdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.field_activity_status_hst.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.field_activity_status_hst.fldstatusfromdate IS 'Status from';

--
--

COMMENT ON COLUMN public.field_activity_status_hst.fldstatustodate IS 'Status to';

--
--

COMMENT ON COLUMN public.field_activity_status_hst.fldstatus IS 'Status';

--
--

COMMENT ON COLUMN public.field_activity_status_hst.fldnpdidfield IS 'NPDID field';

--
--

CREATE TABLE public.field_description (
    fldname character varying(40) NOT NULL,
    flddescriptionheading character varying(255) NOT NULL,
    flddescriptiontext text NOT NULL,
    fldnpdidfield bigint NOT NULL,
    flddescriptiondateupdated date NOT NULL
);

--
--

COMMENT ON COLUMN public.field_description.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.field_description.flddescriptionheading IS 'Heading';

--
--

COMMENT ON COLUMN public.field_description.flddescriptiontext IS 'Text';

--
--

COMMENT ON COLUMN public.field_description.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.field_description.flddescriptiondateupdated IS 'Date updated';

--
--

CREATE TABLE public.field_investment_yearly (
    prfinformationcarrier character varying(40) NOT NULL,
    prfyear bigint NOT NULL,
    prfinvestmentsmillnok numeric(13,6) NOT NULL,
    prfnpdidinformationcarrier bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.field_investment_yearly.prfinformationcarrier IS 'Field (Discovery)';

--
--

COMMENT ON COLUMN public.field_investment_yearly.prfyear IS 'Year';

--
--

COMMENT ON COLUMN public.field_investment_yearly.prfinvestmentsmillnok IS 'Investments [mill NOK norminal values]';

--
--

COMMENT ON COLUMN public.field_investment_yearly.prfnpdidinformationcarrier IS 'NPDID information carrier';

--
--

CREATE TABLE public.field_licensee_hst (
    fldname character varying(40) NOT NULL,
    fldownername character varying(40) NOT NULL,
    fldownerkind character varying(40) NOT NULL,
    fldownerfrom date NOT NULL,
    fldownerto date,
    fldlicenseefrom date NOT NULL,
    fldlicenseeto date NOT NULL,
    cmplongname character varying(200) NOT NULL,
    fldcompanyshare numeric(13,6) NOT NULL,
    fldsdfishare numeric(13,6),
    fldnpdidfield bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    fldlicenseedateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.field_licensee_hst.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.field_licensee_hst.fldownername IS 'Owner name';

--
--

COMMENT ON COLUMN public.field_licensee_hst.fldownerkind IS 'Owner kind';

--
--

COMMENT ON COLUMN public.field_licensee_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.field_licensee_hst.fldcompanyshare IS 'Company share [%]';

--
--

COMMENT ON COLUMN public.field_licensee_hst.fldsdfishare IS 'SDFI [%]';

--
--

COMMENT ON COLUMN public.field_licensee_hst.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.field_licensee_hst.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.field_licensee_hst.fldlicenseedateupdated IS 'Date updated';

--
--

CREATE TABLE public.field_operator_hst (
    fldname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    fldoperatorfrom date NOT NULL,
    fldoperatorto date NOT NULL,
    fldnpdidfield bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    fldoperatordateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.field_operator_hst.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.field_operator_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.field_operator_hst.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.field_operator_hst.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.field_operator_hst.fldoperatordateupdated IS 'Date updated';

--
--

CREATE TABLE public.field_owner_hst (
    fldname character varying(40) NOT NULL,
    fldownerkind character varying(40) NOT NULL,
    fldownername character varying(40) NOT NULL,
    fldownershipfromdate date NOT NULL,
    fldownershiptodate date NOT NULL,
    fldnpdidfield bigint NOT NULL,
    fldnpdidowner bigint NOT NULL,
    fldownerdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.field_owner_hst.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.field_owner_hst.fldownerkind IS 'Owner kind';

--
--

COMMENT ON COLUMN public.field_owner_hst.fldownername IS 'Owner name';

--
--

COMMENT ON COLUMN public.field_owner_hst.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.field_owner_hst.fldnpdidowner IS 'NPDID owner';

--
--

COMMENT ON COLUMN public.field_owner_hst.fldownerdateupdated IS 'Date updated';

--
--

CREATE TABLE public.field_production_monthly (
    prfinformationcarrier character varying(40) NOT NULL,
    prfyear bigint NOT NULL,
    prfmonth bigint NOT NULL,
    prfprdoilnetmillsm3 numeric(13,6) NOT NULL,
    prfprdgasnetbillsm3 numeric(13,6) NOT NULL,
    prfprdnglnetmillsm3 numeric(13,6) NOT NULL,
    prfprdcondensatenetmillsm3 numeric(13,6) NOT NULL,
    prfprdoenetmillsm3 numeric(13,6) NOT NULL,
    prfprdproducedwaterinfieldmillsm3 numeric(13,6) NOT NULL,
    prfnpdidinformationcarrier bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.field_production_monthly.prfinformationcarrier IS 'Field (Discovery)';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfyear IS 'Year';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfmonth IS 'Month';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfprdoilnetmillsm3 IS 'Net - oil [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfprdgasnetbillsm3 IS 'Net - gas [bill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfprdnglnetmillsm3 IS 'Net - NGL [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfprdcondensatenetmillsm3 IS 'Net - condensate [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfprdoenetmillsm3 IS 'Net - oil equivalents [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfprdproducedwaterinfieldmillsm3 IS 'Produced water in field [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_monthly.prfnpdidinformationcarrier IS 'NPDID information carrier';

--
--

CREATE TABLE public.field_production_totalt_ncs_month (
    prfyear bigint NOT NULL,
    prfmonth bigint NOT NULL,
    prfprdoilnetmillsm3 numeric(13,6) NOT NULL,
    prfprdgasnetbillsm3 numeric(13,6) NOT NULL,
    prfprdnglnetmillsm3 numeric(13,6) NOT NULL,
    prfprdcondensatenetmillsm3 numeric(13,6) NOT NULL,
    prfprdoenetmillsm3 numeric(13,6) NOT NULL,
    prfprdproducedwaterinfieldmillsm3 numeric(13,6) NOT NULL
);

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfyear IS 'Year';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfmonth IS 'Month';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfprdoilnetmillsm3 IS 'Net - oil [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfprdgasnetbillsm3 IS 'Net - gas [bill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfprdnglnetmillsm3 IS 'Net - NGL [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfprdcondensatenetmillsm3 IS 'Net - condensate [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfprdoenetmillsm3 IS 'Net - oil equivalents [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_month.prfprdproducedwaterinfieldmillsm3 IS 'Produced water in field [mill Sm3]';

--
--

CREATE TABLE public.field_production_totalt_ncs_year (
    prfyear bigint NOT NULL,
    prfprdoilnetmillsm numeric(13,6) NOT NULL,
    prfprdgasnetbillsm numeric(13,6) NOT NULL,
    prfprdcondensatenetmillsm3 numeric(13,6) NOT NULL,
    prfprdnglnetmillsm3 numeric(13,6) NOT NULL,
    prfprdoenetmillsm3 numeric(13,6) NOT NULL,
    prfprdproducedwaterinfieldmillsm3 numeric(13,6) NOT NULL
);

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_year.prfyear IS 'Year';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_year.prfprdcondensatenetmillsm3 IS 'Net - condensate [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_year.prfprdnglnetmillsm3 IS 'Net - NGL [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_year.prfprdoenetmillsm3 IS 'Net - oil equivalents [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_totalt_ncs_year.prfprdproducedwaterinfieldmillsm3 IS 'Produced water in field [mill Sm3]';

--
--

CREATE TABLE public.field_production_yearly (
    prfinformationcarrier character varying(40) NOT NULL,
    prfyear bigint NOT NULL,
    prfprdoilnetmillsm3 numeric(13,6) NOT NULL,
    prfprdgasnetbillsm3 numeric(13,6) NOT NULL,
    prfprdnglnetmillsm3 numeric(13,6) NOT NULL,
    prfprdcondensatenetmillsm3 numeric(13,6) NOT NULL,
    prfprdoenetmillsm3 numeric(13,6) NOT NULL,
    prfprdproducedwaterinfieldmillsm3 numeric(13,6) NOT NULL,
    prfnpdidinformationcarrier bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.field_production_yearly.prfinformationcarrier IS 'Field (Discovery)';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfyear IS 'Year';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfprdoilnetmillsm3 IS 'Net - oil [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfprdgasnetbillsm3 IS 'Net - gas [bill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfprdnglnetmillsm3 IS 'Net - NGL [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfprdcondensatenetmillsm3 IS 'Net - condensate [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfprdoenetmillsm3 IS 'Net - oil equivalents [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfprdproducedwaterinfieldmillsm3 IS 'Produced water in field [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_production_yearly.prfnpdidinformationcarrier IS 'NPDID information carrier';

--
--

CREATE TABLE public.field_reserves (
    fldname character varying(40) NOT NULL,
    fldrecoverableoil numeric(13,6) NOT NULL,
    fldrecoverablegas numeric(13,6) NOT NULL,
    fldrecoverablengl numeric(13,6) NOT NULL,
    fldrecoverablecondensate numeric(13,6) NOT NULL,
    fldrecoverableoe numeric(13,6) NOT NULL,
    fldremainingoil numeric(13,6) NOT NULL,
    fldremaininggas numeric(13,6) NOT NULL,
    fldremainingngl numeric(13,6) NOT NULL,
    fldremainingcondensate numeric(13,6) NOT NULL,
    fldremainingoe numeric(13,6) NOT NULL,
    flddateoffresestdisplay date NOT NULL,
    fldnpdidfield bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.field_reserves.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.field_reserves.fldrecoverableoil IS 'Orig. recoverable oil [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_reserves.fldrecoverablegas IS 'Orig. recoverable gas [bill Sm3]';

--
--

COMMENT ON COLUMN public.field_reserves.fldrecoverablengl IS 'Orig. recoverable NGL [mill tonn]';

--
--

COMMENT ON COLUMN public.field_reserves.fldrecoverablecondensate IS 'Orig. recoverable cond. [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_reserves.fldrecoverableoe IS 'Orig. recoverable oil eq. [mill Sm3 o.e]';

--
--

COMMENT ON COLUMN public.field_reserves.fldremainingoil IS 'Remaining oil [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_reserves.fldremaininggas IS 'Remaining gas [bill Sm3]';

--
--

COMMENT ON COLUMN public.field_reserves.fldremainingngl IS 'Remaining NGL [mill tonn]';

--
--

COMMENT ON COLUMN public.field_reserves.fldremainingcondensate IS 'Remaining cond. [mill Sm3]';

--
--

COMMENT ON COLUMN public.field_reserves.fldremainingoe IS 'Remaining oil eq. [mill Sm3 o.e]';

--
--

COMMENT ON COLUMN public.field_reserves.flddateoffresestdisplay IS 'Reserves updated date';

--
--

COMMENT ON COLUMN public.field_reserves.fldnpdidfield IS 'NPDID field';

--
--

CREATE TABLE public.fldarea (
    fldnpdidfield bigint NOT NULL,
    fldname character varying(40) NOT NULL,
    dscnpdiddiscovery bigint NOT NULL,
    dscname character varying(40) NOT NULL,
    dscresinclindiscoveryname character varying(40),
    dscnpdidresinclindiscovery bigint,
    dscincludedinfld character varying(3) NOT NULL,
    dschctype character varying(40) NOT NULL,
    fldhctype character varying(40) NOT NULL,
    dsccurrentactivitystatus character varying(40) NOT NULL,
    fldcurrentactivitystatus character varying(40) NOT NULL,
    flddsclabel character varying(40) NOT NULL,
    dscfacturl character varying(200) NOT NULL,
    fldfacturl character varying(200) NOT NULL,
    flddscareageometrywkt_ed50 text NOT NULL
);

--
--

COMMENT ON COLUMN public.fldarea.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.fldarea.fldname IS 'Field name';

--
--

COMMENT ON COLUMN public.fldarea.dscnpdiddiscovery IS 'NPDID discovery';

--
--

COMMENT ON COLUMN public.fldarea.dscname IS 'Discovery name';

--
--

COMMENT ON COLUMN public.fldarea.dscresinclindiscoveryname IS 'Resources incl. in';

--
--

COMMENT ON COLUMN public.fldarea.dschctype IS 'HC type';

--
--

COMMENT ON COLUMN public.fldarea.dsccurrentactivitystatus IS 'Current activity status';

--
--

CREATE TABLE public.licence (
    prlname character varying(50) NOT NULL,
    prllicensingactivityname character varying(40) NOT NULL,
    prlmainarea character varying(40),
    prlstatus character varying(40) NOT NULL,
    prldategranted date NOT NULL,
    prldatevalidto date NOT NULL,
    prloriginalarea numeric(13,6) NOT NULL,
    prlcurrentarea character varying(20) NOT NULL,
    prlphasecurrent character varying(40),
    prlnpdidlicence bigint NOT NULL,
    prlfactpageurl character varying(200) NOT NULL,
    prlfactmapurl character varying(200),
    prldateupdated date,
    prldateupdatedmax date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence.prllicensingactivityname IS 'Licensing activity';

--
--

COMMENT ON COLUMN public.licence.prlmainarea IS 'Main area';

--
--

COMMENT ON COLUMN public.licence.prlstatus IS 'Status';

--
--

COMMENT ON COLUMN public.licence.prldategranted IS 'Date granted';

--
--

COMMENT ON COLUMN public.licence.prldatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.licence.prloriginalarea IS 'Original area [km2]';

--
--

COMMENT ON COLUMN public.licence.prlcurrentarea IS 'Current area';

--
--

COMMENT ON COLUMN public.licence.prlphasecurrent IS 'Phase - current';

--
--

COMMENT ON COLUMN public.licence.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence.prlfactpageurl IS 'Fact page';

--
--

COMMENT ON COLUMN public.licence.prlfactmapurl IS 'Fact map';

--
--

COMMENT ON COLUMN public.licence.prldateupdated IS 'Date main level updated';

--
--

COMMENT ON COLUMN public.licence.prldateupdatedmax IS 'Date all updated';

--
--

CREATE TABLE public.licence_area_poly_hst (
    prlname character varying(50) NOT NULL,
    prlareapolydatevalidfrom date NOT NULL,
    prlareapolydatevalidto date NOT NULL,
    prlareapolynationcode character varying(2) NOT NULL,
    prlareapolyblockname character varying(40) NOT NULL,
    prlareapolystratigraphical character varying(4) NOT NULL,
    prlareapolypolyno bigint NOT NULL,
    prlareapolypolyarea numeric(13,6) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    prlareadateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlareapolydatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlareapolydatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlareapolyblockname IS 'Block name';

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlareapolystratigraphical IS 'Stratigraphcal';

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlareapolypolyarea IS 'Polygon area [km2]';

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_area_poly_hst.prlareadateupdated IS 'Date updated';

--
--

CREATE TABLE public.licence_licensee_hst (
    prlname character varying(50) NOT NULL,
    prllicenseedatevalidfrom date NOT NULL,
    prllicenseedatevalidto date NOT NULL,
    cmplongname character varying(200) NOT NULL,
    prllicenseeinterest numeric(13,6) NOT NULL,
    prllicenseesdfi numeric(13,6),
    prloperdatevalidfrom date,
    prloperdatevalidto date,
    prlnpdidlicence bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    prllicenseedateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prllicenseedatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prllicenseedatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prllicenseeinterest IS 'Interest [%]';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prllicenseesdfi IS 'SDFI [%]';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prloperdatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prloperdatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.licence_licensee_hst.prllicenseedateupdated IS 'Date updated';

--
--

CREATE TABLE public.licence_oper_hst (
    prlname character varying(50) NOT NULL,
    prloperdatevalidfrom date NOT NULL,
    prloperdatevalidto date NOT NULL,
    cmplongname character varying(200) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    prloperdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_oper_hst.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence_oper_hst.prloperdatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.licence_oper_hst.prloperdatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.licence_oper_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.licence_oper_hst.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_oper_hst.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.licence_oper_hst.prloperdateupdated IS 'Date updated';

--
--

CREATE TABLE public.licence_petreg_licence (
    ptlname character varying(40) NOT NULL,
    ptldateawarded date NOT NULL,
    ptldatevalidfrom date NOT NULL,
    ptldatevalidto date NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    ptldateupdated date,
    ptldateupdatedmax date NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_petreg_licence.ptlname IS 'Tillatelse';

--
--

COMMENT ON COLUMN public.licence_petreg_licence.ptldatevalidfrom IS 'Gyldig fra dato';

--
--

COMMENT ON COLUMN public.licence_petreg_licence.ptldatevalidto IS 'Gyldig til dato';

--
--

COMMENT ON COLUMN public.licence_petreg_licence.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_petreg_licence.ptldateupdated IS 'Dato hovednivå oppdatert';

--
--

COMMENT ON COLUMN public.licence_petreg_licence.ptldateupdatedmax IS 'Dato alle oppdatert';

--
--

CREATE TABLE public.licence_petreg_licence_licencee (
    ptlname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    ptllicenseeinterest numeric(13,6) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    ptllicenseedateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_petreg_licence_licencee.ptlname IS 'Tillatelse';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_licencee.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_licencee.ptllicenseeinterest IS 'Andel [%]';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_licencee.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_licencee.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_licencee.ptllicenseedateupdated IS 'Dato oppdatert';

--
--

CREATE TABLE public.licence_petreg_licence_oper (
    ptlname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    ptloperdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_petreg_licence_oper.ptlname IS 'Tillatelse';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_oper.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_oper.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_oper.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.licence_petreg_licence_oper.ptloperdateupdated IS 'Dato oppdatert';

--
--

CREATE TABLE public.licence_petreg_message (
    prlname character varying(50) NOT NULL,
    ptlmessagedocumentno bigint NOT NULL,
    ptlmessage text NOT NULL,
    ptlmessageregistereddate date NOT NULL,
    ptlmessagekinddesc character varying(100) NOT NULL,
    ptlmessagedateupdated date,
    prlnpdidlicence bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_petreg_message.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence_petreg_message.ptlmessage IS 'Utdrag av dokument';

--
--

COMMENT ON COLUMN public.licence_petreg_message.ptlmessageregistereddate IS 'Registreringsdato';

--
--

COMMENT ON COLUMN public.licence_petreg_message.ptlmessagekinddesc IS 'Type';

--
--

COMMENT ON COLUMN public.licence_petreg_message.ptlmessagedateupdated IS 'Dato oppdatert';

--
--

COMMENT ON COLUMN public.licence_petreg_message.prlnpdidlicence IS 'NPDID production licence';

--
--

CREATE TABLE public.licence_phase_hst (
    prlname character varying(50) NOT NULL,
    prldatephasevalidfrom date NOT NULL,
    prldatephasevalidto date NOT NULL,
    prlphase character varying(40) NOT NULL,
    prldategranted date NOT NULL,
    prldatevalidto date NOT NULL,
    prldateinitialperiodexpires date NOT NULL,
    prlactivestatusindicator character varying(40) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    prlphasedateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_phase_hst.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prldatephasevalidfrom IS 'Date phase valid from';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prldatephasevalidto IS 'Date phase valid to';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prlphase IS 'Phase';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prldategranted IS 'Date granted';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prldatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prldateinitialperiodexpires IS 'Expiry date, initial period';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prlactivestatusindicator IS 'Active';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_phase_hst.prlphasedateupdated IS 'Date updated';

--
--

CREATE TABLE public.licence_task (
    prlname character varying(50) NOT NULL,
    prltaskname character varying(40) NOT NULL,
    prltasktypeno character varying(100) NOT NULL,
    prltasktypeen character varying(200) NOT NULL,
    prltaskstatusno character varying(100) NOT NULL,
    prltaskstatusen character varying(40) NOT NULL,
    prltaskexpirydate date NOT NULL,
    wlbname character varying(60),
    prldatevalidto date NOT NULL,
    prllicensingactivityname character varying(40) NOT NULL,
    cmplongname character varying(200),
    cmpnpdidcompany bigint,
    prlnpdidlicence bigint NOT NULL,
    prltaskid bigint NOT NULL,
    prltaskrefid bigint,
    prltaskdateupdated date,
    datesyncnpd date NOT NULL,
    UNIQUE (prltaskid) 
);

--
--

COMMENT ON COLUMN public.licence_task.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence_task.prltaskname IS 'Task name (norwegian)';

--
--

COMMENT ON COLUMN public.licence_task.prltasktypeen IS 'Type of task';

--
--

COMMENT ON COLUMN public.licence_task.prltaskstatusen IS 'Task status';

--
--

COMMENT ON COLUMN public.licence_task.prltaskexpirydate IS 'Expiry date';

--
--

COMMENT ON COLUMN public.licence_task.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.licence_task.prldatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.licence_task.prllicensingactivityname IS 'Licensing activity';

--
--

COMMENT ON COLUMN public.licence_task.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.licence_task.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.licence_task.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_task.prltaskid IS 'Task ID';

--
--

COMMENT ON COLUMN public.licence_task.prltaskrefid IS 'Referred task ID';

--
--

COMMENT ON COLUMN public.licence_task.prltaskdateupdated IS 'Date updated';

--
--

CREATE TABLE public.licence_transfer_hst (
    prlname character varying(50) NOT NULL,
    prltransferdatevalidfrom date NOT NULL,
    prltransferdirection character varying(4) NOT NULL,
    prltransferkind character varying(40),
    cmplongname character varying(200) NOT NULL,
    prltransferredinterest numeric(13,6) NOT NULL,
    prltransfersdfi numeric(13,6),
    prlnpdidlicence bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    prltransferdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prltransferdatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prltransferdirection IS 'Transfer direction';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prltransferkind IS 'Transfer kind';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prltransferredinterest IS 'Transferred interest [%]';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prltransfersdfi IS 'SDFI [%]';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.licence_transfer_hst.prltransferdateupdated IS 'Date updated';

--
--

CREATE TABLE public.pipline (
    pipnpdidpipe bigint NOT NULL,
    pipnpdidfromfacility bigint NOT NULL,
    pipnpdidtofacility bigint NOT NULL,
    pipnpdidoperator bigint,
    pipname character varying(50) NOT NULL,
    pipnamefromfacility character varying(50) NOT NULL,
    pipnametofacility character varying(50) NOT NULL,
    pipnamecurrentoperator character varying(100),
    pipcurrentphase character varying(40) NOT NULL,
    pipmedium character varying(20) NOT NULL,
    pipmaingrouping character varying(20) NOT NULL,
    pipdimension numeric(13,6) NOT NULL,
    piplinegeometrywkt public.geometry(MultiLineString,4326)
);

--
--

CREATE TABLE public.prlarea (
    prlname character varying(50) NOT NULL,
    prlactive character varying(20) NOT NULL,
    prlcurrentarea character varying(20) NOT NULL,
    prldategranted date NOT NULL,
    prldatevalidto date NOT NULL,
    prlareapolydatevalidfrom date NOT NULL,
    prlareapolydatevalidto date NOT NULL,
    prlareapolyfromzvalue bigint NOT NULL,
    prlareapolytozvalue bigint NOT NULL,
    prlareapolyvertlimen text,
    prlareapolyvertlimno text,
    prlstratigraphical character varying(3) NOT NULL,
    prlareapolystratigraphical character varying(4) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    prllastoperatornameshort character varying(40) NOT NULL,
    prllastoperatornamelong character varying(200) NOT NULL,
    prllicensingactivityname character varying(40) NOT NULL,
    prllastoperatornpdidcompany bigint NOT NULL,
    prlfacturl character varying(200) NOT NULL,
    prlareageometrywkt text NOT NULL,
    prlarea_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.prlarea.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.prlarea.prlactive IS 'Active';

--
--

COMMENT ON COLUMN public.prlarea.prlcurrentarea IS 'Current area';

--
--

COMMENT ON COLUMN public.prlarea.prldategranted IS 'Date granted';

--
--

COMMENT ON COLUMN public.prlarea.prldatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.prlarea.prlareapolydatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.prlarea.prlareapolydatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.prlarea.prlareapolystratigraphical IS 'Stratigraphcal';

--
--

COMMENT ON COLUMN public.prlarea.prlnpdidlicence IS 'NPDID production licence';

--
--

COMMENT ON COLUMN public.prlarea.prllicensingactivityname IS 'Licensing activity';

--
--

CREATE SEQUENCE public.prlarea_prlarea_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.prlarea_prlarea_id_seq OWNED BY public.prlarea.prlarea_id;

--
--

CREATE TABLE public.prlareasplitbyblock (
    prlname character varying(50) NOT NULL,
    prlactive character varying(20) NOT NULL,
    prlcurrentarea character varying(20) NOT NULL,
    prldategranted date NOT NULL,
    prldatevalidto date NOT NULL,
    prlareapolydatevalidfrom date NOT NULL,
    prlareapolydatevalidto date NOT NULL,
    prlareapolypolyno bigint NOT NULL,
    prlareapolypolyarea numeric(13,6) NOT NULL,
    blcname character varying(40) NOT NULL,
    prlareapolyfromzvalue bigint NOT NULL,
    prlareapolytozvalue bigint NOT NULL,
    prlareapolyvertlimen text,
    prlareapolyvertlimno text,
    prlstratigraphical character varying(3) NOT NULL,
    prllastoperatornpdidcompany bigint NOT NULL,
    prllastoperatornameshort character varying(40) NOT NULL,
    prllastoperatornamelong character varying(200) NOT NULL,
    prllicensingactivityname character varying(40) NOT NULL,
    prlfacturl character varying(200) NOT NULL,
    prlareapolystratigraphical character varying(4) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    prlareageometrywkt text NOT NULL
);

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlname IS 'Production licence';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlactive IS 'Active';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlcurrentarea IS 'Current area';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prldategranted IS 'Date granted';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prldatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlareapolydatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlareapolydatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlareapolypolyarea IS 'Polygon area [km2]';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.blcname IS 'Block name';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prllicensingactivityname IS 'Licensing activity';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlareapolystratigraphical IS 'Stratigraphcal';

--
--

COMMENT ON COLUMN public.prlareasplitbyblock.prlnpdidlicence IS 'NPDID production licence';

--
--

CREATE TABLE public.seaarea (
    seasurveyname character varying(100) NOT NULL,
    seanpdidsurvey bigint NOT NULL,
    seafactmapurl character varying(260),
    seafactpageurl character varying(200),
    seastatus character varying(100) NOT NULL,
    seageographicalarea character varying(100) NOT NULL,
    seamarketavailable character varying(20) NOT NULL,
    seasurveytypemain character varying(100) NOT NULL,
    seasurveytypepart character varying(100),
    seacompanyreported character varying(100) NOT NULL,
    seasourcetype character varying(100),
    seasourcenumber character varying(100),
    seasourcesize character varying(100),
    seasourcepressure character varying(100),
    seasensortype character varying(100),
    seasensornumbers character varying(40),
    seasensorlength character varying(100),
    seaplanfromdate date NOT NULL,
    seadatestarting date,
    seaplantodate date NOT NULL,
    seadatefinalized date,
    seaplancdpkm bigint,
    seacdptotalkm bigint,
    seaplanboatkm bigint,
    seaboattotalkm bigint,
    sea3dkm2 numeric(13,6),
    seapolygonkind character varying(100) NOT NULL,
    seaarea_id bigint NOT NULL,
    seapolygeometrywkt public.geometry(Polygon,4326)
);

--
--

COMMENT ON COLUMN public.seaarea.seasurveyname IS 'Survey name';

--
--

COMMENT ON COLUMN public.seaarea.seanpdidsurvey IS 'NPDID for survey';

--
--

COMMENT ON COLUMN public.seaarea.seafactmapurl IS 'Fact Map';

--
--

COMMENT ON COLUMN public.seaarea.seastatus IS 'Status';

--
--

COMMENT ON COLUMN public.seaarea.seamarketavailable IS 'Marked available';

--
--

COMMENT ON COLUMN public.seaarea.seasurveytypemain IS 'Main type';

--
--

COMMENT ON COLUMN public.seaarea.seasurveytypepart IS 'Sub type';

--
--

COMMENT ON COLUMN public.seaarea.seacompanyreported IS 'Company - responsible';

--
--

COMMENT ON COLUMN public.seaarea.seasourcetype IS 'Source type';

--
--

COMMENT ON COLUMN public.seaarea.seasourcenumber IS 'Number of sources';

--
--

COMMENT ON COLUMN public.seaarea.seasourcesize IS 'Source size';

--
--

COMMENT ON COLUMN public.seaarea.seasourcepressure IS 'Source pressure';

--
--

COMMENT ON COLUMN public.seaarea.seasensortype IS 'Sensor type';

--
--

COMMENT ON COLUMN public.seaarea.seasensornumbers IS 'Numbers of sensors';

--
--

COMMENT ON COLUMN public.seaarea.seasensorlength IS 'Sensor length [m]';

--
--

COMMENT ON COLUMN public.seaarea.seaplanfromdate IS 'Start date - planned';

--
--

COMMENT ON COLUMN public.seaarea.seadatestarting IS 'Start date - actual';

--
--

COMMENT ON COLUMN public.seaarea.seaplantodate IS 'Completed date - planned';

--
--

COMMENT ON COLUMN public.seaarea.seadatefinalized IS 'Completed date - actual';

--
--

COMMENT ON COLUMN public.seaarea.seaplancdpkm IS 'Total length - planned [cdp km]';

--
--

COMMENT ON COLUMN public.seaarea.seacdptotalkm IS 'Total length - actual [cdp km]';

--
--

COMMENT ON COLUMN public.seaarea.seaplanboatkm IS 'Total length - planned [boat km]';

--
--

COMMENT ON COLUMN public.seaarea.seaboattotalkm IS 'Total length - actual [boat km]';

--
--

COMMENT ON COLUMN public.seaarea.sea3dkm2 IS 'Total net area - planned 3D/4D [km2]';

--
--

COMMENT ON COLUMN public.seaarea.seapolygonkind IS 'Kind of polygon';

--
--

CREATE SEQUENCE public.seaarea_seaarea_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.seaarea_seaarea_id_seq OWNED BY public.seaarea.seaarea_id;

--
--

CREATE TABLE public.seamultiline (
    seasurveyname character varying(100) NOT NULL,
    seafactmapurl character varying(260),
    seafactpageurl character varying(200),
    seastatus character varying(100) NOT NULL,
    seamarketavailable character varying(20) NOT NULL,
    seasurveytypemain character varying(100) NOT NULL,
    seasurveytypepart character varying(100) NOT NULL,
    seacompanyreported character varying(100) NOT NULL,
    seasourcetype character varying(100) NOT NULL,
    seasourcenumber character varying(100),
    seasourcesize character varying(100),
    seasourcepressure character varying(100),
    seasensortype character varying(100) NOT NULL,
    seasensornumbers character varying(40) NOT NULL,
    seasensorlength character varying(100) NOT NULL,
    seaplanfromdate date NOT NULL,
    seadatestarting date,
    seaplantodate date NOT NULL,
    seadatefinalized date,
    seaplancdpkm bigint NOT NULL,
    seacdptotalkm bigint,
    seaplanboatkm bigint NOT NULL,
    seaboattotalkm bigint,
    seamultilinegeometrywkt text NOT NULL
);

--
--

COMMENT ON COLUMN public.seamultiline.seasurveyname IS 'Survey name';

--
--

COMMENT ON COLUMN public.seamultiline.seafactmapurl IS 'Fact Map';

--
--

COMMENT ON COLUMN public.seamultiline.seastatus IS 'Status';

--
--

COMMENT ON COLUMN public.seamultiline.seamarketavailable IS 'Marked available';

--
--

COMMENT ON COLUMN public.seamultiline.seasurveytypemain IS 'Main type';

--
--

COMMENT ON COLUMN public.seamultiline.seasurveytypepart IS 'Sub type';

--
--

COMMENT ON COLUMN public.seamultiline.seacompanyreported IS 'Company - responsible';

--
--

COMMENT ON COLUMN public.seamultiline.seasourcetype IS 'Source type';

--
--

COMMENT ON COLUMN public.seamultiline.seasourcenumber IS 'Number of sources';

--
--

COMMENT ON COLUMN public.seamultiline.seasourcesize IS 'Source size';

--
--

COMMENT ON COLUMN public.seamultiline.seasourcepressure IS 'Source pressure';

--
--

COMMENT ON COLUMN public.seamultiline.seasensortype IS 'Sensor type';

--
--

COMMENT ON COLUMN public.seamultiline.seasensornumbers IS 'Numbers of sensors';

--
--

COMMENT ON COLUMN public.seamultiline.seasensorlength IS 'Sensor length [m]';

--
--

COMMENT ON COLUMN public.seamultiline.seaplanfromdate IS 'Start date - planned';

--
--

COMMENT ON COLUMN public.seamultiline.seadatestarting IS 'Start date - actual';

--
--

COMMENT ON COLUMN public.seamultiline.seaplantodate IS 'Completed date - planned';

--
--

COMMENT ON COLUMN public.seamultiline.seadatefinalized IS 'Completed date - actual';

--
--

COMMENT ON COLUMN public.seamultiline.seaplancdpkm IS 'Total length - planned [cdp km]';

--
--

COMMENT ON COLUMN public.seamultiline.seacdptotalkm IS 'Total length - actual [cdp km]';

--
--

COMMENT ON COLUMN public.seamultiline.seaplanboatkm IS 'Total length - planned [boat km]';

--
--

COMMENT ON COLUMN public.seamultiline.seaboattotalkm IS 'Total length - actual [boat km]';

--
--

CREATE TABLE public.seis_acquisition (
    seaname character varying(100) NOT NULL,
    seaplanfromdate date NOT NULL,
    seanpdidsurvey bigint NOT NULL,
    seastatus character varying(100) NOT NULL,
    seageographicalarea character varying(100) NOT NULL,
    seasurveytypemain character varying(100) NOT NULL,
    seasurveytypepart character varying(100),
    seacompanyreported character varying(100) NOT NULL,
    seaplantodate date NOT NULL,
    seadatestarting date,
    seadatefinalized date,
    seacdptotalkm bigint,
    seaboattotalkm bigint,
    sea3dkm2 numeric(13,6),
    seasampling character varying(20),
    seashallowdrilling character varying(20),
    seageotechnical character varying(20),
    datesyncnpd date NOT NULL,
    UNIQUE (seanpdidsurvey),
    UNIQUE (seaname)
);

--
--

COMMENT ON COLUMN public.seis_acquisition.seaname IS 'Survey name';

--
--

COMMENT ON COLUMN public.seis_acquisition.seaplanfromdate IS 'Start date - planned';

--
--

COMMENT ON COLUMN public.seis_acquisition.seanpdidsurvey IS 'NPDID for survey';

--
--

COMMENT ON COLUMN public.seis_acquisition.seastatus IS 'Status';

--
--

COMMENT ON COLUMN public.seis_acquisition.seasurveytypemain IS 'Main type';

--
--

COMMENT ON COLUMN public.seis_acquisition.seasurveytypepart IS 'Sub type';

--
--

COMMENT ON COLUMN public.seis_acquisition.seacompanyreported IS 'Company - responsible';

--
--

COMMENT ON COLUMN public.seis_acquisition.seaplantodate IS 'Completed date - planned';

--
--

COMMENT ON COLUMN public.seis_acquisition.seadatestarting IS 'Start date - actual';

--
--

COMMENT ON COLUMN public.seis_acquisition.seadatefinalized IS 'Completed date - actual';

--
--

COMMENT ON COLUMN public.seis_acquisition.seacdptotalkm IS 'Total length - actual [cdp km]';

--
--

COMMENT ON COLUMN public.seis_acquisition.seaboattotalkm IS 'Total length - actual [boat km]';

--
--

COMMENT ON COLUMN public.seis_acquisition.sea3dkm2 IS 'Total net area - planned 3D/4D [km2]';

--
--

COMMENT ON COLUMN public.seis_acquisition.seasampling IS 'Sampling';

--
--

COMMENT ON COLUMN public.seis_acquisition.seashallowdrilling IS 'Shallow drilling';

--
--

COMMENT ON COLUMN public.seis_acquisition.seageotechnical IS 'Geotechnical measurement';

--
--

CREATE TABLE public.seis_acquisition_coordinates_inc_turnarea (
    seasurveyname character varying(100) NOT NULL,
    seanpdidsurvey bigint NOT NULL,
    seapolygonpointnumber bigint NOT NULL,
    seapolygonnsdeg bigint NOT NULL,
    seapolygonnsmin bigint NOT NULL,
    seapolygonnssec numeric(13,6) NOT NULL,
    seapolygonewdeg bigint NOT NULL,
    seapolygonewmin bigint NOT NULL,
    seapolygonewsec numeric(13,6) NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seasurveyname IS 'Survey name';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seanpdidsurvey IS 'NPDID for survey';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seapolygonpointnumber IS 'Point number';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seapolygonnsdeg IS 'NS degrees';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seapolygonnsmin IS 'NS minutes';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seapolygonnssec IS 'NS seconds';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seapolygonewdeg IS 'EW degrees';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seapolygonewmin IS 'EW minutes';

--
--

COMMENT ON COLUMN public.seis_acquisition_coordinates_inc_turnarea.seapolygonewsec IS 'EW seconds';

--
--

CREATE TABLE public.seis_acquisition_progress (
    seaprogressdate date NOT NULL,
    seaprogresstext2 character varying(40) NOT NULL,
    seaprogresstext text NOT NULL,
    seaprogressdescription text,
    seanpdidsurvey bigint NOT NULL,
    seis_acquisition_progress_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.seis_acquisition_progress.seanpdidsurvey IS 'NPDID for survey';

--
--

CREATE SEQUENCE public.seis_acquisition_progress_seis_acquisition_progress_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.seis_acquisition_progress_seis_acquisition_progress_id_seq OWNED BY public.seis_acquisition_progress.seis_acquisition_progress_id;

--
--

CREATE TABLE public.strat_litho_wellbore (
    wlbname character varying(60) NOT NULL,
    lsutopdepth numeric(13,6) NOT NULL,
    lsubottomdepth numeric(13,6) NOT NULL,
    lsuname character varying(20) NOT NULL,
    lsulevel character varying(9) NOT NULL,
    lsunpdidlithostrat bigint NOT NULL,
    wlbcompletiondate date NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    lsuwellboreupdateddate date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.lsutopdepth IS 'Top depth [m]';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.lsubottomdepth IS 'Bottom depth [m]';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.lsuname IS 'Lithostrat. unit';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.lsulevel IS 'Level';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.lsunpdidlithostrat IS 'NPDID lithostrat. unit';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore.lsuwellboreupdateddate IS 'Date updated';

--
--

CREATE TABLE public.strat_litho_wellbore_core (
    wlbname character varying(60) NOT NULL,
    lsucorelenght numeric(13,6) NOT NULL,
    lsuname character varying(20) NOT NULL,
    lsulevel character varying(9) NOT NULL,
    wlbcompletiondate date NOT NULL,
    lsunpdidlithostrat bigint NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.strat_litho_wellbore_core.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore_core.lsucorelenght IS 'Core length [m]';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore_core.lsuname IS 'Lithostrat. unit';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore_core.lsulevel IS 'Level';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore_core.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore_core.lsunpdidlithostrat IS 'NPDID lithostrat. unit';

--
--

COMMENT ON COLUMN public.strat_litho_wellbore_core.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

CREATE TABLE public.tuf_operator_hst (
    tufname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    tufoperdatevalidfrom date NOT NULL,
    tufoperdatevalidto date NOT NULL,
    tufnpdidtuf bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.tuf_operator_hst.tufname IS 'TUF';

--
--

COMMENT ON COLUMN public.tuf_operator_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.tuf_operator_hst.tufoperdatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.tuf_operator_hst.tufoperdatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.tuf_operator_hst.tufnpdidtuf IS 'NPDID tuf';

--
--

COMMENT ON COLUMN public.tuf_operator_hst.cmpnpdidcompany IS 'NPDID company';

--
--

CREATE TABLE public.tuf_owner_hst (
    tufname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    tufownerdatevalidfrom date NOT NULL,
    tufownerdatevalidto date NOT NULL,
    tufownershare numeric(13,6) NOT NULL,
    tufnpdidtuf bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.tuf_owner_hst.tufname IS 'TUF';

--
--

COMMENT ON COLUMN public.tuf_owner_hst.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.tuf_owner_hst.tufownerdatevalidfrom IS 'Date valid from';

--
--

COMMENT ON COLUMN public.tuf_owner_hst.tufownerdatevalidto IS 'Date valid to';

--
--

COMMENT ON COLUMN public.tuf_owner_hst.tufownershare IS 'Share [%]';

--
--

COMMENT ON COLUMN public.tuf_owner_hst.tufnpdidtuf IS 'NPDID tuf';

--
--

COMMENT ON COLUMN public.tuf_owner_hst.cmpnpdidcompany IS 'NPDID company';

--
--

CREATE TABLE public.tuf_petreg_licence (
    ptlname character varying(40) NOT NULL,
    tufname character varying(40) NOT NULL,
    ptldatevalidfrom date NOT NULL,
    ptldatevalidto date NOT NULL,
    tufnpdidtuf bigint NOT NULL,
    ptldateupdated date,
    ptldateupdatedmax date NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.tuf_petreg_licence.ptlname IS 'Tillatelse';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence.tufname IS 'TUF';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence.ptldatevalidfrom IS 'Gyldig fra dato';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence.ptldatevalidto IS 'Gyldig til dato';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence.tufnpdidtuf IS 'NPDID tuf';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence.ptldateupdated IS 'Dato hovednivå oppdatert';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence.ptldateupdatedmax IS 'Dato alle oppdatert';

--
--

CREATE TABLE public.tuf_petreg_licence_licencee (
    ptlname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    ptllicenseeinterest numeric(13,6) NOT NULL,
    tufname character varying(40) NOT NULL,
    tufnpdidtuf bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    ptllicenseedateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_licencee.ptlname IS 'Tillatelse';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_licencee.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_licencee.ptllicenseeinterest IS 'Andel [%]';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_licencee.tufname IS 'TUF';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_licencee.tufnpdidtuf IS 'NPDID tuf';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_licencee.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_licencee.ptllicenseedateupdated IS 'Dato oppdatert';

--
--

CREATE TABLE public.tuf_petreg_licence_oper (
    textbox42 character varying(20) NOT NULL,
    textbox2 character varying(20) NOT NULL,
    ptlname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    tufname character varying(40) NOT NULL,
    tufnpdidtuf bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    ptloperdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_oper.ptlname IS 'Tillatelse';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_oper.cmplongname IS 'Company name';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_oper.tufname IS 'TUF';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_oper.tufnpdidtuf IS 'NPDID tuf';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_oper.cmpnpdidcompany IS 'NPDID company';

--
--

COMMENT ON COLUMN public.tuf_petreg_licence_oper.ptloperdateupdated IS 'Dato oppdatert';

--
--

CREATE TABLE public.tuf_petreg_message (
    ptlname character varying(40) NOT NULL,
    ptlmessagedocumentno bigint NOT NULL,
    ptlmessage text NOT NULL,
    ptlmessageregistereddate date NOT NULL,
    ptlmessagekinddesc character varying(100) NOT NULL,
    tufname character varying(40) NOT NULL,
    ptlmessagedateupdated date,
    tufnpdidtuf bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.tuf_petreg_message.ptlname IS 'Tillatelse';

--
--

COMMENT ON COLUMN public.tuf_petreg_message.ptlmessage IS 'Utdrag av dokument';

--
--

COMMENT ON COLUMN public.tuf_petreg_message.ptlmessageregistereddate IS 'Registreringsdato';

--
--

COMMENT ON COLUMN public.tuf_petreg_message.ptlmessagekinddesc IS 'Type';

--
--

COMMENT ON COLUMN public.tuf_petreg_message.tufname IS 'TUF';

--
--

COMMENT ON COLUMN public.tuf_petreg_message.ptlmessagedateupdated IS 'Dato oppdatert';

--
--

COMMENT ON COLUMN public.tuf_petreg_message.tufnpdidtuf IS 'NPDID tuf';

--
--

CREATE TABLE public.wellbore_casing_and_lot (
    wlbname character varying(60) NOT NULL,
    wlbcasingtype character varying(10),
    wlbcasingdiameter character varying(6),
    wlbcasingdepth numeric(13,6) NOT NULL,
    wlbholediameter character varying(6),
    wlbholedepth numeric(13,6) NOT NULL,
    wlblotmuddencity numeric(13,6) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbcasingdateupdated date,
    datesyncnpd date NOT NULL,
    wellbore_casing_and_lot_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbcasingtype IS 'Casing type';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbcasingdiameter IS 'Casing diam. [inch]';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbcasingdepth IS 'Casing depth [m]';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbholediameter IS 'Hole diam. [inch]';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbholedepth IS 'Hole depth[m]';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlblotmuddencity IS 'LOT mud eqv. [g/cm3]';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_casing_and_lot.wlbcasingdateupdated IS 'Date updated';

--
--

CREATE SEQUENCE public.wellbore_casing_and_lot_wellbore_casing_and_lot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.wellbore_casing_and_lot_wellbore_casing_and_lot_id_seq OWNED BY public.wellbore_casing_and_lot.wellbore_casing_and_lot_id;

--
--

CREATE TABLE public.wellbore_coordinates (
    wlbwellborename character varying(40) NOT NULL,
    wlbdrillingoperator character varying(60) NOT NULL,
    wlbproductionlicence character varying(40),
    wlbwelltype character varying(20),
    wlbpurposeplanned character varying(40),
    wlbcontent character varying(40),
    wlbentrydate date,
    wlbcompletiondate date,
    wlbfield character varying(40),
    wlbmainarea character varying(40) NOT NULL,
    wlbgeodeticdatum character varying(6),
    wlbnsdeg bigint NOT NULL,
    wlbnsmin bigint NOT NULL,
    wlbnssec numeric(6,2) NOT NULL,
    wlbnscode character varying(1),
    wlbewdeg bigint NOT NULL,
    wlbewmin bigint NOT NULL,
    wlbewsec numeric(6,2) NOT NULL,
    wlbewcode character varying(1),
    wlbnsdecdeg numeric(13,6) NOT NULL,
    wlbewdesdeg numeric(13,6) NOT NULL,
    wlbnsutm numeric(13,6) NOT NULL,
    wlbewutm numeric(13,6) NOT NULL,
    wlbutmzone bigint NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbwellborename IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbdrillingoperator IS 'Drilling operator';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbproductionlicence IS 'Drilled in production licence';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbwelltype IS 'Type';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbpurposeplanned IS 'Purpose - planned';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbcontent IS 'Content';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbentrydate IS 'Entry date';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbfield IS 'Field';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbmainarea IS 'Main area';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbgeodeticdatum IS 'Geodetic datum';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbnsdeg IS 'NS degrees';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbnsmin IS 'NS minutes';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbnssec IS 'NS seconds';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbnscode IS 'NS code';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbewdeg IS 'EW degrees';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbewmin IS 'EW minutes';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbewsec IS 'EW seconds';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbewcode IS 'EW code';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbnsdecdeg IS 'NS decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbewdesdeg IS 'EW decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbnsutm IS 'NS UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbewutm IS 'EW UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbutmzone IS 'UTM zone';

--
--

COMMENT ON COLUMN public.wellbore_coordinates.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

CREATE TABLE public.wellbore_core (
    wlbname character varying(60) NOT NULL,
    wlbcorenumber bigint NOT NULL,
    wlbcoreintervaltop numeric(13,6),
    wlbcoreintervalbottom numeric(13,6),
    wlbcoreintervaluom character varying(6),
    wlbtotalcorelength numeric(13,6) NOT NULL,
    wlbnumberofcores bigint NOT NULL,
    wlbcoresampleavailable character varying(3) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbcoredateupdated date,
    datesyncnpd date NOT NULL,
    wellbore_core_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_core.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbcorenumber IS 'Core sample number';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbcoreintervaltop IS 'Core sample - top depth';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbcoreintervalbottom IS 'Core sample - bottom depth';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbcoreintervaluom IS 'Core sample depth - uom';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbtotalcorelength IS 'Total core sample length [m]';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbnumberofcores IS 'Number of cores samples';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbcoresampleavailable IS 'Core samples available';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_core.wlbcoredateupdated IS 'Date updated';

--
--

CREATE TABLE public.wellbore_core_photo (
    wlbname character varying(60) NOT NULL,
    wlbcorenumber bigint NOT NULL,
    wlbcorephototitle character varying(200) NOT NULL,
    wlbcorephotoimgurl character varying(200) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbcorephotodateupdated date,
    wellbore_core_photo_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_core_photo.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_core_photo.wlbcorenumber IS 'Core sample number';

--
--

COMMENT ON COLUMN public.wellbore_core_photo.wlbcorephototitle IS 'Core photo title';

--
--

COMMENT ON COLUMN public.wellbore_core_photo.wlbcorephotoimgurl IS 'Core photo URL';

--
--

COMMENT ON COLUMN public.wellbore_core_photo.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_core_photo.wlbcorephotodateupdated IS 'Date updated';

--
--

CREATE SEQUENCE public.wellbore_core_photo_wellbore_core_photo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.wellbore_core_photo_wellbore_core_photo_id_seq OWNED BY public.wellbore_core_photo.wellbore_core_photo_id;

--
--

CREATE SEQUENCE public.wellbore_core_wellbore_core_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.wellbore_core_wellbore_core_id_seq OWNED BY public.wellbore_core.wellbore_core_id;

--
--

CREATE TABLE public.wellbore_development_all (
    wlbwellborename character varying(40) NOT NULL,
    wlbwell character varying(40) NOT NULL,
    wlbdrillingoperator character varying(60) NOT NULL,
    wlbdrillingoperatorgroup character varying(20) NOT NULL,
    wlbproductionlicence character varying(40) NOT NULL,
    wlbpurposeplanned character varying(40),
    wlbcontent character varying(40),
    wlbwelltype character varying(20) NOT NULL,
    wlbentrydate date,
    wlbcompletiondate date,
    wlbfield character varying(40) NOT NULL,
    wlbdrillpermit character varying(10) NOT NULL,
    wlbdiscovery character varying(40) NOT NULL,
    wlbdiscoverywellbore character varying(3) NOT NULL,
    wlbkellybushelevation numeric(13,6) NOT NULL,
    wlbfinalverticaldepth numeric(6,2),
    wlbtotaldepth numeric(13,6) NOT NULL,
    wlbwaterdepth numeric(13,6) NOT NULL,
    wlbmainarea character varying(40) NOT NULL,
    wlbdrillingfacility character varying(50),
    wlbfacilitytypedrilling character varying(40),
    wlbproductionfacility character varying(50),
    wlblicensingactivity character varying(40) NOT NULL,
    wlbmultilateral character varying(3) NOT NULL,
    wlbcontentplanned character varying(40),
    wlbentryyear bigint NOT NULL,
    wlbcompletionyear bigint NOT NULL,
    wlbreclassfromwellbore character varying(40),
    wlbplotsymbol bigint NOT NULL,
    wlbgeodeticdatum character varying(6),
    wlbnsdeg bigint NOT NULL,
    wlbnsmin bigint NOT NULL,
    wlbnssec numeric(6,2) NOT NULL,
    wlbnscode character varying(1) NOT NULL,
    wlbewdeg bigint NOT NULL,
    wlbewmin bigint NOT NULL,
    wlbewsec numeric(6,2) NOT NULL,
    wlbewcode character varying(1),
    wlbnsdecdeg numeric(13,6) NOT NULL,
    wlbewdesdeg numeric(13,6) NOT NULL,
    wlbnsutm numeric(13,6) NOT NULL,
    wlbewutm numeric(13,6) NOT NULL,
    wlbutmzone bigint NOT NULL,
    wlbnamepart1 bigint NOT NULL,
    wlbnamepart2 bigint NOT NULL,
    wlbnamepart3 character varying(1) NOT NULL,
    wlbnamepart4 bigint NOT NULL,
    wlbnamepart5 character varying(2),
    wlbnamepart6 character varying(2),
    wlbfactpageurl character varying(200) NOT NULL,
    wlbfactmapurl character varying(200) NOT NULL,
    wlbdiskoswellboretype character varying(20) NOT NULL,
    wlbdiskoswellboreparent character varying(40),
    wlbnpdidwellbore bigint NOT NULL,
    dscnpdiddiscovery bigint NOT NULL,
    fldnpdidfield bigint NOT NULL,
    wlbwdssqcdate date,
    prlnpdidproductionlicence bigint NOT NULL,
    fclnpdidfacilitydrilling bigint,
    fclnpdidfacilityproducing bigint,
    wlbnpdidwellborereclass bigint NOT NULL,
    wlbdiskoswelloperator character varying(40) NOT NULL,
    wlbdateupdated date NOT NULL,
    wlbdateupdatedmax date NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbwellborename IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbwell IS 'Well name';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdrillingoperator IS 'Drilling operator';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdrillingoperatorgroup IS 'Drilling operator group';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbproductionlicence IS 'Drilled in production licence';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbpurposeplanned IS 'Purpose - planned';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbcontent IS 'Content';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbwelltype IS 'Type';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbentrydate IS 'Entry date';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbfield IS 'Field';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdrillpermit IS 'Drill permit';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdiscovery IS 'Discovery';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdiscoverywellbore IS 'Discovery wellbore';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbkellybushelevation IS 'Kelly bushing elevation [m]';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbfinalverticaldepth IS 'Final vertical depth (TVD) [m RKB]';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbtotaldepth IS 'Total depth (MD) [m RKB]';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbwaterdepth IS 'Water depth [m]';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbmainarea IS 'Main area';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdrillingfacility IS 'Drilling facility';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbfacilitytypedrilling IS 'Facility type, drilling';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbproductionfacility IS 'Production facility';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlblicensingactivity IS 'Licensing activity awarded in';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbmultilateral IS 'Multilateral';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbcontentplanned IS 'Content - planned';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbentryyear IS 'Entry year';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbcompletionyear IS 'Completion year';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbreclassfromwellbore IS 'Reclassified from wellbore';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbplotsymbol IS 'Plot symbol';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbgeodeticdatum IS 'Geodetic datum';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnsdeg IS 'NS degrees';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnsmin IS 'NS minutes';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnssec IS 'NS seconds';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnscode IS 'NS code';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbewdeg IS 'EW degrees';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbewmin IS 'EW minutes';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbewsec IS 'EW seconds';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbewcode IS 'EW code';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnsdecdeg IS 'NS decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbewdesdeg IS 'EW decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnsutm IS 'NS UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbewutm IS 'EW UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbutmzone IS 'UTM zone';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnamepart1 IS 'Wellbore name, part 1';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnamepart2 IS 'Wellbore name, part 2';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnamepart3 IS 'Wellbore name, part 3';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnamepart4 IS 'Wellbore name, part 4';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnamepart5 IS 'Wellbore name, part 5';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnamepart6 IS 'Wellbore name, part 6';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbfactpageurl IS 'FactPage url';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbfactmapurl IS 'FactMap url';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdiskoswellboretype IS 'DISKOS Well Type';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdiskoswellboreparent IS 'DISKOS Wellbore Parent';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_development_all.dscnpdiddiscovery IS 'NPDID discovery';

--
--

COMMENT ON COLUMN public.wellbore_development_all.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.wellbore_development_all.prlnpdidproductionlicence IS 'NPDID production licence drilled in';

--
--

COMMENT ON COLUMN public.wellbore_development_all.fclnpdidfacilitydrilling IS 'NPDID drilling facility';

--
--

COMMENT ON COLUMN public.wellbore_development_all.fclnpdidfacilityproducing IS 'NPDID production facility';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbnpdidwellborereclass IS 'NPDID wellbore reclassified from';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdiskoswelloperator IS 'DISKOS well operator';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdateupdated IS 'Date main level updated';

--
--

COMMENT ON COLUMN public.wellbore_development_all.wlbdateupdatedmax IS 'Date all updated';

--
--

CREATE TABLE public.wellbore_document (
    wlbname character varying(60) NOT NULL,
    wlbdocumenttype character varying(40) NOT NULL,
    wlbdocumentname character varying(200) NOT NULL,
    wlbdocumenturl character varying(200) NOT NULL,
    wlbdocumentformat character varying(40) NOT NULL,
    wlbdocumentsize numeric(13,6) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbdocumentdateupdated date,
    datesyncnpd date NOT NULL,
    wellbore_document_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_document.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_document.wlbdocumenttype IS 'Document type';

--
--

COMMENT ON COLUMN public.wellbore_document.wlbdocumentname IS 'Document name';

--
--

COMMENT ON COLUMN public.wellbore_document.wlbdocumenturl IS 'Document URL';

--
--

COMMENT ON COLUMN public.wellbore_document.wlbdocumentformat IS 'Document format';

--
--

COMMENT ON COLUMN public.wellbore_document.wlbdocumentsize IS 'Document size [MB]';

--
--

COMMENT ON COLUMN public.wellbore_document.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_document.wlbdocumentdateupdated IS 'Date updated';

--
--

CREATE SEQUENCE public.wellbore_document_wellbore_document_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.wellbore_document_wellbore_document_id_seq OWNED BY public.wellbore_document.wellbore_document_id;

--
--

CREATE TABLE public.wellbore_dst (
    wlbname character varying(60) NOT NULL,
    wlbdsttestnumber numeric(13,6) NOT NULL,
    wlbdstfromdepth numeric(13,6) NOT NULL,
    wlbdsttodepth numeric(13,6) NOT NULL,
    wlbdstchokesize numeric(13,6) NOT NULL,
    wlbdstfinshutinpress numeric(13,6) NOT NULL,
    wlbdstfinflowpress numeric(13,6) NOT NULL,
    wlbdstbottomholepress numeric(13,6) NOT NULL,
    wlbdstoilprod bigint NOT NULL,
    wlbdstgasprod bigint NOT NULL,
    wlbdstoildensity numeric(13,6) NOT NULL,
    wlbdstgasdensity numeric(13,6) NOT NULL,
    wlbdstgasoilrelation bigint NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbdstdateupdated date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdsttestnumber IS 'Test number';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstfromdepth IS 'From depth MD [m]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdsttodepth IS 'To depth MD [m]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstchokesize IS 'Choke size [mm]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstfinshutinpress IS 'Final shut-in pressure [MPa]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstfinflowpress IS 'Final flow pressure [MPa]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstbottomholepress IS 'Bottom hole pressure [MPa]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstoilprod IS 'Oil [Sm3/day]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstgasprod IS 'Gas [Sm3/day]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstoildensity IS 'Oil density [g/cm3]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstgasdensity IS 'Gas grav. rel.air';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstgasoilrelation IS 'GOR [m3/m3]';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_dst.wlbdstdateupdated IS 'Date updated';

--
--

CREATE TABLE public.wellbore_exploration_all (
    wlbwellborename character varying(40) NOT NULL,
    wlbwell character varying(40) NOT NULL,
    wlbdrillingoperator character varying(60) NOT NULL,
    wlbdrillingoperatorgroup character varying(20) NOT NULL,
    wlbproductionlicence character varying(40) NOT NULL,
    wlbpurpose character varying(40) NOT NULL,
    wlbstatus character varying(40),
    wlbcontent character varying(40),
    wlbwelltype character varying(20) NOT NULL,
    wlbentrydate date,
    wlbcompletiondate date,
    wlbfield character varying(40),
    wlbdrillpermit character varying(10) NOT NULL,
    wlbdiscovery character varying(40),
    wlbdiscoverywellbore character varying(3) NOT NULL,
    wlbbottomholetemperature bigint,
    wlbseismiclocation character varying(200),
    wlbmaxinclation numeric(6,2),
    wlbkellybushelevation numeric(13,6) NOT NULL,
    wlbfinalverticaldepth numeric(6,2),
    wlbtotaldepth numeric(13,6) NOT NULL,
    wlbwaterdepth numeric(13,6) NOT NULL,
    wlbageattd character varying(40),
    wlbformationattd character varying(40),
    wlbmainarea character varying(40) NOT NULL,
    wlbdrillingfacility character varying(50) NOT NULL,
    wlbfacilitytypedrilling character varying(40) NOT NULL,
    wlblicensingactivity character varying(40) NOT NULL,
    wlbmultilateral character varying(3) NOT NULL,
    wlbpurposeplanned character varying(40) NOT NULL,
    wlbentryyear bigint NOT NULL,
    wlbcompletionyear bigint NOT NULL,
    wlbreclassfromwellbore character varying(40),
    wlbreentryexplorationactivity character varying(40),
    wlbplotsymbol bigint NOT NULL,
    wlbformationwithhc1 character varying(20),
    wlbagewithhc1 character varying(20),
    wlbformationwithhc2 character varying(20),
    wlbagewithhc2 character varying(20),
    wlbformationwithhc3 character varying(20),
    wlbagewithhc3 character(20),
    wlbdrillingdays bigint NOT NULL,
    wlbreentry character varying(3) NOT NULL,
    wlbgeodeticdatum character varying(6),
    wlbnsdeg bigint NOT NULL,
    wlbnsmin bigint NOT NULL,
    wlbnssec numeric(6,2) NOT NULL,
    wlbnscode character varying(1) NOT NULL,
    wlbewdeg bigint NOT NULL,
    wlbewmin bigint NOT NULL,
    wlbewsec numeric(6,2) NOT NULL,
    wlbewcode character varying(1) NOT NULL,
    wlbnsdecdeg numeric(13,6) NOT NULL,
    wlbewdesdeg numeric(13,6) NOT NULL,
    wlbnsutm numeric(13,6) NOT NULL,
    wlbewutm numeric(13,6) NOT NULL,
    wlbutmzone bigint NOT NULL,
    wlbnamepart1 bigint NOT NULL,
    wlbnamepart2 bigint NOT NULL,
    wlbnamepart3 character varying(1),
    wlbnamepart4 bigint NOT NULL,
    wlbnamepart5 character varying(2),
    wlbnamepart6 character varying(2),
    wlbpressreleaseurl character varying(200),
    wlbfactpageurl character varying(200) NOT NULL,
    wlbfactmapurl character varying(200) NOT NULL,
    wlbdiskoswellboretype character varying(20) NOT NULL,
    wlbdiskoswellboreparent character varying(40),
    wlbwdssqcdate date,
    wlbnpdidwellbore bigint NOT NULL,
    dscnpdiddiscovery bigint,
    fldnpdidfield bigint,
    fclnpdidfacilitydrilling bigint NOT NULL,
    wlbnpdidwellborereclass bigint NOT NULL,
    prlnpdidproductionlicence bigint NOT NULL,
    wlbdiskoswelloperator character varying(40) NOT NULL,
    wlbdateupdated date NOT NULL,
    wlbdateupdatedmax date NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbwellborename IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbwell IS 'Well name';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdrillingoperator IS 'Drilling operator';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdrillingoperatorgroup IS 'Drilling operator group';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbproductionlicence IS 'Drilled in production licence';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbpurpose IS 'Purpose';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbstatus IS 'Status';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbcontent IS 'Content';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbwelltype IS 'Type';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbentrydate IS 'Entry date';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbfield IS 'Field';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdrillpermit IS 'Drill permit';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdiscovery IS 'Discovery';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdiscoverywellbore IS 'Discovery wellbore';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbbottomholetemperature IS 'Bottom hole temperature [°C]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbseismiclocation IS 'Seismic location';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbmaxinclation IS 'Maximum inclination [°]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbkellybushelevation IS 'Kelly bushing elevation [m]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbfinalverticaldepth IS 'Final vertical depth (TVD) [m RKB]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbtotaldepth IS 'Total depth (MD) [m RKB]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbwaterdepth IS 'Water depth [m]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbageattd IS 'Oldest penetrated age';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbformationattd IS 'Oldest penetrated formation';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbmainarea IS 'Main area';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdrillingfacility IS 'Drilling facility';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbfacilitytypedrilling IS 'Facility type, drilling';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlblicensingactivity IS 'Licensing activity awarded in';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbmultilateral IS 'Multilateral';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbpurposeplanned IS 'Purpose - planned';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbentryyear IS 'Entry year';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbcompletionyear IS 'Completion year';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbreclassfromwellbore IS 'Reclassified from wellbore';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbreentryexplorationactivity IS 'Reentry activity';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbplotsymbol IS 'Plot symbol';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbformationwithhc1 IS '1st level with HC, formation';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbagewithhc1 IS '1st level with HC, age';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbformationwithhc2 IS '2nd level with HC, formation';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbagewithhc2 IS '2nd level with HC, age';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbformationwithhc3 IS '3rd level with HC, formation';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbagewithhc3 IS '3rd level with HC, age';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdrillingdays IS 'Drilling days';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbreentry IS 'Reentry';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbgeodeticdatum IS 'Geodetic datum';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnsdeg IS 'NS degrees';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnsmin IS 'NS minutes';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnssec IS 'NS seconds';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnscode IS 'NS code';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbewdeg IS 'EW degrees';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbewmin IS 'EW minutes';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbewsec IS 'EW seconds';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbewcode IS 'EW code';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnsdecdeg IS 'NS decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbewdesdeg IS 'EW decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnsutm IS 'NS UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbewutm IS 'EW UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbutmzone IS 'UTM zone';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnamepart1 IS 'Wellbore name, part 1';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnamepart2 IS 'Wellbore name, part 2';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnamepart3 IS 'Wellbore name, part 3';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnamepart4 IS 'Wellbore name, part 4';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnamepart5 IS 'Wellbore name, part 5';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnamepart6 IS 'Wellbore name, part 6';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbfactpageurl IS 'FactPage url';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbfactmapurl IS 'FactMap url';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdiskoswellboretype IS 'DISKOS Well Type';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdiskoswellboreparent IS 'DISKOS Wellbore Parent';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbwdssqcdate IS 'WDSS QC date';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.dscnpdiddiscovery IS 'NPDID discovery';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.fldnpdidfield IS 'NPDID field';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.fclnpdidfacilitydrilling IS 'NPDID drilling facility';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbnpdidwellborereclass IS 'NPDID wellbore reclassified from';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.prlnpdidproductionlicence IS 'NPDID production licence drilled in';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdiskoswelloperator IS 'DISKOS well operator';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdateupdated IS 'Date main level updated';

--
--

COMMENT ON COLUMN public.wellbore_exploration_all.wlbdateupdatedmax IS 'Date all updated';

--
--

CREATE TABLE public.wellbore_formation_top (
    wlbname character varying(60) NOT NULL,
    lsutopdepth numeric(13,6) NOT NULL,
    lsubottomdepth numeric(13,6) NOT NULL,
    lsuname character varying(20) NOT NULL,
    lsulevel character varying(9) NOT NULL,
    lsunameparent character varying(20),
    wlbnpdidwellbore bigint NOT NULL,
    lsunpdidlithostrat bigint NOT NULL,
    lsunpdidlithostratparent bigint,
    lsuwellboreupdateddate date,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_formation_top.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsutopdepth IS 'Top depth [m]';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsubottomdepth IS 'Bottom depth [m]';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsuname IS 'Lithostrat. unit';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsulevel IS 'Level';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsunameparent IS 'Lithostrat. unit, parent';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsunpdidlithostrat IS 'NPDID lithostrat. unit';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsunpdidlithostratparent IS 'NPDID parent lithostrat. unit';

--
--

COMMENT ON COLUMN public.wellbore_formation_top.lsuwellboreupdateddate IS 'Date updated';

--
--

CREATE TABLE public.wellbore_mud (
    wlbname character varying(60) NOT NULL,
    wlbmd numeric(13,6) NOT NULL,
    wlbmudweightatmd numeric(13,6) NOT NULL,
    wlbmudviscosityatmd numeric(13,6) NOT NULL,
    wlbyieldpointatmd numeric(13,6) NOT NULL,
    wlbmudtype character varying(40),
    wlbmuddatemeasured date,
    wlbnpdidwellbore bigint NOT NULL,
    wlbmuddateupdated date,
    datesyncnpd date NOT NULL,
    wellbore_mud_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbmd IS 'Depth MD [m]';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbmudweightatmd IS 'Mud weight [g/cm3]';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbmudviscosityatmd IS 'Visc. [mPa.s]';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbyieldpointatmd IS 'Yield point [Pa]';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbmudtype IS 'Mud type';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbmuddatemeasured IS 'Date measured';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_mud.wlbmuddateupdated IS 'Date updated';

--
--

CREATE SEQUENCE public.wellbore_mud_wellbore_mud_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.wellbore_mud_wellbore_mud_id_seq OWNED BY public.wellbore_mud.wellbore_mud_id;

--
--

CREATE TABLE public.wellbore_npdid_overview (
    wlbwellborename character varying(40) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbwell character varying(40) NOT NULL,
    wlbwelltype character varying(20),
    datesyncnpd date NOT NULL,
    UNIQUE (wlbnpdidwellbore)
);

--
--

COMMENT ON COLUMN public.wellbore_npdid_overview.wlbwellborename IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_npdid_overview.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_npdid_overview.wlbwell IS 'Well name';

--
--

COMMENT ON COLUMN public.wellbore_npdid_overview.wlbwelltype IS 'Type';

--
--

CREATE TABLE public.wellbore_oil_sample (
    wlbname character varying(60) NOT NULL,
    wlboilsampletesttype character varying(4),
    wlboilsampletestnumber character varying(10),
    wlboilsampletopdepth numeric(13,6) NOT NULL,
    wlboilsamplebottomdepth numeric(13,6) NOT NULL,
    wlboilsamplefluidtype character varying(20),
    wlboilsampletestdate date,
    wlboilsampledatereceiveddate date,
    wlbnpdidwellbore bigint NOT NULL,
    wlboilsampledateupdated date,
    datesyncnpd date NOT NULL,
    wellbore_oil_sample_id bigint NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlbname IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsampletesttype IS 'Test type';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsampletestnumber IS 'Bottle test number';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsampletopdepth IS 'Top depth MD [m]';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsamplebottomdepth IS 'Bottom depth MD [m]';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsamplefluidtype IS 'Fluid type';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsampletestdate IS 'Test date and time of day';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsampledatereceiveddate IS 'Received date';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_oil_sample.wlboilsampledateupdated IS 'Date updated';

--
--

CREATE SEQUENCE public.wellbore_oil_sample_wellbore_oil_sample_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
--

ALTER SEQUENCE public.wellbore_oil_sample_wellbore_oil_sample_id_seq OWNED BY public.wellbore_oil_sample.wellbore_oil_sample_id;

--
--

CREATE TABLE public.wellbore_shallow_all (
    wlbwellborename character varying(40) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbwell character varying(40) NOT NULL,
    wlbdrillingoperator character varying(60) NOT NULL,
    wlbproductionlicence character varying(40),
    wlbdrillingfacility character varying(50),
    wlbentrydate date,
    wlbcompletiondate date,
    wlbdrillpermit character varying(10) NOT NULL,
    wlbtotaldepth numeric(13,6) NOT NULL,
    wlbwaterdepth numeric(13,6) NOT NULL,
    wlbmainarea character varying(40) NOT NULL,
    wlbentryyear bigint NOT NULL,
    wlbcompletionyear bigint NOT NULL,
    wlbseismiclocation character varying(200),
    wlbgeodeticdatum character varying(6),
    wlbnsdeg bigint NOT NULL,
    wlbnsmin bigint NOT NULL,
    wlbnssec numeric(6,2) NOT NULL,
    wlbnscode character varying(1),
    wlbewdeg bigint NOT NULL,
    wlbewmin bigint NOT NULL,
    wlbewsec numeric(6,2) NOT NULL,
    wlbewcode character varying(1),
    wlbnsdecdeg numeric(13,6) NOT NULL,
    wlbewdesdeg numeric(13,6) NOT NULL,
    wlbnsutm numeric(13,6) NOT NULL,
    wlbewutm numeric(13,6) NOT NULL,
    wlbutmzone bigint NOT NULL,
    wlbnamepart1 bigint NOT NULL,
    wlbnamepart2 bigint NOT NULL,
    wlbnamepart3 character varying(1) NOT NULL,
    wlbnamepart4 bigint NOT NULL,
    wlbnamepart5 character varying(2),
    wlbnamepart6 character varying(2),
    wlbdateupdated date NOT NULL,
    wlbdateupdatedmax date NOT NULL,
    datesyncnpd date NOT NULL
);

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbwellborename IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbwell IS 'Well name';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbdrillingoperator IS 'Drilling operator';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbproductionlicence IS 'Drilled in production licence';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbdrillingfacility IS 'Drilling facility';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbentrydate IS 'Entry date';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbdrillpermit IS 'Drill permit';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbtotaldepth IS 'Total depth (MD) [m RKB]';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbwaterdepth IS 'Water depth [m]';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbmainarea IS 'Main area';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbentryyear IS 'Entry year';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbcompletionyear IS 'Completion year';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbseismiclocation IS 'Seismic location';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbgeodeticdatum IS 'Geodetic datum';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnsdeg IS 'NS degrees';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnsmin IS 'NS minutes';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnssec IS 'NS seconds';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnscode IS 'NS code';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbewdeg IS 'EW degrees';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbewmin IS 'EW minutes';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbewsec IS 'EW seconds';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbewcode IS 'EW code';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnsdecdeg IS 'NS decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbewdesdeg IS 'EW decimal degrees';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnsutm IS 'NS UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbewutm IS 'EW UTM [m]';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbutmzone IS 'UTM zone';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnamepart1 IS 'Wellbore name, part 1';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnamepart2 IS 'Wellbore name, part 2';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnamepart3 IS 'Wellbore name, part 3';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnamepart4 IS 'Wellbore name, part 4';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnamepart5 IS 'Wellbore name, part 5';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbnamepart6 IS 'Wellbore name, part 6';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbdateupdated IS 'Date main level updated';

--
--

COMMENT ON COLUMN public.wellbore_shallow_all.wlbdateupdatedmax IS 'Date all updated';

--
--

CREATE TABLE public.wlbpoint (
    wlbnpdidwellbore bigint NOT NULL,
    wlbwellname character varying(40) NOT NULL,
    wlbwellborename character varying(40) NOT NULL,
    wlbfield character varying(40),
    wlbproductionlicence character varying(40),
    wlbwelltype character varying(20),
    wlbdrillingoperator character varying(60) NOT NULL,
    wlbmultilateral character varying(3) NOT NULL,
    wlbdrillingfacility character varying(50),
    wlbproductionfacility character varying(50),
    wlbentrydate date,
    wlbcompletiondate date,
    wlbcontent character varying(40),
    wlbstatus character varying(40),
    wlbsymbol bigint NOT NULL,
    wlbpurpose character varying(40),
    wlbwaterdepth numeric(13,6) NOT NULL,
    wlbfactpageurl character varying(200),
    wlbfactmapurl character varying(200),
    wlbdiscoverywellbore character varying(3) NOT NULL,
    wlbpointgeometrywkt point NOT NULL
);

--
--

COMMENT ON COLUMN public.wlbpoint.wlbnpdidwellbore IS 'NPDID wellbore';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbwellborename IS 'Wellbore name';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbfield IS 'Field';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbproductionlicence IS 'Drilled in production licence';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbwelltype IS 'Type';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbdrillingoperator IS 'Drilling operator';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbmultilateral IS 'Multilateral';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbdrillingfacility IS 'Drilling facility';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbproductionfacility IS 'Production facility';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbentrydate IS 'Entry date';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbcompletiondate IS 'Completion date';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbcontent IS 'Content';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbstatus IS 'Status';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbpurpose IS 'Purpose';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbwaterdepth IS 'Water depth [m]';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbfactpageurl IS 'FactPage url';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbfactmapurl IS 'FactMap url';

--
--

COMMENT ON COLUMN public.wlbpoint.wlbdiscoverywellbore IS 'Discovery wellbore';

--
--

ALTER TABLE ONLY public.apaareagross ALTER COLUMN apaareagross_id SET DEFAULT nextval('public.apaareagross_apaareagross_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.apaareanet ALTER COLUMN apaareanet_id SET DEFAULT nextval('public.apaareanet_apaareanet_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.prlarea ALTER COLUMN prlarea_id SET DEFAULT nextval('public.prlarea_prlarea_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.seaarea ALTER COLUMN seaarea_id SET DEFAULT nextval('public.seaarea_seaarea_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.seis_acquisition_progress ALTER COLUMN seis_acquisition_progress_id SET DEFAULT nextval('public.seis_acquisition_progress_seis_acquisition_progress_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.wellbore_casing_and_lot ALTER COLUMN wellbore_casing_and_lot_id SET DEFAULT nextval('public.wellbore_casing_and_lot_wellbore_casing_and_lot_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.wellbore_core ALTER COLUMN wellbore_core_id SET DEFAULT nextval('public.wellbore_core_wellbore_core_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.wellbore_core_photo ALTER COLUMN wellbore_core_photo_id SET DEFAULT nextval('public.wellbore_core_photo_wellbore_core_photo_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.wellbore_document ALTER COLUMN wellbore_document_id SET DEFAULT nextval('public.wellbore_document_wellbore_document_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.wellbore_mud ALTER COLUMN wellbore_mud_id SET DEFAULT nextval('public.wellbore_mud_wellbore_mud_id_seq'::regclass);

--
--

ALTER TABLE ONLY public.wellbore_oil_sample ALTER COLUMN wellbore_oil_sample_id SET DEFAULT nextval('public.wellbore_oil_sample_wellbore_oil_sample_id_seq'::regclass);

--
--

--
--
--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

Ekofisk Z, a production facility, and Ekofisk VB, a subsea template for water injection wells.', 43506, '2013-05-01');
one for oil and one for rich gas.', 18116481, '2013-05-08');
--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

12 m tow depth', 'Noder', 'Max. 800', 'Size of NODE assembly is 1 m  x 1m', '2011-08-01', '2011-08-23', '2011-10-01', '2011-09-05', 5000, 4000, 4000, 555, 3406.720000, 'Område unntatt snuområde', 2385, '0103000020E61000000100000005000000000000000000FC3F0000000000E04F40000000000000FC3F00000000001050400000000000000840000000000010504000000000000008400000000000E04F40000000000000FC3F0000000000E04F40');
12 m tow depth', 'Noder', 'Max. 800', 'Size of NODE assembly is 1 m  x 1m', '2011-08-01', '2011-08-23', '2011-10-01', '2011-09-05', 5000, 4000, 4000, 555, 3406.720000, 'Område inkludert snuområde', 2386, '0103000020E61000000100000005000000AE282504ABAAFA3F4529215855D54F40AE282504ABAAFA3F5D6BEF5355155040A96BED7DAAAA08405D6BEF5355155040A96BED7DAAAA08404529215855D54F40AE282504ABAAFA3F4529215855D54F40');
--
--

--
--

--
--

--
--

Anmodning om forlenget innsamlings periode. Sluttdato var satt til 16 Mai, vi er heldige om vi  klarer å begynne til denne dato. Ny slutt dato er nå satt til 19 Juni.Justering av antall linje kilometer fra ca. 350 til ca. 380 km.Informasjon om Fiskerikyndig og Utvinningstillatelser oppdatert.Det vil sannsynligvis bli fartøyet M/V ''Sea Explorer'' som kommer til å samle inn ST13304 Undersøkelsen.Utover dette, Ingen endringer.', 7803, 43);
Anmodning om forlenget innsamlings periode. Sluttdato var satt til 16 Mai, vi er heldige om vi  klarer å begynne til denne dato. Ny slutt dato er nå satt til 19 Juni.Justering av antall linje kilometer fra ca. 350 til ca. 380 km.Informasjon om Fiskerikyndig og Utvinningstillatelser oppdatert.Det vil sannsynligvis bli fartøyet M/V ''Sea Explorer'' som kommer til å samle inn ST13304 Undersøkelsen.Utover dette, Ingen endringer.', 7803, 47);
1. Noen biter av linjene i øst gikk utover først oppgitte netto område2. Området noe utvidet i sørøst,vi ønsker å samle inn noe mer Multistråle Ekkolodd data her.3. Noen seismikk linjer er lagt til, undersøkelsen er øket med ca. 260 km seismikk, 30 km med vanlig site survey kilde 160 kubikk tommer, og 230 km med en liten kilde på 10 kubikk tommer, UHRS data (Ultra High Resolution )4. Sålangt en lite produktiv start, vi antar at vi derfor kommer til å holde på noe lenger enn 23 mai. Vi anmoder derfor om en forlenget innsamlings periode til 7 Juni.Vi holder oss til den tillatelsen vi har inntil vi har fått et OK for denne endrings melding.', 7795, 100);
Vi anmoder om en forlenget tidsperiode da arbeidet i bBarentsahvet har tatt noe lenger tid enn beregnet. I tillegg vi har noen arebeider på Midt-Norge som vi trenger å få utført med M/V ''Sea Explorer''. I tillegg har satt netto og brutto Områder like.', 7619, 1773);
Vi anmoder om en forlenget tidsperiode da arbeidet i bBarentsahvet har tatt noe lenger tid enn beregnet. I tillegg vi har noen arebeider på Midt-Norge som vi trenger å få utført med M/V ''Sea Explorer''. I tillegg har satt netto og brutto Områder like.', 7619, 1776);
Leiv R. Stensen erstatter Marisol Montoya. Utover dette, ingen endringer.', 7572, 2169);
justering av survey linjer innenfor området', 7580, 2354);
Statoil ønsker å forlenge tidsperioden for innsamling av denne undersøkelsen til 19 April. I tillegg har leiv R. Stensen erstattet Marisol Montoya som en av våre kontakt personer. Utover dette er det ingen endringer.', 7574, 2406);
Vi har endret litt på området, og gitt netto område (hvor vi bruker luft kanoner) og brutto området (inkludert snuing av fartøy).Vi har bedt om endret innsamlings periode, siden vi ligger litt på etterskudd med det vi hadde håpet å klare. Så ny avslutnings dato er 24 Mars.En ny kontakt person.', 7551, 2489);
1. Grunnet ugunstig vær, anmoder vi om forlenget innsamlingsperiode til 27 mars. Vi har enda ikke fått startet på denne undersøkelsen.2. Leiv R. Stensen erstatter Marisol Montoya som en av kontaktpersonene for undersøkelsen.Utover dette, ingen endringer.', 7546, 2503);
1.Slik værmeldingen er for den nære fremtid; Ser det ikke ut til at vi vil kunne avslutte Borestedsundersøkelse ST11313 den 23. Februar slik vi hadde håpet. Statoil anmoder derfor om å få holde på med ST11313 innsamlingen til 13 Mars.2. Leif R. Stensen overtar som av kontaktperson etter Marisol Montoya3. Ny fiskerikyndig er ombord.', 7536, 2507);
Vi har endret litt på området, og gitt netto område (hvor vi bruker luft kanoner) og brutto området (inkludert snuing av fartøy).Vi har bedt om endret innsamlings periode, siden vi ligger litt på etterskudd med det vi hadde håpet å klare. Så ny avslutnings dato er 24 Mars.En ny kontakt person.', 7551, 2513);
switched temporarily back to NATS before weather put both vessels on standby. Back on WATS acquisition starting today (after this reporting period)', 7420, 3354);
samt redusert antall kabler fra 12 til 10.', 7466, 3516);
in good communication, generally keeping out of the way', 7420, 3642);
Det var usikkerhet rundt lokasjonen som gjør at vi sender endringsmelding, på ny lokasjon. Ny antatt oppstarts dato.', 7462, 3755);
Det er ønske om å samle inn noen seismiske linjer for et par ekstra Avlastingsbrønner til Template H på Vigdis Nordøst. Derfor har vi lagt til noen linjer til dette programmet, slik at området blir noe større og antall km øker med ca. 50 kilometer. Vi kommer sannsynligvis til å starte opp denne undersøkelsen i neste uke, og da bruker vi den tillatelsen vi allerede har fått. Det er stort sett bare noen linje biter som gjør at området må utvides noe for run in og out. Slik det ser ut nå, vil vi mobilisere i Hull, og er nok ikke i Blokk 34/7 før om 8-9 dager.', 7374, 4156);
endring av båt;endring av feskerikundige', 7209, 4573);
endring av båt;endring av feskerikundige', 7209, 4574);
Antall km økes, og vi skifter til et fartøy vi kan få ganske snart.', 7355, 4641);
Siden det er mye som haster så samler vi inn de viktigste linjene av Undersøkelse ST10308 i Blokk 15/8. Deretter steamer vi til Blokk 6407/8 for å samle inn Borestedsundersøkelse ST10306 i Blokk 6407/8. Det gjenværende for undersøkelse ST10308 gjøres når det er gitt tillatelse fra britiske myndigheter og lisenser.', 7275, 5121);
1. Tidperiode, pga gytetid2. Endring av innsamlingsfartøy', 7204, 6062);
endring av båt;endring av feskerikundige', 7209, 6084);
--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

--
--

DG0902-108-411 SP370', 'ED50', 56, 55, 53.62, 'N', 2, 40, 16.30, 'E', 56.931600, 2.671200, 6309957.000000, 479988.170000, 31, 1, 3, 'U', 15, NULL, NULL, '2012-07-25', '2012-07-25', '2013-05-08');
DG0902-108-411 SP370', 'ED50', 56, 55, 53.46, 'N', 2, 40, 16.36, 'E', 56.931500, 2.671200, 6309952.050000, 479989.160000, 31, 1, 3, 'U', 16, NULL, NULL, '2012-07-25', '2012-07-25', '2013-05-08');
--
--

--
-- PostgreSQL database dump complete
--

ALTER TABLE ONLY public.apaareagross
    ADD CONSTRAINT "apaAreaGross_pkey" PRIMARY KEY (apaareagross_id);
ALTER TABLE ONLY public.apaareanet
    ADD CONSTRAINT "apaAreaNet_pkey" PRIMARY KEY (apaareanet_id, qdrname, blkname, prvname, blkid);
ALTER TABLE ONLY public.baaarea
    ADD CONSTRAINT "baaArea_pkey" PRIMARY KEY (baanpdidbsnsarrarea, baanpdidbsnsarrareapoly);
ALTER TABLE ONLY public.bsns_arr_area_area_poly_hst
    ADD CONSTRAINT bsns_arr_area_area_poly_hst_pkey PRIMARY KEY (baanpdidbsnsarrarea, baaareapolyblockname, baaareapolyno, baaareapolydatevalidfrom, baaareapolydatevalidto);
ALTER TABLE ONLY public.bsns_arr_area_licensee_hst
    ADD CONSTRAINT bsns_arr_area_licensee_hst_pkey PRIMARY KEY (baanpdidbsnsarrarea, cmpnpdidcompany, baalicenseedatevalidfrom, baalicenseedatevalidto);
ALTER TABLE ONLY public.bsns_arr_area_operator
    ADD CONSTRAINT bsns_arr_area_operator_pkey PRIMARY KEY (baanpdidbsnsarrarea);
ALTER TABLE ONLY public.bsns_arr_area
    ADD CONSTRAINT bsns_arr_area_pkey PRIMARY KEY (baanpdidbsnsarrarea);
ALTER TABLE ONLY public.bsns_arr_area_transfer_hst
    ADD CONSTRAINT bsns_arr_area_transfer_hst_pkey PRIMARY KEY (baanpdidbsnsarrarea, baatransferdirection, cmpnpdidcompany, baatransferdatevalidfrom);
ALTER TABLE ONLY public.company
    ADD CONSTRAINT company_pkey PRIMARY KEY (cmpnpdidcompany);
ALTER TABLE ONLY public.company_reserves
    ADD CONSTRAINT company_reserves_pkey PRIMARY KEY (cmpnpdidcompany, fldnpdidfield);
ALTER TABLE ONLY public.discovery
    ADD CONSTRAINT discovery_pkey PRIMARY KEY (dscnpdiddiscovery);
ALTER TABLE ONLY public.discovery_reserves
    ADD CONSTRAINT discovery_reserves_pkey PRIMARY KEY (dscnpdiddiscovery, dscreservesrc);
ALTER TABLE ONLY public.dscarea
    ADD CONSTRAINT "dscArea_pkey" PRIMARY KEY (dscnpdiddiscovery, dschctype);
ALTER TABLE ONLY public.facility_fixed
    ADD CONSTRAINT facility_fixed_pkey PRIMARY KEY (fclnpdidfacility);
ALTER TABLE ONLY public.facility_moveable
    ADD CONSTRAINT facility_moveable_pkey PRIMARY KEY (fclnpdidfacility);
ALTER TABLE ONLY public.fclpoint
    ADD CONSTRAINT "fclPoint_pkey" PRIMARY KEY (fclnpdidfacility);
ALTER TABLE ONLY public.field_activity_status_hst
    ADD CONSTRAINT field_activity_status_hst_pkey PRIMARY KEY (fldnpdidfield, fldstatus, fldstatusfromdate, fldstatustodate);
ALTER TABLE ONLY public.field_description
    ADD CONSTRAINT field_description_pkey PRIMARY KEY (fldnpdidfield, flddescriptionheading);
ALTER TABLE ONLY public.field_investment_yearly
    ADD CONSTRAINT field_investment_yearly_pkey PRIMARY KEY (prfnpdidinformationcarrier, prfyear);
ALTER TABLE ONLY public.field_licensee_hst
    ADD CONSTRAINT field_licensee_hst_pkey PRIMARY KEY (fldnpdidfield, cmpnpdidcompany, fldlicenseefrom, fldlicenseeto);
ALTER TABLE ONLY public.field_operator_hst
    ADD CONSTRAINT field_operator_hst_pkey PRIMARY KEY (fldnpdidfield, cmpnpdidcompany, fldoperatorfrom, fldoperatorto);
ALTER TABLE ONLY public.field_owner_hst
    ADD CONSTRAINT field_owner_hst_pkey PRIMARY KEY (fldnpdidfield, fldnpdidowner, fldownershipfromdate, fldownershiptodate);
ALTER TABLE ONLY public.field
    ADD CONSTRAINT field_pkey PRIMARY KEY (fldnpdidfield);
ALTER TABLE ONLY public.field_production_monthly
    ADD CONSTRAINT field_production_monthly_pkey PRIMARY KEY (prfnpdidinformationcarrier, prfyear, prfmonth);
ALTER TABLE ONLY public.field_production_totalt_ncs_month
    ADD CONSTRAINT "field_production_totalt_NCS_month_pkey" PRIMARY KEY (prfyear, prfmonth);
ALTER TABLE ONLY public.field_production_totalt_ncs_year
    ADD CONSTRAINT "field_production_totalt_NCS_year_pkey" PRIMARY KEY (prfyear);
ALTER TABLE ONLY public.field_production_yearly
    ADD CONSTRAINT field_production_yearly_pkey PRIMARY KEY (prfnpdidinformationcarrier, prfyear);
ALTER TABLE ONLY public.field_reserves
    ADD CONSTRAINT field_reserves_pkey PRIMARY KEY (fldnpdidfield);
ALTER TABLE ONLY public.fldarea
    ADD CONSTRAINT "fldArea_pkey" PRIMARY KEY (dscnpdiddiscovery, dschctype);
ALTER TABLE ONLY public.licence_area_poly_hst
    ADD CONSTRAINT licence_area_poly_hst_pkey PRIMARY KEY (prlnpdidlicence, prlareapolyblockname, prlareapolypolyno, prlareapolydatevalidfrom, prlareapolydatevalidto);
ALTER TABLE ONLY public.licence_licensee_hst
    ADD CONSTRAINT licence_licensee_hst_pkey PRIMARY KEY (prlnpdidlicence, cmpnpdidcompany, prllicenseedatevalidfrom, prllicenseedatevalidto);
ALTER TABLE ONLY public.licence_oper_hst
    ADD CONSTRAINT licence_oper_hst_pkey PRIMARY KEY (prlnpdidlicence, cmpnpdidcompany, prloperdatevalidfrom, prloperdatevalidto);
ALTER TABLE ONLY public.licence_petreg_licence_licencee
    ADD CONSTRAINT licence_petreg_licence_licencee_pkey PRIMARY KEY (prlnpdidlicence, cmpnpdidcompany);
ALTER TABLE ONLY public.licence_petreg_licence_oper
    ADD CONSTRAINT licence_petreg_licence_oper_pkey PRIMARY KEY (prlnpdidlicence);
ALTER TABLE ONLY public.licence_petreg_licence
    ADD CONSTRAINT licence_petreg_licence_pkey PRIMARY KEY (prlnpdidlicence);
ALTER TABLE ONLY public.licence_petreg_message
    ADD CONSTRAINT licence_petreg_message_pkey PRIMARY KEY (prlnpdidlicence, ptlmessagedocumentno);
ALTER TABLE ONLY public.licence_phase_hst
    ADD CONSTRAINT licence_phase_hst_pkey PRIMARY KEY (prlnpdidlicence, prlphase, prldatephasevalidfrom, prldatephasevalidto);
ALTER TABLE ONLY public.licence
    ADD CONSTRAINT licence_pkey PRIMARY KEY (prlnpdidlicence);
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT licence_task_pkey PRIMARY KEY (prlnpdidlicence, prltaskid);
ALTER TABLE ONLY public.licence_transfer_hst
    ADD CONSTRAINT licence_transfer_hst_pkey PRIMARY KEY (prlnpdidlicence, prltransferdirection, cmpnpdidcompany, prltransferdatevalidfrom);
ALTER TABLE ONLY public.pipline
    ADD CONSTRAINT "pipLine_pkey" PRIMARY KEY (pipnpdidpipe);
ALTER TABLE ONLY public.prlareasplitbyblock
    ADD CONSTRAINT "prlAreaSplitByBlock_pkey" PRIMARY KEY (prlnpdidlicence, blcname, prlareapolypolyno, prlareapolydatevalidfrom, prlareapolydatevalidto);
ALTER TABLE ONLY public.prlarea
    ADD CONSTRAINT "prlArea_pkey" PRIMARY KEY (prlarea_id, prlnpdidlicence, prlareapolydatevalidfrom, prlareapolydatevalidto);
ALTER TABLE ONLY public.seaarea
    ADD CONSTRAINT "seaArea_pkey" PRIMARY KEY (seaarea_id, seasurveyname);
ALTER TABLE ONLY public.seamultiline
    ADD CONSTRAINT "seaMultiline_pkey" PRIMARY KEY (seasurveyname);
ALTER TABLE ONLY public.seis_acquisition_coordinates_inc_turnarea
    ADD CONSTRAINT seis_acquisition_coordinates_inc_turnarea_pkey PRIMARY KEY (seasurveyname, seapolygonpointnumber);
ALTER TABLE ONLY public.seis_acquisition
    ADD CONSTRAINT seis_acquisition_pkey PRIMARY KEY (seanpdidsurvey, seaname);
ALTER TABLE ONLY public.seis_acquisition_progress
    ADD CONSTRAINT seis_acquisition_progress_pkey PRIMARY KEY (seis_acquisition_progress_id, seaprogresstext2);
ALTER TABLE ONLY public.strat_litho_wellbore_core
    ADD CONSTRAINT strat_litho_wellbore_core_pkey PRIMARY KEY (wlbnpdidwellbore, lsunpdidlithostrat);
ALTER TABLE ONLY public.strat_litho_wellbore
    ADD CONSTRAINT strat_litho_wellbore_pkey PRIMARY KEY (wlbnpdidwellbore, lsunpdidlithostrat, lsutopdepth, lsubottomdepth);
ALTER TABLE ONLY public.tuf_operator_hst
    ADD CONSTRAINT tuf_operator_hst_pkey PRIMARY KEY (tufnpdidtuf, cmpnpdidcompany, tufoperdatevalidfrom, tufoperdatevalidto);
ALTER TABLE ONLY public.tuf_owner_hst
    ADD CONSTRAINT tuf_owner_hst_pkey PRIMARY KEY (tufnpdidtuf, cmpnpdidcompany, tufownerdatevalidfrom, tufownerdatevalidto);
ALTER TABLE ONLY public.tuf_petreg_licence_licencee
    ADD CONSTRAINT tuf_petreg_licence_licencee_pkey PRIMARY KEY (tufnpdidtuf, cmpnpdidcompany);
ALTER TABLE ONLY public.tuf_petreg_licence_oper
    ADD CONSTRAINT tuf_petreg_licence_oper_pkey PRIMARY KEY (tufnpdidtuf);
ALTER TABLE ONLY public.tuf_petreg_licence
    ADD CONSTRAINT tuf_petreg_licence_pkey PRIMARY KEY (tufnpdidtuf);
ALTER TABLE ONLY public.tuf_petreg_message
    ADD CONSTRAINT tuf_petreg_message_pkey PRIMARY KEY (tufnpdidtuf, ptlmessagedocumentno);
ALTER TABLE ONLY public.bsns_arr_area
    ADD CONSTRAINT "uq_bsns_arr_area_baaNpdidBsnsArrArea" UNIQUE (baanpdidbsnsarrarea);
ALTER TABLE ONLY public.company
    ADD CONSTRAINT "uq_company_cmpLongName" UNIQUE (cmplongname);
ALTER TABLE ONLY public.company
    ADD CONSTRAINT "uq_company_cmpNpdidCompany" UNIQUE (cmpnpdidcompany);
ALTER TABLE ONLY public.company
    ADD CONSTRAINT "uq_company_cmpShortName" UNIQUE (cmpshortname);
ALTER TABLE ONLY public.discovery
    ADD CONSTRAINT "uq_discovery_dscNpdidDiscovery" UNIQUE (dscnpdiddiscovery);
ALTER TABLE ONLY public.facility_fixed
    ADD CONSTRAINT "uq_facility_fixed_fclNpdidFacility" UNIQUE (fclnpdidfacility);
ALTER TABLE ONLY public.field
    ADD CONSTRAINT "uq_field_fldNpdidField" UNIQUE (fldnpdidfield);
ALTER TABLE ONLY public.licence
    ADD CONSTRAINT "uq_licence_prlNpdidLicence" UNIQUE (prlnpdidlicence);
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT "uq_licence_task_prlTaskID" UNIQUE (prltaskid);
ALTER TABLE ONLY public.seis_acquisition
    ADD CONSTRAINT "uq_seis_acquisition_seaName" UNIQUE (seaname);
ALTER TABLE ONLY public.seis_acquisition
    ADD CONSTRAINT "uq_seis_acquisition_seaNpdidSurvey" UNIQUE (seanpdidsurvey);
ALTER TABLE ONLY public.tuf_petreg_licence
    ADD CONSTRAINT "uq_tuf_petreg_licence_tufNpdidTuf" UNIQUE (tufnpdidtuf);
ALTER TABLE ONLY public.wellbore_npdid_overview
    ADD CONSTRAINT "uq_wellbore_npdid_overview_wlbNpdidWellbore" UNIQUE (wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_casing_and_lot
    ADD CONSTRAINT wellbore_casing_and_lot_pkey PRIMARY KEY (wellbore_casing_and_lot_id, wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_coordinates
    ADD CONSTRAINT wellbore_coordinates_pkey PRIMARY KEY (wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_core_photo
    ADD CONSTRAINT wellbore_core_photo_pkey PRIMARY KEY (wellbore_core_photo_id, wlbnpdidwellbore, wlbcorenumber, wlbcorephototitle);
ALTER TABLE ONLY public.wellbore_core
    ADD CONSTRAINT wellbore_core_pkey PRIMARY KEY (wellbore_core_id, wlbnpdidwellbore, wlbcorenumber);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_pkey PRIMARY KEY (wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_document
    ADD CONSTRAINT wellbore_document_pkey PRIMARY KEY (wellbore_document_id, wlbnpdidwellbore, wlbdocumentname);
ALTER TABLE ONLY public.wellbore_dst
    ADD CONSTRAINT wellbore_dst_pkey PRIMARY KEY (wlbnpdidwellbore, wlbdsttestnumber);
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_pkey PRIMARY KEY (wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_formation_top
    ADD CONSTRAINT wellbore_formation_top_pkey PRIMARY KEY (wlbnpdidwellbore, lsunpdidlithostrat, lsutopdepth, lsubottomdepth);
ALTER TABLE ONLY public.wellbore_mud
    ADD CONSTRAINT wellbore_mud_pkey PRIMARY KEY (wellbore_mud_id, wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_npdid_overview
    ADD CONSTRAINT wellbore_npdid_overview_pkey PRIMARY KEY (wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_oil_sample
    ADD CONSTRAINT wellbore_oil_sample_pkey PRIMARY KEY (wellbore_oil_sample_id, wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_shallow_all
    ADD CONSTRAINT wellbore_shallow_all_pkey PRIMARY KEY (wlbnpdidwellbore);
ALTER TABLE ONLY public.wlbpoint
    ADD CONSTRAINT "wlbPoint_pkey" PRIMARY KEY (wlbnpdidwellbore);
ALTER TABLE ONLY public.baaarea
    ADD CONSTRAINT "baaArea_ibfk_1" FOREIGN KEY (baanpdidbsnsarrarea) REFERENCES public.bsns_arr_area(baanpdidbsnsarrarea);
ALTER TABLE ONLY public.bsns_arr_area_area_poly_hst
    ADD CONSTRAINT bsns_arr_area_area_poly_hst_ibfk_1 FOREIGN KEY (baanpdidbsnsarrarea) REFERENCES public.bsns_arr_area(baanpdidbsnsarrarea);
ALTER TABLE ONLY public.bsns_arr_area_licensee_hst
    ADD CONSTRAINT bsns_arr_area_licensee_hst_ibfk_1 FOREIGN KEY (baanpdidbsnsarrarea) REFERENCES public.bsns_arr_area(baanpdidbsnsarrarea);
ALTER TABLE ONLY public.bsns_arr_area_licensee_hst
    ADD CONSTRAINT bsns_arr_area_licensee_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.bsns_arr_area_operator
    ADD CONSTRAINT bsns_arr_area_operator_ibfk_1 FOREIGN KEY (baanpdidbsnsarrarea) REFERENCES public.bsns_arr_area(baanpdidbsnsarrarea);
ALTER TABLE ONLY public.bsns_arr_area_operator
    ADD CONSTRAINT bsns_arr_area_operator_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.bsns_arr_area_transfer_hst
    ADD CONSTRAINT bsns_arr_area_transfer_hst_ibfk_1 FOREIGN KEY (baanpdidbsnsarrarea) REFERENCES public.bsns_arr_area(baanpdidbsnsarrarea);
ALTER TABLE ONLY public.bsns_arr_area_transfer_hst
    ADD CONSTRAINT bsns_arr_area_transfer_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.company_reserves
    ADD CONSTRAINT company_reserves_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.company_reserves
    ADD CONSTRAINT company_reserves_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.discovery
    ADD CONSTRAINT discovery_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.discovery
    ADD CONSTRAINT discovery_ibfk_2 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.discovery_reserves
    ADD CONSTRAINT discovery_reserves_ibfk_1 FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery);
ALTER TABLE ONLY public.dscarea
    ADD CONSTRAINT "dscArea_ibfk_1" FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.dscarea
    ADD CONSTRAINT "dscArea_ibfk_2" FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery) NOT VALID;
ALTER TABLE ONLY public.dscarea
    ADD CONSTRAINT "dscArea_ibfk_3" FOREIGN KEY (dscnpdidresinclindiscovery) REFERENCES public.discovery(dscnpdiddiscovery) NOT VALID;
ALTER TABLE ONLY public.facility_moveable
    ADD CONSTRAINT facility_moveable_ibfk_1 FOREIGN KEY (fclnpdidcurrentrespcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.fclpoint
    ADD CONSTRAINT "fclPoint_ibfk_1" FOREIGN KEY (fclnpdidfacility) REFERENCES public.facility_fixed(fclnpdidfacility) NOT VALID;
ALTER TABLE ONLY public.fclpoint
    ADD CONSTRAINT "fclPoint_ibfk_2" FOREIGN KEY (fclbelongstos) REFERENCES public.tuf_petreg_licence(tufnpdidtuf) NOT VALID;
ALTER TABLE ONLY public.field_activity_status_hst
    ADD CONSTRAINT field_activity_status_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.field_description
    ADD CONSTRAINT field_description_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.field
    ADD CONSTRAINT field_ibfk_1 FOREIGN KEY (fldnpdidowner) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.field
    ADD CONSTRAINT field_ibfk_2 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.field
    ADD CONSTRAINT field_ibfk_3 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.field_investment_yearly
    ADD CONSTRAINT field_investment_yearly_ibfk_1 FOREIGN KEY (prfnpdidinformationcarrier) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.field_licensee_hst
    ADD CONSTRAINT field_licensee_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.field_licensee_hst
    ADD CONSTRAINT field_licensee_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.field_operator_hst
    ADD CONSTRAINT field_operator_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.field_operator_hst
    ADD CONSTRAINT field_operator_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.field_owner_hst
    ADD CONSTRAINT field_owner_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.field_reserves
    ADD CONSTRAINT field_reserves_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.fldarea
    ADD CONSTRAINT "fldArea_ibfk_1" FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.fldarea
    ADD CONSTRAINT "fldArea_ibfk_2" FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery) NOT VALID;
ALTER TABLE ONLY public.fldarea
    ADD CONSTRAINT "fldArea_ibfk_3" FOREIGN KEY (dscnpdidresinclindiscovery) REFERENCES public.discovery(dscnpdiddiscovery) NOT VALID;
ALTER TABLE ONLY public.licence_area_poly_hst
    ADD CONSTRAINT licence_area_poly_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_licensee_hst
    ADD CONSTRAINT licence_licensee_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_licensee_hst
    ADD CONSTRAINT licence_licensee_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.licence_oper_hst
    ADD CONSTRAINT licence_oper_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_oper_hst
    ADD CONSTRAINT licence_oper_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.licence_petreg_licence
    ADD CONSTRAINT licence_petreg_licence_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_petreg_licence_licencee
    ADD CONSTRAINT licence_petreg_licence_licencee_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_petreg_licence_licencee
    ADD CONSTRAINT licence_petreg_licence_licencee_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.licence_petreg_licence_oper
    ADD CONSTRAINT licence_petreg_licence_oper_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_petreg_licence_oper
    ADD CONSTRAINT licence_petreg_licence_oper_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.licence_petreg_message
    ADD CONSTRAINT licence_petreg_message_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_phase_hst
    ADD CONSTRAINT licence_phase_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT licence_task_ibfk_1 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT licence_task_ibfk_2 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT licence_task_ibfk_3 FOREIGN KEY (prltaskrefid) REFERENCES public.licence_task(prltaskid) NOT VALID;
ALTER TABLE ONLY public.licence_transfer_hst
    ADD CONSTRAINT licence_transfer_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.licence_transfer_hst
    ADD CONSTRAINT licence_transfer_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.pipline
    ADD CONSTRAINT "pipLine_ibfk_1" FOREIGN KEY (pipnpdidoperator) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.prlareasplitbyblock
    ADD CONSTRAINT "prlAreaSplitByBlock_ibfk_1" FOREIGN KEY (prllastoperatornpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.prlareasplitbyblock
    ADD CONSTRAINT "prlAreaSplitByBlock_ibfk_2" FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.prlarea
    ADD CONSTRAINT "prlArea_ibfk_1" FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.prlarea
    ADD CONSTRAINT "prlArea_ibfk_2" FOREIGN KEY (prllastoperatornpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.seaarea
    ADD CONSTRAINT "seaArea_ibfk_1" FOREIGN KEY (seanpdidsurvey) REFERENCES public.seis_acquisition(seanpdidsurvey) NOT VALID;
ALTER TABLE ONLY public.seamultiline
    ADD CONSTRAINT "seaMultiline_ibfk_1" FOREIGN KEY (seasurveyname) REFERENCES public.seis_acquisition(seaname) NOT VALID;
ALTER TABLE ONLY public.seis_acquisition_coordinates_inc_turnarea
    ADD CONSTRAINT seis_acquisition_coordinates_inc_turnarea_ibfk_1 FOREIGN KEY (seanpdidsurvey) REFERENCES public.seis_acquisition(seanpdidsurvey) NOT VALID;
ALTER TABLE ONLY public.seis_acquisition
    ADD CONSTRAINT seis_acquisition_ibfk_1 FOREIGN KEY (seacompanyreported) REFERENCES public.company(cmplongname) NOT VALID;
ALTER TABLE ONLY public.seis_acquisition_progress
    ADD CONSTRAINT seis_acquisition_progress_ibfk_1 FOREIGN KEY (seanpdidsurvey) REFERENCES public.seis_acquisition(seanpdidsurvey) NOT VALID;
ALTER TABLE ONLY public.strat_litho_wellbore_core
    ADD CONSTRAINT strat_litho_wellbore_core_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.strat_litho_wellbore
    ADD CONSTRAINT strat_litho_wellbore_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.tuf_operator_hst
    ADD CONSTRAINT tuf_operator_hst_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf) NOT VALID;
ALTER TABLE ONLY public.tuf_operator_hst
    ADD CONSTRAINT tuf_operator_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.tuf_owner_hst
    ADD CONSTRAINT tuf_owner_hst_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf) NOT VALID;
ALTER TABLE ONLY public.tuf_owner_hst
    ADD CONSTRAINT tuf_owner_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.tuf_petreg_licence_licencee
    ADD CONSTRAINT tuf_petreg_licence_licencee_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf) NOT VALID;
ALTER TABLE ONLY public.tuf_petreg_licence_licencee
    ADD CONSTRAINT tuf_petreg_licence_licencee_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.tuf_petreg_licence_oper
    ADD CONSTRAINT tuf_petreg_licence_oper_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf) NOT VALID;
ALTER TABLE ONLY public.tuf_petreg_licence_oper
    ADD CONSTRAINT tuf_petreg_licence_oper_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany) NOT VALID;
ALTER TABLE ONLY public.tuf_petreg_message
    ADD CONSTRAINT tuf_petreg_message_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf) NOT VALID;
ALTER TABLE ONLY public.wellbore_casing_and_lot
    ADD CONSTRAINT wellbore_casing_and_lot_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_coordinates
    ADD CONSTRAINT wellbore_coordinates_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_core
    ADD CONSTRAINT wellbore_core_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_core_photo
    ADD CONSTRAINT wellbore_core_photo_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_1 FOREIGN KEY (wlbdrillingoperator) REFERENCES public.company(cmplongname) NOT VALID;
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_2 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_3 FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery) NOT VALID;
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_4 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_5 FOREIGN KEY (prlnpdidproductionlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_6 FOREIGN KEY (wlbnpdidwellborereclass) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_7 FOREIGN KEY (wlbdiskoswelloperator) REFERENCES public.company(cmpshortname) NOT VALID;
ALTER TABLE ONLY public.wellbore_document
    ADD CONSTRAINT wellbore_document_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_dst
    ADD CONSTRAINT wellbore_dst_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_1 FOREIGN KEY (wlbdrillingoperator) REFERENCES public.company(cmplongname) NOT VALID;
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_2 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_3 FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery) NOT VALID;
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_4 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield) NOT VALID;
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_5 FOREIGN KEY (wlbnpdidwellborereclass) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_6 FOREIGN KEY (prlnpdidproductionlicence) REFERENCES public.licence(prlnpdidlicence) NOT VALID;
ALTER TABLE ONLY public.wellbore_formation_top
    ADD CONSTRAINT wellbore_formation_top_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_mud
    ADD CONSTRAINT wellbore_mud_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_oil_sample
    ADD CONSTRAINT wellbore_oil_sample_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wellbore_shallow_all
    ADD CONSTRAINT wellbore_shallow_all_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;
ALTER TABLE ONLY public.wlbpoint
    ADD CONSTRAINT "wlbPoint_ibfk_1" FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore) NOT VALID;

## Parsed table definitions
{}

## Sample rows
{}

## Tool-derived structural evidence
{
  "enabled_tools": [
    "schema_profiler"
  ],
  "schema_summary": {
    "num_tables": 0,
    "num_columns": 0,
    "num_foreign_keys": 0
  },
  "join_graph": {}
}


## Ontology / Mapping decision standard

Apply the following standards explicitly before producing the final JSON.

### A. Class decisions
1. Entity class
- Represent something as a class if it has stable identity, behaves like a domain entity,
  and naturally serves as a relation endpoint.

2. Value-domain class
- If a non-FK value column contains reusable named concepts/entities rather than free text,
  consider lifting that value domain into a class.

3. Value-object class
- If multiple columns jointly form a structured object (for example address-like bundles),
  and the object depends on a host entity and lacks a natural global URI, consider a value-object class.

4. Association class
- If a connector table has meaningful payload attributes describing the relation itself,
  prefer reification into an association class instead of collapsing to a direct relation.

5. Restricted class
- If class membership is defined by an explicit condition that changes the class extension,
  model that as a restricted class instead of turning the condition into an ordinary property.

6. Type-promotion caution
- Do NOT promote type/category/role values into subclasses by default.
- Prefer typing assertions unless there is strong evidence that the promoted class has stable ontology-level meaning.

### B. Relation decisions
1. Object property
- Use an object property when two class instances are linked semantically.

2. Conditional relation family
- If the same join skeleton supports different semantics based on a discriminator column
  (for example relationtype / role / kind), split them into distinct relations instead of one generic relation.

3. Shortcut relation
- Only materialize a shortcut relation if the direct projected relation has stable semantic meaning.
- Do not add arbitrary shortcuts blindly.

4. Extra relation caution
- A schema-supported relation may still be conservative or optional.
  Avoid inventing extra relations unless structural evidence is clear.

### C. Attribute decisions
1. Literal data property
- Use a literal property for ordinary text, numbers, dates, and scalar measurements.

2. Resource-valued property
- If a value is already a URI or should become a URI-like resource target
  (for example homepage, photo, sameAs target, mailto email), do not treat it as an ordinary literal.

3. Composed data property
- If multiple columns together form one ontology-level value
  (for example first name + last name -> full name), prefer the composed property when semantically appropriate.

4. Typing assertion
- If a column expresses instance type/category membership,
  prefer a typing assertion over an ordinary literal property.

### D. Identity decisions
1. uriPattern
- Use uriPattern when identity should be represented as a URI constructed from one or more columns.

2. uriColumn
- Use uriColumn when the database already stores the intended URI and the value should remain a resource.

3. bNodeIdColumns
- Use bNodeIdColumns when an object should exist as a node but has no natural global URI,
  and local identity anchored by host/entity columns is sufficient.

4. Multiple class maps
- The same conceptual class may require multiple class maps if the database provides multiple source identities.
  Do not collapse them blindly if source-specific identity matters.

### E. Condition and join decisions
1. Class membership condition
- A condition belongs to a class if it defines which rows instantiate that class.

2. Relation discriminator condition
- A condition belongs to a relation if it distinguishes different relation meanings.

3. Semantic filter condition
- Keep a condition if it removes semantically invalid values.

4. Non-essential guard
- Avoid adding IS NOT NULL-style conditions unless they are truly semantically necessary.
- Null guards are usually not mapping identity.

5. Essential joins
- Keep joins required to ground owner/target semantics.

6. Redundant joins
- Avoid stronger-than-necessary joins when a simpler semantically sufficient join exists.

### Default preferences
- Prefer typing assertion over subclass promotion unless subclass evidence is strong.
- Prefer literal property over value-domain class unless the value domain behaves like reusable concepts.
- Prefer value-object class over flat literals only when structured-object evidence is strong.
- Prefer minimal semantically sufficient joins over stronger joins.
- Prefer semantic conditions over non-semantic null guards.

## Output format
Return a JSON object with the following top-level keys:
- classes
- data_properties
- object_properties
- subclass_relations
- class_mappings
- data_property_mappings
- object_property_mappings
- diagnostics

### Canonical draft constraints
- Use exact top-level keys listed above.
- For classes, use fields:
  - id
  - label
  - status
  - confidence
  - description (optional)

- For data_properties, use fields:
  - id
  - label
  - domain
  - datatype
  - status
  - confidence

- For object_properties, use fields:
  - id
  - label
  - domain
  - range
  - join_paths
  - status
  - confidence

- For class_mappings, use fields:
  - class_id
  - instance_id_template
  - from_tables
  - identifier_columns
  - status
  - confidence
  - identifier_kind (optional: "uri_pattern" | "bnode")
  - bnode_id_columns (optional)
  - condition (optional)
  - join_paths (optional)
  - subclass_of (optional)
  - translate_with (optional)

- For data_property_mappings, use fields:
  - data_property_id
  - source_table
  - source_columns
  - applies_to_class
  - join_paths
  - value_template
  - status
  - confidence
  - value_kind (optional: "column" | "uri_column" | "pattern" | "uri_pattern" | "sql_expression" | "constant")
  - datatype (optional)
  - condition (optional)
  - translate_with (optional)
  - constant_value (optional)
  - sql_expression (optional)

- For object_property_mappings, use fields:
  - object_property_id
  - from_class
  - to_class
  - from_tables
  - join_paths
  - source_identifier_columns
  - target_identifier_columns
  - status
  - confidence
  - condition (optional)
  - dynamic_property (optional)
  - translate_with (optional)

### Join path format
Use ONLY this format:
[
  ["hotel.id", "=", "room.hotel_id"]
]

Do not output join_paths as objects or free-form strings.

### Important modeling guidance
- Prefer one object property direction unless the inverse is explicitly necessary.
- If a table is a weak entity, its identifier should reflect dependency.
- If a table is a pure connector table, prefer a relationship rather than a class.
- If a connector table has meaningful extra attributes, consider reification.
- If a class should not have a stable URI pattern and is better modeled as a blank-node-based class, say so explicitly.
- Distinguish literal-valued mappings from URI-valued mappings.
- Do not invent domain properties unsupported by schema or samples.
- When tool-derived evidence is present, treat it as strong structural guidance.
- For data properties sourced from auxiliary/value tables, include join_paths that connect the owner class instance to the value table.
- For type/category/role columns, prefer typing-aware modeling over naive literal output.
- For condition-bearing classes or relations, decide whether the condition is semantically defining or only a non-essential guard.
- For mapping-based faithfulness, preserve class restrictions, resource-valued properties, multi-source identities, and relation splitting when structurally justified.

### Burr-oriented mapping coverage
When constructing mappings, consider the full range of Burr/D2RQ-relevant fields that may be needed downstream.

For class mappings, relevant fields may include:
- id
- class
- name
- prefix
- bNodeIdColumns
- condition
- join
- subClassOf
- additionalClassDefinitionProperty
- translateWith
- mapping_id

For property mappings, relevant fields may include:
- property
- belongsToClass / belongsToClassMap
- refersToClass / refersToClassMap
- dynamicProperty
- join
- condition
- column
- uriColumn
- pattern
- uriPattern
- sqlExpression
- constantValue
- datatype
- translateWith
- mapping_id

Use these only when justified by schema / evidence. Do not invent fields unsupported by the scenario.
If a class should be blank-node based, make that explicit via bNodeIdColumns.
If a property value should be URI-valued rather than literal-valued, distinguish uriColumn / uriPattern from column / pattern.

Return JSON only.
