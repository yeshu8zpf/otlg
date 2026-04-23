You are given a relational database scenario.

## Scenario path
/root/ontology/burr_benchmark/real-world/mondial

## Compact schema SQL
CREATE TABLE Country
(Name VARCHAR(50) NOT NULL UNIQUE,
 Code VARCHAR(4) CONSTRAINT CountryKey PRIMARY KEY,
 Capital VARCHAR(50),
 Province VARCHAR(50),
 Area DECIMAL,
 Population DECIMAL);

CREATE TABLE City
(Name VARCHAR(50),
 Country VARCHAR(4),
 Province VARCHAR(50),
 Population DECIMAL,
 Latitude DECIMAL,
 Longitude DECIMAL,
 Elevation DECIMAL,
 CONSTRAINT CityKey PRIMARY KEY (Name, Country, Province)
 );

CREATE TABLE Population
(Country VARCHAR(4) CONSTRAINT PopKey PRIMARY KEY,
 Population_Growth DECIMAL,
 Infant_Mortality DECIMAL
 );

CREATE TABLE Province
(Name VARCHAR(50) CONSTRAINT PrName NOT NULL ,
 Country  VARCHAR(4) CONSTRAINT PrCountry NOT NULL ,
 Population DECIMAL,
 Area DECIMAL,
 Capital VARCHAR(50),
 CapProv VARCHAR(50),
 CONSTRAINT PrKey PRIMARY KEY (Name, Country)
 );

CREATE TABLE Economy
(Country VARCHAR(4) CONSTRAINT EconomyKey PRIMARY KEY,
 GDP DECIMAL,
 Agriculture DECIMAL,
 Service DECIMAL,
 Industry DECIMAL,
 Inflation DECIMAL,
 Unemployment DECIMAL
 );

CREATE TABLE Politics
(Country VARCHAR(4) CONSTRAINT PoliticsKey PRIMARY KEY,
 Independence DATE,
 WasDependent VARCHAR(50),
 Dependent  VARCHAR(4),
 Government VARCHAR(120)
 );

CREATE TABLE Religion
(Country VARCHAR(4),
 Name VARCHAR(50),
 Percentage DECIMAL,
 CONSTRAINT ReligionKey PRIMARY KEY (Name, Country)
 );

CREATE TABLE EthnicGroup
(Country VARCHAR(4),
 Name VARCHAR(50),
 Percentage DECIMAL,
 CONSTRAINT EthnicKey PRIMARY KEY (Name, Country));

CREATE TABLE Spoken
(Country VARCHAR(4),
 Language VARCHAR(50),
 Percentage DECIMAL,
 CONSTRAINT SpokenKey PRIMARY KEY (Country, Language)
 );

CREATE TABLE Language
(Name VARCHAR(50) ,
 Superlanguage VARCHAR(50),
 CONSTRAINT LanguageKey PRIMARY KEY (Name)
 );

CREATE TABLE Countrypops
(Country VARCHAR(4),
 Year DECIMAL,
 Population DECIMAL,
 CONSTRAINT CountryPopsKey PRIMARY KEY (Country, Year)
 );

CREATE TABLE Countryothername
(Country VARCHAR(4),
 othername VARCHAR(50),
 CONSTRAINT CountryOthernameKey PRIMARY KEY (Country, othername));

CREATE TABLE Countrylocalname
(Country VARCHAR(4),
 localname VARCHAR(300),
 CONSTRAINT CountrylocalnameKey PRIMARY KEY (Country)
 );

CREATE TABLE Provpops
(Province VARCHAR(50),
 Country VARCHAR(4),
 Year DECIMAL ,
 Population DECIMAL,
 CONSTRAINT ProvPopKey PRIMARY KEY (Country, Province, Year)
 );

CREATE TABLE Provinceothername
(Province VARCHAR(50),
 Country VARCHAR(4),
 othername VARCHAR(50),
 CONSTRAINT ProvOthernameKey PRIMARY KEY (Country, Province, othername)
 );

CREATE TABLE Provincelocalname
(Province VARCHAR(50),
 Country VARCHAR(4),
 localname VARCHAR(300),
 CONSTRAINT ProvlocalnameKey PRIMARY KEY (Country, Province)
 );

CREATE TABLE Citypops
(City VARCHAR(50),
 Country VARCHAR(4),
 Province VARCHAR(50),
 Year DECIMAL,
 Population DECIMAL,
 CONSTRAINT CityPopKey PRIMARY KEY (Country, Province, City, Year)
 );

CREATE TABLE Cityothername
(City VARCHAR(50),
 Country VARCHAR(4),
 Province VARCHAR(50),
 othername VARCHAR(50),
 CONSTRAINT CityOthernameKey PRIMARY KEY (Country, Province, City, othername)
 );

CREATE TABLE Citylocalname
(City VARCHAR(50),
 Country VARCHAR(4),
 Province VARCHAR(50),
 localname VARCHAR(300),
 CONSTRAINT CitylocalnameKey PRIMARY KEY (Country, Province, City)
 );

CREATE TABLE Continent
(Name VARCHAR(20) CONSTRAINT ContinentKey PRIMARY KEY,
 Area DECIMAL(10)
 );

CREATE TABLE borders
(Country1 VARCHAR(4),
 Country2 VARCHAR(4),
 Length DECIMAL ,
 CONSTRAINT BorderKey PRIMARY KEY (Country1,Country2)
 );

CREATE TABLE encompasses
(Country VARCHAR(4) NOT NULL,
 Continent VARCHAR(20) NOT NULL,
 Percentage DECIMAL,
 CONSTRAINT EncompassesKey PRIMARY KEY (Country,Continent)
 );

CREATE TABLE Organization
(Abbreviation VARCHAR(12) Constraint OrgKey PRIMARY KEY,
 Name VARCHAR(100) NOT NULL,
 City VARCHAR(50) ,
 Country VARCHAR(4) , 
 Province VARCHAR(50) ,
 Established DATE,
 CONSTRAINT OrgNameUnique UNIQUE (Name)
 );

CREATE TABLE isMember
(Country VARCHAR(4),
 Organization VARCHAR(12),
 Type VARCHAR(60) DEFAULT 'member',
 CONSTRAINT MemberKey PRIMARY KEY (Country,Organization)
  );

CREATE TABLE Mountain
(Name VARCHAR(50) CONSTRAINT MountainKey PRIMARY KEY,
 Mountains VARCHAR(50),
 Elevation DECIMAL,
 Type VARCHAR(10),
 Latitude DECIMAL,
  Longitude DECIMAL);

CREATE TABLE Desert
(Name VARCHAR(50) CONSTRAINT DesertKey PRIMARY KEY,
 Area DECIMAL,
 Latitude DECIMAL,
  Longitude DECIMAL);

CREATE TABLE Island
(Name VARCHAR(50) CONSTRAINT IslandKey PRIMARY KEY,
 Islands VARCHAR(50),
 Area DECIMAL ,
 Elevation DECIMAL,
 Type VARCHAR(15),
 Latitude DECIMAL,
  Longitude DECIMAL);

CREATE TABLE Lake
(Name VARCHAR(50) CONSTRAINT LakeKey PRIMARY KEY,
 River VARCHAR(50),
 Area DECIMAL ,
 Elevation DECIMAL,
 Depth DECIMAL,
 Height DECIMAL,
 Type VARCHAR(12),
 Latitude DECIMAL,
  Longitude DECIMAL  
);

CREATE TABLE Sea
(Name VARCHAR(50) CONSTRAINT SeaKey PRIMARY KEY,
 Area DECIMAL,
 Depth DECIMAL);

CREATE TABLE River
(Name VARCHAR(50) CONSTRAINT RiverKey PRIMARY KEY,
 River VARCHAR(50),
 Lake VARCHAR(50),
 Sea VARCHAR(50),
 Length DECIMAL,
 Area DECIMAL,
 SourceLatitude DECIMAL,
 SourceLongitude DECIMAL,
 Mountains VARCHAR(50),
 SourceElevation DECIMAL,
 EstuaryLatitude DECIMAL,
 EstuaryLongitude DECIMAL,
 EstuaryElevation DECIMAL,
 CONSTRAINT RivFlowsInto 
     CHECK ((River IS NULL AND Lake IS NULL)
            OR (River IS NULL AND Sea IS NULL)
            OR (Lake IS NULL AND Sea is NULL))
);

CREATE TABLE RiverThrough
(River VARCHAR(50),
 Lake  VARCHAR(50),
 CONSTRAINT RThroughKey PRIMARY KEY (River,Lake)
  );

CREATE TABLE geo_Mountain
(Mountain VARCHAR(50) ,
 Country VARCHAR(4) ,
 Province VARCHAR(50) ,
 CONSTRAINT GMountainKey PRIMARY KEY (Province,Country,Mountain)
  );

CREATE TABLE geo_Desert
(Desert VARCHAR(50) ,
 Country VARCHAR(4) ,
 Province VARCHAR(50) ,
 CONSTRAINT GDesertKey PRIMARY KEY (Province, Country, Desert)
  );

CREATE TABLE geo_Island
(Island VARCHAR(50) , 
 Country VARCHAR(4) ,
 Province VARCHAR(50) ,
 CONSTRAINT GIslandKey PRIMARY KEY (Province, Country, Island)
  );

CREATE TABLE geo_River
(River VARCHAR(50), 
 Country VARCHAR(4),
 Province VARCHAR(50),
 CONSTRAINT GRiverKey PRIMARY KEY (Province ,Country, River)
  );

CREATE TABLE geo_Sea
(Sea VARCHAR(50) ,
 Country VARCHAR(4)  ,
 Province VARCHAR(50) ,
 CONSTRAINT GSeaKey PRIMARY KEY (Province, Country, Sea)
  );

CREATE TABLE geo_Lake
(Lake VARCHAR(50) ,
 Country VARCHAR(4) ,
 Province VARCHAR(50) ,
 CONSTRAINT GLakeKey PRIMARY KEY (Province, Country, Lake)
  );

CREATE TABLE geo_Source
(River VARCHAR(50) ,
 Country VARCHAR(4) ,
 Province VARCHAR(50) ,
 CONSTRAINT GSourceKey PRIMARY KEY (Province, Country, River)
  );

CREATE TABLE geo_Estuary
(River VARCHAR(50) ,
 Country VARCHAR(4) ,
 Province VARCHAR(50) ,
 CONSTRAINT GEstuaryKey PRIMARY KEY (Province, Country, River)
  );

CREATE TABLE mergesWith
(Sea1 VARCHAR(50) ,
 Sea2 VARCHAR(50) ,
 CONSTRAINT MergesWithKey PRIMARY KEY (Sea1, Sea2)
  );

CREATE TABLE located
(City VARCHAR(50) ,
 Province VARCHAR(50) ,
 Country VARCHAR(4) ,
 River VARCHAR(50),
 Lake VARCHAR(50),
 Sea VARCHAR(50));

CREATE TABLE locatedOn
(City VARCHAR(50) ,
 Province VARCHAR(50) ,
 Country VARCHAR(4) ,
 Island VARCHAR(50) ,
 CONSTRAINT locatedOnKey PRIMARY KEY (City, Province, Country, Island)
  );

CREATE TABLE islandIn
(Island VARCHAR(50) ,
 Sea VARCHAR(50) ,
 Lake VARCHAR(50) ,
 River VARCHAR(50)
  );

CREATE TABLE MountainOnIsland
(Mountain VARCHAR(50),
 Island   VARCHAR(50),
 CONSTRAINT MountainIslKey PRIMARY KEY (Mountain, Island)
  );

CREATE TABLE LakeOnIsland
(Lake    VARCHAR(50),
 Island  VARCHAR(50),
 CONSTRAINT LakeIslKey PRIMARY KEY (Lake, Island)
  );

CREATE TABLE RiverOnIsland
(River   VARCHAR(50),
 Island  VARCHAR(50),
 CONSTRAINT RiverIslKey PRIMARY KEY (River, Island)
  );
 
 COMMIT;

 COMMIT;

 formally constitutional monarchy');
 parliamentary democracy');
 authoritarian presidential rule with little power outside the executive branch');
 authoritarian presidential rule, with little power outside the executive branch');
 self-governing with locally elected governor, lieutenant governor, and legislature');
 multiparty presidential regime established 1960');
 multiparty presidential regime');
 multiparty presidential regime');
 multiparty presidential regime');
 presidential, multiparty system');
 self-governing territory');
 strong democratic tradition');
 executive branch dominates government structure');
 Social Unitarian State');
 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

 COMMIT;

ALTER TABLE Country 
  ADD CONSTRAINT fk_capital FOREIGN KEY (Capital, Code, Province) REFERENCES City(Name, Country, Province);

ALTER TABLE Countryothername
  ADD CONSTRAINT CountryOthernameFK FOREIGN KEY (Country) REFERENCES Country(Code);

ALTER TABLE Countrylocalname
  ADD CONSTRAINT CountrylocalnameFK FOREIGN KEY (Country) REFERENCES Country(Code);

ALTER TABLE City 
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE Province 
  ADD CONSTRAINT PrCountryFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE Province 
  ADD CONSTRAINT PrCapitalFK FOREIGN KEY (Capital, Country, CapProv) REFERENCES City(Name, Country, Province);

ALTER TABLE Economy 
  ADD CONSTRAINT EconomyFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE Population 
  ADD CONSTRAINT PopulationFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE Politics 
  ADD CONSTRAINT PoliticsFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE Politics 
  ADD CONSTRAINT PoliticsFK2 FOREIGN KEY (Dependent) References Country(Code);

ALTER TABLE Religion 
  ADD CONSTRAINT ReligionFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE EthnicGroup 
  ADD CONSTRAINT EthnicFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE Spoken 
  ADD CONSTRAINT SpokenFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE Spoken 
  ADD CONSTRAINT SpokenFK2 FOREIGN KEY (Language) References Language(Name);

ALTER TABLE Language 
  ADD CONSTRAINT LanguageFK FOREIGN KEY (Superlanguage) References Language(Name);

ALTER TABLE Countrypops 
  ADD CONSTRAINT CountryPopsFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE Provpops 
  ADD CONSTRAINT ProvPopFK FOREIGN KEY (Country, Province) References Province(Country, Name);

ALTER TABLE Provinceothername 
  ADD CONSTRAINT ProvOthernameFK FOREIGN KEY (Country, Province) References Province(Country, Name);

ALTER TABLE Provincelocalname 
  ADD CONSTRAINT ProvlocalnameFK FOREIGN KEY (Country, Province) References Province(Country, Name);

ALTER TABLE Citypops 
  ADD CONSTRAINT CityPopFK FOREIGN KEY (City, Country, Province) References City(Name, Country, Province);

ALTER TABLE Cityothername 
  ADD CONSTRAINT CityOthernameFK FOREIGN KEY (City, Country, Province) References City(Name, Country, Province);

ALTER TABLE Citylocalname 
  ADD CONSTRAINT CitylocalnameFK FOREIGN KEY (City, Country, Province ) References City(Name, Country, Province);

ALTER TABLE borders 
  ADD CONSTRAINT Country1FK FOREIGN KEY (Country1) References Country(Code);

ALTER TABLE borders 
  ADD CONSTRAINT Country2FK FOREIGN KEY (Country2) References Country(Code);

ALTER TABLE encompasses 
  ADD CONSTRAINT CountryFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE encompasses 
  ADD CONSTRAINT ContinentFK FOREIGN KEY (Continent) References Continent(Name);

ALTER TABLE Organization 
  ADD CONSTRAINT CityFK FOREIGN KEY (City, Country, Province) References City(Name, Country, Province);

ALTER TABLE isMember 
  ADD CONSTRAINT CountryFK FOREIGN KEY (Country) References Country(Code);

ALTER TABLE isMember 
  ADD CONSTRAINT OrganizationFK FOREIGN KEY (Organization) References Organization(Abbreviation);

ALTER TABLE Lake 
  ADD CONSTRAINT LakeFK FOREIGN KEY (River) REFERENCES River(Name);

ALTER TABLE River 
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) References River(Name);

ALTER TABLE River 
  ADD CONSTRAINT LakeFK FOREIGN KEY (Lake) References Lake(Name);

ALTER TABLE River 
  ADD CONSTRAINT SeaFK FOREIGN KEY (Sea) References Sea(Name);

ALTER TABLE RiverThrough 
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) References River(Name);

ALTER TABLE RiverThrough 
  ADD CONSTRAINT LakeFK FOREIGN KEY (Lake) References Lake(Name);

ALTER TABLE Located
  ADD CONSTRAINT CityFK FOREIGN KEY (City, Country, Province) REFERENCES City(Name, Country, Province);

ALTER TABLE geo_Sea
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE geo_Sea
  ADD CONSTRAINT SeaFK FOREIGN KEY (Sea) REFERENCES Sea(Name);

ALTER TABLE geo_Lake
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE geo_Lake
  ADD CONSTRAINT LakeFK FOREIGN KEY (Lake) REFERENCES Lake(Name);

ALTER TABLE LakeOnIsland
  ADD CONSTRAINT LakeFK FOREIGN KEY (Lake) REFERENCES Lake(Name);

ALTER TABLE LakeOnIsland
  ADD CONSTRAINT IslandFK FOREIGN KEY (Island) REFERENCES Island(Name);

ALTER TABLE RiverOnIsland
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) REFERENCES River(Name);

ALTER TABLE RiverOnIsland
  ADD CONSTRAINT IslandFK FOREIGN KEY (Island) REFERENCES Island(Name);

ALTER TABLE geo_River
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE geo_River
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) REFERENCES River(Name);

ALTER TABLE geo_Source
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) REFERENCES River(Name);

ALTER TABLE geo_Source
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE geo_Estuary
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) REFERENCES River(Name);

ALTER TABLE geo_Estuary
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE located
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) REFERENCES River(Name);

ALTER TABLE located
  ADD CONSTRAINT LakeFK FOREIGN KEY (Lake) REFERENCES Lake(Name);

ALTER TABLE located
  ADD CONSTRAINT SeaFK FOREIGN KEY (Sea) REFERENCES Sea(Name);

ALTER TABLE geo_Island
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE geo_Island
  ADD CONSTRAINT IslandFK FOREIGN KEY (Island) REFERENCES Island(Name);

ALTER TABLE locatedOn
  ADD CONSTRAINT CityFK FOREIGN KEY (City, Country, Province) REFERENCES City(Name, Country, Province);

ALTER TABLE locatedOn
  ADD CONSTRAINT IslandFK FOREIGN KEY (Island) REFERENCES Island(Name);

ALTER TABLE geo_Mountain
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE geo_Mountain
  ADD CONSTRAINT MountainFK FOREIGN KEY (Mountain) REFERENCES Mountain(Name);

ALTER TABLE geo_Desert
  ADD CONSTRAINT ProvinceFK FOREIGN KEY (Country, Province) REFERENCES Province(Country, Name);

ALTER TABLE geo_Desert
  ADD CONSTRAINT DesertFK FOREIGN KEY (Desert) REFERENCES Desert(Name);

ALTER TABLE MountainOnIsland
  ADD CONSTRAINT MountainFK FOREIGN KEY (Mountain) REFERENCES Mountain(Name);

ALTER TABLE MountainOnIsland
  ADD CONSTRAINT IslandFK FOREIGN KEY (Island) REFERENCES Island(Name);

ALTER TABLE islandIn
  ADD CONSTRAINT IslandFK FOREIGN KEY (Island) REFERENCES Island(Name);

ALTER TABLE islandIn
  ADD CONSTRAINT RiverFK FOREIGN KEY (River) REFERENCES River(Name);

ALTER TABLE islandIn
  ADD CONSTRAINT LakeFK FOREIGN KEY (Lake) REFERENCES Lake(Name);

ALTER TABLE islandIn
  ADD CONSTRAINT SeaFK FOREIGN KEY (Sea) REFERENCES Sea(Name);

ALTER TABLE mergesWith
  ADD CONSTRAINT Sea1FK FOREIGN KEY (Sea1) REFERENCES Sea(Name);

ALTER TABLE mergesWith
  ADD CONSTRAINT Sea2FK FOREIGN KEY (Sea2) REFERENCES Sea(Name);

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

## Sample rows
{}

## Tool-derived structural evidence
{
  "enabled_tools": [
    "schema_profiler"
  ],
  "schema_summary": {
    "num_tables": 47,
    "num_columns": 182,
    "num_foreign_keys": 69
  },
  "join_graph": {
    "Country": [
      {
        "to_table": "City",
        "from_columns": [
          "Capital",
          "Code",
          "Province"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "Country.Capital",
            "=",
            "City.Name"
          ],
          [
            "Country.Code",
            "=",
            "City.Country"
          ],
          [
            "Country.Province",
            "=",
            "City.Province"
          ]
        ]
      }
    ],
    "City": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "City.Country",
            "=",
            "Province.Country"
          ],
          [
            "City.Province",
            "=",
            "Province.Name"
          ]
        ]
      }
    ],
    "Population": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Population.Country",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "Province": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Province.Country",
            "=",
            "Country.Code"
          ]
        ]
      },
      {
        "to_table": "City",
        "from_columns": [
          "Capital",
          "Country",
          "CapProv"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "Province.Capital",
            "=",
            "City.Name"
          ],
          [
            "Province.Country",
            "=",
            "City.Country"
          ],
          [
            "Province.CapProv",
            "=",
            "City.Province"
          ]
        ]
      }
    ],
    "Economy": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Economy.Country",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "Politics": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Politics.Country",
            "=",
            "Country.Code"
          ]
        ]
      },
      {
        "to_table": "Country",
        "from_columns": [
          "Dependent"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Politics.Dependent",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "Religion": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Religion.Country",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "EthnicGroup": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "EthnicGroup.Country",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "Spoken": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Spoken.Country",
            "=",
            "Country.Code"
          ]
        ]
      },
      {
        "to_table": "Language",
        "from_columns": [
          "Language"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "Spoken.Language",
            "=",
            "Language.Name"
          ]
        ]
      }
    ],
    "Language": [
      {
        "to_table": "Language",
        "from_columns": [
          "Superlanguage"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "Language.Superlanguage",
            "=",
            "Language.Name"
          ]
        ]
      }
    ],
    "Countrypops": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Countrypops.Country",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "Countryothername": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Countryothername.Country",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "Countrylocalname": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "Countrylocalname.Country",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "Provpops": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "Provpops.Country",
            "=",
            "Province.Country"
          ],
          [
            "Provpops.Province",
            "=",
            "Province.Name"
          ]
        ]
      }
    ],
    "Provinceothername": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "Provinceothername.Country",
            "=",
            "Province.Country"
          ],
          [
            "Provinceothername.Province",
            "=",
            "Province.Name"
          ]
        ]
      }
    ],
    "Provincelocalname": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "Provincelocalname.Country",
            "=",
            "Province.Country"
          ],
          [
            "Provincelocalname.Province",
            "=",
            "Province.Name"
          ]
        ]
      }
    ],
    "Citypops": [
      {
        "to_table": "City",
        "from_columns": [
          "City",
          "Country",
          "Province"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "Citypops.City",
            "=",
            "City.Name"
          ],
          [
            "Citypops.Country",
            "=",
            "City.Country"
          ],
          [
            "Citypops.Province",
            "=",
            "City.Province"
          ]
        ]
      }
    ],
    "Cityothername": [
      {
        "to_table": "City",
        "from_columns": [
          "City",
          "Country",
          "Province"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "Cityothername.City",
            "=",
            "City.Name"
          ],
          [
            "Cityothername.Country",
            "=",
            "City.Country"
          ],
          [
            "Cityothername.Province",
            "=",
            "City.Province"
          ]
        ]
      }
    ],
    "Citylocalname": [
      {
        "to_table": "City",
        "from_columns": [
          "City",
          "Country",
          "Province"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "Citylocalname.City",
            "=",
            "City.Name"
          ],
          [
            "Citylocalname.Country",
            "=",
            "City.Country"
          ],
          [
            "Citylocalname.Province",
            "=",
            "City.Province"
          ]
        ]
      }
    ],
    "Continent": [],
    "borders": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country1"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "borders.Country1",
            "=",
            "Country.Code"
          ]
        ]
      },
      {
        "to_table": "Country",
        "from_columns": [
          "Country2"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "borders.Country2",
            "=",
            "Country.Code"
          ]
        ]
      }
    ],
    "encompasses": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "encompasses.Country",
            "=",
            "Country.Code"
          ]
        ]
      },
      {
        "to_table": "Continent",
        "from_columns": [
          "Continent"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "encompasses.Continent",
            "=",
            "Continent.Name"
          ]
        ]
      }
    ],
    "Organization": [
      {
        "to_table": "City",
        "from_columns": [
          "City",
          "Country",
          "Province"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "Organization.City",
            "=",
            "City.Name"
          ],
          [
            "Organization.Country",
            "=",
            "City.Country"
          ],
          [
            "Organization.Province",
            "=",
            "City.Province"
          ]
        ]
      }
    ],
    "isMember": [
      {
        "to_table": "Country",
        "from_columns": [
          "Country"
        ],
        "to_columns": [
          "Code"
        ],
        "joins": [
          [
            "isMember.Country",
            "=",
            "Country.Code"
          ]
        ]
      },
      {
        "to_table": "Organization",
        "from_columns": [
          "Organization"
        ],
        "to_columns": [
          "Abbreviation"
        ],
        "joins": [
          [
            "isMember.Organization",
            "=",
            "Organization.Abbreviation"
          ]
        ]
      }
    ],
    "Mountain": [],
    "Desert": [],
    "Island": [],
    "Lake": [
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "Lake.River",
            "=",
            "River.Name"
          ]
        ]
      }
    ],
    "Sea": [],
    "River": [
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "River.River",
            "=",
            "River.Name"
          ]
        ]
      },
      {
        "to_table": "Lake",
        "from_columns": [
          "Lake"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "River.Lake",
            "=",
            "Lake.Name"
          ]
        ]
      },
      {
        "to_table": "Sea",
        "from_columns": [
          "Sea"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "River.Sea",
            "=",
            "Sea.Name"
          ]
        ]
      }
    ],
    "RiverThrough": [
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "RiverThrough.River",
            "=",
            "River.Name"
          ]
        ]
      },
      {
        "to_table": "Lake",
        "from_columns": [
          "Lake"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "RiverThrough.Lake",
            "=",
            "Lake.Name"
          ]
        ]
      }
    ],
    "geo_Mountain": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_Mountain.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_Mountain.Province",
            "=",
            "Province.Name"
          ]
        ]
      },
      {
        "to_table": "Mountain",
        "from_columns": [
          "Mountain"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_Mountain.Mountain",
            "=",
            "Mountain.Name"
          ]
        ]
      }
    ],
    "geo_Desert": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_Desert.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_Desert.Province",
            "=",
            "Province.Name"
          ]
        ]
      },
      {
        "to_table": "Desert",
        "from_columns": [
          "Desert"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_Desert.Desert",
            "=",
            "Desert.Name"
          ]
        ]
      }
    ],
    "geo_Island": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_Island.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_Island.Province",
            "=",
            "Province.Name"
          ]
        ]
      },
      {
        "to_table": "Island",
        "from_columns": [
          "Island"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_Island.Island",
            "=",
            "Island.Name"
          ]
        ]
      }
    ],
    "geo_River": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_River.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_River.Province",
            "=",
            "Province.Name"
          ]
        ]
      },
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_River.River",
            "=",
            "River.Name"
          ]
        ]
      }
    ],
    "geo_Sea": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_Sea.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_Sea.Province",
            "=",
            "Province.Name"
          ]
        ]
      },
      {
        "to_table": "Sea",
        "from_columns": [
          "Sea"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_Sea.Sea",
            "=",
            "Sea.Name"
          ]
        ]
      }
    ],
    "geo_Lake": [
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_Lake.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_Lake.Province",
            "=",
            "Province.Name"
          ]
        ]
      },
      {
        "to_table": "Lake",
        "from_columns": [
          "Lake"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_Lake.Lake",
            "=",
            "Lake.Name"
          ]
        ]
      }
    ],
    "geo_Source": [
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_Source.River",
            "=",
            "River.Name"
          ]
        ]
      },
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_Source.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_Source.Province",
            "=",
            "Province.Name"
          ]
        ]
      }
    ],
    "geo_Estuary": [
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "geo_Estuary.River",
            "=",
            "River.Name"
          ]
        ]
      },
      {
        "to_table": "Province",
        "from_columns": [
          "Country",
          "Province"
        ],
        "to_columns": [
          "Country",
          "Name"
        ],
        "joins": [
          [
            "geo_Estuary.Country",
            "=",
            "Province.Country"
          ],
          [
            "geo_Estuary.Province",
            "=",
            "Province.Name"
          ]
        ]
      }
    ],
    "mergesWith": [
      {
        "to_table": "Sea",
        "from_columns": [
          "Sea1"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "mergesWith.Sea1",
            "=",
            "Sea.Name"
          ]
        ]
      },
      {
        "to_table": "Sea",
        "from_columns": [
          "Sea2"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "mergesWith.Sea2",
            "=",
            "Sea.Name"
          ]
        ]
      }
    ],
    "located": [
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "located.River",
            "=",
            "River.Name"
          ]
        ]
      },
      {
        "to_table": "Lake",
        "from_columns": [
          "Lake"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "located.Lake",
            "=",
            "Lake.Name"
          ]
        ]
      },
      {
        "to_table": "Sea",
        "from_columns": [
          "Sea"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "located.Sea",
            "=",
            "Sea.Name"
          ]
        ]
      }
    ],
    "locatedOn": [
      {
        "to_table": "City",
        "from_columns": [
          "City",
          "Country",
          "Province"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "locatedOn.City",
            "=",
            "City.Name"
          ],
          [
            "locatedOn.Country",
            "=",
            "City.Country"
          ],
          [
            "locatedOn.Province",
            "=",
            "City.Province"
          ]
        ]
      },
      {
        "to_table": "Island",
        "from_columns": [
          "Island"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "locatedOn.Island",
            "=",
            "Island.Name"
          ]
        ]
      }
    ],
    "islandIn": [
      {
        "to_table": "Island",
        "from_columns": [
          "Island"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "islandIn.Island",
            "=",
            "Island.Name"
          ]
        ]
      },
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "islandIn.River",
            "=",
            "River.Name"
          ]
        ]
      },
      {
        "to_table": "Lake",
        "from_columns": [
          "Lake"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "islandIn.Lake",
            "=",
            "Lake.Name"
          ]
        ]
      },
      {
        "to_table": "Sea",
        "from_columns": [
          "Sea"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "islandIn.Sea",
            "=",
            "Sea.Name"
          ]
        ]
      }
    ],
    "MountainOnIsland": [
      {
        "to_table": "Mountain",
        "from_columns": [
          "Mountain"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "MountainOnIsland.Mountain",
            "=",
            "Mountain.Name"
          ]
        ]
      },
      {
        "to_table": "Island",
        "from_columns": [
          "Island"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "MountainOnIsland.Island",
            "=",
            "Island.Name"
          ]
        ]
      }
    ],
    "LakeOnIsland": [
      {
        "to_table": "Lake",
        "from_columns": [
          "Lake"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "LakeOnIsland.Lake",
            "=",
            "Lake.Name"
          ]
        ]
      },
      {
        "to_table": "Island",
        "from_columns": [
          "Island"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "LakeOnIsland.Island",
            "=",
            "Island.Name"
          ]
        ]
      }
    ],
    "RiverOnIsland": [
      {
        "to_table": "River",
        "from_columns": [
          "River"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "RiverOnIsland.River",
            "=",
            "River.Name"
          ]
        ]
      },
      {
        "to_table": "Island",
        "from_columns": [
          "Island"
        ],
        "to_columns": [
          "Name"
        ],
        "joins": [
          [
            "RiverOnIsland.Island",
            "=",
            "Island.Name"
          ]
        ]
      }
    ],
    "Located": [
      {
        "to_table": "City",
        "from_columns": [
          "City",
          "Country",
          "Province"
        ],
        "to_columns": [
          "Name",
          "Country",
          "Province"
        ],
        "joins": [
          [
            "Located.City",
            "=",
            "City.Name"
          ],
          [
            "Located.Country",
            "=",
            "City.Country"
          ],
          [
            "Located.Province",
            "=",
            "City.Province"
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
