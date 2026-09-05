"""
SQLite database connection helper.

Each thread gets its own SQLite connection.
The database file is local to the Simulator.
"""

import os
import sqlite3
import threading

from config import Config


_cfg = Config()
_local = threading.local()


def _make_conn():
    # Make sure the database directory exists
    db_dir = os.path.dirname(_cfg.DB_PATH)

    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(
        _cfg.DB_PATH,
        timeout=30,
        check_same_thread=False
    )

    # Return rows that behave like dictionaries
    conn.row_factory = sqlite3.Row

    # Improve concurrent read/write behaviour
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def get_conn():
    conn = getattr(_local, "conn", None)

    if conn is None:
        conn = _make_conn()
        _local.conn = conn
    else:
        try:
            conn.execute("SELECT 1")
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

            conn = _make_conn()
            _local.conn = conn

    return conn


def release_conn(conn):
    """
    Keep the connection alive for the current thread.

    We don't close it after every query because the application
    performs many database operations.
    """
    pass