-- 三眼仔飞行棋 D1 (SQLite) schema
-- 建表: wrangler d1 execute ludo-game --remote --file=schema.sql

CREATE TABLE IF NOT EXISTS ludo_rooms (
  id             TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  host_id        TEXT NOT NULL,
  status         TEXT NOT NULL DEFAULT 'waiting',
  max_players    INTEGER NOT NULL DEFAULT 4,
  current_player INTEGER NOT NULL DEFAULT 0,
  game_state     TEXT,
  created_at     INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at     INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE IF NOT EXISTS ludo_players (
  id         TEXT PRIMARY KEY,
  room_id    TEXT NOT NULL REFERENCES ludo_rooms(id) ON DELETE CASCADE,
  nickname   TEXT NOT NULL,
  avatar_id  TEXT NOT NULL,
  color_idx  INTEGER NOT NULL,
  player_idx INTEGER NOT NULL,
  is_ready   INTEGER NOT NULL DEFAULT 0,
  joined_at  INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE IF NOT EXISTS ludo_actions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id     TEXT NOT NULL,
  player_id   TEXT NOT NULL,
  action_type TEXT NOT NULL,
  dice_val    INTEGER,
  piece_idx   INTEGER,
  game_state  TEXT,
  created_at  INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_players_room   ON ludo_players(room_id);
CREATE INDEX IF NOT EXISTS idx_actions_room   ON ludo_actions(room_id, id);
CREATE INDEX IF NOT EXISTS idx_rooms_status   ON ludo_rooms(status, created_at DESC);
