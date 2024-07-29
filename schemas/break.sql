DROP TABLE IF EXISTS break;

CREATE TABLE break (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competition_id INTEGER NOT NULL,
  discipline TEXT NOT NULL,
  day TEXT NOT NULL,
  duration INTEGER NOT NULL,
  idx INTEGER NOT NULL
);
