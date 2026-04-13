You are given a relational database scenario.

## Scenario path
/root/ontology/burr_benchmark/real-world/mondial


## Parsed table definitions
{
  "City": "Name VARCHAR(50),\n Country VARCHAR(4),\n Province VARCHAR(50),\n Population DECIMAL,\n Latitude DECIMAL,\n Longitude DECIMAL,\n Elevation DECIMAL,\n CONSTRAINT CityKey PRIMARY KEY (Name, Country, Province)",
  "Citylocalname": "City VARCHAR(50),\n Country VARCHAR(4),\n Province VARCHAR(50),\n localname VARCHAR(300),\n CONSTRAINT CitylocalnameKey PRIMARY KEY (Country, Province, City)",
  "Cityothername": "City VARCHAR(50),\n Country VARCHAR(4),\n Province VARCHAR(50),\n othername VARCHAR(50),\n CONSTRAINT CityOthernameKey PRIMARY KEY (Country, Province, City, othername)",
  "Citypops": "City VARCHAR(50),\n Country VARCHAR(4),\n Province VARCHAR(50),\n Year DECIMAL,\n Population DECIMAL,\n CONSTRAINT CityPopKey PRIMARY KEY (Country, Province, City, Year)",
  "Continent": "Name VARCHAR(20) CONSTRAINT ContinentKey PRIMARY KEY,\n Area DECIMAL(10)",
  "Country": "Name VARCHAR(50) NOT NULL UNIQUE,\n Code VARCHAR(4) CONSTRAINT CountryKey PRIMARY KEY,\n Capital VARCHAR(50),\n Province VARCHAR(50),\n Area DECIMAL,\n Population DECIMAL",
  "Countrylocalname": "Country VARCHAR(4),\n localname VARCHAR(300),\n CONSTRAINT CountrylocalnameKey PRIMARY KEY (Country)",
  "Countryothername": "Country VARCHAR(4),\n othername VARCHAR(50),\n CONSTRAINT CountryOthernameKey PRIMARY KEY (Country, othername)",
  "Countrypops": "Country VARCHAR(4),\n Year DECIMAL,\n Population DECIMAL,\n CONSTRAINT CountryPopsKey PRIMARY KEY (Country, Year)",
  "Desert": "Name VARCHAR(50) CONSTRAINT DesertKey PRIMARY KEY,\n Area DECIMAL,\n Latitude DECIMAL,\n  Longitude DECIMAL",
  "Economy": "Country VARCHAR(4) CONSTRAINT EconomyKey PRIMARY KEY,\n GDP DECIMAL,\n Agriculture DECIMAL,\n Service DECIMAL,\n Industry DECIMAL,\n Inflation DECIMAL,\n Unemployment DECIMAL",
  "EthnicGroup": "Country VARCHAR(4),\n Name VARCHAR(50),\n Percentage DECIMAL,\n CONSTRAINT EthnicKey PRIMARY KEY (Name, Country)",
  "Island": "Name VARCHAR(50) CONSTRAINT IslandKey PRIMARY KEY,\n Islands VARCHAR(50),\n Area DECIMAL ,\n Elevation DECIMAL,\n Type VARCHAR(15),\n Latitude DECIMAL,\n  Longitude DECIMAL",
  "Lake": "Name VARCHAR(50) CONSTRAINT LakeKey PRIMARY KEY,\n River VARCHAR(50),\n Area DECIMAL ,\n Elevation DECIMAL,\n Depth DECIMAL,\n Height DECIMAL,\n Type VARCHAR(12),\n Latitude DECIMAL,\n  Longitude DECIMAL",
  "LakeOnIsland": "Lake    VARCHAR(50),\n Island  VARCHAR(50),\n CONSTRAINT LakeIslKey PRIMARY KEY (Lake, Island)",
  "Language": "Name VARCHAR(50) ,\n Superlanguage VARCHAR(50),\n CONSTRAINT LanguageKey PRIMARY KEY (Name)",
  "Mountain": "Name VARCHAR(50) CONSTRAINT MountainKey PRIMARY KEY,\n Mountains VARCHAR(50),\n Elevation DECIMAL,\n Type VARCHAR(10),\n Latitude DECIMAL,\n  Longitude DECIMAL",
  "MountainOnIsland": "Mountain VARCHAR(50),\n Island   VARCHAR(50),\n CONSTRAINT MountainIslKey PRIMARY KEY (Mountain, Island)",
  "Organization": "Abbreviation VARCHAR(12) Constraint OrgKey PRIMARY KEY,\n Name VARCHAR(100) NOT NULL,\n City VARCHAR(50) ,\n Country VARCHAR(4) ,\n Province VARCHAR(50) ,\n Established DATE,\n CONSTRAINT OrgNameUnique UNIQUE (Name)",
  "Politics": "Country VARCHAR(4) CONSTRAINT PoliticsKey PRIMARY KEY,\n Independence DATE,\n WasDependent VARCHAR(50),\n Dependent  VARCHAR(4),\n Government VARCHAR(120)",
  "Population": "Country VARCHAR(4) CONSTRAINT PopKey PRIMARY KEY,\n Population_Growth DECIMAL,\n Infant_Mortality DECIMAL",
  "Province": "Name VARCHAR(50) CONSTRAINT PrName NOT NULL ,\n Country  VARCHAR(4) CONSTRAINT PrCountry NOT NULL ,\n Population DECIMAL,\n Area DECIMAL,\n Capital VARCHAR(50),\n CapProv VARCHAR(50),\n CONSTRAINT PrKey PRIMARY KEY (Name, Country)",
  "Provincelocalname": "Province VARCHAR(50),\n Country VARCHAR(4),\n localname VARCHAR(300),\n CONSTRAINT ProvlocalnameKey PRIMARY KEY (Country, Province)",
  "Provinceothername": "Province VARCHAR(50),\n Country VARCHAR(4),\n othername VARCHAR(50),\n CONSTRAINT ProvOthernameKey PRIMARY KEY (Country, Province, othername)",
  "Provpops": "Province VARCHAR(50),\n Country VARCHAR(4),\n Year DECIMAL ,\n Population DECIMAL,\n CONSTRAINT ProvPopKey PRIMARY KEY (Country, Province, Year)",
  "Religion": "Country VARCHAR(4),\n Name VARCHAR(50),\n Percentage DECIMAL,\n CONSTRAINT ReligionKey PRIMARY KEY (Name, Country)",
  "River": "Name VARCHAR(50) CONSTRAINT RiverKey PRIMARY KEY,\n River VARCHAR(50),\n Lake VARCHAR(50),\n Sea VARCHAR(50),\n Length DECIMAL,\n Area DECIMAL,\n SourceLatitude DECIMAL,\n SourceLongitude DECIMAL,\n Mountains VARCHAR(50),\n SourceElevation DECIMAL,\n EstuaryLatitude DECIMAL,\n EstuaryLongitude DECIMAL,\n EstuaryElevation DECIMAL,\n CONSTRAINT RivFlowsInto\n     CHECK ((River IS NULL AND Lake IS NULL)\n            OR (River IS NULL AND Sea IS NULL)\n            OR (Lake IS NULL AND Sea is NULL))",
  "RiverOnIsland": "River   VARCHAR(50),\n Island  VARCHAR(50),\n CONSTRAINT RiverIslKey PRIMARY KEY (River, Island)",
  "RiverThrough": "River VARCHAR(50),\n Lake  VARCHAR(50),\n CONSTRAINT RThroughKey PRIMARY KEY (River,Lake)",
  "Sea": "Name VARCHAR(50) CONSTRAINT SeaKey PRIMARY KEY,\n Area DECIMAL,\n Depth DECIMAL",
  "Spoken": "Country VARCHAR(4),\n Language VARCHAR(50),\n Percentage DECIMAL,\n CONSTRAINT SpokenKey PRIMARY KEY (Country, Language)",
  "borders": "Country1 VARCHAR(4),\n Country2 VARCHAR(4),\n Length DECIMAL ,\n CONSTRAINT BorderKey PRIMARY KEY (Country1,Country2)",
  "encompasses": "Country VARCHAR(4) NOT NULL,\n Continent VARCHAR(20) NOT NULL,\n Percentage DECIMAL,\n CONSTRAINT EncompassesKey PRIMARY KEY (Country,Continent)",
  "geo_Desert": "Desert VARCHAR(50) ,\n Country VARCHAR(4) ,\n Province VARCHAR(50) ,\n CONSTRAINT GDesertKey PRIMARY KEY (Province, Country, Desert)",
  "geo_Estuary": "River VARCHAR(50) ,\n Country VARCHAR(4) ,\n Province VARCHAR(50) ,\n CONSTRAINT GEstuaryKey PRIMARY KEY (Province, Country, River)",
  "geo_Island": "Island VARCHAR(50) ,\n Country VARCHAR(4) ,\n Province VARCHAR(50) ,\n CONSTRAINT GIslandKey PRIMARY KEY (Province, Country, Island)",
  "geo_Lake": "Lake VARCHAR(50) ,\n Country VARCHAR(4) ,\n Province VARCHAR(50) ,\n CONSTRAINT GLakeKey PRIMARY KEY (Province, Country, Lake)",
  "geo_Mountain": "Mountain VARCHAR(50) ,\n Country VARCHAR(4) ,\n Province VARCHAR(50) ,\n CONSTRAINT GMountainKey PRIMARY KEY (Province,Country,Mountain)",
  "geo_River": "River VARCHAR(50),\n Country VARCHAR(4),\n Province VARCHAR(50),\n CONSTRAINT GRiverKey PRIMARY KEY (Province ,Country, River)",
  "geo_Sea": "Sea VARCHAR(50) ,\n Country VARCHAR(4)  ,\n Province VARCHAR(50) ,\n CONSTRAINT GSeaKey PRIMARY KEY (Province, Country, Sea)"
}


## Tool-derived structural evidence
{
  "enabled_tools": [
    "mapping_verifier_lite",
    "pattern_detector",
    "schema_profiler"
  ],
  "schema_summary": {
    "num_tables": 46,
    "num_foreign_keys": 0,
    "num_composite_primary_keys": 30
  },
  "join_graph": {
    "Country": [],
    "City": [],
    "Population": [],
    "Province": [],
    "Economy": [],
    "Politics": [],
    "Religion": [],
    "EthnicGroup": [],
    "Spoken": [],
    "Language": [],
    "Countrypops": [],
    "Countryothername": [],
    "Countrylocalname": [],
    "Provpops": [],
    "Provinceothername": [],
    "Provincelocalname": [],
    "Citypops": [],
    "Cityothername": [],
    "Citylocalname": [],
    "Continent": [],
    "borders": [],
    "encompasses": [],
    "Organization": [],
    "isMember": [],
    "Mountain": [],
    "Desert": [],
    "Island": [],
    "Lake": [],
    "Sea": [],
    "River": [],
    "RiverThrough": [],
    "geo_Mountain": [],
    "geo_Desert": [],
    "geo_Island": [],
    "geo_River": [],
    "geo_Sea": [],
    "geo_Lake": [],
    "geo_Source": [],
    "geo_Estuary": [],
    "mergesWith": [],
    "located": [],
    "locatedOn": [],
    "islandIn": [],
    "MountainOnIsland": [],
    "LakeOnIsland": [],
    "RiverOnIsland": []
  },
  "instance_summary": {
    "tables": {},
    "cross_table_value_overlap": []
  },
  "hypothesis_summary": {
    "num_hypotheses": 46,
    "by_kind": {
      "ClassHypothesis": 46
    },
    "by_status": {
      "proposed": 46
    }
  },
  "hypotheses": [
    {
      "kind": "ClassHypothesis",
      "statement": "Table City likely maps to ontology class City",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "City",
        "suggested_label": "City"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Name",
            "Country",
            "Province"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Province likely maps to ontology class Province",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Province",
        "suggested_label": "Province"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Name",
            "Country"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Religion likely maps to ontology class Religion",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Religion",
        "suggested_label": "Religion"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Name",
            "Country"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table EthnicGroup likely maps to ontology class Ethnicgroup",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "EthnicGroup",
        "suggested_label": "Ethnicgroup"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Name",
            "Country"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Spoken likely maps to ontology class Spoken",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Spoken",
        "suggested_label": "Spoken"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Language"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Language likely maps to ontology class Language",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Language",
        "suggested_label": "Language"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Name"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Countrypops likely maps to ontology class Countrypops",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Countrypops",
        "suggested_label": "Countrypops"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Year"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Countryothername likely maps to ontology class Countryothername",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Countryothername",
        "suggested_label": "Countryothername"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "othername"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Countrylocalname likely maps to ontology class Countrylocalname",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Countrylocalname",
        "suggested_label": "Countrylocalname"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Provpops likely maps to ontology class Provpops",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Provpops",
        "suggested_label": "Provpops"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Province",
            "Year"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Provinceothername likely maps to ontology class Provinceothername",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Provinceothername",
        "suggested_label": "Provinceothername"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Province",
            "othername"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Provincelocalname likely maps to ontology class Provincelocalname",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Provincelocalname",
        "suggested_label": "Provincelocalname"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Province"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Citypops likely maps to ontology class Citypops",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Citypops",
        "suggested_label": "Citypops"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Province",
            "City",
            "Year"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Cityothername likely maps to ontology class Cityothername",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Cityothername",
        "suggested_label": "Cityothername"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Province",
            "City",
            "othername"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table Citylocalname likely maps to ontology class Citylocalname",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "Citylocalname",
        "suggested_label": "Citylocalname"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Province",
            "City"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table borders likely maps to ontology class Borders",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "borders",
        "suggested_label": "Borders"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country1",
            "Country2"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table encompasses likely maps to ontology class Encompasses",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "encompasses",
        "suggested_label": "Encompasses"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Continent"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table isMember likely maps to ontology class Ismember",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "isMember",
        "suggested_label": "Ismember"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Country",
            "Organization"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table RiverThrough likely maps to ontology class Riverthrough",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "RiverThrough",
        "suggested_label": "Riverthrough"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "River",
            "Lake"
          ]
        }
      ]
    },
    {
      "kind": "ClassHypothesis",
      "statement": "Table geo_Mountain likely maps to ontology class Geo_Mountain",
      "confidence": 0.7999999999999999,
      "payload": {
        "table": "geo_Mountain",
        "suggested_label": "Geo_Mountain"
      },
      "evidence": [
        {
          "type": "primary_key",
          "value": [
            "Province",
            "Country",
            "Mountain"
          ]
        }
      ]
    }
  ],
  "revision_guidance": []
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
- For data_properties, use fields:
  - id
  - label
  - domain
  - range
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

Return JSON only.
