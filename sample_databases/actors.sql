
DROP DATABASE IF EXISTS actors;
CREATE DATABASE IF NOT EXISTS actors;
USE actors;

SELECT 'CREATING DATABASE STRUCTURE' as 'INFO';

DROP TABLE IF EXISTS actors;

/*!50503 set default_storage_engine = InnoDB */;
/*!50503 select CONCAT('storage engine: ', @@default_storage_engine) as INFO */;

CREATE TABLE actors (
actor_name  VARCHAR(80)   NOT NULL,
gender ENUM('male','female')   NOT NULL,
dob DATE  NOT NULL,
birthplace VARCHAR(80) NOT NULL,
award ENUM('oscar','golden globe','bafta'),
height FLOAT NOT NULL,
PRIMARY KEY (actor_name)
);

SELECT 'LOADING actors' as 'INFO';
source load_actors.dump ;