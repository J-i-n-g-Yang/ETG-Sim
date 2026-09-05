/**
 * api.js — thin fetch() wrapper around /api/*
 * Derives the app base path from this module's own URL so it works
 * correctly under any sub-path (e.g. /GOHub/townhall/).
 */

// Strip "/static/js/api.js" from this module's URL to get the app root path.
const BASE = new URL(import.meta.url).pathname.replace(/\/static\/js\/api\.js$/, "");

async function _req(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const r = await fetch(BASE + path, opts);
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: r.statusText }));
    throw Object.assign(new Error(err.error || r.statusText), { status: r.status, data: err });
  }
  return r.json();
}

const api = {
  join:         (display_name, event_code) => _req("POST", "/api/join", { display_name, event_code }),
  state:        ()                         => _req("GET",  "/api/state"),
  player:       (user_id)                  => _req("GET",  `/api/player/${encodeURIComponent(user_id)}`),
  bet:          (body)                     => _req("POST", "/api/bet",  body),
  distribution: (round_id)                 => _req("GET",  `/api/distribution?round_id=${round_id}`),
  history:      (game, limit = 20)         => _req("GET",  `/api/history?game=${game}&limit=${limit}`),
  leaderboard:  (top = 10)                 => _req("GET",  `/api/leaderboard?top=${top}`),

  // Solo mode — stateless, no user_id/round_id, no shared credits
  solo: {
    spin: (game, bets) => _req("POST", "/api/solo/spin", { game, bets }),
  },

  // Control (operator)
  ctrl: {
    _h: (pin) => ({ "X-Control-Pin": pin }),
    open:        (pin)          => _req("POST", "/api/control/open",         { pin }),
    lock:        (pin)          => _req("POST", "/api/control/lock",         { pin }),
    reveal:      (pin)          => _req("POST", "/api/control/reveal",       { pin }),
    next:        (pin)          => _req("POST", "/api/control/next_round",   { pin }),
    extend:      (pin, seconds) => _req("POST", "/api/control/extend",       { pin, seconds }),
    void:        (pin)          => _req("POST", "/api/control/void",         { pin, confirm: true }),
    // Backend requires confirm=true in the body or it 400s with
    // "Send confirm=true to reset" — that mismatch is why Reset always failed.
    reset:       (pin)          => _req("POST", "/api/control/reset",        { pin, confirm: true }),
    status:      (pin)          => _req("GET",  `/api/control/status?pin=${encodeURIComponent(pin)}`),
    setGame:     (pin, game)    => _req("POST", "/api/control/set_game",     { pin, game }),
    randomEvent: (pin)          => _req("POST", "/api/control/random_event", { pin }),
    autoStart:   (pin, enabled) => _req("POST", "/api/control/auto_start",   { pin, enabled }),
  },
};

export default api;
