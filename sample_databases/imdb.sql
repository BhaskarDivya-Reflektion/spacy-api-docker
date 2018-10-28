
DROP DATABASE IF EXISTS imdb;
CREATE DATABASE IF NOT EXISTS imdb;
USE imdb;

SELECT 'CREATING DATABASE STRUCTURE' as 'INFO';

DROP TABLE IF EXISTS movies;

/*!50503 set default_storage_engine = InnoDB */;
/*!50503 select CONCAT('storage engine: ', @@default_storage_engine) as INFO */;

CREATE TABLE movies (
color   VARCHAR(30)   NOT NULL,
director_name  VARCHAR(80)   NOT NULL,
num_critic_for_reviews  INT   NOT NULL,
duration  INT   NOT NULL,
director_facebook_likes INT   NOT NULL,
actor_3_facebook_likes  INT   NOT NULL,
actor_2_name  VARCHAR(80)   NOT NULL,
actor_1_facebook_likes  INT   NOT NULL,
gross  INT  ,
genres   VARCHAR(80)   NOT NULL,
actor_1_name  VARCHAR(80)   NOT NULL,
movie_title  DATE    NOT NULL,
num_voted_users  INT   NOT NULL,
cast_total_facebook_likes  INT   NOT NULL,
actor_3_name  VARCHAR(80)   NOT NULL,
facenumber_in_poster  INT   NOT NULL,
plot_keywords   VARCHAR(160)   NOT NULL,
movie_imdb_link  VARCHAR(80)   NOT NULL,
num_user_for_reviews  INT   NOT NULL,
language  VARCHAR(30)   NOT NULL,
country  VARCHAR(30)   NOT NULL,
content_rating  VARCHAR(20)   NOT NULL,
budget  INT   NOT NULL,
title_year INT   NOT NULL,
actor_2_facebook_likes  INT   NOT NULL,
imdb_score  FLOAT   NOT NULL,
aspect_ratio  FLOAT   NOT NULL,
movie_facebook_likes   INT   NOT NULL,
PRIMARY KEY (movie_title, title_year)
);

SELECT 'LOADING movies' as 'INFO';
source load_movies.dump ;