-- 三眼仔飞行棋 数据库建表脚本
-- 在 Supabase SQL Editor 里粘贴并运行即可

CREATE TABLE IF NOT EXISTS ludo_rooms (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  host_id TEXT NOT NULL,
  status TEXT DEFAULT 'waiting',
  max_players INT DEFAULT 4,
  current_player INT DEFAULT 0,
  game_state JSONB DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ludo_players (
  id TEXT PRIMARY KEY,
  room_id TEXT REFERENCES ludo_rooms(id) ON DELETE CASCADE,
  nickname TEXT NOT NULL,
  avatar_id TEXT NOT NULL,
  color_idx INT NOT NULL,
  player_idx INT NOT NULL,
  is_ready BOOLEAN DEFAULT FALSE,
  joined_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ludo_actions (
  id BIGSERIAL PRIMARY KEY,
  room_id TEXT REFERENCES ludo_rooms(id) ON DELETE CASCADE,
  player_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  dice_val INT,
  piece_idx INT,
  game_state JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE ludo_rooms   REPLICA IDENTITY FULL;
ALTER TABLE ludo_players REPLICA IDENTITY FULL;
ALTER TABLE ludo_actions REPLICA IDENTITY FULL;

ALTER TABLE ludo_rooms   ENABLE ROW LEVEL SECURITY;
ALTER TABLE ludo_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE ludo_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all" ON ludo_rooms   FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON ludo_players FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON ludo_actions FOR ALL USING (true) WITH CHECK (true);

ALTER PUBLICATION supabase_realtime ADD TABLE ludo_rooms, ludo_players, ludo_actions;
