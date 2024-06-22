DROP TABLE IF EXISTS start;

CREATE TABLE start (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competition_athlete_id INTEGER NOT NULL,
  discipline TEXT NOT NULL,
  lane INTEGER NOT NULL,
  OT TEXT NOT NULL,
  PB TEXT,
  AP TEXT,
  RP TEXT,
  card TEXT,
  penalty TEXT,
  remarks TEXT
);
