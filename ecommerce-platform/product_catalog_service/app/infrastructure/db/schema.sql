-- =====================================================================
-- Product Catalog Service — MySQL Schema
-- Database: product_catalog_db
-- MySQL is the system of record; Elasticsearch is a derived, rebuildable
-- read index kept in sync via ProductService (see SearchIndexer).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS product_catalog_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE product_catalog_db;

-- ---------------------------------------------------------------------
-- categories: self-referential tree (Composite-style hierarchy) (2.1)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    slug        VARCHAR(160) NOT NULL,
    parent_id   CHAR(36)     NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                             ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_category_slug (slug),
    INDEX idx_category_parent (parent_id),
    CONSTRAINT fk_category_parent FOREIGN KEY (parent_id)
        REFERENCES categories (id) ON DELETE SET NULL
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- products: core listing (2.1, 2.2)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id              CHAR(36)      NOT NULL PRIMARY KEY,
    sku             VARCHAR(64)   NOT NULL,
    name            VARCHAR(255)  NOT NULL,
    description     TEXT          NULL,
    price           DECIMAL(12,2) NOT NULL,
    currency        CHAR(3)       NOT NULL DEFAULT 'INR',
    category_id     CHAR(36)      NOT NULL,
    status          ENUM('DRAFT', 'ACTIVE', 'OUT_OF_STOCK', 'DISCONTINUED')
                                  NOT NULL DEFAULT 'DRAFT',
    stock_quantity  INT UNSIGNED  NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_product_sku (sku),
    INDEX idx_product_category (category_id),
    INDEX idx_product_status (status),
    CONSTRAINT fk_product_category FOREIGN KEY (category_id)
        REFERENCES categories (id) ON DELETE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- product_images: 1:N, one primary image per product (2.2)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_images (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    product_id  CHAR(36)     NOT NULL,
    url         VARCHAR(500) NOT NULL,
    is_primary  BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  SMALLINT     NOT NULL DEFAULT 0,

    INDEX idx_image_product (product_id),
    CONSTRAINT fk_image_product FOREIGN KEY (product_id)
        REFERENCES products (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- product_specifications: flexible key/value spec sheet (2.2)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_specifications (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    product_id  CHAR(36)     NOT NULL,
    spec_key    VARCHAR(100) NOT NULL,
    spec_value  VARCHAR(500) NOT NULL,

    INDEX idx_spec_product (product_id),
    UNIQUE KEY uq_product_spec_key (product_id, spec_key),
    CONSTRAINT fk_spec_product FOREIGN KEY (product_id)
        REFERENCES products (id) ON DELETE CASCADE
) ENGINE = InnoDB;
