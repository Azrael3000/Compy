DROP TABLE IF EXISTS start;

CREATE TABLE start (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competition_athlete_id INTEGER NOT NULL,
  discipline TEXT NOT NULL,
  lane INTEGER NOT NULL,
  day TEXT NOT NULL,
  OT TEXT NOT NULL,
  PB FLOAT,
  AP FLOAT,
  RP FLOAT,
  card TEXT,
  penalty FLOAT,
  remarks TEXT,
  judge_remarks TEXT
);
