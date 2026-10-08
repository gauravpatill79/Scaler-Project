-- =====================================================================
-- Payment Service — MySQL Schema
-- Database: payment_service_db
--
-- No card numbers, bank account numbers, or other raw payment instrument
-- data are stored anywhere in this schema — only the method type and the
-- gateway's own reference for the transaction. Raw instrument data stays
-- with the gateway/PSP, which is standard PCI-DSS scope reduction practice.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS payment_service_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE payment_service_db;

-- ---------------------------------------------------------------------
-- payments: one row per order — order_id is unique, which is also the
-- idempotency guard against a redelivered order.created event.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    id                CHAR(36)      NOT NULL PRIMARY KEY,
    order_id          CHAR(36)      NOT NULL,
    user_id           CHAR(36)      NOT NULL,
    amount            DECIMAL(12,2) NOT NULL,
    currency          CHAR(3)       NOT NULL DEFAULT 'INR',
    method            ENUM('CARD', 'NET_BANKING', 'WALLET', 'UPI') NOT NULL,
    status            ENUM('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')
                                    NOT NULL DEFAULT 'PENDING',
    gateway_reference VARCHAR(100)  NULL,
    receipt_number    VARCHAR(50)   NULL,
    failure_reason    VARCHAR(255)  NULL,
    created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_payment_order (order_id),
    INDEX idx_payment_user (user_id),
    INDEX idx_payment_status (status)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- payment_transactions: audit log of every status change for a payment,
-- covering HLD 3.5's "transaction logs" and PRD 5.2's trust requirement.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment_transactions (
    id          CHAR(36)    NOT NULL PRIMARY KEY,
    payment_id  CHAR(36)    NOT NULL,
    from_status VARCHAR(20) NULL,
    to_status   VARCHAR(20) NOT NULL,
    detail      VARCHAR(255) NULL,
    changed_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_transaction_payment (payment_id),
    CONSTRAINT fk_transaction_payment FOREIGN KEY (payment_id)
        REFERENCES payments (id) ON DELETE CASCADE
) ENGINE = InnoDB;
