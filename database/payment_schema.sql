-- BobaBox payment processing service (Lab 9).
-- This database belongs only to the payment service, standing in for an
-- independent bank. The storefront's inventory and order services never
-- connect to it. Run as the RDS admin user.

CREATE DATABASE IF NOT EXISTS payment_service CHARACTER SET utf8mb4;

-- Replace the password before running. Use the same value for the payment
-- Lambda's DB_PASSWORD environment variable.
CREATE USER IF NOT EXISTS 'payment_svc'@'%' IDENTIFIED BY 'CHANGE_ME';
GRANT SELECT, INSERT ON payment_service.* TO 'payment_svc'@'%';

USE payment_service;

-- Only the last 4 card digits are kept. The CVV is never stored.
CREATE TABLE IF NOT EXISTS PAYMENT (
  ID int auto_increment primary key,
  PAYMENT_TOKEN varchar(32) NOT NULL,
  HOLDER_NAME varchar(255),
  CARD_LAST4 varchar(4),
  EXP_DATE varchar(5),
  AMOUNT decimal(10, 2),
  STATUS varchar(32) default 'Approved',
  CREATED_AT timestamp default CURRENT_TIMESTAMP,
  CONSTRAINT UQ_PAYMENT_TOKEN UNIQUE (PAYMENT_TOKEN)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
