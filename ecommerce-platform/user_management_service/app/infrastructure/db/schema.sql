-- =====================================================================
-- User Management Service — MySQL Schema
-- Database: user_management_db
-- =====================================================================

CREATE DATABASE IF NOT EXISTS user_management_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE user_management_db;

-- ---------------------------------------------------------------------
-- users: core account record (auth-relevant fields only)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              CHAR(36)     NOT NULL PRIMARY KEY,          -- UUID v4
    email           VARCHAR(255) NOT NULL,
    phone           VARCHAR(20)  NULL,
    password_hash   VARCHAR(255) NULL,                          -- NULL for social-only accounts
    status          ENUM('PENDING_VERIFICATION', 'ACTIVE', 'SUSPENDED', 'DEACTIVATED')
                                 NOT NULL DEFAULT 'PENDING_VERIFICATION',
    failed_login_attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
    last_login_at   DATETIME     NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_users_email (email),
    INDEX idx_users_status (status)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- user_profiles: 1:1 with users — non-auth personal details
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id      CHAR(36)     NOT NULL PRIMARY KEY,
    first_name   VARCHAR(100) NULL,
    last_name    VARCHAR(100) NULL,
    avatar_url   VARCHAR(500) NULL,
    date_of_birth DATE        NULL,
    address_line1 VARCHAR(255) NULL,
    address_line2 VARCHAR(255) NULL,
    city         VARCHAR(100) NULL,
    state        VARCHAR(100) NULL,
    postal_code  VARCHAR(20)  NULL,
    country      VARCHAR(100) NULL,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_profile_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- social_accounts: 1:N — supports "login with social media profile" (1.1)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS social_accounts (
    id                CHAR(36)     NOT NULL PRIMARY KEY,
    user_id           CHAR(36)     NOT NULL,
    provider          ENUM('GOOGLE', 'FACEBOOK', 'APPLE') NOT NULL,
    provider_user_id  VARCHAR(255) NOT NULL,
    linked_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_provider_account (provider, provider_user_id),
    INDEX idx_social_user (user_id),
    CONSTRAINT fk_social_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- password_reset_tokens: supports secure reset link (1.4)
-- Store only a hash of the token, never the raw token.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    user_id     CHAR(36)     NOT NULL,
    token_hash  VARCHAR(255) NOT NULL,
    expires_at  DATETIME     NOT NULL,
    used        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_reset_user (user_id),
    INDEX idx_reset_expiry (expires_at),
    CONSTRAINT fk_reset_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- user_sessions: supports session management (6.2). Optional if tokens
-- are pure stateless JWTs; kept here to allow server-side revocation.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_sessions (
    id            CHAR(36)     NOT NULL PRIMARY KEY,
    user_id       CHAR(36)     NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent    VARCHAR(255) NULL,
    ip_address    VARCHAR(45)  NULL,
    expires_at    DATETIME     NOT NULL,
    revoked       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_session_user (user_id),
    CONSTRAINT fk_session_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB;
