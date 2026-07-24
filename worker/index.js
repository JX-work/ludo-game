// 三眼仔飞行棋 Worker: D1-backed API + static assets fallback
// Routes: /api/rooms, /api/rooms/:id, /api/rooms/:id/{join,actions,poll},
//         /api/rooms/:id/players/:pid

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith('/api/')) {
      return env.ASSETS.fetch(request);
    }
    try {
      return await route(request, env, url);
    } catch (e) {
      return json({ error: e.message, stack: e.stack }, 500);
    }
  }
};

async function route(request, env, url) {
  const p = url.pathname;
  const m = request.method;

  if (p === '/api/rooms' && m === 'GET')  return listRooms(env);
  if (p === '/api/rooms' && m === 'POST') return createRoom(env, await request.json());

  const rm = p.match(/^\/api\/rooms\/([^/]+)(\/.*)?$/);
  if (!rm) return json({ error: 'not_found' }, 404);
  const rid  = rm[1];
  const rest = rm[2] || '';

  if (rest === '' && m === 'GET')    return getRoom(env, rid);
  if (rest === '' && m === 'PATCH')  return updateRoom(env, rid, await request.json());
  if (rest === '' && m === 'DELETE') return deleteRoom(env, rid);
  if (rest === '/join'    && m === 'POST') return joinRoom(env, rid, await request.json());
  if (rest === '/actions' && m === 'POST') return postAction(env, rid, await request.json());
  if (rest === '/poll'    && m === 'GET')  return pollRoom(env, rid, url.searchParams);

  const pm = rest.match(/^\/players\/([^/]+)$/);
  if (pm && m === 'DELETE') return leaveRoom(env, rid, pm[1]);

  return json({ error: 'not_found' }, 404);
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8' }
  });
}

const parseGs = (s) => (s ? JSON.parse(s) : null);
const dumpGs  = (g) => (g == null ? null : JSON.stringify(g));

async function listRooms(env) {
  const { results } = await env.DB.prepare(
    `SELECT r.id, r.name, r.host_id, r.status, r.max_players, r.current_player,
            r.created_at, r.updated_at,
            (SELECT COUNT(*) FROM ludo_players WHERE room_id = r.id) AS player_count
       FROM ludo_rooms r
      WHERE r.status = 'waiting'
      ORDER BY r.created_at DESC
      LIMIT 20`
  ).all();
  return json(results);
}

async function createRoom(env, body) {
  const { id, name, host_id, max_players } = body || {};
  if (!id || !name || !host_id) return json({ error: 'missing_fields' }, 400);
  await env.DB.prepare(
    `INSERT INTO ludo_rooms (id, name, host_id, max_players)
     VALUES (?, ?, ?, ?)`
  ).bind(id, name, host_id, Number(max_players) || 4).run();
  return json({ id });
}

async function getRoom(env, rid) {
  const room = await env.DB.prepare('SELECT * FROM ludo_rooms WHERE id = ?').bind(rid).first();
  if (!room) return json({ error: 'not_found' }, 404);
  const { results: players } = await env.DB.prepare(
    'SELECT * FROM ludo_players WHERE room_id = ? ORDER BY player_idx'
  ).bind(rid).all();
  return json({
    ...room,
    game_state: parseGs(room.game_state),
    ludo_players: players
  });
}

async function updateRoom(env, rid, body) {
  const sets = [];
  const vals = [];
  if (body.status !== undefined)         { sets.push('status = ?');         vals.push(body.status); }
  if (body.game_state !== undefined)     { sets.push('game_state = ?');     vals.push(dumpGs(body.game_state)); }
  if (body.current_player !== undefined) { sets.push('current_player = ?'); vals.push(Number(body.current_player)); }
  if (!sets.length) return json({ ok: true });
  sets.push('updated_at = unixepoch()');
  vals.push(rid);
  await env.DB.prepare(`UPDATE ludo_rooms SET ${sets.join(', ')} WHERE id = ?`).bind(...vals).run();
  return json({ ok: true });
}

async function deleteRoom(env, rid) {
  // ON DELETE CASCADE on players; actions has no FK so wipe explicitly
  await env.DB.prepare('DELETE FROM ludo_actions WHERE room_id = ?').bind(rid).run();
  await env.DB.prepare('DELETE FROM ludo_rooms   WHERE id = ?').bind(rid).run();
  return json({ ok: true });
}

async function joinRoom(env, rid, body) {
  const { id, nickname, avatar_id, color_idx, player_idx, is_ready } = body || {};
  if (!id || !nickname || !avatar_id) return json({ error: 'missing_fields' }, 400);
  // Upsert: ludo_players.id is a global PRIMARY KEY, so a player joining a
  // NEW room while an old (id, other_room) row still exists (e.g. host left
  // without cleanup) would collide → SQLITE_CONSTRAINT_PRIMARYKEY → 500.
  // ON CONFLICT(id) DO UPDATE moves the row to the new room in one shot,
  // covering both cases: same-room reconnect and cross-room re-join.
  await env.DB.prepare(
    `INSERT INTO ludo_players (id, room_id, nickname, avatar_id, color_idx, player_idx, is_ready)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       room_id    = excluded.room_id,
       nickname   = excluded.nickname,
       avatar_id  = excluded.avatar_id,
       color_idx  = excluded.color_idx,
       player_idx = excluded.player_idx,
       is_ready   = excluded.is_ready`
  ).bind(id, rid, nickname, avatar_id, Number(color_idx), Number(player_idx), is_ready ? 1 : 0).run();
  return json({ ok: true });
}

async function leaveRoom(env, rid, pid) {
  await env.DB.prepare('DELETE FROM ludo_players WHERE id = ? AND room_id = ?').bind(pid, rid).run();
  return json({ ok: true });
}

async function postAction(env, rid, body) {
  const { player_id, action_type, dice_val, piece_idx, game_state } = body || {};
  if (!player_id || !action_type) return json({ error: 'missing_fields' }, 400);
  const gsStr = dumpGs(game_state);
  const res = await env.DB.prepare(
    `INSERT INTO ludo_actions (room_id, player_id, action_type, dice_val, piece_idx, game_state)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(
    rid, player_id, action_type,
    dice_val  == null ? null : Number(dice_val),
    piece_idx == null ? null : Number(piece_idx),
    gsStr
  ).run();
  // Mirror latest game_state onto room row so reconnects/pollers see snapshot without scanning actions
  if (gsStr != null) {
    await env.DB.prepare(
      'UPDATE ludo_rooms SET game_state = ?, updated_at = unixepoch() WHERE id = ?'
    ).bind(gsStr, rid).run();
  }
  return json({ action_id: res.meta?.last_row_id ?? null });
}

async function pollRoom(env, rid, params) {
  const since = Number(params.get('since') || 0);
  const room = await env.DB.prepare('SELECT * FROM ludo_rooms WHERE id = ?').bind(rid).first();
  if (!room) return json({ error: 'not_found' }, 404);
  const { results: players } = await env.DB.prepare(
    'SELECT * FROM ludo_players WHERE room_id = ? ORDER BY player_idx'
  ).bind(rid).all();
  const { results: acts } = await env.DB.prepare(
    'SELECT * FROM ludo_actions WHERE room_id = ? AND id > ? ORDER BY id ASC LIMIT 40'
  ).bind(rid, since).all();
  return json({
    room:    { ...room, game_state: parseGs(room.game_state) },
    players,
    actions: acts.map(a => ({ ...a, game_state: parseGs(a.game_state) }))
  });
}
