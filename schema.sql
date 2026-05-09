-- ============================================================
-- Smart Healthcare Monitoring System – MySQL Schema
-- Run: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS healthcare_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE healthcare_db;

-- ── Users (admin / doctor / patient login accounts) ──────────
CREATE TABLE IF NOT EXISTS users (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(80)  NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role         ENUM('admin','doctor','patient') NOT NULL DEFAULT 'patient',
    email        VARCHAR(120),
    full_name    VARCHAR(120),
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Patients (profile records) ───────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    patient_id        VARCHAR(20)  NOT NULL UNIQUE,  -- e.g. PT-001
    name              VARCHAR(100) NOT NULL,
    age               INT          NOT NULL,
    gender            ENUM('Male','Female','Other') NOT NULL,
    contact           VARCHAR(20),
    blood_group       VARCHAR(5),
    medical_history   TEXT,
    assigned_doctor_id INT,
    user_id           INT,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_doctor_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id)           REFERENCES users(id) ON DELETE SET NULL
);

-- ── Health Records (vitals per reading) ──────────────────────
CREATE TABLE IF NOT EXISTS health_records (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_id          INT            NOT NULL,
    temperature         DECIMAL(5,2)   NOT NULL,  -- °F
    heart_rate          INT            NOT NULL,  -- bpm
    oxygen_level        DECIMAL(5,2)   NOT NULL,  -- %
    blood_pressure_sys  INT,                       -- mmHg systolic
    blood_pressure_dia  INT,                       -- mmHg diastolic
    status              ENUM('normal','warning','critical') NOT NULL DEFAULT 'normal',
    recorded_at         DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- ── Alerts ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    patient_id  INT          NOT NULL,
    alert_type  VARCHAR(100) NOT NULL,
    message     TEXT         NOT NULL,
    severity    ENUM('warning','critical') NOT NULL,
    is_resolved BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- ── Indexes for performance ───────────────────────────────────
CREATE INDEX idx_health_patient  ON health_records(patient_id);
CREATE INDEX idx_health_recorded ON health_records(recorded_at);
CREATE INDEX idx_alert_patient   ON alerts(patient_id);
CREATE INDEX idx_alert_resolved  ON alerts(is_resolved);
