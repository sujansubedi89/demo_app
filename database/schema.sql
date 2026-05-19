-- database/schema.sql
-- ============================================
-- Run this file once to set up the database
-- In MySQL Workbench: File > Open SQL Script
-- Then press the lightning bolt ⚡ to run
-- ============================================

CREATE DATABASE IF NOT EXISTS nepal_ticketing
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE nepal_ticketing;

CREATE TABLE IF NOT EXISTS tourists (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number    VARCHAR(20)  NOT NULL UNIQUE,
    full_name        VARCHAR(100) NOT NULL,
    passport_number  VARCHAR(30)  NOT NULL,
    nationality      VARCHAR(50)  NOT NULL,
    photo_path       VARCHAR(255) DEFAULT NULL,
    -- visa_type        VARCHAR(30)  NOT NULL,
    -- vehicle_type     VARCHAR(30)  DEFAULT NULL,
    -- vehicle_number   VARCHAR(20)  DEFAULT NULL,
    gender
    country anusar ko price saarc vs FOREIGN
    
    dob
    occupation
    purpose select 3
    area select further SELECT
    entrypoint exit point 
    entry_date       DATE         NOT NULL,
    expiry_date      DATE         NOT NULL,
    created_by       VARCHAR(50)  NOT NULL,
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    synced           TINYINT(1)   DEFAULT 0
);

CREATE TABLE IF NOT EXISTS checkpost_logs (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number    VARCHAR(20)  NOT NULL,
    checkpost_name   VARCHAR(50)  NOT NULL,
    officer_name     VARCHAR(50)  NOT NULL,
    scan_time        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    status           VARCHAR(10)  NOT NULL DEFAULT 'PASS',
    synced           TINYINT(1)   DEFAULT 0,
    FOREIGN KEY (ticket_number) REFERENCES tourists(ticket_number)
);

CREATE TABLE IF NOT EXISTS checkposts (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(50)  NOT NULL UNIQUE,
    location  VARCHAR(100) DEFAULT NULL,
    is_active TINYINT(1)   DEFAULT 1
);

CREATE TABLE IF NOT EXISTS officers (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100) NOT NULL,
    checkpost     VARCHAR(50)  NOT NULL,
    is_active     TINYINT(1)   DEFAULT 1,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO checkposts (name, location) VALUES
    ('Birgunj',       'Parsa District, Bagmati Province'),
    ('Bhairahawa',    'Rupandehi District, Lumbini Province'),
    ('Kakarbhitta',   'Jhapa District, Koshi Province'),
    ('Dhangadhi',     'Kailali District, Sudurpashchim Province'),
    ('Mahendranagar', 'Kanchanpur District, Sudurpashchim Province');

-- Create the app MySQL user
CREATE USER IF NOT EXISTS 'ticket_app'@'localhost'
    IDENTIFIED BY 'Nepal@2026';

GRANT ALL PRIVILEGES ON nepal_ticketing.* TO 'ticket_app'@'localhost';
FLUSH PRIVILEGES;

SHOW TABLES;