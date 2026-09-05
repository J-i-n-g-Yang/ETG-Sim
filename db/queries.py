"""
Database queries for the ETG Simulator.

This version uses SQLite instead of SQL Server.
"""

import json
from datetime import datetime

import db.pool as pool


def _row_to_dict(cursor, row) -> dict:
    if row is None:
        return None

    return {
        key: row[key]
        for key in row.keys()
    }


# --------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------- #

def run_migrations():
    """
    Create the SQLite database and all required tables.

    Safe to run every time the application starts.
    """

    conn = pool.get_conn()

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS townhall_players (
            user_id       TEXT NOT NULL PRIMARY KEY,
            display_name  TEXT NOT NULL UNIQUE,
            credits       REAL NOT NULL DEFAULT 1000,
            created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS townhall_rounds (
            round_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            game            TEXT NOT NULL,
            game_index      INTEGER NOT NULL,
            round_number    INTEGER NOT NULL,
            phase            TEXT NOT NULL,
            betting_ends_at TIMESTAMP NULL,
            outcome_json    TEXT NULL,
            event_multiplier REAL NOT NULL DEFAULT 1,
            lightning_json  TEXT NULL,
            settled_at      TIMESTAMP NULL,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS townhall_bets (
            bet_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id       INTEGER NOT NULL,
            user_id        TEXT NOT NULL,
            game           TEXT NOT NULL,
            wager_type     TEXT NOT NULL,
            amount         REAL NOT NULL,
            payout         REAL NULL,
            balance_after  REAL NULL,
            bet_uid        TEXT NULL,
            ts             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS IX_bets_round
            ON townhall_bets(round_id);

        CREATE INDEX IF NOT EXISTS IX_bets_user
            ON townhall_bets(user_id);

        CREATE UNIQUE INDEX IF NOT EXISTS UX_bets_uid
            ON townhall_bets(bet_uid)
            WHERE bet_uid IS NOT NULL;
        """
    )

    conn.commit()


# --------------------------------------------------------------- #
# Players
# --------------------------------------------------------------- #

def get_player(user_id: str) -> dict | None:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT user_id, display_name, credits
        FROM townhall_players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    return dict(row) if row else None


def get_player_by_name(display_name: str) -> dict | None:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT user_id, display_name, credits
        FROM townhall_players
        WHERE display_name = ?
        """,
        (display_name,)
    )

    row = cur.fetchone()

    return dict(row) if row else None


def insert_player(
    user_id: str,
    display_name: str,
    starting_credits: float
) -> dict:

    conn = pool.get_conn()

    conn.execute(
        """
        INSERT INTO townhall_players
            (user_id, display_name, credits)
        VALUES (?, ?, ?)
        """,
        (user_id, display_name, starting_credits)
    )

    conn.commit()

    return {
        "user_id": user_id,
        "display_name": display_name,
        "credits": starting_credits
    }


def debit_player(user_id: str, amount: float) -> bool:
    """
    Atomic guarded debit.

    Returns True only when the player has enough credits.
    """

    conn = pool.get_conn()

    cur = conn.execute(
        """
        UPDATE townhall_players
        SET credits = credits - ?
        WHERE user_id = ?
          AND credits >= ?
        """,
        (amount, user_id, amount)
    )

    conn.commit()

    return cur.rowcount == 1


def get_player_credits(user_id: str) -> float | None:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT credits
        FROM townhall_players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    return float(row[0]) if row else None


def leaderboard(top: int = 10) -> list[dict]:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT display_name, credits
        FROM townhall_players
        ORDER BY credits DESC, created_at ASC
        LIMIT ?
        """,
        (top,)
    )

    rows = cur.fetchall()

    return [
        {
            "display_name": row["display_name"],
            "credits": float(row["credits"])
        }
        for row in rows
    ]


def player_count() -> int:
    conn = pool.get_conn()

    cur = conn.execute(
        "SELECT COUNT(*) FROM townhall_players"
    )

    return cur.fetchone()[0]


# --------------------------------------------------------------- #
# Rounds
# --------------------------------------------------------------- #

def create_round(
    game: str,
    game_index: int,
    round_number: int,
    betting_ends_at: datetime
) -> int:

    conn = pool.get_conn()

    cur = conn.execute(
        """
        INSERT INTO townhall_rounds
            (
                game,
                game_index,
                round_number,
                phase,
                betting_ends_at
            )
        VALUES (?, ?, ?, 'BETTING_OPEN', ?)
        """,
        (
            game,
            game_index,
            round_number,
            betting_ends_at
        )
    )

    conn.commit()

    return cur.lastrowid


def get_round(round_id: int) -> dict | None:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT
            round_id,
            game,
            game_index,
            round_number,
            phase,
            betting_ends_at,
            outcome_json,
            event_multiplier,
            lightning_json
        FROM townhall_rounds
        WHERE round_id = ?
        """,
        (round_id,)
    )

    row = cur.fetchone()

    return dict(row) if row else None


def get_latest_active_round() -> dict | None:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT
            round_id,
            game,
            game_index,
            round_number,
            phase,
            betting_ends_at,
            outcome_json,
            event_multiplier,
            lightning_json
        FROM townhall_rounds
        WHERE phase NOT IN (
            'SETTLED',
            'VOIDED',
            'GAME_OVER'
        )
        ORDER BY round_id DESC
        LIMIT 1
        """
    )

    row = cur.fetchone()

    return dict(row) if row else None


def update_round_phase(round_id: int, phase: str):
    conn = pool.get_conn()

    conn.execute(
        """
        UPDATE townhall_rounds
        SET phase = ?
        WHERE round_id = ?
        """,
        (phase, round_id)
    )

    conn.commit()


def update_round_betting_end(
    round_id: int,
    ends_at: datetime
):
    conn = pool.get_conn()

    conn.execute(
        """
        UPDATE townhall_rounds
        SET betting_ends_at = ?
        WHERE round_id = ?
        """,
        (ends_at, round_id)
    )

    conn.commit()


def update_round_multiplier(
    round_id: int,
    multiplier: float
):
    conn = pool.get_conn()

    conn.execute(
        """
        UPDATE townhall_rounds
        SET event_multiplier = ?
        WHERE round_id = ?
        """,
        (multiplier, round_id)
    )

    conn.commit()


def update_round_lightning(
    round_id: int,
    lightning_json: str
):
    conn = pool.get_conn()

    conn.execute(
        """
        UPDATE townhall_rounds
        SET lightning_json = ?
        WHERE round_id = ?
        """,
        (lightning_json, round_id)
    )

    conn.commit()


# --------------------------------------------------------------- #
# Bets
# --------------------------------------------------------------- #

def insert_bet(
    round_id: int,
    user_id: str,
    game: str,
    wager_type: str,
    amount: float,
    bet_uid: str | None = None
):
    conn = pool.get_conn()

    conn.execute(
        """
        INSERT INTO townhall_bets
            (
                round_id,
                user_id,
                game,
                wager_type,
                amount,
                bet_uid
            )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            round_id,
            user_id,
            game,
            wager_type,
            amount,
            bet_uid
        )
    )

    conn.commit()


def bet_uid_exists(bet_uid: str) -> bool:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT 1
        FROM townhall_bets
        WHERE bet_uid = ?
        """,
        (bet_uid,)
    )

    return cur.fetchone() is not None


def get_player_round_total(
    user_id: str,
    round_id: int
) -> float:

    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM townhall_bets
        WHERE round_id = ?
          AND user_id = ?
        """,
        (round_id, user_id)
    )

    return float(cur.fetchone()[0])


def get_player_round_bets(
    user_id: str,
    round_id: int
) -> list:

    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT wager_type, amount, payout
        FROM townhall_bets
        WHERE round_id = ?
          AND user_id = ?
        ORDER BY bet_id
        """,
        (round_id, user_id)
    )

    rows = cur.fetchall()

    return [
        {
            "wager_type": row["wager_type"],
            "amount": float(row["amount"]),
            "payout": (
                float(row["payout"])
                if row["payout"] is not None
                else None
            )
        }
        for row in rows
    ]


def distribution(round_id: int) -> dict:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT
            wager_type,
            SUM(amount) AS total,
            COUNT(*) AS cnt
        FROM townhall_bets
        WHERE round_id = ?
        GROUP BY wager_type
        """,
        (round_id,)
    )

    rows = cur.fetchall()

    totals = {
        row["wager_type"]: float(row["total"])
        for row in rows
    }

    bet_count = sum(
        row["cnt"]
        for row in rows
    )

    return {
        "round_id": round_id,
        "totals": totals,
        "bet_count": bet_count
    }


def history(
    game: str,
    limit: int = 20
) -> list[dict]:

    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT round_number, outcome_json
        FROM townhall_rounds
        WHERE game = ?
          AND phase = 'SETTLED'
          AND outcome_json IS NOT NULL
        ORDER BY round_id DESC
        LIMIT ?
        """,
        (game, limit)
    )

    rows = cur.fetchall()

    return [
        {
            "round_number": row["round_number"],
            "outcome": json.loads(row["outcome_json"])
        }
        for row in rows
    ]


def round_bet_count(round_id: int) -> dict:
    conn = pool.get_conn()

    cur = conn.execute(
        """
        SELECT
            COUNT(*) AS cnt,
            COALESCE(SUM(amount), 0) AS total
        FROM townhall_bets
        WHERE round_id = ?
        """,
        (round_id,)
    )

    row = cur.fetchone()

    return {
        "bet_count": row["cnt"],
        "total_wagered": float(row["total"])
    }


def reset_event(starting_credits: float):
    conn = pool.get_conn()

    try:
        conn.execute("BEGIN")

        conn.execute(
            "DELETE FROM townhall_bets"
        )

        conn.execute(
            "DELETE FROM townhall_rounds"
        )

        conn.execute(
            """
            UPDATE townhall_players
            SET credits = ?
            """,
            (starting_credits,)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise