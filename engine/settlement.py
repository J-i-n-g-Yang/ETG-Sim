"""
Exactly-once settlement.
"""

import json
from decimal import Decimal

import db.queries as queries
import db.pool as pool
import game.registry as registry


def settle_round(round_id: int, game: str, config) -> dict:
    conn = pool.get_conn()

    try:
        conn.execute("BEGIN")

        # Phase guard
        cur = conn.execute(
            """
            UPDATE townhall_rounds
            SET phase = 'REVEALING'
            WHERE round_id = ?
              AND phase = 'BETTING_LOCKED'
            """,
            (round_id,)
        )

        if cur.rowcount == 0:
            conn.rollback()

            return {
                "ok": True,
                "already_settled": True,
                "outcome": _load_outcome(round_id)
            }

        # Event multiplier
        cur = conn.execute(
            """
            SELECT COALESCE(event_multiplier, 1.0)
            FROM townhall_rounds
            WHERE round_id = ?
            """,
            (round_id,)
        )

        mult_row = cur.fetchone()

        event_multiplier = (
            float(mult_row[0])
            if mult_row
            else 1.0
        )

        # Lightning event
        cur = conn.execute(
            """
            SELECT lightning_json
            FROM townhall_rounds
            WHERE round_id = ?
            """,
            (round_id,)
        )

        lightning_row = cur.fetchone()

        lightning = (
            json.loads(lightning_row[0])
            if lightning_row
            and lightning_row[0]
            else None
        )

        # Generate outcome exactly once
        mod = registry.get_module(game)

        outcome = mod.resolve()

        outcome_json = json.dumps(outcome)

        conn.execute(
            """
            UPDATE townhall_rounds
            SET
                outcome_json = ?,
                phase = 'SETTLED',
                settled_at = CURRENT_TIMESTAMP
            WHERE round_id = ?
            """,
            (outcome_json, round_id)
        )

        # Fetch bets
        cur = conn.execute(
            """
            SELECT
                bet_id,
                user_id,
                wager_type,
                amount
            FROM townhall_bets
            WHERE round_id = ?
            """,
            (round_id,)
        )

        bets = cur.fetchall()

        # Settle bets
        for row in bets:
            bet_id = row["bet_id"]
            user_id = row["user_id"]
            wager_type = row["wager_type"]
            amount = Decimal(str(row["amount"]))

            if game == "roulette":
                returned = mod.payout(
                    wager_type,
                    amount,
                    outcome,
                    lightning=lightning
                )
            else:
                returned = mod.payout(
                    wager_type,
                    amount,
                    outcome
                )

            # Apply event multiplier to net winnings only
            if returned > 0 and event_multiplier != 1.0:
                net_win = returned - amount

                returned = (
                    amount
                    + net_win * Decimal(
                        str(event_multiplier)
                    )
                )

            payout_val = returned - amount

            # Credit winners
            if returned > 0:
                conn.execute(
                    """
                    UPDATE townhall_players
                    SET credits = credits + ?
                    WHERE user_id = ?
                    """,
                    (float(returned), user_id)
                )

            # Record payout
            conn.execute(
                """
                UPDATE townhall_bets
                SET
                    payout = ?,
                    balance_after = (
                        SELECT credits
                        FROM townhall_players
                        WHERE user_id = ?
                    )
                WHERE bet_id = ?
                """,
                (
                    float(payout_val),
                    user_id,
                    bet_id
                )
            )

        conn.commit()

        return {
            "ok": True,
            "outcome": outcome
        }

    except Exception as exc:
        conn.rollback()

        return {
            "ok": False,
            "error": str(exc)
        }


def void_round(round_id: int) -> dict:
    """
    Refund all stakes for a round and mark it VOIDED.
    """

    conn = pool.get_conn()

    try:
        conn.execute("BEGIN")

        cur = conn.execute(
            """
            UPDATE townhall_rounds
            SET phase = 'VOIDED'
            WHERE round_id = ?
              AND phase NOT IN (
                  'VOIDED',
                  'GAME_OVER'
              )
            """,
            (round_id,)
        )

        if cur.rowcount == 0:
            conn.rollback()

            return {
                "ok": False,
                "error": "Round already voided or closed"
            }

        cur = conn.execute(
            """
            SELECT
                user_id,
                amount,
                payout
            FROM townhall_bets
            WHERE round_id = ?
            """,
            (round_id,)
        )

        for row in cur.fetchall():

            user_id = row["user_id"]
            amount = float(row["amount"])
            payout = row["payout"]

            # `payout` (when set) is the NET result already applied to the
            # player's balance at settlement time: (returned - amount), and
            # can be negative for a loss. It was credited on top of the
            # `amount` debit taken at bet time, so fully undoing a settled
            # bet just means reversing that net effect: adjustment = -payout.
            #
            # The old formula `amount - max(0.0, payout)` only reversed
            # losses correctly (payout <= 0) — for a WIN (payout > 0) it
            # computed 0, so voiding a round the player had won left them
            # holding the winnings instead of clawing them back.
            if payout is None:
                # Bet was never settled (round voided pre-reveal) — only the
                # original stake debit needs to be refunded.
                adjustment = amount
            else:
                adjustment = -float(payout)

            if adjustment != 0:
                conn.execute(
                    """
                    UPDATE townhall_players
                    SET credits = credits + ?
                    WHERE user_id = ?
                    """,
                    (adjustment, user_id)
                )

        conn.commit()

        return {"ok": True}

    except Exception as exc:
        conn.rollback()

        return {
            "ok": False,
            "error": str(exc)
        }


def _load_outcome(round_id: int):
    row = queries.get_round(round_id)

    if row and row.get("outcome_json"):
        return json.loads(row["outcome_json"])

    return None