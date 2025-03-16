DROP TABLE IF EXISTS competition_athlete;

CREATE TABLE competition_athlete (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competition_id INTEGER NOT NULL,
  athlete_id INTEGER NOT NULL,
  special_ranking BOOL NOT NULL DEFAULT 0,
  paid BOOL NOT NULL DEFAULT 0,
  medical_checked BOOL NOT NULL DEFAULT 0,
  registered BOOL NOT NULL DEFAULT 0
);
