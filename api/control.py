"""
Operator control panel endpoints — all PIN-gated.

PIN is passed in the X-Control-Pin header or as pin in JSON body.
"""

from flask import Blueprint, request, jsonify, current_app
from api.routes import get_session, sse_hub
import db.queries as queries

control_bp = Blueprint("control", __name__)


def _check_pin() -> bool:
    pin = (request.headers.get("X-Control-Pin")
           or request.args.get("pin", "")
           or (request.get_json(silent=True) or {}).get("pin", ""))
    return str(pin) == str(current_app.config["CONTROL_PIN"])


def _pin_error():
    return jsonify({"error": "Unauthorized — wrong PIN"}), 403


# --------------------------------------------------------------- #
# Phase transitions                                                #
# --------------------------------------------------------------- #

@control_bp.route("/open", methods=["POST"])
def open_betting():
    if not _check_pin():
        return _pin_error()
    result = get_session().open_betting()
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/lock", methods=["POST"])
def lock():
    if not _check_pin():
        return _pin_error()
    result = get_session().lock()
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/reveal", methods=["POST"])
def reveal():
    if not _check_pin():
        return _pin_error()
    result = get_session().reveal()
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/next_round", methods=["POST"])
def next_round():
    """Alias: open_betting already advances the round counter."""
    if not _check_pin():
        return _pin_error()
    result = get_session().open_betting()
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/next_game", methods=["POST"])
def next_game():
    if not _check_pin():
        return _pin_error()
    result = get_session().next_game()
    return jsonify(result)


@control_bp.route("/set_game", methods=["POST"])
def set_game():
    if not _check_pin():
        return _pin_error()
    data = request.get_json(silent=True) or {}
    game = str(data.get("game", "")).lower()
    if game not in ("baccarat", "sicbo", "roulette"):
        return jsonify({"error": "game must be one of: baccarat, sicbo, roulette"}), 400
    result = get_session().set_game(game)
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/random_event", methods=["POST"])
def random_event():
    if not _check_pin():
        return _pin_error()
    result = get_session().random_event()
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/auto_start", methods=["POST"])
def auto_start():
    if not _check_pin():
        return _pin_error()
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled", False))
    result = get_session().set_auto_start(enabled)
    return jsonify(result)


@control_bp.route("/extend", methods=["POST"])
def extend_timer():
    if not _check_pin():
        return _pin_error()
    data = request.get_json(silent=True) or {}
    extra = int(data.get("seconds", 10))
    extra = max(1, min(extra, 120))
    result = get_session().extend_timer(extra)
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/void", methods=["POST"])
def void_round():
    if not _check_pin():
        return _pin_error()
    result = get_session().void_round()
    return (jsonify(result), 200) if result["ok"] else (jsonify(result), 409)


@control_bp.route("/reset", methods=["POST"])
def reset():
    if not _check_pin():
        return _pin_error()
    data = request.get_json(silent=True) or {}
    if not data.get("confirm"):
        return jsonify({"error": "Send confirm=true to reset"}), 400
    queries.reset_event(float(current_app.config["STARTING_CREDITS"]))
    # Force session to reload from DB on next request
    import api.routes as ar
    ar._session = None
    state = get_session().get_state()
    # Dedicated signal (separate from phase_change) so every connected player
    # terminal knows to drop its cached balance and re-fetch the real one —
    # phase_change alone doesn't tell clients their credits changed underneath
    # them, which is why the header balance used to go stale after a reset.
    sse_hub.broadcast("event_reset", {"starting_credits": float(current_app.config["STARTING_CREDITS"])})
    sse_hub.broadcast("phase_change", state)
    sse_hub.broadcast("leaderboard_update", {})
    return jsonify({"ok": True, "message": "Event reset — all credits restored"})


# --------------------------------------------------------------- #
# Status                                                            #
# --------------------------------------------------------------- #

@control_bp.route("/status")
def status():
    if not _check_pin():
        return _pin_error()
    session_state = get_session().get_state()
    round_id = session_state.get("round_id")
    bet_stats = queries.round_bet_count(round_id) if round_id else {"bet_count": 0, "total_wagered": 0}
    return jsonify({
        "state":       session_state,
        "players":     queries.player_count(),
        "sse_clients": sse_hub.subscriber_count,
        **bet_stats,
    })
