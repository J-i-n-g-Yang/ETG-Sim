import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_PATH = os.environ.get(
        "DB_PATH",
        os.path.join(
            os.path.dirname(__file__),
            "data",
            "etg_sim.db",
        ),
    )

    EVENT_CODE = os.environ.get(
        "EVENT_CODE",
        "TOWNHALL2026",
    )

    CONTROL_PIN = os.environ.get(
        "CONTROL_PIN",
        "1234",
    )

    STARTING_CREDITS = int(
        os.environ.get(
            "STARTING_CREDITS",
            "100000",
        )
    )

    BETTING_SECONDS = int(
        os.environ.get(
            "BETTING_SECONDS",
            "35",
        )
    )

    MAX_BET = int(
        os.environ.get(
            "MAX_BET",
            "20000",
        )
    )

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-only-change-me",
    )