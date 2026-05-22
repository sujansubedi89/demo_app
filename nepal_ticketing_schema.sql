-- ============================================================
-- NEPAL TOURIST PERMIT SYSTEM - DATABASE SCHEMA
-- ============================================================
-- BEGINNER'S GUIDE TO READING THIS FILE:
--
-- Lines starting with "--" are COMMENTS. SQL ignores them.
-- They are just notes for humans reading the code.
--
-- CREATE TABLE = Make a new table (like a new Excel sheet)
-- VARCHAR(50)  = Text, max 50 characters
-- INT          = Whole number (1, 2, 3...)
-- DATE         = A date like 2026-05-22
-- ENUM         = Only allows specific values, like a dropdown
-- DEFAULT      = What value to use if nothing is given
-- NOT NULL     = This field MUST have a value, cannot be empty
-- PRIMARY KEY  = The unique ID for each row (auto-numbers itself)
-- FOREIGN KEY  = Links this column to another table's ID
-- ============================================================


-- STEP 1: Create the database (the whole container/workbook)
CREATE DATABASE IF NOT EXISTS nepal_ticketing
    CHARACTER SET utf8mb4        -- Supports all languages + emojis
    COLLATE utf8mb4_unicode_ci;  -- How to sort/compare text

-- STEP 2: Tell MySQL "use this database for all commands below"
USE nepal_ticketing;


-- ============================================================
-- TABLE 1: countries
-- Stores list of countries a tourist can come from.
-- SAARC countries (India, Pakistan, Bangladesh, etc.) pay
-- a different (lower) fee than non-SAARC countries.
-- ============================================================
CREATE TABLE IF NOT EXISTS countries (
    id          INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID, auto-numbers
    code        VARCHAR(5)   NOT NULL,           -- e.g. "NP", "IN", "US"
    name        VARCHAR(100) NOT NULL,           -- e.g. "Nepal", "India"
    nationality VARCHAR(100) DEFAULT NULL,       -- e.g. "Nepali", "Indian"
    is_saarc    TINYINT(1)   NOT NULL DEFAULT 0, -- 1 = SAARC, 0 = Non-SAARC
    status      TINYINT(1)   NOT NULL DEFAULT 1, -- 1 = Active, 0 = Hidden
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- TABLE 2: occupations
-- List of jobs a tourist can select from (Doctor, Teacher, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS occupations (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,           -- e.g. "Teacher", "Engineer"
    status     TINYINT(1)   NOT NULL DEFAULT 1,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- TABLE 3: purposes
-- The 3 purposes a tourist selects: Trekking, Tourism, Research
-- ============================================================
CREATE TABLE IF NOT EXISTS purposes (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       ENUM('Trekking','Tourism','Research') NOT NULL,
    status     TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME   DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Pre-fill the 3 purposes automatically
INSERT IGNORE INTO purposes (name) VALUES
    ('Trekking'),
    ('Tourism'),
    ('Research');


-- ============================================================
-- TABLE 4: trekking_regions
-- The areas/routes a tourist can trek.
-- e.g. Everest Region, Annapurna Circuit, Langtang, Chitwan
-- ============================================================
CREATE TABLE IF NOT EXISTS trekking_regions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,  -- e.g. "Everest Base Camp"
    description VARCHAR(255) DEFAULT NULL,
    status      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Pre-fill common trekking regions
INSERT IGNORE INTO trekking_regions (name) VALUES
    ('Everest Region'),
    ('Annapurna Circuit'),
    ('Annapurna Base Camp'),
    ('Langtang Region'),
    ('Manaslu Circuit'),
    ('Upper Mustang'),
    ('Kanchenjunga Region'),
    ('Dolpo Region');


-- ============================================================
-- TABLE 5: checkposts
-- Entry and exit points (border crossings / checkposts)
-- ============================================================
CREATE TABLE IF NOT EXISTS checkposts (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL UNIQUE,
    location  VARCHAR(150) DEFAULT NULL,
    type      ENUM('entry','exit','both') NOT NULL DEFAULT 'both',
    is_active TINYINT(1)   DEFAULT 1,
    created_at DATETIME    DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO checkposts (name, location, type) VALUES
    ('Birgunj',       'Parsa District, Bagmati Province',             'both'),
    ('Bhairahawa',    'Rupandehi District, Lumbini Province',          'both'),
    ('Kakarbhitta',   'Jhapa District, Koshi Province',                'both'),
    ('Dhangadhi',     'Kailali District, Sudurpashchim Province',      'both'),
    ('Mahendranagar', 'Kanchanpur District, Sudurpashchim Province',   'both'),
    ('Rasuwagadhi',   'Rasuwa District, Bagmati Province',             'both'),
    ('Tatopani',      'Sindhupalchok District, Bagmati Province',      'both');


-- ============================================================
-- TABLE 6: fees
-- Permit fees depending on:
--   - Whether tourist is from SAARC or Non-SAARC country
--   - Whether it is a normal fee or extension fee
-- This is separate so you can update fees without touching code.
-- ============================================================
CREATE TABLE IF NOT EXISTS fees (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    region_id       INT          NOT NULL,     -- Links to trekking_regions
    saarc_fee       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    non_saarc_fee   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    saarc_ext_fee   DECIMAL(10,2) NOT NULL DEFAULT 0.00,  -- Extension fee SAARC
    non_saarc_ext_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,-- Extension fee Non-SAARC
    vat_percent     DECIMAL(5,2)  DEFAULT 0.00,
    applicable_from DATE          NOT NULL,    -- Fee is valid starting this date
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- This links region_id → trekking_regions.id
    -- If you try to add a fee for a region that doesn't exist, MySQL will ERROR
    FOREIGN KEY (region_id) REFERENCES trekking_regions(id)
);


-- ============================================================
-- TABLE 7: organizations
-- Travel agencies (agents) who apply on behalf of tourists.
-- Types: EP = Entry Post, CP = Check Post, AG = Agency/Agent
-- ============================================================
CREATE TABLE IF NOT EXISTS organizations (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(20)  DEFAULT NULL,     -- Agency code
    type        ENUM('EP','CP','AG') NOT NULL, -- Entry Post / Check Post / Agent
    name        VARCHAR(150) NOT NULL,
    address     VARCHAR(255) DEFAULT NULL,
    phone       VARCHAR(20)  DEFAULT NULL,
    email       VARCHAR(100) DEFAULT NULL,
    status      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- TABLE 8: officers / users
-- People who log in to the system (officers at checkposts, admins)
-- ============================================================
CREATE TABLE IF NOT EXISTS officers (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,       -- NEVER store plain password!
    full_name     VARCHAR(100) NOT NULL,
    role          ENUM('admin','issuer','agent','checkpost') NOT NULL DEFAULT 'checkpost',
    organization_id INT        DEFAULT NULL,   -- Which org do they belong to?
    is_active     TINYINT(1)   DEFAULT 1,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);


-- ============================================================
-- TABLE 9: tourists  ← THE MAIN TABLE
-- One row = one tourist applying for a permit.
-- This is the heart of the whole system.
-- ============================================================
CREATE TABLE IF NOT EXISTS tourists (
    id               INT AUTO_INCREMENT PRIMARY KEY,

    -- PERMIT IDENTITY
    ticket_number    VARCHAR(30)  NOT NULL UNIQUE, -- e.g. "TIMS-2026-00001"
    slug             VARCHAR(50)  DEFAULT NULL,    -- URL-friendly ID

    -- PERSONAL DETAILS
    first_name       VARCHAR(100) NOT NULL,
    mid_name         VARCHAR(100) DEFAULT NULL,
    last_name        VARCHAR(100) NOT NULL,
    dob              DATE         NOT NULL,         -- Date of Birth
    gender           ENUM('M','F','O') NOT NULL,    -- Male, Female, Other

    -- COUNTRY & FEES
    -- country_id links to countries table → tells us SAARC or not
    country_id       INT          NOT NULL,
    nationality      VARCHAR(100) DEFAULT NULL,

    -- CONTACT / DOCUMENT
    passport_number  VARCHAR(30)  NOT NULL,
    photo_path       VARCHAR(255) DEFAULT NULL,     -- File path to uploaded photo
    email_address    VARCHAR(150) DEFAULT NULL,
    contact_number   VARCHAR(20)  DEFAULT NULL,
    permanent_address VARCHAR(255) DEFAULT NULL,

    -- OCCUPATION (links to occupations table)
    occupation_id    INT          DEFAULT NULL,

    -- PURPOSE: Trekking / Tourism / Research (links to purposes table)
    purpose_id       INT          NOT NULL,

    -- TREKKING REGION (links to trekking_regions table)
    region_id        INT          DEFAULT NULL,

    -- ENTRY & EXIT POINTS (links to checkposts table)
    entry_post_id    INT          DEFAULT NULL,
    exit_post_id     INT          DEFAULT NULL,

    -- PERMIT DATES
    entry_date       DATE         NOT NULL,
    expiry_date      DATE         NOT NULL,

    -- GUIDE DETAILS (guide hired for trekking)
    guide_name       VARCHAR(150) DEFAULT NULL,
    guide_contact    VARCHAR(20)  DEFAULT NULL,
    guide_total      INT          DEFAULT NULL,     -- Number of guides
    guide_trained    TINYINT(1)   DEFAULT NULL,     -- 1=Trained, 0=Not

    -- PORTER DETAILS
    porter_name      VARCHAR(150) DEFAULT NULL,
    porter_contact   VARCHAR(20)  DEFAULT NULL,
    porter_total     INT          DEFAULT NULL,     -- Number of porters

    -- PAYMENT
    fee              DECIMAL(10,2) DEFAULT NULL,    -- Total fee charged
    payment_method   VARCHAR(50)  DEFAULT NULL,     -- Cash / Card / Online
    receipt          VARCHAR(100) DEFAULT NULL,     -- Receipt number
    paid_at          DATE         DEFAULT NULL,
    fiscal_year      VARCHAR(20)  DEFAULT NULL,     -- e.g. "2082/83"

    -- WHO PROCESSED THIS
    agent_id         INT          DEFAULT NULL,     -- Officer who entered data
    issuer_id        INT          DEFAULT NULL,     -- Officer who approved/issued
    agent_org_id     INT          DEFAULT NULL,
    issuer_org_id    INT          DEFAULT NULL,

    -- STATUS
    -- 0=Draft, 1=Applied, 2=Paid, 3=Issued, 4=Rejected
    status           TINYINT(1)   NOT NULL DEFAULT 0,
    group_permit     TINYINT(1)   NOT NULL DEFAULT 0, -- 1 = part of group

    -- AUDIT (track IP and browser for security)
    applied_at       DATE         DEFAULT NULL,
    issued_at        DATE         DEFAULT NULL,
    ip_address       VARCHAR(50)  DEFAULT NULL,
    created_by       VARCHAR(50)  DEFAULT NULL,
    synced           TINYINT(1)   DEFAULT 0,        -- For offline sync
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- -------------------------------------------------------
    -- FOREIGN KEYS — these "link" columns to other tables
    -- Think of it like: country_id here must exist in countries.id
    -- -------------------------------------------------------
    FOREIGN KEY (country_id)    REFERENCES countries(id),
    FOREIGN KEY (occupation_id) REFERENCES occupations(id),
    FOREIGN KEY (purpose_id)    REFERENCES purposes(id),
    FOREIGN KEY (region_id)     REFERENCES trekking_regions(id),
    FOREIGN KEY (entry_post_id) REFERENCES checkposts(id),
    FOREIGN KEY (exit_post_id)  REFERENCES checkposts(id),
    FOREIGN KEY (agent_id)      REFERENCES officers(id),
    FOREIGN KEY (issuer_id)     REFERENCES officers(id),
    FOREIGN KEY (agent_org_id)  REFERENCES organizations(id),
    FOREIGN KEY (issuer_org_id) REFERENCES organizations(id)
);


-- ============================================================
-- TABLE 10: checkpost_logs
-- Every time a tourist passes through a checkpost, log it here.
-- One tourist can have MANY log entries (entry + exit + mid points).
-- ============================================================
CREATE TABLE IF NOT EXISTS checkpost_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tourist_id      INT          NOT NULL,       -- Which tourist?
    ticket_number   VARCHAR(30)  NOT NULL,       -- Quick reference
    checkpost_id    INT          NOT NULL,       -- Which checkpost scanned them?
    officer_id      INT          DEFAULT NULL,   -- Who scanned?
    scan_time       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('PASS','FLAG','OVERSTAY') NOT NULL DEFAULT 'PASS',
    notes           TEXT         DEFAULT NULL,
    synced          TINYINT(1)   DEFAULT 0,

    FOREIGN KEY (tourist_id)   REFERENCES tourists(id),
    FOREIGN KEY (checkpost_id) REFERENCES checkposts(id),
    FOREIGN KEY (officer_id)   REFERENCES officers(id)
);


-- ============================================================
-- TABLE 11: notices
-- System notices/announcements shown to agents or officers
-- ============================================================
CREATE TABLE IF NOT EXISTS notices (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    recipient  VARCHAR(100) DEFAULT NULL,  -- Specific user or 'all'
    message    TEXT         NOT NULL,
    status     ENUM('Y','N') NOT NULL DEFAULT 'Y',
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- USEFUL QUERIES TO REMEMBER (save these!)
-- ============================================================

-- See all your tables:
-- SHOW TABLES;

-- See columns of a table:
-- DESCRIBE tourists;

-- Count all tourists:
-- SELECT COUNT(*) FROM tourists;

-- See all issued permits:
-- SELECT * FROM tourists WHERE status = 3;

-- See tourists from SAARC countries:
-- SELECT t.*, c.name AS country_name
-- FROM tourists t
-- JOIN countries c ON t.country_id = c.id
-- WHERE c.is_saarc = 1;

-- ============================================================
SHOW TABLES;
