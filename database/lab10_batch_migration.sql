-- Run once on the storefront database, right before deploying the Lab 10
-- order Lambda and turning on the batch schedule.
--
-- Orders placed before Lab 10 already had their stock subtracted by the old
-- order Lambda but are still 'New'. Mark them 'Processed' so the batch
-- Lambda does not subtract them a second time.
UPDATE CUSTOMER_ORDER SET STATUS = 'Processed' WHERE STATUS = 'New';
