DROP TABLE IF EXISTS athlete;

CREATE TABLE athlete (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  aida_id TEXT,
  gender TEXT NOT NULL,
  country TEXT NOT NULL,
  special_ranking BOOL,
  club TEXT
);
