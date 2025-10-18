-- clean create_tables.sql (no BOM)
CREATE SCHEMA IF NOT EXISTS fifa;

CREATE TABLE IF NOT EXISTS fifa.teams (
  team_id            BIGINT PRIMARY KEY,
  team_name          TEXT,
  country            TEXT,
  league             TEXT,
  overall_rating     INTEGER,
  attack             INTEGER,
  midfield           INTEGER,
  defense            INTEGER,
  fifa_rank          INTEGER,
  founded_year       INTEGER,
  stadium            TEXT
);

CREATE TABLE IF NOT EXISTS fifa.players (
  player_id          BIGINT PRIMARY KEY,
  player_name        TEXT,
  common_name        TEXT,
  nationality        TEXT,
  dob                DATE,
  age                INTEGER,
  height_cm          INTEGER,
  weight_kg          INTEGER,
  preferred_foot     TEXT,
  position           TEXT,
  overall            INTEGER,
  potential          INTEGER,
  value_eur          NUMERIC,
  wage_eur           NUMERIC,
  club_name          TEXT,
  club_id            BIGINT,
  team_id            BIGINT REFERENCES fifa.teams(team_id),
  joined             DATE,
  contract_until     INTEGER,
  international_reps INTEGER,
  gender             TEXT
);

CREATE TABLE IF NOT EXISTS fifa.coaches (
  coach_id           BIGINT PRIMARY KEY,
  coach_name         TEXT,
  nationality        TEXT,
  team_id            BIGINT REFERENCES fifa.teams(team_id),
  age                INTEGER,
  experience_years   INTEGER,
  preferred_formation TEXT
);

CREATE INDEX IF NOT EXISTS idx_players_team ON fifa.players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_club ON fifa.players(club_id);
CREATE INDEX IF NOT EXISTS idx_teams_country ON fifa.teams(country);
CREATE INDEX IF NOT EXISTS idx_coaches_team ON fifa.coaches(team_id);