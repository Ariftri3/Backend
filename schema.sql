-- ============================================
-- MindCare App - Database Schema
-- ============================================

CREATE DATABASE IF NOT EXISTS mental_health_app;
USE mental_health_app;

-- ============================================
-- Tabel Users (pengguna)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nama        VARCHAR(100)    NOT NULL,
    email       VARCHAR(150)    NOT NULL UNIQUE,
    password    VARCHAR(255)    NOT NULL,
    foto_url    VARCHAR(255)    DEFAULT NULL,
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Tabel Mood Logs (catatan mood harian)
-- Digunakan oleh: Dashboard, Statistics
-- ============================================
CREATE TABLE IF NOT EXISTS mood_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    mood_value  FLOAT           NOT NULL,   -- nilai 1.0 - 5.0
    mood_label  VARCHAR(50)     NOT NULL,   -- 'Sangat Buruk', 'Buruk', 'Biasa', 'Baik', 'Sangat Baik'
    catatan     TEXT            DEFAULT NULL,
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Tabel Journals (jurnal harian)
-- Digunakan oleh: Journal
-- ============================================
CREATE TABLE IF NOT EXISTS journals (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    title       VARCHAR(200)    NOT NULL,
    content     TEXT            NOT NULL,
    mood        VARCHAR(50)     DEFAULT NULL,
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Tabel Assessments (hasil penilaian kesehatan mental)
-- Digunakan oleh: Assessment
-- ============================================
CREATE TABLE IF NOT EXISTS assessments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    score       INT             NOT NULL,   -- 0 - 100
    level       VARCHAR(50)     NOT NULL,   -- 'Rendah', 'Sedang', 'Tinggi'
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Tabel Chat Histories (riwayat chatbot)
-- Digunakan oleh: Chatbot
-- ============================================
CREATE TABLE IF NOT EXISTS chat_histories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    message     TEXT            NOT NULL,
    reply       TEXT            NOT NULL,
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
