
DROP DATABASE IF EXISTS email;
CREATE DATABASE IF NOT EXISTS email;
USE email;

SELECT 'CREATING DATABASE STRUCTURE' as 'INFO';

DROP TABLE IF EXISTS email;

/*!50503 set default_storage_engine = InnoDB */;
/*!50503 select CONCAT('storage engine: ', @@default_storage_engine) as INFO */;

CREATE TABLE email (
time TIMESTAMP NOT NULL,
browser VARCHAR(50),
campaign VARCHAR(80),
city VARCHAR(80) NOT NULL,
count INT NOT NULL,
device VARCHAR(80),
domain_hash VARCHAR(100) NOT NULL,
domain_name VARCHAR(80),
event_type ENUM('open','click') NOT NULL,
geohash VARCHAR(100),
os ENUM('iOS','OS X','Windows 7'),
rec_type ENUM('not personalized','personalized'),
region VARCHAR(80),
PRIMARY KEY (time,domain_hash)
);

SELECT 'LOADING email' as 'INFO';
source load_email.dump ;