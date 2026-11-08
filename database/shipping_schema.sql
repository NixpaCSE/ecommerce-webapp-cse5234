-- BobaBox shipping company (separate from the storefront).
-- Run this as the RDS admin user, on the same MySQL instance as the
-- storefront and payment databases. It creates its own database. The
-- storefront Lambda never connects to it.
--
-- One database holds both tables. A packet belongs to a shipment, so the
-- two have to share a shipping_token. Splitting them into two databases
-- would drop that link. The storefront still keeps SHIPPING_INFO for the
-- address the customer typed; this database is the shipping company's copy.
--
-- Sample from the lab slide: 3 line items, 10 units each, 1.0 lb per unit.
-- That is one shipment row and three packet rows at 10.00 lb, all with the
-- same shipping_token:
--
--   shipment
--     shipping_token  business_id    order_id  street      city      state  zip    status     created_at
--     a3f1c9e2-...    STORE-BOBABOX  BBA-...   1 Main St   Columbus  OH     43215  INITIATED  (now)
--
--   packet
--     shipping_token  packet_id  line_item_id  weight_lb
--     a3f1c9e2-...    1          L1            10.00
--     a3f1c9e2-...    2          L2            10.00
--     a3f1c9e2-...    3          L3            10.00

CREATE DATABASE IF NOT EXISTS shipping_service CHARACTER SET utf8mb4;

-- Replace the password before running. Use the same value for the shipping
-- Lambda's DB_PASSWORD environment variable.
CREATE USER IF NOT EXISTS 'shipping_svc'@'%' IDENTIFIED BY 'CHANGE_ME';
GRANT SELECT, INSERT ON shipping_service.* TO 'shipping_svc'@'%';

USE shipping_service;

-- Drops make this script safe to re-run. Do not run it once real shipments
-- are stored. There is no business table: BobaBox is the only storefront,
-- and its registration id is written on each shipment by the order Lambda.
DROP TABLE IF EXISTS packet;
DROP TABLE IF EXISTS shipment;
DROP TABLE IF EXISTS business;

CREATE TABLE IF NOT EXISTS shipment (
  shipping_token varchar(36) NOT NULL,
  business_id varchar(32) NOT NULL,
  order_id varchar(64) NOT NULL,
  street varchar(255) NOT NULL,
  city varchar(255) NOT NULL,
  state varchar(32) NOT NULL,
  zip varchar(16) NOT NULL,
  status varchar(32) NOT NULL DEFAULT 'INITIATED',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (shipping_token),
  CONSTRAINT UQ_SHIPMENT_BUSINESS_ORDER UNIQUE (business_id, order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- packet_id is 1, 2, 3... inside one shipment, so the same order's packets
-- stay together under one shipping_token.
CREATE TABLE IF NOT EXISTS packet (
  shipping_token varchar(36) NOT NULL,
  packet_id int NOT NULL,
  line_item_id varchar(64) NOT NULL,
  weight_lb decimal(8, 2) NOT NULL,
  PRIMARY KEY (shipping_token, packet_id),
  CONSTRAINT FK_PACKET_SHIPMENT FOREIGN KEY (shipping_token) REFERENCES shipment (shipping_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
