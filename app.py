import logging
import time

from flask import Flask, render_template, redirect, url_for

from config import Config
from api.routes import api_bp
from api.control import control_bp
from api.solo import solo_bp


class _SuppressSSEDisconnect(logging.Filter):
    """Silence the noisy 'client disconnected' Werkzeug log for /api/events."""

    def filter(self, record):
        return (
            "client disconnected"
            not in record.getMessage().lower()
        )


def create_app():
    logging.getLogger("werkzeug").addFilter(
        _SuppressSSEDisconnect()
    )

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    app.config.from_object(Config)

    # Cache-bust static JS on every server restart.
    app.jinja_env.globals["static_v"] = int(
        time.time()
    )

    # Apply any pending DB schema migrations before serving requests.
    import db.queries as _q

    _q.run_migrations()

    app.register_blueprint(
        api_bp,
        url_prefix="/api",
    )

    app.register_blueprint(
        control_bp,
        url_prefix="/api/control",
    )

    app.register_blueprint(
        solo_bp,
        url_prefix="/api/solo",
    )

    @app.after_request
    def no_cache_html(response):
        """
        Prevent browsers from caching HTML pages so url_for paths
        are always current.
        """

        if "text/html" in response.content_type:
            response.headers[
                "Cache-Control"
            ] = (
                "no-store, no-cache, "
                "must-revalidate, max-age=0"
            )

            response.headers[
                "Pragma"
            ] = "no-cache"

            response.headers[
                "Expires"
            ] = "0"

        return response

    # ============================================================
    # PORTAL
    # ============================================================

    @app.route("/")
    def portal():
        return render_template(
            "portal.html"
        )

    # ============================================================
    # MULTIPLAYER
    # ============================================================

    @app.route("/multiplayer")
    def lobby():
        return render_template(
            "lobby.html"
        )

    @app.route("/play")
    def play():
        return render_template(
            "game.html",
            max_bet=app.config[
                "MAX_BET"
            ],
        )

    # ============================================================
    # SOLO — DICE / WHEEL / CARD GAMES
    # ============================================================

    _SOLO_GAMES = (
        "baccarat",
        "sicbo",
        "roulette",
        "craps",
        "great_fortune_dice",
    )

    @app.route(
        "/games/<game_name>"
    )
    def solo_game(game_name):
        if (
            game_name
            not in _SOLO_GAMES
        ):
            return redirect(
                url_for("portal")
            )

        display_names = {
            "great_fortune_dice":
                "Great Fortune Dice",

            "craps":
                "Craps",
        }

        return render_template(
            "solo_game.html",

            game=
                game_name,

            game_display=
                display_names.get(
                    game_name,
                    game_name.capitalize(),
                ),

            max_bet=
                app.config[
                    "MAX_BET"
                ],

            starting_credits=
                app.config[
                    "STARTING_CREDITS"
                ],
        )

    # ============================================================
    # FELT TEMPLATES
    # ============================================================

    _FELT_GAMES = {
        "sicbo":
            "felt_sicbo.html",

        "craps":
            "felt_craps.html",

        "great_fortune_dice":
            "felt_gfd.html",
    }

    @app.route(
        "/felt/<game_name>"
    )
    def felt(game_name):
        template = (
            _FELT_GAMES.get(
                game_name
            )
        )

        if not template:
            return redirect(
                url_for("portal")
            )

        return render_template(
            template
        )

    # ============================================================
    # SOLO — BLACKJACK FAMILY
    # ============================================================

    _BJ_VARIANTS = {
        "blackjack_lucky8": {
            "name":
                "Blackjack Lucky 8",

            "icon":
                "🃏",
        },

        "blackjack_freebet": {
            "name":
                "Free Bet Blackjack",

            "icon":
                "💸",
        },

        "blackjack_kingsbounty": {
            "name":
                "King's Bounty Blackjack",

            "icon":
                "👑",
        },

        "pontoon": {
            "name":
                "Pontoon",

            "icon":
                "⚓",
        },
    }

    @app.route(
        "/games/blackjack/<variant>"
    )
    def blackjack_game(variant):
        if (
            variant
            not in _BJ_VARIANTS
        ):
            return redirect(
                url_for("portal")
            )

        meta = (
            _BJ_VARIANTS[
                variant
            ]
        )

        return render_template(
            "blackjack_game.html",

            game=
                variant,

            game_name=
                meta["name"],

            game_icon=
                meta["icon"],

            max_bet=
                app.config[
                    "MAX_BET"
                ],

            starting_credits=
                app.config[
                    "STARTING_CREDITS"
                ],
        )

    # ============================================================
    # PROJECTOR / OPERATOR
    # ============================================================

    @app.route("/projector")
    def projector():
        return render_template(
            "projector.html"
        )

    @app.route("/control")
    def control_page():
        return render_template(
            "control.html"
        )

    return app


app = create_app()