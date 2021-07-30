DROP TABLE IF EXISTS repository;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT, 
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL, 
  image TEXT
);

CREATE TABLE repository (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL, 
  link TEXT NOT NULL,
  user_id INTEGER,
  creation_date timestamp,
  analysis_date timestamp,
  analysed INTEGER
);