DROP TABLE IF EXISTS records;

CREATE TABLE records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  federation TEXT NOT NULL,
  country TEXT NOT NULL,
  class TEXT NOT NULL,
  gender TEXT NOT NULL,
  discipline TEXT NOT NULL,
  value REAL NOT NULL
);