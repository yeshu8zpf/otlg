You are given a relational database scenario.

## Scenario path
/root/ontology/burr_benchmark/real-world/iswc


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

### Canonical constraints
- Use exact top-level keys listed above.
- For classes, use fields:
  - id
  - label
  - status
  - confidence
  - description (optional)
- For data_property_mappings, use fields:
  - data_property_id
  - source_table
  - source_columns
  - applies_to_class
  - join_paths
  - value_template
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
- For data_property_mappings, use fields:
  - data_property_id
  - source_table
  - source_columns
  - applies_to_class
  - value_template
  - status
  - confidence
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
- Do not invent domain properties unsupported by schema or samples.
- When tool-derived evidence is present, treat it as strong structural guidance.
- For data properties sourced from auxiliary/value tables, include join_paths that connect the owner class instance to the value table.


Return JSON only.
