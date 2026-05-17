from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY,
  guild_id INTEGER,
  status TEXT NOT NULL,
  current_turn INTEGER NOT NULL,
  max_turns INTEGER NOT NULL,
  processing_turn INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
  id INTEGER NOT NULL,
  game_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  color TEXT NOT NULL,
  discord_role_id INTEGER,
  discord_channel_id INTEGER,
  orders_locked INTEGER NOT NULL DEFAULT 0,
  donated_units_this_turn INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (id, game_id),
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cities (
  id INTEGER NOT NULL,
  game_id INTEGER NOT NULL,
  owner_type TEXT NOT NULL,
  owner_team_id INTEGER,
  castle_level INTEGER NOT NULL,
  units INTEGER NOT NULL,
  PRIMARY KEY (id, game_id),
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL,
  turn_number INTEGER NOT NULL,
  actor_type TEXT NOT NULL,
  team_id INTEGER,
  type TEXT NOT NULL,
  source_city_id INTEGER,
  target_city_id INTEGER,
  units INTEGER NOT NULL,
  upgrade_cost INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS unit_reservations (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL,
  turn_number INTEGER NOT NULL,
  team_id INTEGER,
  city_id INTEGER NOT NULL,
  order_id INTEGER NOT NULL,
  units INTEGER NOT NULL,
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS turn_history (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL,
  turn_number INTEGER NOT NULL,
  killed_units INTEGER NOT NULL,
  events_json TEXT NOT NULL,
  processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (game_id, turn_number),
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS battle_history (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL,
  turn_number INTEGER NOT NULL,
  target_city_id INTEGER NOT NULL,
  defender_owner_type TEXT NOT NULL,
  defender_team_id INTEGER,
  defender_units INTEGER NOT NULL,
  attackers_json TEXT NOT NULL,
  winner_owner_type TEXT NOT NULL,
  winner_team_id INTEGER,
  remaining_units INTEGER NOT NULL,
  killed_units INTEGER NOT NULL,
  random_seed INTEGER,
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS admin_audit_log (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL,
  turn_number INTEGER NOT NULL,
  host_user_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  before_json TEXT NOT NULL,
  after_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exports (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  format TEXT NOT NULL,
  created_by_user_id INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS message_refs (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  team_id INTEGER,
  channel_id INTEGER NOT NULL,
  message_id INTEGER NOT NULL,
  FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_orders_game_turn_team
  ON orders(game_id, turn_number, team_id);
CREATE INDEX IF NOT EXISTS ix_orders_game_turn_actor
  ON orders(game_id, turn_number, actor_type);
CREATE INDEX IF NOT EXISTS ix_unit_reservations_game_turn_city
  ON unit_reservations(game_id, turn_number, city_id);
CREATE INDEX IF NOT EXISTS ix_teams_game_channel
  ON teams(game_id, discord_channel_id);
CREATE INDEX IF NOT EXISTS ix_teams_game_role
  ON teams(game_id, discord_role_id);
"""
