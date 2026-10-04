-- =====================================================================
-- Order Management Service — MySQL Schema
-- Database: order_service_db
-- =====================================================================

CREATE DATABASE IF NOT EXISTS order_service_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE order_service_db;

-- ---------------------------------------------------------------------
-- orders: one row per order, address embedded (no separate address
-- book in this service — User Management owns the user's saved
-- addresses; this is a point-in-time snapshot for the order).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id                CHAR(36)      NOT NULL PRIMARY KEY,
    user_id           CHAR(36)      NOT NULL,
    status            ENUM('PENDING_PAYMENT', 'PAID', 'PROCESSING', 'SHIPPED',
                            'DELIVERED', 'CANCELLED', 'PAYMENT_FAILED')
                                     NOT NULL DEFAULT 'PENDING_PAYMENT',
    total_amount      DECIMAL(12,2) NOT NULL,
    currency          CHAR(3)       NOT NULL DEFAULT 'INR',
    tracking_number   VARCHAR(100)  NULL,

    address_line1     VARCHAR(255)  NOT NULL,
    address_line2     VARCHAR(255)  NULL,
    address_city      VARCHAR(100)  NOT NULL,
    address_state     VARCHAR(100)  NOT NULL,
    address_postal_code VARCHAR(20) NOT NULL,
    address_country   VARCHAR(100)  NOT NULL,

    created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_order_user (user_id),
    INDEX idx_order_status (status)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- order_items: line items, price/name snapshotted at order time —
-- never joined against Product Catalog's live price after creation.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id              CHAR(36)      NOT NULL PRIMARY KEY,
    order_id        CHAR(36)      NOT NULL,
    product_id      CHAR(36)      NOT NULL,
    name_snapshot   VARCHAR(255)  NOT NULL,
    price_snapshot  DECIMAL(12,2) NOT NULL,
    quantity        INT UNSIGNED  NOT NULL,

    INDEX idx_order_item_order (order_id),
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id)
        REFERENCES orders (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- order_status_history: audit trail backing order tracking (4.3)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_status_history (
    id          CHAR(36)   NOT NULL PRIMARY KEY,
    order_id    CHAR(36)   NOT NULL,
    from_status VARCHAR(30) NULL,
    to_status   VARCHAR(30) NOT NULL,
    changed_at  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_status_history_order (order_id),
    CONSTRAINT fk_status_history_order FOREIGN KEY (order_id)
        REFERENCES orders (id) ON DELETE CASCADE
) ENGINE = InnoDB;
