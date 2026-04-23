You are given a relational database scenario.

## Scenario path
/root/ontology/burr_benchmark/real-world/iswc

## Compact schema SQL
CREATE TABLE conferences (
  ConfID int NOT NULL default '0',
  Name varchar(100) default NULL,
  URI varchar(200) default NULL,
  Date varchar(50) default NULL,
  Location varchar(50) default NULL,
  Datum timestamp(0) default NULL,
  PRIMARY KEY  (ConfID)
) ;

-- 
-- SQLINES DEMO *** table `conferences`
-- 

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `organizations`
-- 

CREATE TABLE organizations (
  OrgID int NOT NULL default '0',
  Type varchar(50) default NULL,
  Name varchar(200) default NULL,
  Address varchar(200),
  Location varchar(50) default NULL,
  Postcode varchar(10) default NULL,
  Country varchar(50) default NULL,
  URI varchar(100) default NULL,
  Belongsto int default NULL,
  Homepage varchar(200) default NULL,
  PRIMARY KEY  (OrgID)
) ;

CREATE INDEX Belongsto ON organizations (Belongsto);

-- 
-- SQLINES DEMO *** table `organizations`
-- 

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `papers`
-- 

CREATE TABLE papers (
  PaperID int NOT NULL default '0',
  Title varchar(200) default NULL,
  Abstract varchar(2000),
  URI varchar(200) default NULL,
  Year int default NULL,
  Conference int default NULL,
  Publish int default NULL,
  PRIMARY KEY  (PaperID)
) ;

CREATE INDEX Conference ON papers (Conference);

-- 
-- SQLINES DEMO *** table `papers`
-- 

they have little ability to interact with heterogeneous data and information types. Because we haven''t yet delivered large-scale, agent-based mediation, some commentators argue that the Semantic Web has failed to deliver. We argue that agents can only flourish when standards are well established and that the Web standards for expressing shared meaning have progressed steadily over the past five years. Furthermore, we see the use of ontologies in the e-science community presaging ultimate success for the Semantic Web--just as the use of HTTP within the CERN particle physics community led to the revolutionary success of the original Web. This article is part of a special issue on the Future of AI.', 'http://eprints.ecs.soton.ac.uk/12614/01/Semantic_Web_Revisted.pdf', 2006, NULL, 1),
(8, 'D2R Server - Publishing Relational Databases on the Web as SPARQL Endpoints', 'The Resource Description Framework and the SPARQL query language provide a standardized way for exposing and linking data sources on the Web. D2R Server is a turn-key solution for making the content of existing, non-RDF databases accessible as SPARQL endpoints. The server takes SPARQL queries from the Web and rewrites them via a mapping into SQL queries against a relational database. This on-the-fly translation allows RDF applications to access the content of large databases without having to replicate them into RDF. D2R Server can be used to integrate existing databases into RDF systems, and to add SPARQL interfaces to database-backed software products. In the talk, we will give an introduction into the D2RQ mapping language, which is used to define mappings between relational and RDF schemata, and demonstrate how D2R Server can be used to extend a WordPress blog with a SPARQL interface.', 'http://www.wiwiss.fu-berlin.de/suhl/bizer/d2r-server/resources/d2r-server-slides-www2006.pdf', 2006, 23542, 1);

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `persons`
-- 

CREATE TABLE persons (
  PerID int NOT NULL default '0',
  Type varchar(50) default NULL,
  FirstName varchar(100) default NULL,
  LastName varchar(100) default NULL,
  Address varchar(2000) default NULL,
  Email varchar(100) default NULL,
  Homepage varchar(50) default NULL,
  Phone varchar(200) default NULL,
  URI varchar(200) default NULL,
  Photo varchar(200) default NULL,
  PRIMARY KEY  (PerID)
) ;

-- 
-- SQLINES DEMO *** table `persons`
-- 

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `rel_paper_topic`
-- 

CREATE TABLE rel_paper_topic (
  PaperID int NOT NULL default '0',
  TopicID int NOT NULL default '0',
  RelationType int default NULL,
  PRIMARY KEY  (PaperID,TopicID)
) ;

CREATE INDEX TopicID ON rel_paper_topic (TopicID);

-- 
-- SQLINES DEMO *** table `rel_paper_topic`
-- 

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `rel_person_organization`
-- 

CREATE TABLE rel_person_organization (
  PersonID int NOT NULL default '0',
  OrganizationID int NOT NULL default '0',
  PRIMARY KEY  (PersonID,OrganizationID)
) ;

CREATE INDEX OrganizationID ON rel_person_organization (OrganizationID);

-- 
-- SQLINES DEMO *** table `rel_person_organization`
-- 

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `rel_person_paper`
-- 

CREATE TABLE rel_person_paper (
  PersonID int NOT NULL default '0',
  PaperID int NOT NULL default '0',
  PRIMARY KEY  (PersonID,PaperID)
) ;

CREATE INDEX PaperID ON rel_person_paper (PaperID);

-- 
-- SQLINES DEMO *** table `rel_person_paper`
-- 

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `rel_person_topic`
-- 

CREATE TABLE rel_person_topic (
  PersonID int NOT NULL default '0',
  TopicID int NOT NULL default '0',
  PRIMARY KEY  (PersonID,TopicID)
) ;

-- CREATE INDEX TopicID ON rel_person_topic (TopicID);

-- 
-- SQLINES DEMO *** table `rel_person_topic`
-- 

-- SQLINES DEMO *** ---------------------------------------

-- 
-- SQLINES DEMO *** or table `topics`
-- 

CREATE TABLE topics (
  TopicID int NOT NULL default '0',
  TopicName varchar(50) default NULL,
  URI varchar(200) default NULL,
  ParentID int default NULL,
  PRIMARY KEY  (TopicID)
) ;

CREATE INDEX ParentID ON topics (ParentID);

-- 
-- SQLINES DEMO *** table `topics`
-- 

-- 
-- SQLINES DEMO *** umped tables
-- 

-- 
-- SQLINES DEMO *** able `organizations`
-- 
ALTER TABLE organizations
  ADD CONSTRAINT organizations_ibfk_1 FOREIGN KEY (Belongsto) REFERENCES organizations (OrgID);

-- 
-- SQLINES DEMO *** able `papers`
-- 
ALTER TABLE papers
  ADD CONSTRAINT papers_ibfk_1 FOREIGN KEY (Conference) REFERENCES conferences (ConfID);

-- 
-- SQLINES DEMO *** able `rel_paper_topic`
-- 
ALTER TABLE rel_paper_topic
  ADD CONSTRAINT rel_paper_topic_ibfk_1 FOREIGN KEY (PaperID) REFERENCES papers (PaperID),
  ADD CONSTRAINT rel_paper_topic_ibfk_2 FOREIGN KEY (TopicID) REFERENCES topics (TopicID);

-- 
-- SQLINES DEMO *** able `rel_person_organization`
-- 
ALTER TABLE rel_person_organization
  ADD CONSTRAINT rel_person_organization_ibfk_1 FOREIGN KEY (PersonID) REFERENCES persons (PerID),
  ADD CONSTRAINT rel_person_organization_ibfk_2 FOREIGN KEY (OrganizationID) REFERENCES organizations (OrgID);

-- 
-- SQLINES DEMO *** able `rel_person_paper`
-- 
ALTER TABLE rel_person_paper
  ADD CONSTRAINT rel_person_paper_ibfk_1 FOREIGN KEY (PersonID) REFERENCES persons (PerID),
  ADD CONSTRAINT rel_person_paper_ibfk_2 FOREIGN KEY (PaperID) REFERENCES papers (PaperID);

-- 
-- SQLINES DEMO *** able `rel_person_topic`
-- 
ALTER TABLE rel_person_topic
  ADD CONSTRAINT rel_person_topic_ibfk_1 FOREIGN KEY (PersonID) REFERENCES persons (PerID),
  ADD CONSTRAINT rel_person_topic_ibfk_2 FOREIGN KEY (TopicID) REFERENCES topics (TopicID);

-- 
-- SQLINES DEMO *** able `topics`
-- 
ALTER TABLE topics
  ADD CONSTRAINT topics_ibfk_1 FOREIGN KEY (ParentID) REFERENCES topics (TopicID);

## Parsed table definitions
{
  "conferences": "ConfID int NOT NULL default '0',\n  Name varchar(100) default NULL,\n  URI varchar(200) default NULL,\n  Date varchar(50) default NULL,\n  Location varchar(50) default NULL,\n  Datum timestamp(0) default NULL,\n  PRIMARY KEY  (ConfID)\n) ;\n--\n-- SQLINES DEMO *** table `conferences`\n--\nINSERT INTO conferences (ConfID, Name, URI, Date, Location, Datum) VALUES\n(23541, 'International Semantic Web Conference 2002', 'http://annotation.semanticweb.org/iswc/iswc.daml#ISWC_2002', 'June 9-12, 2002', 'Sardinia', '2002-10-09 00:00:00'),\n(23542, '15th International World Wide Web Conference', NULL, 'May 23-26, 2006', 'Edinburgh', '2006-05-23 00:00:00'",
  "organizations": "OrgID int NOT NULL default '0',\n  Type varchar(50) default NULL,\n  Name varchar(200) default NULL,\n  Address varchar(200),\n  Location varchar(50) default NULL,\n  Postcode varchar(10) default NULL,\n  Country varchar(50) default NULL,\n  URI varchar(100) default NULL,\n  Belongsto int default NULL,\n  Homepage varchar(200) default NULL,\n  PRIMARY KEY  (OrgID)\n) ;\nCREATE INDEX Belongsto ON organizations (Belongsto",
  "papers": "PaperID int NOT NULL default '0',\n  Title varchar(200) default NULL,\n  Abstract varchar(2000),\n  URI varchar(200) default NULL,\n  Year int default NULL,\n  Conference int default NULL,\n  Publish int default NULL,\n  PRIMARY KEY  (PaperID)\n) ;\nCREATE INDEX Conference ON papers (Conference",
  "persons": "PerID int NOT NULL default '0',\n  Type varchar(50) default NULL,\n  FirstName varchar(100) default NULL,\n  LastName varchar(100) default NULL,\n  Address varchar(2000) default NULL,\n  Email varchar(100) default NULL,\n  Homepage varchar(50) default NULL,\n  Phone varchar(200) default NULL,\n  URI varchar(200) default NULL,\n  Photo varchar(200) default NULL,\n  PRIMARY KEY  (PerID)\n) ;\n--\n-- SQLINES DEMO *** table `persons`\n--\nINSERT INTO persons (PerID, Type, FirstName, LastName, Address, Email, Homepage, Phone, URI, Photo) VALUES\n(1, 'Full_Professor', 'Yolanda', 'Gil', NULL, 'gil@isi.edu', 'http://www.isi.edu/~gil', '310-448-8794', 'http://trellis.semanticweb.org/expect/web/semanticweb/iswc02_trellis.pdf#Yolanda Gil', 'http://www.isi.edu/~gil/y.g.v4.tiff'),\n(2, NULL, 'Varun', 'Ratnakar', NULL, 'varunr@isi.edu', 'http://www.isi.edu/~varunr', NULL, 'http://trellis.semanticweb.org/expect/web/semanticweb/iswc02_trellis.pdf#Varun Ratnakar', NULL),\n(3, 'Researcher', 'Jim', 'Blythe', NULL, 'blythe@isi.edu', 'http://www.isi.edu/~varunr', NULL, 'http://trellis.semanticweb.org/expect/web/semanticweb/iswc02_trellis.pdf#Jim Blythe', NULL),\n(4, 'Researcher', 'Andreas', 'Eberhart', 'International Uni\n... [truncated]",
  "rel_paper_topic": "PaperID int NOT NULL default '0',\n  TopicID int NOT NULL default '0',\n  RelationType int default NULL,\n  PRIMARY KEY  (PaperID,TopicID)\n) ;\nCREATE INDEX TopicID ON rel_paper_topic (TopicID",
  "rel_person_organization": "PersonID int NOT NULL default '0',\n  OrganizationID int NOT NULL default '0',\n  PRIMARY KEY  (PersonID,OrganizationID)\n) ;\nCREATE INDEX OrganizationID ON rel_person_organization (OrganizationID",
  "rel_person_paper": "PersonID int NOT NULL default '0',\n  PaperID int NOT NULL default '0',\n  PRIMARY KEY  (PersonID,PaperID)\n) ;\nCREATE INDEX PaperID ON rel_person_paper (PaperID",
  "rel_person_topic": "PersonID int NOT NULL default '0',\n  TopicID int NOT NULL default '0',\n  PRIMARY KEY  (PersonID,TopicID)\n) ;\n-- CREATE INDEX TopicID ON rel_person_topic (TopicID",
  "topics": "TopicID int NOT NULL default '0',\n  TopicName varchar(50) default NULL,\n  URI varchar(200) default NULL,\n  ParentID int default NULL,\n  PRIMARY KEY  (TopicID)\n) ;\nCREATE INDEX ParentID ON topics (ParentID"
}

## Sample rows
{}

## Tool-derived structural evidence
{
  "enabled_tools": [
    "schema_profiler"
  ],
  "schema_summary": {
    "num_tables": 9,
    "num_columns": 56,
    "num_foreign_keys": 7
  },
  "join_graph": {
    "conferences": [],
    "organizations": [
      {
        "to_table": "organizations",
        "from_columns": [
          "Belongsto"
        ],
        "to_columns": [
          "OrgID"
        ],
        "joins": [
          [
            "organizations.Belongsto",
            "=",
            "organizations.OrgID"
          ]
        ]
      }
    ],
    "papers": [
      {
        "to_table": "conferences",
        "from_columns": [
          "Conference"
        ],
        "to_columns": [
          "ConfID"
        ],
        "joins": [
          [
            "papers.Conference",
            "=",
            "conferences.ConfID"
          ]
        ]
      }
    ],
    "persons": [],
    "rel_paper_topic": [
      {
        "to_table": "papers",
        "from_columns": [
          "PaperID"
        ],
        "to_columns": [
          "PaperID"
        ],
        "joins": [
          [
            "rel_paper_topic.PaperID",
            "=",
            "papers.PaperID"
          ]
        ]
      }
    ],
    "rel_person_organization": [
      {
        "to_table": "persons",
        "from_columns": [
          "PersonID"
        ],
        "to_columns": [
          "PerID"
        ],
        "joins": [
          [
            "rel_person_organization.PersonID",
            "=",
            "persons.PerID"
          ]
        ]
      }
    ],
    "rel_person_paper": [
      {
        "to_table": "persons",
        "from_columns": [
          "PersonID"
        ],
        "to_columns": [
          "PerID"
        ],
        "joins": [
          [
            "rel_person_paper.PersonID",
            "=",
            "persons.PerID"
          ]
        ]
      }
    ],
    "rel_person_topic": [
      {
        "to_table": "persons",
        "from_columns": [
          "PersonID"
        ],
        "to_columns": [
          "PerID"
        ],
        "joins": [
          [
            "rel_person_topic.PersonID",
            "=",
            "persons.PerID"
          ]
        ]
      }
    ],
    "topics": [
      {
        "to_table": "topics",
        "from_columns": [
          "ParentID"
        ],
        "to_columns": [
          "TopicID"
        ],
        "joins": [
          [
            "topics.ParentID",
            "=",
            "topics.TopicID"
          ]
        ]
      }
    ]
  }
}


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
