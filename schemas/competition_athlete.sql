DROP TABLE IF EXISTS competition_athlete;

CREATE TABLE competition_athlete (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competition_id INTEGER NOT NULL,
  athlete_id INTEGER NOT NULL
);
