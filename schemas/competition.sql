DROP TABLE IF EXISTS competition;

CREATE TABLE competition (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  save_date TEXT NOT NULL,
  version TEXT NOT NULL,
  lane_style TEXT NOT NULL,
  comp_type TEXT NOT NULL,
  comp_file TEXT NOT NULL,
  start_date TEXT,
  end_date TEXT,
  sponsor_img TEXT,
  selected_country TEXT,
  disciplines INTEGER NOT NULL,
  special_ranking_name TEXT,
  publish_result INTEGER NOT NULL DEFAULT 0
);
