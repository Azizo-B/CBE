-- Drop tables if they exist
DROP TABLE IF EXISTS meta;
DROP TABLE IF EXISTS code;
DROP TABLE IF EXISTS enterprise;
DROP TABLE IF EXISTS establishment;
DROP TABLE IF EXISTS denomination;
DROP TABLE IF EXISTS address;
DROP TABLE IF EXISTS contact;
DROP TABLE IF EXISTS activity;
DROP TABLE IF EXISTS branch;

-- Drop indexes if they exist
DROP INDEX IF EXISTS idx_establishment_enterprise;
DROP INDEX IF EXISTS idx_denomination_entity;
DROP INDEX IF EXISTS idx_address_entity;
DROP INDEX IF EXISTS idx_contact_entity;
DROP INDEX IF EXISTS idx_activity_entity;
DROP INDEX IF EXISTS idx_branch_enterprise;

-- Create tables and indexes
CREATE TABLE IF NOT EXISTS meta (
    Variable TEXT PRIMARY KEY,
    Value TEXT
);


CREATE TABLE IF NOT EXISTS code (
    Category TEXT,
    Code TEXT,
    Language TEXT,
    Description TEXT,
    PRIMARY KEY (Category, Code, Language)
);


CREATE TABLE IF NOT EXISTS enterprise (
    EnterpriseNumber TEXT PRIMARY KEY,
    Status TEXT,
    JuridicalSituation TEXT,
    TypeOfEnterprise TEXT,
    JuridicalForm TEXT,
    JuridicalFormCAC TEXT,
    StartDate TEXT
);


CREATE TABLE IF NOT EXISTS establishment (
    EstablishmentNumber TEXT PRIMARY KEY,
    StartDate TEXT,
    EnterpriseNumber TEXT,
    FOREIGN KEY (EnterpriseNumber) REFERENCES enterprise(EnterpriseNumber)
);

-- Index on EnterpriseNumber for faster joins and lookups
CREATE INDEX idx_establishment_enterprise ON establishment (EnterpriseNumber);


CREATE TABLE IF NOT EXISTS denomination (
    EntityNumber TEXT,
    Language TEXT,
    TypeOfDenomination TEXT,
    Denomination TEXT,
    PRIMARY KEY (EntityNumber, Language, TypeOfDenomination, Denomination)
);

-- Indexes on EntityNumber for improved filtering and joins
CREATE INDEX idx_denomination_entity ON denomination (EntityNumber);


CREATE TABLE IF NOT EXISTS address (
    EntityNumber TEXT,
    TypeOfAddress TEXT,
    CountryNL TEXT,
    CountryFR TEXT,
    Zipcode TEXT,
    MunicipalityNL TEXT,
    MunicipalityFR TEXT,
    StreetNL TEXT,
    StreetFR TEXT,
    HouseNumber TEXT,
    Box TEXT,
    ExtraAddressInfo TEXT,
    DateStrikingOff TEXT,
    PRIMARY KEY (EntityNumber, TypeOfAddress)
);

-- Indexes on EntityNumber for improved filtering and joins
CREATE INDEX idx_address_entity ON address (EntityNumber);


CREATE TABLE IF NOT EXISTS contact (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    EntityNumber TEXT,
    EntityContact TEXT,
    ContactType TEXT,
    Value TEXT
);

-- Indexes on EntityNumber for improved filtering and joins
CREATE INDEX idx_contact_entity ON contact (EntityNumber);


CREATE TABLE IF NOT EXISTS activity (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    EntityNumber TEXT,
    ActivityGroup TEXT,
    NaceVersion TEXT,
    NaceCode TEXT,
    Classification TEXT
);

-- Indexes on EntityNumber for improved filtering and joins
CREATE INDEX idx_activity_entity ON activity (EntityNumber);


CREATE TABLE IF NOT EXISTS branch (
    Id TEXT PRIMARY KEY,
    StartDate TEXT,
    EnterpriseNumber TEXT,
    FOREIGN KEY (EnterpriseNumber) REFERENCES enterprise(EnterpriseNumber)
);

 -- Index on EnterpriseNumber for faster joins and lookups
CREATE INDEX idx_branch_enterprise ON branch (EnterpriseNumber);
