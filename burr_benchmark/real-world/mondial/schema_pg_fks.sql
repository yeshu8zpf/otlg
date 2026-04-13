 \c postgres
\set database_name real_world__mondial__fk

SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = :'database_name' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS :database_name;
CREATE DATABASE :database_name;
\c :database_name;
SET default_tablespace = '';
SET default_with_oids = false;

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

