\c postgres
\set database_name real_world__npd__original
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
CREATE TABLE public.apaareagross (
    apamap_no bigint NOT NULL,
    apaareageometryewkt text NOT NULL,
    apaareageometry_kml_wgs84 text NOT NULL,
    apaareagross_id bigint NOT NULL
);
CREATE SEQUENCE public.apaareagross_apaareagross_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.apaareagross_apaareagross_id_seq OWNED BY public.apaareagross.apaareagross_id;
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
CREATE SEQUENCE public.apaareanet_apaareanet_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.apaareanet_apaareanet_id_seq OWNED BY public.apaareanet.apaareanet_id;
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
CREATE TABLE public.bsns_arr_area_operator (
    baaname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    baanpdidbsnsarrarea bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    baaoperatordateupdated date,
    datesyncnpd date NOT NULL
);
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
    datesyncnpd date NOT NULL
);
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
CREATE TABLE public.field_activity_status_hst (
    fldname character varying(40) NOT NULL,
    fldstatusfromdate date NOT NULL,
    fldstatustodate date NOT NULL,
    fldstatus character varying(40) NOT NULL,
    fldnpdidfield bigint NOT NULL,
    fldstatusdateupdated date,
    datesyncnpd date NOT NULL
);
CREATE TABLE public.field_description (
    fldname character varying(40) NOT NULL,
    flddescriptionheading character varying(255) NOT NULL,
    flddescriptiontext text NOT NULL,
    fldnpdidfield bigint NOT NULL,
    flddescriptiondateupdated date NOT NULL
);
CREATE TABLE public.field_investment_yearly (
    prfinformationcarrier character varying(40) NOT NULL,
    prfyear bigint NOT NULL,
    prfinvestmentsmillnok numeric(13,6) NOT NULL,
    prfnpdidinformationcarrier bigint NOT NULL,
    datesyncnpd date NOT NULL
);
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
CREATE TABLE public.field_production_totalt_ncs_year (
    prfyear bigint NOT NULL,
    prfprdoilnetmillsm numeric(13,6) NOT NULL,
    prfprdgasnetbillsm numeric(13,6) NOT NULL,
    prfprdcondensatenetmillsm3 numeric(13,6) NOT NULL,
    prfprdnglnetmillsm3 numeric(13,6) NOT NULL,
    prfprdoenetmillsm3 numeric(13,6) NOT NULL,
    prfprdproducedwaterinfieldmillsm3 numeric(13,6) NOT NULL
);
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
CREATE TABLE public.licence_petreg_licence_licencee (
    ptlname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    ptllicenseeinterest numeric(13,6) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    ptllicenseedateupdated date,
    datesyncnpd date NOT NULL
);
CREATE TABLE public.licence_petreg_licence_oper (
    ptlname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    prlnpdidlicence bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    ptloperdateupdated date,
    datesyncnpd date NOT NULL
);
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
    datesyncnpd date NOT NULL
);
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
CREATE SEQUENCE public.prlarea_prlarea_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.prlarea_prlarea_id_seq OWNED BY public.prlarea.prlarea_id;
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
CREATE SEQUENCE public.seaarea_seaarea_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.seaarea_seaarea_id_seq OWNED BY public.seaarea.seaarea_id;
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
    datesyncnpd date NOT NULL
);
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
CREATE TABLE public.seis_acquisition_progress (
    seaprogressdate date NOT NULL,
    seaprogresstext2 character varying(40) NOT NULL,
    seaprogresstext text NOT NULL,
    seaprogressdescription text,
    seanpdidsurvey bigint NOT NULL,
    seis_acquisition_progress_id bigint NOT NULL
);
CREATE SEQUENCE public.seis_acquisition_progress_seis_acquisition_progress_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.seis_acquisition_progress_seis_acquisition_progress_id_seq OWNED BY public.seis_acquisition_progress.seis_acquisition_progress_id;
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
CREATE TABLE public.tuf_operator_hst (
    tufname character varying(40) NOT NULL,
    cmplongname character varying(200) NOT NULL,
    tufoperdatevalidfrom date NOT NULL,
    tufoperdatevalidto date NOT NULL,
    tufnpdidtuf bigint NOT NULL,
    cmpnpdidcompany bigint NOT NULL,
    datesyncnpd date NOT NULL
);
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
CREATE SEQUENCE public.wellbore_casing_and_lot_wellbore_casing_and_lot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.wellbore_casing_and_lot_wellbore_casing_and_lot_id_seq OWNED BY public.wellbore_casing_and_lot.wellbore_casing_and_lot_id;
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
CREATE TABLE public.wellbore_core_photo (
    wlbname character varying(60) NOT NULL,
    wlbcorenumber bigint NOT NULL,
    wlbcorephototitle character varying(200) NOT NULL,
    wlbcorephotoimgurl character varying(200) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbcorephotodateupdated date,
    wellbore_core_photo_id bigint NOT NULL
);
CREATE SEQUENCE public.wellbore_core_photo_wellbore_core_photo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.wellbore_core_photo_wellbore_core_photo_id_seq OWNED BY public.wellbore_core_photo.wellbore_core_photo_id;
CREATE SEQUENCE public.wellbore_core_wellbore_core_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.wellbore_core_wellbore_core_id_seq OWNED BY public.wellbore_core.wellbore_core_id;
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
CREATE SEQUENCE public.wellbore_document_wellbore_document_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.wellbore_document_wellbore_document_id_seq OWNED BY public.wellbore_document.wellbore_document_id;
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
CREATE SEQUENCE public.wellbore_mud_wellbore_mud_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.wellbore_mud_wellbore_mud_id_seq OWNED BY public.wellbore_mud.wellbore_mud_id;
CREATE TABLE public.wellbore_npdid_overview (
    wlbwellborename character varying(40) NOT NULL,
    wlbnpdidwellbore bigint NOT NULL,
    wlbwell character varying(40) NOT NULL,
    wlbwelltype character varying(20),
    datesyncnpd date NOT NULL
);
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
CREATE SEQUENCE public.wellbore_oil_sample_wellbore_oil_sample_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.wellbore_oil_sample_wellbore_oil_sample_id_seq OWNED BY public.wellbore_oil_sample.wellbore_oil_sample_id;
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
ALTER TABLE ONLY public.apaareagross ALTER COLUMN apaareagross_id SET DEFAULT nextval('public.apaareagross_apaareagross_id_seq'::regclass);
ALTER TABLE ONLY public.apaareanet ALTER COLUMN apaareanet_id SET DEFAULT nextval('public.apaareanet_apaareanet_id_seq'::regclass);
ALTER TABLE ONLY public.prlarea ALTER COLUMN prlarea_id SET DEFAULT nextval('public.prlarea_prlarea_id_seq'::regclass);
ALTER TABLE ONLY public.seaarea ALTER COLUMN seaarea_id SET DEFAULT nextval('public.seaarea_seaarea_id_seq'::regclass);
ALTER TABLE ONLY public.seis_acquisition_progress ALTER COLUMN seis_acquisition_progress_id SET DEFAULT nextval('public.seis_acquisition_progress_seis_acquisition_progress_id_seq'::regclass);
ALTER TABLE ONLY public.wellbore_casing_and_lot ALTER COLUMN wellbore_casing_and_lot_id SET DEFAULT nextval('public.wellbore_casing_and_lot_wellbore_casing_and_lot_id_seq'::regclass);
ALTER TABLE ONLY public.wellbore_core ALTER COLUMN wellbore_core_id SET DEFAULT nextval('public.wellbore_core_wellbore_core_id_seq'::regclass);
ALTER TABLE ONLY public.wellbore_core_photo ALTER COLUMN wellbore_core_photo_id SET DEFAULT nextval('public.wellbore_core_photo_wellbore_core_photo_id_seq'::regclass);
ALTER TABLE ONLY public.wellbore_document ALTER COLUMN wellbore_document_id SET DEFAULT nextval('public.wellbore_document_wellbore_document_id_seq'::regclass);
ALTER TABLE ONLY public.wellbore_mud ALTER COLUMN wellbore_mud_id SET DEFAULT nextval('public.wellbore_mud_wellbore_mud_id_seq'::regclass);
ALTER TABLE ONLY public.wellbore_oil_sample ALTER COLUMN wellbore_oil_sample_id SET DEFAULT nextval('public.wellbore_oil_sample_wellbore_oil_sample_id_seq'::regclass);
INSERT INTO public.apaareagross VALUES (999, '010600000001000000010300000001000000A7000000B4AAAAAAAAAA32406D66666666A65140B4AAAAAAAAAA32400700000000B05140B4AAAAAAAAAA32400000000000C051401C000000000033400000000000C0514068555555555533400000000000C051406855555555553340F9FFFFFFFFCF514098AAAAAAAAAA3340F9FFFFFFFFCF514098AAAAAAAAAA33400700000000E0514098AAAAAAAAAA33400700000000F051401C000000000034400700000000F051401C00000000003440000000000000524068555555555534400000000000005240D0AAAAAAAAAA344000000000000052400000000000003540000000000000524068555555555535400000000000005240D0AAAAAAAAAA35400000000000005240D0AAAAAAAAAA3540070000000010524000000000000036400700000000105240685555555555364007000000001052400BAAAAAAAAAA36400700000000105240E4FFFFFFFFFF36400700000000105240E4FFFFFFFFFF36400000000000005240F8545555555537400000000000005240EFA9AAAAAAAA374000000000000052401C0000000000384000000000000052404C555555555538400000000000005240B4AAAAAAAAAA384000000000000052401C0000000000394000000000000052404C5555555555394000000000000052404C555555555539400700000000F05140EFA9AAAAAAAA39400700000000F051401C00000000003A400700000000F051401C00000000003A408D88888888E851401C00000000003A400700000000E051409D77777777B739400700000000E051401EEFEEEEEE6E39400700000000E051404C555555555539400700000000E051404C55555555553940F4EEEEEEEEDE51403522222222223940F4EEEEEEEEDE5140E7DDDDDDDD1D3940F4EEEEEEEEDE5140E7DDDDDDDD1D3940E0DDDDDDDDDD5140E6EEEEEEEEEE3840E0DDDDDDDDDD51406666666666E63840E0DDDDDDDDDD51406666666666E63840CDCCCCCCCCDC514002EFEEEEEEAE3840CDCCCCCCCCDC5140B4AAAAAAAAAA3840CDCCCCCCCCDC5140B4AAAAAAAAAA3840B9BBBBBBBBDB51408366666666663840B9BBBBBBBBDB51406666666666263840B9BBBBBBBBDB51406666666666263840A6AAAAAAAADA514022DDDDDDDD1D3840A6AAAAAAAADA5140B699999999D93740A6AAAAAAAADA51400000000000C03740A6AAAAAAAADA51400000000000C037409A99999999D951409A999999999937409A99999999D951409A999999999937408D88888888D85140FE101111119137408D88888888D85140B2BBBBBBBB7B37408D88888888D85140B2BBBBBBBB7B37408177777777D7514083666666666637408177777777D7514083666666666637406D66666666D651401A111111115137406D66666666D651401A111111115137405A55555555D551407F888888884837405A55555555D55140CEBBBBBBBB3B37405A55555555D55140CEBBBBBBBB3B37404744444444D4514066666666662637404744444444D4514066666666662637403333333333D35140B6999999991937403333333333D3514055101111111137403333333333D351401A111111111137402722222222D25140E4FFFFFFFFFF36402722222222D25140E4FFFFFFFFFF3640F9FFFFFFFFCF51403711111111D13640F9FFFFFFFFCF51403711111111D13640EDEEEEEEEECE5140B2BBBBBBBBBB3640FBEEEEEEEECE5140B2BBBBBBBBBB3640E7DDDDDDDDCD51401733333333B33640E7DDDDDDDDCD5140B4AAAAAAAAAA3640E7DDDDDDDDCD5140B4AAAAAAAAAA3640D4CCCCCCCCCC51404C55555555953640D4CCCCCCCCCC51404C55555555953640C0BBBBBBBBCB51401C00000000803640C0BBBBBBBBCB51401C00000000803640ADAAAAAAAACA5140E6EEEEEEEE6E3640ADAAAAAAAACA5140D0AAAAAAAA6A3640ADAAAAAAAACA5140D0AAAAAAAA6A36409A99999999C9514068555555555536409A99999999C9514068555555555536408688888888C851404E444444444436408688888888C851404E444444444436407377777777C7514033333333333336407377777777C7514002EFEEEEEE2E36407377777777C7514002EFEEEEEE2E36406D66666666C6514003DEDDDDDD1D36406D66666666C6514003DEDDDDDD1D36405A55555555C551409B888888880836405A55555555C551409B888888880836404E44444444C451406577777777F735404E44444444C451406577777777F735403A33333333C351404F33333333F335403A33333333C351403522222222E235403A33333333C351403522222222E235402722222222C251403711111111D135402722222222C251403711111111D135401311111111C15140B2BBBBBBBBBB35401311111111C151405EBBBBBBBBBB35400000000000C05140D0AAAAAAAAAA35400000000000C05140D0AAAAAAAAAA3540EDEEEEEEEEBE51406855555555953540EDEEEEEEEEBE51406855555555953540E7DDDDDDDDBD51401C00000000803540E7DDDDDDDDBD51401C00000000803540C6CCCCCCCCBC514098AAAAAAAA6A3540C6CCCCCCCCBC514003DEDDDDDD5D3540C6CCCCCCCCBC514003DEDDDDDD5D3540C7BBBBBBBBBB5140EBBBBBBBBB3B3540C7BBBBBBBBBB5140EBBBBBBBBB3B3540ADAAAAAAAABA5140B4AAAAAAAA2A3540ADAAAAAAAABA5140B699999999193540ADAAAAAAAABA5140B699999999193540A199999999B951409D77777777F73440A199999999B951409D77777777F734408D88888888B851403522222222E234408D88888888B851404C55555555D534408D88888888B851404C55555555D534407A77777777B751403333333333B334407A77777777B751403333333333B334406666666666B6514068555555559534406666666666B651401A111111119134406666666666B651401A111111119134405355555555B55140E6EEEEEEEE6E34405355555555B55140E6EEEEEEEE6E34404044444444B4514068555555555534404044444444B45140E9CCCCCCCC4C34404044444444B45140E9CCCCCCCC4C34403A33333333B35140B4AAAAAAAA2A34403A33333333B35140B4AAAAAAAA2A34402722222222B2514037111111111134402722222222B2514047888888880834402722222222B251409B888888880834401A11111111B151408366666666E633401A11111111B151408366666666E633400700000000B051407F88888888C833400700000000B0514098AAAAAAAAAA33400700000000B0514098AAAAAAAAAA3340EDEEEEEEEEAE51403522222222A23340EDEEEEEEEEAE51403522222222A23340E0DDDDDDDDAD51404E44444444843340E0DDDDDDDDAD51404E44444444843340CDCCCCCCCCAC51401922222222623340CDCCCCCCCCAC514019222222226233409DBBBBBBBBAB51403711111111513340B9BBBBBBBBAB51404E44444444443340B9BBBBBBBBAB51404E44444444443340B4AAAAAAAAAA51403522222222223340B4AAAAAAAAAA514035222222222233409399999999A951406A444444440433409399999999A951406A444444440433408D88888888A851403522222222E232408D88888888A851403522222222E232407A77777777A75140E7DDDDDDDDDD32407A77777777A75140B788888888C832407A77777777A751403244444444C432407A77777777A751403244444444C432406D66666666A651409D77777777B732406D66666666A65140B4AAAAAAAAAA32406D66666666A65140', '<MultiGeometry><Polygon><outerBoundaryIs><LinearRing><coordinates>18.665070369140565,70.600082911304639 18.665059491055402,70.750089707504685 18.665040986788618,71.00010105370248 18.998392209660604,71.000103690632272 19.3317434783363,71.00010629603689 19.331724941804207,71.250117667935683 19.665076482427242,71.250120242726865 19.665057688025097,71.500131638590787 19.665038389075082,71.750143056884667 19.998390448889257,71.750145601775316 19.998370871503607,72.000157042871081 20.331723224990316,72.00015955667034 20.665075624359673,72.000162038384204 20.998428068966106,72.000164487928657 21.331780558163015,72.000166905220809 21.665133091301819,72.000169290178789 21.665114254794517,72.250180756323502 21.998467089478751,72.25018310945282 22.331819967432672,72.250185430035785 22.66517288799383,72.250187717993839 22.998525850501039,72.250189973249519 22.998543650254419,72.000178505070863 23.331896393324037,72.000180727168996 23.665249176414342,72.00018291646505 23.998601998867994,72.000185072884918 24.331954860023277,72.000187196355625 24.66530775922028,72.000189286805266 24.998660695796374,72.000191344163085 25.332013669087853,72.000193368359419 25.33202920774611,71.750181919860225 25.665381959828864,71.750183910810833 25.998734746780222,71.750185868516709 25.998741622524879,71.633513866648244 25.998749377958106,71.500174441819993 25.715399719915162,71.500172779855831 25.432050086629392,71.500171093903589 25.332044339690405,71.500170493142065 25.332045334429637,71.483503065481756 25.132033859864212,71.483501855019426 25.115366237556497,71.483501753609815 25.115367241206659,71.466834326051469 24.932023410673747,71.466833205093522 24.898688169916436,71.466833000209022 24.898689182428619,71.450165572754386 24.682010136850625,71.450164232963417 24.665342518590737,71.450164129325188 24.665343540728813,71.433496701976338 24.398661673925712,71.433495032568459 24.148647445113024,71.433493448366022 24.148648490579593,71.416826021136927 24.115313263260983,71.416825808514233 23.848631458160771,71.41682409571257 23.748625787451523,71.416823447999164 23.748626850442385,71.400156020891473 23.598618358019145,71.400155043801249 23.59861942638824,71.383487616803237 23.565284208501687,71.383487398773823 23.481946165457042,71.383486852268817 23.481947237574765,71.36681942537885 23.398609200927186,71.366818876835652 23.398610275176633,71.350151450051968 23.315272244924003,71.350150899472155 23.315273321293244,71.333483472795251 23.281938111459837,71.333483251994195 23.231935297433974,71.333482920180472 23.231936375911118,71.316815493610761 23.148598358442921,71.316814938962622 23.148599439016127,71.300147512500416 23.098596632077399,71.300147178737021 23.065261427936669,71.300146955820566 23.065262510594877,71.283479529466334 22.998592106646612,71.283479082661287 22.998594272654344,71.250144230268077 22.815250687195849,71.250142994869748 22.815251776035733,71.233475568841726 22.731913790494772,71.233475004051584 22.731914881372155,71.216807578133043 22.698579689411574,71.216807351651198 22.665244497845801,71.216807124844436 22.665245589967672,71.200139699034267 22.581907616689364,71.200139130604498 22.581908710827495,71.183471704904562 22.498570743923651,71.183471134454351 22.498571840066539,71.166803708865061 22.431901471442174,71.166803251051974 22.41523387953508,71.166803136396055 22.415234977671258,71.150135710917908 22.33189702351007,71.1501351364318 22.331898123628136,71.13346771106508 22.265227765193753,71.133467250025717 22.265228866510199,71.116799824769046 22.198558512767345,71.116799362442165 22.181890924582525,71.116799246658204 22.181892027860012,71.100131821513997 22.115221679207121,71.100131357577112 22.115222783665867,71.083463932543381 22.03188485395815,71.083463350813474 22.031885960357247,71.066795925892791 21.965215621475082,71.066795459062917 21.965216729038445,71.050128034253561 21.948549145335832,71.050127917346273 21.881878811537867,71.050127448910217 21.881879921021039,71.033460024214605 21.815209591899315,71.033459554496261 21.815210702529907,71.016792129912787 21.731872797222994,71.016791540961705 21.731873909752668,71.000124116492699 21.665203590381157,71.000123643890433 21.665204704041876,70.983456219534219 21.581866810915724,70.983455626981126 21.581867926455629,70.96678820274029 21.49853003967171,70.966787608187332 21.49853115707981,70.950120184061817 21.415193276635843,70.950119587510684 21.365190549606734,70.950119228616074 21.365191671128315,70.933451804613995 21.231851076283082,70.933450844048494 21.231852201895418,70.916783420170034 21.165181909962001,70.916782937971817 21.098511619694371,70.91678245449117 21.098512749374823,70.900115030737382 20.965172179834227,70.900114059951562 20.965173313560193,70.8834466363231 20.881835464731459,70.883446026993909 20.831832756696084,70.883445660436792 20.831833894445047,70.866778236934508 20.698493350273878,70.86677725595419 20.698494492023393,70.850109832578894 20.581821526622058,70.85010897004878 20.565153960561044,70.850108846511105 20.565155106288703,70.83344142326348 20.431814587551152,70.833440432114742 20.431815737234647,70.816773008995625 20.331810357093698,70.816772262305818 20.298475231237841,70.816772012772489 20.298476384854901,70.800104589782904 20.165135891614558,70.800103588492007 20.165137049142988,70.783436165632281 20.065131688142479,70.783435411344641 20.031796568674576,70.783435159280188 20.031797730092588,70.766767736551415 19.898457262412464,70.766766725144819 19.8984584276973,70.750099302547639 19.781785529297689,70.750098413427253 19.665112636260393,70.750097520426607 19.665113809748931,70.733430097981582 19.631778699893268,70.733429842132992 19.631779872846501,70.716762419801583 19.515106996890296,70.716761521864484 19.515108172922286,70.700094099663673 19.381767755663876,70.700093068737658 19.381768935477488,70.683425646671267 19.315098732389941,70.683425129328668 19.265096081240788,70.683424740493464 19.265097264095736,70.66675731855959 19.131756871682303,70.666756278227297 19.131758058277505,70.650088856429363 19.015085225800089,70.650087942031291 19.015086415399441,70.633420520367153 18.881746047876437,70.633419470652896 18.881747241174917,70.616752049126362 18.865079696453606,70.616751917562326 18.781741974540015,70.616751258564733 18.765074430496128,70.616751126529792 18.765075626761803,70.600083705138061 18.715072997441386,70.60008330857417 18.665070369140565,70.600082911304639</coordinates></LinearRing></outerBoundaryIs></Polygon></MultiGeometry>', 2);
INSERT INTO public.apaareagross VALUES (999, '0106000000010000000103000000010000007400000084FFFFFFFFFF1B400000000000A050407C00000000001C400000000000B050407A4A09C1AAAA1A400000000000B05040BEB5F63E555519400000000000B05040BEB5F63E555519400700000000C05040BEB5F63E555519400700000000D050407A4A09C1AAAA1A400700000000D050407C00000000001C400700000000D0504045B6F63E55551D400700000000D05040FC59CE5569AB1E400700000000D05040FC59CE5569AB1E400700000000C0504081000000000020400700000000C05040E1AAAAAAAAAA20400700000000C0504062555555555521400700000000C0504081000000000022400700000000C0504041ABAAAAAAAA22400700000000C05040A0555555555523400700000000C0504000000000000024400700000000C05040D0AAAAAAAAAA24400700000000C0504011565555555525400700000000C0504071000000000026400700000000C05040D0AAAAAAAAAA26400700000000C05040A0555555555527400700000000C0504073DBF86E9BE226400CB05780FDAF5040D0AAAAAAAAAA26401FF7E3A70FA850406DBC4F686C7226400000000000A05040E40208D08D0426400700000000905040710000000000264004C70355548F50403FDE014FF8982540070000000080504011565555555525408008F672B2755040852FDEDE972F25400E00000000705040677F464B5AC824400700000000605040D0AAAAAAAAAA24404F6F82BE565B5040D866AF022D63244007000000005050400000000000002440F9FFFFFFFF3F5040A055555555552340F9FFFFFFFF3F50407F88888888082340F9FFFFFFFF3F50407F88888888082340B9BBBBBBBB4B5040DECCCCCCCC4C2240B9BBBBBBBB4B5040DECCCCCCCC4C22409A99999999495040DF3C4444444422409A999999994950405F4444444444224081777777774750401DBCBBBBBB3B22408177777777475040C004BCBBBB3B22406B5455555545504022333333333322403E55555555455040223333333333224033333333334350407F61AAAAAA2A22403333333333435040BFCDA7AAAA2A2240421A11111141504062222222222222401311111111415040806B222222222240F9FFFFFFFF3F50408100000000002240F9FFFFFFFF3F50406255555555552140F9FFFFFFFF3F5040E1AAAAAAAAAA2040F9FFFFFFFF3F5040E1AAAAAAAAAA204007000000005050400474EAFFFFFF1F40EA02000000505040821DD5FFFFFF1F40DB05000000405040BF54D5FFFFFF1F40F705000000305040008DD5FFFFFF1F40050600000020504040C5D5FFFFFF1F401A0600000010504043FFD5FFFFFF1F4028060000000050403FB892AAAAAA1E404503000000005040FF29485555551D40A601000000005040C093F5FFFFFF1B4036010000000050403E2DF2FFFFFF1B405A03000000E04F4083B0F5FFFFFF1B407902000000C04F403F23F9FFFFFF1B40F634333333B34F40BFBBB5BBBBBB1B40A134333333B34F40BFBBB5BBBBBB1B409612111111B14F403CCE0C1111111B402612111111B14F403CCE0C1111111B400DF0EEEEEEAE4F40C5AAAAAAAAAA1A4002EFEEEEEEAE4F407E53858888881A40C7EFEEEEEEAE4F407E53858888881A40A0CDCCCCCCAC4F403B9CFDFFFFFF194076CDCCCCCCAC4F40BF00000000001A40B4AAAAAAAAAA4F4080B286888888194017ABAAAAAAAA4F4080B2868888881940F088888888A84F40FA555555555519408D88888888A84F40BAAA0F1111111940D488888888A84F40BAAA0F1111111940BB66666666A64F407C8C9899999918409F66666666A64F407C8C9899999918407844444444A44F4043592122222218407844444444A44F4043592122222218405122222222A24F403D47FFFFFFFF17405122222222A24F403D47FFFFFFFF17402A00000000A04F4081DC5455555517402A00000000A04F4081DC54555555174003DEDDDDDD9D4F400587DDDDDDDD164003DEDDDDDD9D4F400587DDDDDDDD1640DDBBBBBBBB9B4F40FDAAAAAAAAAA1640CEBBBBBBBB9B4F40415FAAAAAAAA16401C00000000804F40C13A5555555515401C00000000804F40FFF7FFFFFFFF13401C00000000804F40FCFAFFFFFFFF13400E00000000A04F40FDAAAAAAAAAA12400E00000000A04F40FDAAAAAAAAAA1240F2FFFFFFFFBF4F40FDAAAAAAAAAA12400E00000000E04F40FCFAFFFFFFFF13400E00000000E04F40FEF3FFFFFFFF134000000000000050407FEEFFFFFFFF134007000000001050403FF3FFFFFFFF13400700000000205040FFF7FFFFFFFF13400E0000000030504042395555555515400E000000003050407F5DAAAAAAAA16400E00000000305040FE40FFFFFFFF17401C00000000305040FE40FFFFFFFF174015000000004050407F3FFFFFFFFF174015000000005050407C000000000018401C000000006050407C0000000000184000000000007050407C000000000018400700000000805040FA555555555519400700000000805040C5AAAAAAAAAA1A40070000000080504084FFFFFFFFFF1B40070000000080504084FFFFFFFFFF1B40070000000090504084FFFFFFFFFF1B400000000000A05040', '<MultiGeometry><Polygon><outerBoundaryIs><LinearRing><coordinates>6.998161522944367,66.499791001466903 6.998144254976092,66.749801779432133 6.664798091361738,66.749798132469166 6.331450982348647,66.749794458936464 6.331433083425588,66.999805262555299 6.331414793314422,67.249816098846935 6.664762162765371,67.249819779829423 6.998108588033124,67.249823434116891 7.331455068703286,67.249827061596747 7.665529643264361,67.249830669980327 7.665547402559634,66.999819819233238 7.998166819907005,66.999823381458853 8.331513662644412,66.999826924393318 8.664860558356022,66.99983044009727 8.99820750658299,66.999833928451721 9.331554506864016,66.999837389338609 9.664901558736505,66.999840822640749 9.998248661736254,66.999844228241926 10.331595815397412,66.999847606026862 10.664943019252064,66.999850955881186 10.998290272830255,66.999854277691554 11.331637575661134,66.999857571345473 11.664984927272084,66.999860836731486 11.440916816765302,66.749695277903498 11.331661250588288,66.62579690079049 11.221814535662469,66.499834817318032 11.007232209122508,66.249821913407828 10.998338040871788,66.239343596354544 10.797113820499453,65.999809079713643 10.665015358386109,65.838817528455024 10.591306583599652,65.749796315934447 10.389671602058606,65.499783621854135 10.331692999123888,65.426949381277097 10.192067201972902,65.24977099717961 9.998371154963472,64.999758441765621 9.665025048864409,64.999755061938174 9.515019316410166,64.999753532144481 9.51500877804966,65.183094633204831 9.148328046842154,65.183090867836 9.148329991197908,65.149756121255763 9.131662687369941,65.149755949347153 9.131664627339816,65.116421203427862 9.114997324397361,65.116421031474857 9.114999260023737,65.083086286213984 9.098331957927465,65.083086114219711 9.098333889163781,65.04975136962571 9.081666587944616,65.049751197584229 9.081668514539869,65.016416453687611 9.065001214562052,65.01641628156861 9.065002176514161,64.999748909855953 8.99833297793681,64.99974822088636 8.664987013968,64.999744759893574 8.331641098233549,64.999741272078793 8.331626284972204,65.249751856716387 7.998280303828073,65.249748338532896 7.99829522866258,64.999737757581357 7.998309861876232,64.749727212880103 7.99832421082745,64.499716704896315 7.998338283794339,64.249706234084044 7.998352088737201,63.999695800893733 7.665006698013719,63.999692275108657 7.331661354434045,63.999688723140927 6.998316058360894,63.999685145110369 6.99832990471143,63.74967476196678 6.998343492342623,63.499664417440769 6.998348856595998,63.399660290542073 6.93167985047403,63.399659573801479 6.931680741877811,63.382992219983997 6.765008238037745,63.382990423768739 6.765009131527172,63.366323070265963 6.665005637020702,63.366321989536864 6.631671139534029,63.366321628782835 6.631672034459591,63.34965427556773 6.498334052615408,63.349652830097547 6.498334949106744,63.332985477170183 6.381664223328734,63.33298420912773 6.381665120781941,63.316316856476945 6.331663384057145,63.316316312114679 6.264994403209997,63.316315585407068 6.264995301756744,63.299648233032656 6.148324592259669,63.299646958942716 6.148325491892376,63.282979606845473 6.031654790476855,63.282978329742249 6.03165569118795,63.266310977922942 5.998321206777846,63.266310612494223 5.998322106998979,63.249643260880234 5.831649695302834,63.249641430081155 5.831650597525887,63.232974078790697 5.714979918704384,63.232972793570674 5.714980821985128,63.216305442560568 5.664979105253819,63.216304890849237 5.664990759014933,62.999629344406763 5.331646088282163,62.999625655777599 4.998301466033029,62.999621942105129 4.998287819126682,63.249632181512951 4.664943154645217,63.249628438244329 4.664929158562107,63.499638712744172 4.664914897035992,63.749649026579171 4.99825974935809,63.74965277908197 4.99824531158144,63.999663136367481 4.998230594786203,64.249673532064278 4.9982155907722,64.499683965725552 4.998200291010022,64.749694436901748 5.331545595407733,64.749698181972207 5.664890951691341,64.749701901509042 5.998236359445757,64.749705595386573 5.998221074168161,64.999716116390317 5.998205481943558,65.249726673878385 5.998189573423344,65.499737267390827 5.998173338738833,65.749747896463489 5.998156767745746,65.999758560630681 6.33150278755662,65.999762248933592 6.664848860709199,65.999765910994412 6.998194986772433,65.999769546689151 6.998178429782097,66.249780257060422 6.998161522944367,66.499791001466903</coordinates></LinearRing></outerBoundaryIs></Polygon></MultiGeometry>', 3);
INSERT INTO public.apaareagross VALUES (999, '010600000001000000010300000001000000A6000000C2555555555511401C00000000004F407A7C707821551140D7B7FB9804C04E40C2555555555511400E00000000C04E40C2555555555511401C00000000A04E40C2555555555511401C00000000804E40C3BBBBBBBBBB11401C00000000804E40C3BBBBBBBBBB11400E00000000604E40C3BBBBBBBBBB1140F2FFFFFFFF3F4E40C255555555551140F2FFFFFFFF3F4E40C2555555555511400000000000204E4000000000000010400000000000204E408256555555550D400000000000204E408256555555550D400E00000000004E408256555555550D400E00000000E04D408256555555550D401C00000000C04D408256555555550D401C00000000A04D408256555555550D400E00000000804D4000000000000010400E00000000804D400000000000001040F2FFFFFFFF5F4D4000000000000010401C00000000404D40C2555555555511401C00000000404D40C2555555555511400E00000000204D4081AAAAAAAAAA12400E00000000204D4081AAAAAAAAAA12400E00000000004D4000000000000014400E00000000004D4000000000000014401C00000000E04C407F555555555515401C00000000E04C403EAAAAAAAAAA16401C00000000E04C403EAAAAAAAAAA16401C00000000C04C4000000000000018401C00000000C04C407F555555555519400E00000000C04C40FDAAAAAAAAAA1A400E00000000C04C40BCFFFFFFFFFF1B400E00000000C04C40BCFFFFFFFFFF1B40F2FFFFFFFF9F4C40BCFFFFFFFFFF1B40DE44D8F0F4984C40C358F28B25BF1B407466666666964C40C5AAAAAAAAAA1B40D4091F86A5954C40FCDCDAAF28A21B404C55555555954C40C255555555551B40A6EC791180924C400000000000001B405924E09B578F4C40FDAAAAAAAAAA1A40CB63396B2C8C4C4001BF0E9C33821A40B4AAAAAAAA8A4C40FA55555555551A401EF89D39FE884C404400000000001A40FA1C5B1ECD854C4041ABAAAAAAAA19406ED2701999824C404565F4B6AC6519400E00000000804C407F555555555519400E00000000804C407F555555555519409618DF2A627F4C40BCFFFFFFFFFF1840802AF369287C4C40C5AAAAAAAAAA1840931A7879EB784C400355555555551840CAD6A2B6AB754C40FB77E6F87B4C18407655555555754C4000000000000018406F23260A69724C40FDAAAAAAAAAA17403AC5B45C236F4C40035555555555174092800197DA6B4C407D337D898B361740B4AAAAAAAA6A4C400000000000001740624341168F684C403EAAAAAAAAAA1640CD1F3F7D40654C407FF8E6D5C42316401C00000000604C407F555555555515408EA85AF8E7574C404022222222221440CEBBBBBBBB4B4C4000000000000014404AEE3517924A4C404029A471F7CB12400E00000000404C4081AAAAAAAAAA12408CDD6E5CD93E4C40C2555555555511407092F0AAF4324C400000000000001040A76C9E5FE3264C400AA69C7EB27E0E400E00000000204C408256555555550D40D0B99034A51A4C4084ABAAAAAAAA0A4055C7DFE3390E4C400000000000000A40507EB1E4170B4C4002E63D30BC6108400E00000000204C4087000000000008400D53E077E6244C400574D98615DF05400E00000000404C4003555555555505404D398F9DCA464C40F7B4814E1BE80440788FC2F5284C4C407BBBB88D065004401C00000000604C40FD0EE689FA5703400E00000000804C4006AAAAAAAAAA02405A330FC218964C407B28F03B735C02400E00000000A04C4084476FCB5A5D01401C00000000C04C40875ACFD49C5A00401C00000000E04C4087000000000000401236855919EB4C4014400AD7A370FF3FB2703D0AD7F34C4000B070F46D10FE3F0E00000000004D4014ABAAAAAAAAFA3FC6FEFB17B91D4D4010107FD88367FA3F0E00000000204D40F6BDBBBBBBBBF73FF3A3703D0A374D40FC3BE0091F06F83F1C00000000404D400B3965D04512F93FF2FFFFFFFF5F4D4000F9E78F5622FA3F0E00000000804D4014ABAAAAAAAAFA3FC7FC87F4DB8F4D4009DBF2686E36FB3F1C00000000A04D400AC82F96FC62FB3F93EB51B81EA54D40FCB37A381F62FD3F1C00000000C04D40FB610BB660CBFF3F0E00000000E04D408700000000000040DFC23F7FB4E24D400736D069039D0040B45F2CF9C5F24D40F6F400032E7500400E00000000004E40874FCCB0085B004020C90148A2084E4000F7E6D5C41300400000000000204E408700000000000040C5A291806F264E400407EF5CB661FF3FF2FFFFFFFF3F4E40034082E2C798FE3F0E00000000604E40F67042ACAFCCFD3F1C00000000804E40FCAF4C8353FDFC3F1C00000000A04E40FE703D0AD7A3FC3F0474DA40A7AD4E4013B353994F43FB3F0E00000000C04E4014ABAAAAAAAAFA3F45F879C8E3C74E40F6285C8FC2F5F83F83B1E4174BDE4E40EAF2D57B17DCF83F83B1E4174BDE4E400CFFB991EEB6F83F0E00000000E04E40063C201CC6F7F53F1C00000000004F40EC5455555555F53FE4DEDB8250074F40FA035020AF0AF53FB7AFADAAAA0A4F40EA3925B5341CF43F2A92585555154F400B2AF7180000F43F7C706B4797164F400E6EC8CC592CF33F1B6F000000204F400BEB02C0EDD8F23F23DF73FEB1234F40F7A8AAAAAAAAF23F60368613AB254F40EF100EE35B45F23F86AF022DFB294F40EAE056A39334F23FB4AAAAAAAA2A4F40F6CCA85BB2B9F13F56E17A14AE2F4F40EC5455555555F13F3600252BAC334F40F8BD7935F12CF13F2DC3403946354F4008263108AC9CF03FF430BE55C43A4F40FD5D6F392210F03F0E00000000404F40EC5455555555F53F0E00000000404F4011AEAAAAAAAAFA3F0E00000000404F4087000000000000400E00000000404F4006AAAAAAAAAA02400E00000000404F4003555555555505400E00000000404F4087000000000008400E00000000404F4084ABAAAAAAAA0A400E00000000404F408256555555550D400E00000000404F4000000000000010402A00000000404F40BE111111111111402A00000000404F40BE11111111111140DDBBBBBBBB3B4F404022222222221140DDBBBBBBBB3B4F4040222222222211407377777777374F403E333333333311407377777777374F403E333333333311407655555555354F4040454444444411407655555555354F407F54E3A59B4411404133333333334F40C2555555555511404133333333334F40C2555555555511400C11111111314F40C0666666666611400C11111111314F40C0666666666611401EEFEEEEEE2E4F40C2787777777711401EEFEEEEEE2E4F40C278777777771140DBCCCCCCCC2C4F404188888888881140DBCCCCCCCC2C4F404188888888881140D0AAAAAAAA2A4F40429A999999991140D0AAAAAAAA2A4F40429A999999991140A988888888284F40C5AAAAAAAAAA1140A988888888284F40C5AAAAAAAAAA11406666666666264F40C4CDCCCCCCCC11406666666666264F4005CDCCCCCCCC11404E44444444244F4005F0EEEEEEEE11405C44444444244F4005F0EEEEEEEE11403522222222224F407B232222222212403522222222224F407B232222222212400000000000204F407D666666666612400000000000204F407D6666666666124003DEDDDDDD1D4F4000ACAAAAAAAA124003DEDDDDDD1D4F40BFA8AAAAAAAA12401C00000000004F40C2555555555511401C00000000004F40', '<MultiGeometry><Polygon><outerBoundaryIs><LinearRing><coordinates>4.331612180906903,61.999559093771097 4.331446818260797,61.499679354188586 4.331644674597042,61.499539044131978 4.331660482354825,61.249529090086767 4.331676007440409,60.999519183769721 4.431679118360682,60.99952063378359 4.431694343870172,60.749510772529959 4.431709301328479,60.499500959784676 4.331706238217381,60.499499515932754 4.33172095761778,60.249489755210213 3.998377532461695,60.249484936344395 3.66503417063123,60.249480092345763 3.665048786040898,59.999470402036032 3.665063149859905,59.749460761599643 3.665077268242845,59.4994511714211 3.665091147143809,59.24944163188097 3.665104792324465,58.999432143355641 3.998447790182674,58.999436933655815 3.998461138143454,58.749427485535215 3.998474264531399,58.499418089090582 4.331817185458596,58.499422832664486 4.331830028276388,58.249413477182522 4.665172941295895,58.249418184905572 4.66518550740294,57.999408870655436 4.99852841246202,57.999413542423817 4.998540708506467,57.74940426967224 5.331883605551432,57.749408905385799 5.665226560074247,57.749413515987875 5.665238526955081,57.49940427396006 5.998581472679374,57.499408848324578 6.331924474825542,57.499413397336497 6.665267533066392,57.499417920842149 6.998610647072602,57.499422418688283 6.998622160283701,57.249413185966503 6.998624669594032,57.194386160963766 6.935290398705466,57.174409576553074 6.915290084022056,57.168522980546477 6.906981620139272,57.166075556806469 6.831955445043162,57.143940402225255 6.748620815114151,57.119266153323629 6.665286193848553,57.094508567494479 6.625768919652622,57.08273538111662 6.581951581617584,57.069659311111174 6.498616978286773,57.044721162067034 6.415282383848418,57.019694120375163 6.347906370718671,56.999395244723679 6.331947579299201,56.999395028629309 6.331947798294003,56.994578186049168 6.248613221489142,56.96937613698087 6.165278653930541,56.94407686166771 6.081944095104267,56.918691471639818 6.073302301804947,56.916055147082702 5.998609545128215,56.893217189031155 5.91527500411952,56.867651235976929 5.831940472195014,56.84199083461197 5.801873375045848,56.832715087727145 5.748605948841592,56.816247096464927 5.66527143455399,56.790408910035019 5.53353347480937,56.749375066120827 5.331933466738113,56.686136682676029 5.03192941773867,56.591029127557796 4.998595571145595,56.581945007874737 4.697777112602289,56.499354552173841 4.66525718077027,56.490362112822588 4.331918927183255,56.397437494530578 3.998580810844031,56.303151708661737 3.810442060670134,56.249333275254671 3.665242831677634,56.207496422405583 3.331904989576034,56.110463302966522 3.248570550563822,56.085986264426062 3.046280000275219,56.24932251466241 2.998554761605775,56.287606528063101 2.732465699879847,56.499326930109916 2.665200326268525,56.552386192582468 2.611863611423437,56.594328591714429 2.537595982186807,56.749333064773317 2.416464105223407,56.999340294991107 2.331828442720983,57.17197585384465 2.293631954419635,57.249347543408717 2.169057856087469,57.499354808839023 2.042702914191656,57.749362090120883 1.998452833202363,57.836075730170556 1.963448368946577,57.904366611916991 1.877452226437258,57.999368842719768 1.665089828230543,58.231585390977607 1.648693995180475,58.249374695436458 1.481740947573368,58.429378892239285 1.499898779008541,58.499381758967907 1.565353622158926,58.749392042209479 1.631763845554084,58.999402395510046 1.665041166306461,59.12330755261037 1.699157223585245,59.249412818913527 1.710033036137676,59.289414493162965 1.834813431488976,59.499424313223038 1.985500445235015,59.749436087356273 1.998346799648668,59.770570420170557 2.07500829587919,59.89610970393484 2.055551623712845,59.999446717104668 2.042780743957466,60.066901553990697 2.007971381117166,60.249455645310121 1.998315277805927,60.299735222950851 1.959657499609883,60.499464608834408 1.910584970735874,60.749473606849591 1.860739897194635,60.999482638687084 1.810097269953174,61.249491703505228 1.788242423645106,61.356162247680345 1.702163718514217,61.499499944615209 1.664891830906612,61.561140709555282 1.558210192865959,61.736173812683482 1.551943337394049,61.736173717275982 1.542869938714679,61.7495074425144 1.371178188860573,61.999514782872374 1.331514690467483,62.056660964390751 1.313287401364807,62.082850560991659 1.255057591010739,62.166186335910005 1.248170581748284,62.176011623656485 1.19649156690258,62.249522107533373 1.176122188332413,62.278392396459623 1.164826307473756,62.293806730034682 1.140089827508275,62.327502146251064 1.135992099415791,62.332857853756941 1.105988393085993,62.37202563150251 1.081482637858308,62.403218174064811 1.071620329482495,62.415732413997347 1.036393950957246,62.45864470764262 1.002078845575599,62.499529156675813 1.331483383709477,62.499534230705436 1.664827002037165,62.499539341233721 1.998170691042048,62.499544427269605 2.33151445037398,62.499549488640909 2.664858279680261,62.499554525176293 2.998202178605536,62.499559536705263 3.3315461467921,62.499564523058211 3.664890183880062,62.499569484066306 3.99823428950698,62.499574419561803 4.264909623112015,62.49957834947655 4.264911912773598,62.46624366164351 4.281579121965299,62.466243906650739 4.28158140530136,62.432909219565431 4.298248614061071,62.432909464443242 4.298249753289369,62.416242121173575 4.314916961918225,62.416242365954403 4.315251443592258,62.399575027749904 4.331585307921637,62.399575267539419 4.331586443708245,62.382907924611601 4.348253652075134,62.382908169198409 4.348254786145734,62.366240826442443 4.364921994382196,62.366241070932205 4.364923126740004,62.349573728347082 4.381590334845382,62.349573972739769 4.381591465493605,62.332906630326519 4.398258673469178,62.332906874622125 4.398259802411014,62.31623953238023 4.414927010256014,62.31623977657874 4.414928137494656,62.299572434508356 4.448262553093021,62.299572922646512 4.448263678333438,62.2829055807156 4.481598094007611,62.282906068530366 4.481599217253792,62.266238726738734 4.531600841129511,62.266239457878015 4.531601962087154,62.249572116193228 4.598270795075607,62.249573090009427 4.59827191345085,62.232905748399666 4.664940747925416,62.232906721049275 4.664956244040196,61.99956395822295 4.331612180906903,61.999559093771097</coordinates></LinearRing></outerBoundaryIs></Polygon></MultiGeometry>', 4);
SELECT pg_catalog.setval('public.apaareagross_apaareagross_id_seq', 4, true);
SELECT pg_catalog.setval('public.apaareanet_apaareanet_id_seq', 938, true);
SELECT pg_catalog.setval('public.prlarea_prlarea_id_seq', 1500, true);
SELECT pg_catalog.setval('public.seaarea_seaarea_id_seq', 3129, true);
SELECT pg_catalog.setval('public.seis_acquisition_progress_seis_acquisition_progress_id_seq', 10314, true);
SELECT pg_catalog.setval('public.wellbore_casing_and_lot_wellbore_casing_and_lot_id_seq', 5254, true);
SELECT pg_catalog.setval('public.wellbore_core_photo_wellbore_core_photo_id_seq', 18183, true);
SELECT pg_catalog.setval('public.wellbore_core_wellbore_core_id_seq', 7634, true);
SELECT pg_catalog.setval('public.wellbore_document_wellbore_document_id_seq', 6472, true);
SELECT pg_catalog.setval('public.wellbore_mud_wellbore_mud_id_seq', 27682, true);
SELECT pg_catalog.setval('public.wellbore_oil_sample_wellbore_oil_sample_id_seq', 736, true);
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
    ADD CONSTRAINT "dscArea_ibfk_1" FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.dscarea
    ADD CONSTRAINT "dscArea_ibfk_2" FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery);
ALTER TABLE ONLY public.dscarea
    ADD CONSTRAINT "dscArea_ibfk_3" FOREIGN KEY (dscnpdidresinclindiscovery) REFERENCES public.discovery(dscnpdiddiscovery);
ALTER TABLE ONLY public.facility_moveable
    ADD CONSTRAINT facility_moveable_ibfk_1 FOREIGN KEY (fclnpdidcurrentrespcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.fclpoint
    ADD CONSTRAINT "fclPoint_ibfk_1" FOREIGN KEY (fclnpdidfacility) REFERENCES public.facility_fixed(fclnpdidfacility);
ALTER TABLE ONLY public.fclpoint
    ADD CONSTRAINT "fclPoint_ibfk_2" FOREIGN KEY (fclbelongstos) REFERENCES public.tuf_petreg_licence(tufnpdidtuf);
ALTER TABLE ONLY public.field_activity_status_hst
    ADD CONSTRAINT field_activity_status_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.field_description
    ADD CONSTRAINT field_description_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.field
    ADD CONSTRAINT field_ibfk_1 FOREIGN KEY (fldnpdidowner) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.field
    ADD CONSTRAINT field_ibfk_2 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.field
    ADD CONSTRAINT field_ibfk_3 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.field_investment_yearly
    ADD CONSTRAINT field_investment_yearly_ibfk_1 FOREIGN KEY (prfnpdidinformationcarrier) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.field_licensee_hst
    ADD CONSTRAINT field_licensee_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.field_licensee_hst
    ADD CONSTRAINT field_licensee_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.field_operator_hst
    ADD CONSTRAINT field_operator_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.field_operator_hst
    ADD CONSTRAINT field_operator_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.field_owner_hst
    ADD CONSTRAINT field_owner_hst_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.field_reserves
    ADD CONSTRAINT field_reserves_ibfk_1 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.fldarea
    ADD CONSTRAINT "fldArea_ibfk_1" FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.fldarea
    ADD CONSTRAINT "fldArea_ibfk_2" FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery);
ALTER TABLE ONLY public.fldarea
    ADD CONSTRAINT "fldArea_ibfk_3" FOREIGN KEY (dscnpdidresinclindiscovery) REFERENCES public.discovery(dscnpdiddiscovery);
ALTER TABLE ONLY public.licence_area_poly_hst
    ADD CONSTRAINT licence_area_poly_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_licensee_hst
    ADD CONSTRAINT licence_licensee_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_licensee_hst
    ADD CONSTRAINT licence_licensee_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.licence_oper_hst
    ADD CONSTRAINT licence_oper_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_oper_hst
    ADD CONSTRAINT licence_oper_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.licence_petreg_licence
    ADD CONSTRAINT licence_petreg_licence_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_petreg_licence_licencee
    ADD CONSTRAINT licence_petreg_licence_licencee_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_petreg_licence_licencee
    ADD CONSTRAINT licence_petreg_licence_licencee_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.licence_petreg_licence_oper
    ADD CONSTRAINT licence_petreg_licence_oper_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_petreg_licence_oper
    ADD CONSTRAINT licence_petreg_licence_oper_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.licence_petreg_message
    ADD CONSTRAINT licence_petreg_message_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_phase_hst
    ADD CONSTRAINT licence_phase_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT licence_task_ibfk_1 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT licence_task_ibfk_2 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_task
    ADD CONSTRAINT licence_task_ibfk_3 FOREIGN KEY (prltaskrefid) REFERENCES public.licence_task(prltaskid);
ALTER TABLE ONLY public.licence_transfer_hst
    ADD CONSTRAINT licence_transfer_hst_ibfk_1 FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.licence_transfer_hst
    ADD CONSTRAINT licence_transfer_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.pipline
    ADD CONSTRAINT "pipLine_ibfk_1" FOREIGN KEY (pipnpdidoperator) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.prlareasplitbyblock
    ADD CONSTRAINT "prlAreaSplitByBlock_ibfk_1" FOREIGN KEY (prllastoperatornpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.prlareasplitbyblock
    ADD CONSTRAINT "prlAreaSplitByBlock_ibfk_2" FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.prlarea
    ADD CONSTRAINT "prlArea_ibfk_1" FOREIGN KEY (prlnpdidlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.prlarea
    ADD CONSTRAINT "prlArea_ibfk_2" FOREIGN KEY (prllastoperatornpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.seaarea
    ADD CONSTRAINT "seaArea_ibfk_1" FOREIGN KEY (seanpdidsurvey) REFERENCES public.seis_acquisition(seanpdidsurvey);
ALTER TABLE ONLY public.seamultiline
    ADD CONSTRAINT "seaMultiline_ibfk_1" FOREIGN KEY (seasurveyname) REFERENCES public.seis_acquisition(seaname);
ALTER TABLE ONLY public.seis_acquisition_coordinates_inc_turnarea
    ADD CONSTRAINT seis_acquisition_coordinates_inc_turnarea_ibfk_1 FOREIGN KEY (seanpdidsurvey) REFERENCES public.seis_acquisition(seanpdidsurvey);
ALTER TABLE ONLY public.seis_acquisition
    ADD CONSTRAINT seis_acquisition_ibfk_1 FOREIGN KEY (seacompanyreported) REFERENCES public.company(cmplongname);
ALTER TABLE ONLY public.seis_acquisition_progress
    ADD CONSTRAINT seis_acquisition_progress_ibfk_1 FOREIGN KEY (seanpdidsurvey) REFERENCES public.seis_acquisition(seanpdidsurvey);
ALTER TABLE ONLY public.strat_litho_wellbore_core
    ADD CONSTRAINT strat_litho_wellbore_core_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.strat_litho_wellbore
    ADD CONSTRAINT strat_litho_wellbore_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.tuf_operator_hst
    ADD CONSTRAINT tuf_operator_hst_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf);
ALTER TABLE ONLY public.tuf_operator_hst
    ADD CONSTRAINT tuf_operator_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.tuf_owner_hst
    ADD CONSTRAINT tuf_owner_hst_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf);
ALTER TABLE ONLY public.tuf_owner_hst
    ADD CONSTRAINT tuf_owner_hst_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.tuf_petreg_licence_licencee
    ADD CONSTRAINT tuf_petreg_licence_licencee_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf);
ALTER TABLE ONLY public.tuf_petreg_licence_licencee
    ADD CONSTRAINT tuf_petreg_licence_licencee_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.tuf_petreg_licence_oper
    ADD CONSTRAINT tuf_petreg_licence_oper_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf);
ALTER TABLE ONLY public.tuf_petreg_licence_oper
    ADD CONSTRAINT tuf_petreg_licence_oper_ibfk_2 FOREIGN KEY (cmpnpdidcompany) REFERENCES public.company(cmpnpdidcompany);
ALTER TABLE ONLY public.tuf_petreg_message
    ADD CONSTRAINT tuf_petreg_message_ibfk_1 FOREIGN KEY (tufnpdidtuf) REFERENCES public.tuf_petreg_licence(tufnpdidtuf);
ALTER TABLE ONLY public.wellbore_casing_and_lot
    ADD CONSTRAINT wellbore_casing_and_lot_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_coordinates
    ADD CONSTRAINT wellbore_coordinates_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_core
    ADD CONSTRAINT wellbore_core_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_core_photo
    ADD CONSTRAINT wellbore_core_photo_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_1 FOREIGN KEY (wlbdrillingoperator) REFERENCES public.company(cmplongname);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_2 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_3 FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_4 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_5 FOREIGN KEY (prlnpdidproductionlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_6 FOREIGN KEY (wlbnpdidwellborereclass) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_development_all
    ADD CONSTRAINT wellbore_development_all_ibfk_7 FOREIGN KEY (wlbdiskoswelloperator) REFERENCES public.company(cmpshortname);
ALTER TABLE ONLY public.wellbore_document
    ADD CONSTRAINT wellbore_document_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_dst
    ADD CONSTRAINT wellbore_dst_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_1 FOREIGN KEY (wlbdrillingoperator) REFERENCES public.company(cmplongname);
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_2 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_3 FOREIGN KEY (dscnpdiddiscovery) REFERENCES public.discovery(dscnpdiddiscovery);
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_4 FOREIGN KEY (fldnpdidfield) REFERENCES public.field(fldnpdidfield);
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_5 FOREIGN KEY (wlbnpdidwellborereclass) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_exploration_all
    ADD CONSTRAINT wellbore_exploration_all_ibfk_6 FOREIGN KEY (prlnpdidproductionlicence) REFERENCES public.licence(prlnpdidlicence);
ALTER TABLE ONLY public.wellbore_formation_top
    ADD CONSTRAINT wellbore_formation_top_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_mud
    ADD CONSTRAINT wellbore_mud_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_oil_sample
    ADD CONSTRAINT wellbore_oil_sample_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wellbore_shallow_all
    ADD CONSTRAINT wellbore_shallow_all_ibfk_1 FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
ALTER TABLE ONLY public.wlbpoint
    ADD CONSTRAINT "wlbPoint_ibfk_1" FOREIGN KEY (wlbnpdidwellbore) REFERENCES public.wellbore_npdid_overview(wlbnpdidwellbore);
