"""
Player-facing API routes.

All responses are JSON.  Phase changes broadcast via SSE.
"""

import uuid
import time
import threading
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response, current_app
import db.queries as queries
import game.registry as registry
from engine.session import GameSession, SSEHub

api_bp  = Blueprint("api", __name__)
sse_hub = SSEHub()

# Singleton session — created once, imported by app.py
_session: GameSession | None = None
_session_lock = threading.Lock()


def get_session() -> GameSession:
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                from config import Config
                _session = GameSession(Config(), sse_hub)
    return _session


# Per-user rate limiting: last-bet timestamp (in-memory, single process)
_last_bet_ts: dict[str, float] = {}
_BET_COOLDOWN = 0.3  # seconds

# --------------------------------------------------------------- #
# Join                                                              #
# --------------------------------------------------------------- #

@api_bp.route("/join", methods=["POST"])
def join():
    data = request.get_json(silent=True) or {}
    display_name = str(data.get("display_name", "")).strip()[:50]
    event_code   = str(data.get("event_code",   ""))

    if not display_name:
        return jsonify({"error": "display_name required"}), 400
    if event_code != current_app.config["EVENT_CODE"]:
        return jsonify({"error": "Invalid event code"}), 403

    existing = queries.get_player_by_name(display_name)
    if existing:
        # Allow rejoin — return existing player
        return jsonify({
            "user_id":     existing["user_id"],
            "display_name": existing["display_name"],
            "credits":     float(existing["credits"]),
        })

    user_id = str(uuid.uuid4())
    queries.insert_player(user_id, display_name, float(current_app.config["STARTING_CREDITS"]))
    return jsonify({"user_id": user_id, "display_name": display_name,
                     "credits": float(current_app.config["STARTING_CREDITS"])}), 201


# --------------------------------------------------------------- #
# Player lookup (used by client to verify session is still valid)  #
# --------------------------------------------------------------- #

@api_bp.route("/player/<user_id>")
def player_lookup(user_id):
    player = queries.get_player(str(user_id))
    if not player:
        return jsonify({"error": "Player not found"}), 404
    return jsonify({
        "user_id":     player["user_id"],
        "display_name": player["display_name"],
        "credits":     float(player["credits"]),
    })

# --------------------------------------------------------------- #
# State                                                             #
# --------------------------------------------------------------- #

@api_bp.route("/state")
def state():
    return jsonify(get_session().get_state())


# --------------------------------------------------------------- #
# Bet                                                               #
# --------------------------------------------------------------- #

@api_bp.route("/bet", methods=["POST"])
def bet():
    data = request.get_json(silent=True) or {}
    user_id     = str(data.get("user_id",     ""))
    round_id    = data.get("round_id")
    game        = str(data.get("game",        ""))
    wager_type  = str(data.get("wager_type",  ""))
    bet_uid     = data.get("bet_uid")

    # Parse amount
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    max_bet = float(current_app.config.get("MAX_BET", 20000))
    if amount <= 0 or amount > max_bet or amount != amount:  # NaN check
        return jsonify({"error": f"Amount must be 1–{max_bet}"}), 400

    # Validate user
    player = queries.get_player(user_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    # Validate game + wager
    if not registry.validate_wager(game, wager_type):
        return jsonify({"error": "Invalid game/wager_type"}), 400

    # Rate limit
    now = time.monotonic()
    last = _last_bet_ts.get(user_id, 0)
    if now - last < _BET_COOLDOWN:
        return jsonify({"error": "Too fast — wait a moment"}), 429
    _last_bet_ts[user_id] = now

    # Phase & round check
    session_state = get_session().get_state()
    if session_state["phase"] != "BETTING_OPEN":
        return jsonify({"error": "Betting is not open"}), 409
    if session_state["round_id"] != round_id:
        return jsonify({"error": "Stale round_id"}), 409

    # Idempotency
    if bet_uid:
        bet_uid = str(bet_uid)[:64]
        if queries.bet_uid_exists(bet_uid):
            balance = queries.get_player_credits(user_id)
            return jsonify({"accepted": True, "balance": float(balance), "round_id": round_id})

    # Per-round bet cap
    max_round = float(current_app.config.get("MAX_BET", 20000))
    already_bet = queries.get_player_round_total(user_id, round_id)
    if already_bet + amount > max_round:
        remaining = max(0.0, max_round - already_bet)
        return jsonify({"error": f"Round limit {int(max_round)} cr — {int(remaining)} cr remaining this round"}), 400

    # Atomic debit
    if not queries.debit_player(user_id, amount):
        return jsonify({"error": "Insufficient credits"}), 400

    queries.insert_bet(round_id, user_id, game, wager_type, amount, bet_uid or None)

    balance = queries.get_player_credits(user_id)
    sse_hub.broadcast("distribution_update", queries.distribution(round_id))
    return jsonify({"accepted": True, "balance": float(balance), "round_id": round_id})


# --------------------------------------------------------------- #
# Player round bets                                                #
# --------------------------------------------------------------- #

@api_bp.route("/player/<user_id>/bets/<int:round_id>")
def player_round_bets(user_id, round_id):
    bets = queries.get_player_round_bets(str(user_id), round_id)
    return jsonify({"bets": bets, "round_id": round_id})


# --------------------------------------------------------------- #
# Distribution                                                     #
# --------------------------------------------------------------- #

@api_bp.route("/distribution")
def distribution():
    round_id = request.args.get("round_id", type=int)
    if round_id is None:
        s = get_session().get_state()
        round_id = s.get("round_id")
    if round_id is None:
        return jsonify({"round_id": None, "totals": {}, "bet_count": 0})
    return jsonify(queries.distribution(round_id))


# --------------------------------------------------------------- #
# History                                                           #
# --------------------------------------------------------------- #

@api_bp.route("/history")
def history():
    game  = request.args.get("game", "baccarat")
    limit = min(int(request.args.get("limit", 20)), 50)
    return jsonify({"game": game, "results": queries.history(game, limit)})


# --------------------------------------------------------------- #
# Leaderboard                                                      #
# --------------------------------------------------------------- #

@api_bp.route("/leaderboard")
def leaderboard():
    top = min(int(request.args.get("top", 10)), 50)
    return jsonify({
        "players":     queries.leaderboard(top),
        "server_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })


# --------------------------------------------------------------- #
# SSE event stream                                                 #
# --------------------------------------------------------------- #

@api_bp.route("/events")
def events():
    import json

    def generate():
        q = sse_hub.subscribe()
        try:
            # Send current state immediately
            state = get_session().get_state()
            yield f"event: state\ndata: {json.dumps(state)}\n\n"

            while True:
                try:
                    msg = q.get(timeout=5)  # short timeout so dead clients free threads quickly
                    yield msg
                except Exception:
                    # heartbeat keepalive
                    yield ": ping\n\n"
        finally:
            sse_hub.unsubscribe(q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
