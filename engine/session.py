"""
GameSession — the single server-side state machine.

One global instance is created in api/routes.py and shared across all threads.
All mutating methods hold self._lock for thread safety.
"""

import threading
import queue
import json
from datetime import datetime, timezone, timedelta
import db.queries as queries
import game.roulette as roulette

GAMES = ["baccarat", "sicbo", "roulette"]


class SSEHub:
    """Thread-safe broadcast hub for Server-Sent Events."""

    def __init__(self):
        self._lock = threading.Lock()
        self._queues: list[queue.Queue] = []

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=64)
        with self._lock:
            self._queues.append(q)
        return q

    def unsubscribe(self, q: queue.Queue):
        with self._lock:
            try:
                self._queues.remove(q)
            except ValueError:
                pass

    def broadcast(self, event: str, data: dict):
        msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        with self._lock:
            dead = []
            for q in self._queues:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self._queues.remove(q)

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._queues)


class GameSession:
    """
    Persisted state machine.  DB is the source of truth; in-memory is a cache.
    On startup, loads the latest non-closed round from DB to recover mid-event.
    """

    def __init__(self, config, hub: SSEHub):
        self._cfg = config
        self._hub = hub
        self._lock = threading.Lock()
        self._state: dict = {}
        self._auto_start_enabled = False
        self._reload()

    # --------------------------------------------------------------- #
    # Public read                                                       #
    # --------------------------------------------------------------- #

    def get_state(self) -> dict:
        with self._lock:
            self._auto_lock()
            return self._safe_state()

    # --------------------------------------------------------------- #
    # Phase transitions (operator-driven via control panel)             #
    # --------------------------------------------------------------- #

    def open_betting(self) -> dict:
        with self._lock:
            return self._open_betting_locked()

    def set_auto_start(self, enabled: bool) -> dict:
        with self._lock:
            self._auto_start_enabled = bool(enabled)
            self._hub.broadcast("phase_change", self._safe_state())
            return {"ok": True, "auto_start": self._auto_start_enabled}

    def lock(self) -> dict:
        with self._lock:
            if self._state.get("phase") != "BETTING_OPEN":
                return {"ok": False, "error": "Not in BETTING_OPEN"}
            self._set_phase("BETTING_LOCKED")

            if self._state.get("game") == "roulette":
                lightning = roulette.draw_lightning()
                self._state["lightning"] = lightning
                queries.update_round_lightning(self._state["round_id"], json.dumps(lightning))

            self._hub.broadcast("phase_change", self._safe_state())

            if self._state.get("game") == "roulette" and self._state.get("lightning"):
                self._hub.broadcast("lightning", {
                    "round_id": self._state["round_id"],
                    "lightning": self._state["lightning"],
                })

            round_id = self._state["round_id"]
            game     = self._state["game"]
        threading.Thread(target=self._bg_settle, args=(round_id, game), daemon=True).start()
        return {"ok": True}

    def _bg_settle(self, round_id: int, game: str):
        """Settle a round in a background thread — called immediately after lock."""
        import time as _time
        _time.sleep(1.0)  # 1-second grace period: lets the operator set a random_event multiplier
                           # before settlement reads it from the DB and applies it to payouts.
        from engine.settlement import settle_round
        result = settle_round(round_id, game, self._cfg)
        with self._lock:
            if result["ok"] and self._state.get("round_id") == round_id:
                self._state["phase"]   = "SETTLED"
                self._state["outcome"] = result["outcome"]
                self._hub.broadcast("reveal",             {"outcome": result["outcome"]})
                self._hub.broadcast("settled",             self._safe_state())
                self._hub.broadcast("leaderboard_update", {})
                auto_start_now = self._auto_start_enabled
            else:
                auto_start_now = False

        if auto_start_now:
            threading.Thread(target=self._auto_start_next_round, args=(round_id,), daemon=True).start()

    def reveal(self) -> dict:
        """
        Operator-triggered immediate reveal — settles the round now instead of
        waiting for the 1-second auto-settle grace period started by lock().

        settle_round() is exactly-once (guarded by an atomic phase transition in
        the DB), so it's safe even if the background _bg_settle thread from
        lock() fires around the same time — whichever gets there first wins,
        the other just gets back already_settled=True with the same outcome.
        """
        with self._lock:
            if self._state.get("phase") not in ("BETTING_LOCKED", "REVEALING"):
                return {"ok": False, "error": "Not in BETTING_LOCKED"}
            round_id = self._state["round_id"]
            game     = self._state["game"]

        from engine.settlement import settle_round
        result = settle_round(round_id, game, self._cfg)

        auto_start_now = False
        with self._lock:
            if result["ok"] and self._state.get("round_id") == round_id:
                self._state["phase"]   = "SETTLED"
                self._state["outcome"] = result["outcome"]
                self._hub.broadcast("reveal",             {"outcome": result["outcome"]})
                self._hub.broadcast("settled",             self._safe_state())
                self._hub.broadcast("leaderboard_update", {})
                auto_start_now = self._auto_start_enabled

        if auto_start_now:
            threading.Thread(target=self._auto_start_next_round, args=(round_id,), daemon=True).start()

        return {"ok": True} if result["ok"] else result

    def extend_timer(self, extra_seconds: int) -> dict:
        with self._lock:
            if self._state.get("phase") != "BETTING_OPEN":
                return {"ok": False, "error": "Not in BETTING_OPEN"}
            new_end = self._state["betting_ends_at"] + timedelta(seconds=extra_seconds)
            self._state["betting_ends_at"] = new_end
            queries.update_round_betting_end(self._state["round_id"], new_end)
            self._hub.broadcast("phase_change", self._safe_state())
            return {"ok": True}

    def void_round(self) -> dict:
        with self._lock:
            phase = self._state.get("phase")
            if phase not in ("BETTING_OPEN", "BETTING_LOCKED", "REVEALING", "SETTLED"):
                return {"ok": False, "error": f"Cannot void from phase {phase}"}

        from engine.settlement import void_round as do_void
        result = do_void(self._state["round_id"])

        with self._lock:
            if result["ok"]:
                self._state["phase"] = "IDLE"
                self._hub.broadcast("phase_change", self._safe_state())
            return result

    def next_game(self) -> dict:
        with self._lock:
            if self._state.get("phase") not in ("SETTLED", "IDLE"):
                return {"ok": False, "error": "Can only advance game after SETTLED/IDLE"}
            game_index = (self._state.get("game_index", 0) + 1) % len(GAMES)
            game = GAMES[game_index]
            self._state["game"]              = game
            self._state["game_index"]        = game_index
            self._state["round_number"]      = 0
            self._state["event_multiplier"]  = 1.0
            self._state["lightning"]         = None
            self._hub.broadcast("phase_change", self._safe_state())
            return {"ok": True, "game": game}

    def set_game(self, game: str) -> dict:
        with self._lock:
            phase = self._state.get("phase", "IDLE")
            if phase not in ("IDLE", "SETTLED", "GAME_OVER"):
                return {"ok": False, "error": f"Cannot set game from phase {phase}"}
            if game not in GAMES:
                return {"ok": False, "error": f"Unknown game '{game}'"}
            game_index = GAMES.index(game)
            self._state["game"]              = game
            self._state["game_index"]        = game_index
            self._state["round_number"]      = 0
            self._state["event_multiplier"]  = 1.0
            self._state["lightning"]         = None
            if phase == "GAME_OVER":
                self._state["phase"] = "IDLE"
            self._hub.broadcast("phase_change", self._safe_state())
            return {"ok": True, "game": game}

    def random_event(self) -> dict:
        import random as _random
        with self._lock:
            phase = self._state.get("phase")
            if phase not in ("BETTING_OPEN", "BETTING_LOCKED"):
                return {"ok": False, "error": "No active betting round"}
            multiplier = _random.choice([0.5, 2.0, 3.0])
            round_id   = self._state["round_id"]
            self._state["event_multiplier"] = multiplier
        # DB write and SSE broadcast outside the lock
        queries.update_round_multiplier(round_id, multiplier)
        self._hub.broadcast("random_event", {"multiplier": multiplier, "round_id": round_id})
        return {"ok": True, "multiplier": multiplier, "round_id": round_id}

    # --------------------------------------------------------------- #
    # Internal helpers                                                   #
    # --------------------------------------------------------------- #

    def _auto_lock(self):
        """Called inside lock; flips BETTING_OPEN→LOCKED if timer expired."""
        if self._state.get("phase") != "BETTING_OPEN":
            return
        ends = self._state.get("betting_ends_at")
        if ends is None:
            return
        if isinstance(ends, str):
            ends = datetime.fromisoformat(ends.replace("Z", "+00:00"))
        if isinstance(ends, datetime) and ends.tzinfo is None:
            ends = ends.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) >= ends:
            self._set_phase("BETTING_LOCKED")

            if self._state.get("game") == "roulette":
                lightning = roulette.draw_lightning()
                self._state["lightning"] = lightning
                queries.update_round_lightning(self._state["round_id"], json.dumps(lightning))

            self._hub.broadcast("phase_change", self._safe_state())

            if self._state.get("game") == "roulette" and self._state.get("lightning"):
                self._hub.broadcast("lightning", {
                    "round_id": self._state["round_id"],
                    "lightning": self._state["lightning"],
                })

            round_id = self._state["round_id"]
            game     = self._state["game"]
            threading.Thread(target=self._bg_settle, args=(round_id, game), daemon=True).start()

    def _set_phase(self, phase: str):
        self._state["phase"] = phase
        queries.update_round_phase(self._state["round_id"], phase)

    def _open_betting_locked(self) -> dict:
        phase = self._state.get("phase", "IDLE")
        if phase not in ("IDLE", "SETTLED"):
            return {"ok": False, "error": f"Cannot open from phase {phase}"}

        game_index    = self._state.get("game_index", 0)
        game          = self._state.get("game", GAMES[0])
        round_number  = self._state.get("round_number", 0) + 1

        ends_at = datetime.now(timezone.utc) + timedelta(seconds=self._cfg.BETTING_SECONDS)

        round_id = queries.create_round(game, game_index, round_number, ends_at)

        self._state.update({
            "round_id":         round_id,
            "game":             game,
            "game_index":       game_index,
            "round_number":     round_number,
            "phase":            "BETTING_OPEN",
            "betting_ends_at":  ends_at,
            "outcome":          None,
            "event_multiplier": 1.0,
            "lightning":        None,
        })

        self._hub.broadcast("phase_change", self._safe_state())
        return {"ok": True}

    def _auto_start_next_round(self, settled_round_id: int):
        import time as _time
        # Read settled-round context before sleeping so we can pick the right delay.
        with self._lock:
            if self._state.get("round_id") != settled_round_id:
                return
            game          = self._state.get("game", "baccarat")
            has_lightning = bool(self._state.get("lightning"))
            has_event     = float(self._state.get("event_multiplier", 1.0)) != 1.0

        # Per-game delays (seconds) calibrated to exceed the player terminal's REVEAL_DELAY
        # (game.html: baccarat=18s, roulette=10s, sicbo=8s) plus animation/popup finish buffer,
        # so the next round never opens before all results have been shown to players.
        _BASE = {"baccarat": 26, "roulette": 14, "sicbo": 13}
        delay  = float(_BASE.get(game, 15))
        if has_event:     delay += 12.0  # covers EVENT_EXTRA_MS (9.5s) + buffer
        if has_lightning: delay +=  9.0  # covers LIGHTNING_EXTRA_MS (7s) + buffer

        _time.sleep(delay)

        with self._lock:
            if not self._auto_start_enabled:
                return
            if self._state.get("phase") != "SETTLED":
                return
            if self._state.get("round_id") != settled_round_id:
                return
            self._open_betting_locked()

    def _safe_state(self) -> dict:
        """Return a copy of state safe to serialise; hides outcome until REVEALING+."""
        s = dict(self._state)
        phase = s.get("phase", "IDLE")
        if phase not in ("REVEALING", "SETTLED", "GAME_OVER"):
            s["outcome"] = None

        ends = s.get("betting_ends_at")
        if isinstance(ends, datetime):
            s["betting_ends_at"] = ends.strftime("%Y-%m-%dT%H:%M:%SZ")

        s.setdefault("event_multiplier", 1.0)
        s["auto_start"] = self._auto_start_enabled
        s["max_bet"] = self._cfg.MAX_BET
        s["server_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        from game.registry import wager_options
        s["wager_options"] = wager_options(s.get("game", "baccarat"))
        return s

    def _reload(self):
        """Load latest in-progress round from DB (for server restart recovery)."""
        row = queries.get_latest_active_round()
        if row:
            self._state = {
                "round_id":         row["round_id"],
                "game":             row["game"],
                "game_index":       row["game_index"],
                "round_number":     row["round_number"],
                "phase":            row["phase"],
                "betting_ends_at":  row["betting_ends_at"],
                "outcome":          None,
                "event_multiplier": float(row["event_multiplier"]) if row.get("event_multiplier") is not None else 1.0,
                "lightning":        json.loads(row["lightning_json"]) if row.get("lightning_json") else None,
            }
        else:
            self._state = {
                "round_id":         None,
                "game":             GAMES[0],
                "game_index":       0,
                "round_number":     0,
                "phase":            "IDLE",
                "betting_ends_at":  None,
                "outcome":          None,
                "event_multiplier": 1.0,
                "lightning":        None,
            }
