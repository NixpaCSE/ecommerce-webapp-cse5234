-- BobaBox MySQL schema.
-- Drops run first so this script can be applied again on an empty database.
-- Do not run it against the live database if you need to keep existing orders.

SET NAMES utf8mb4;

DROP TABLE IF EXISTS CUSTOMER_ORDER_LINE_ITEM;
DROP TABLE IF EXISTS CUSTOMER_ORDER;
DROP TABLE IF EXISTS PAYMENT_INFO;
DROP TABLE IF EXISTS SHIPPING_INFO;
DROP TABLE IF EXISTS ITEM;

CREATE TABLE ITEM (
  ID int auto_increment primary key,
  ITEM_NUMBER int,
  NAME varchar(255),
  DESCRIPTION varchar(255),
  AVAILABLE_QUANTITY int,
  UNIT_PRICE double,
  IMAGE_URL varchar(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE CUSTOMER_ORDER (
  ID int auto_increment primary key,
  CUSTOMER_NAME varchar(255),
  CUSTOMER_EMAIL varchar(255),
  SHIPPING_INFO_ID_FK int,
  PAYMENT_INFO_ID_FK int,
  STATUS varchar(255) default 'New'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE CUSTOMER_ORDER_LINE_ITEM (
  ID int auto_increment primary key,
  ITEM_NUMBER int,
  ITEM_NAME varchar(255),
  QUANTITY int,
  CUSTOMER_ORDER_ID_FK int
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE PAYMENT_INFO (
  ID int auto_increment primary key,
  HOLDER_NAME varchar(255),
  CARD_NUM varchar(255),
  EXP_DATE varchar(255),
  CVV varchar(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE SHIPPING_INFO (
  ID int auto_increment primary key,
  ADDRESS1 varchar(255),
  ADDRESS2 varchar(255),
  CITY varchar(255),
  STATE varchar(255),
  COUNTRY varchar(255),
  POSTAL_CODE varchar(255),
  EMAIL varchar(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE CUSTOMER_ORDER
  ADD COLUMN CONFIRMATION_CODE varchar(20) NULL;

ALTER TABLE CUSTOMER_ORDER
  ADD CONSTRAINT UQ_CUSTOMER_ORDER_CONFIRMATION_CODE UNIQUE (CONFIRMATION_CODE);

-- Current ITEM rows from the inventory API. Quantities are the live stock
-- (orders already reduced Taro and Brown Sugar to 0, and the other kits to 49).
INSERT INTO ITEM (ID, ITEM_NUMBER, NAME, DESCRIPTION, AVAILABLE_QUANTITY, UNIT_PRICE, IMAGE_URL) VALUES
(1, 1, 'Strawberry Milk Tea Kit', 'Real strawberry purée, black tea, and tapioca pearls. Makes 6 drinks.', 50, 22.49, 'https://bobabox-product-images.s3.us-east-1.amazonaws.com/strawberry.jpg'),
(2, 2, 'Taro Milk Tea Kit', 'Real taro powder, jasmine tea, and tapioca pearls. Makes 6 drinks.', 50, 23.99, 'https://bobabox-product-images.s3.us-east-1.amazonaws.com/taro.jpg'),
(3, 3, 'Brown Sugar Boba Kit', 'Slow-cooked brown sugar syrup and tapioca pearls. Just add milk. Makes 6 drinks.', 50, 24.99, 'https://bobabox-product-images.s3.us-east-1.amazonaws.com/brown-sugar.jpg'),
(4, 4, 'Matcha Latte Kit', 'Ceremonial-grade matcha, cane syrup, and tapioca pearls. Makes 6 drinks.', 50, 26.99, 'https://bobabox-product-images.s3.us-east-1.amazonaws.com/matcha.jpg'),
(5, 5, 'Mango Green Tea Kit', 'Jasmine green tea, mango syrup, and popping boba. Makes 6 drinks.', 50, 22.99, 'https://bobabox-product-images.s3.us-east-1.amazonaws.com/mango.jpg');
