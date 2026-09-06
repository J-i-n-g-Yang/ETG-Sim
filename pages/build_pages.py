"""
Build ETG Sim's static GitHub Pages Solo Edition.

Existing Flask templates are rendered at BUILD TIME only.

The generated _site application itself runs entirely inside the
browser using JavaScript + Pyodide.

The production Flask/Docker application remains unchanged.
"""

from __future__ import annotations

import shutil
import sys

from pathlib import Path


# ================================================================
# PATHS
# ================================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

SITE = (
    ROOT /
    "_site"
)


root_string = str(
    ROOT
)

if root_string not in sys.path:

    sys.path.insert(
        0,
        root_string
    )


from flask import render_template
from app import app

from game import poker_engine


# ================================================================
# BACCARAT
# ================================================================

BACCARAT_VARIANTS = {

    "baccarat_dragon_tiger": {
        "slug":
            "dragon-tiger",

        "name":
            "Dragon Tiger No Commission Baccarat",

        "icon":
            "🐉",
    },

    "baccarat_immortal": {
        "slug":
            "immortal",

        "name":
            "Immortal Dragon Tiger No Commission Baccarat",

        "icon":
            "♾️",
    },

    "baccarat_rising": {
        "slug":
            "rising",

        "name":
            "Rising Dragon Tiger No Commission Baccarat",

        "icon":
            "🔥",
    },
}


# ================================================================
# BLACKJACK
# ================================================================

BLACKJACK_VARIANTS = {

    "blackjack_lucky8": {
        "slug":
            "lucky-8",

        "name":
            "Blackjack Lucky 8",

        "icon":
            "🃏",
    },

    "blackjack_freebet": {
        "slug":
            "free-bet",

        "name":
            "Free Bet Blackjack",

        "icon":
            "💸",
    },

    "blackjack_kingsbounty": {
        "slug":
            "kings-bounty",

        "name":
            "King's Bounty Blackjack",

        "icon":
            "👑",
    },

    "pontoon": {
        "slug":
            "pontoon",

        "name":
            "Pontoon",

        "icon":
            "⚓",
    },
}


# ================================================================
# POKER
#
# Keep the actual engine IDs authoritative.
# ================================================================

POKER_SLUGS = {
    "poker_three_card_xtreme":
        "three-card-xtreme",

    "poker_singapore_stud":
        "singapore-stud",

    "poker_texas_bonus":
        "texas-holdem-bonus",

    "poker_ultimate_texas":
        "ultimate-texas-holdem",

    "poker_mississippi":
        "mississippi-stud",

    "poker_fortune_pai_gow":
        "fortune-pai-gow",
}


# ================================================================
# STATELESS PAGES
# ================================================================

STATELESS_PAGES = [

    {
        "game":
            "sicbo",

        "template":
            "dice_game.html",

        "controller":
            "dice_solo.js",

        "destination":
            "games/sicbo/index.html",

        "game_name":
            "Sic Bo",

        "game_display":
            "Sic Bo",

        "game_icon":
            "🎲",
    },

    {
        "game":
            "great_fortune_dice",

        "template":
            "dice_game.html",

        "controller":
            "dice_solo.js",

        "destination":
            "games/great-fortune-dice/index.html",

        "game_name":
            "Great Fortune Dice",

        "game_display":
            "Great Fortune Dice",

        "game_icon":
            "🎲",
    },

    {
        "game":
            "roulette_single_zero",

        "template":
            "roulette_game.html",

        "controller":
            "roulette_solo.js",

        "destination":
            "games/roulette/single-zero/index.html",

        "game_name":
            "Single Zero Roulette",

        "game_display":
            "Single Zero Roulette",

        "game_icon":
            "🎯",
    },

    {
        "game":
            "roulette_double_zero",

        "template":
            "roulette_game.html",

        "controller":
            "roulette_solo.js",

        "destination":
            "games/roulette/double-zero/index.html",

        "game_name":
            "Double Zero Roulette",

        "game_display":
            "Double Zero Roulette",

        "game_icon":
            "🎯",
    },

    {
        "game":
            "roulette_sands",

        "template":
            "roulette_game.html",

        "controller":
            "roulette_solo.js",

        "destination":
            "games/roulette/sands/index.html",

        "game_name":
            "Sands Roulette",

        "game_display":
            "Sands Roulette",

        "game_icon":
            "🎯",
    },

    {
        "game":
            "royal_three_pictures",

        "template":
            "royal_three_pictures_game.html",

        "controller":
            "royal_three_pictures_solo.js",

        "destination":
            "games/royal-three-pictures/index.html",

        "game_name":
            "Royal Three Pictures",

        "game_display":
            "Royal Three Pictures",

        "game_icon":
            "👑",
    },
]


# ================================================================
# CRAPS
# ================================================================

CRAPS_PAGE = {

    "game":
        "craps",

    "template":
        "dice_game.html",

    "controller":
        "craps_solo.js",

    "destination":
        "games/craps/index.html",

    "game_name":
        "Craps",

    "game_display":
        "Craps",

    "game_icon":
        "🎲",
}


# ================================================================
# DUELING 8'S 21+
# ================================================================

DUELING_8S_PAGE = {
    "game":
        "dueling_8s_21",

    "template":
        "dueling_8s_game.html",

    "controller":
        "dueling_8s_solo.js",

    "destination":
        "games/dueling-8s/index.html",

    "game_name":
        "Dueling 8's 21+",

    "game_display":
        "Dueling 8's 21+",

    "game_icon":
        "8️⃣",
}


# ================================================================
# FILE HELPER
# ================================================================

def write_text(
    path: Path,
    text: str,
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text,
        encoding="utf-8",
    )


# ================================================================
# SCRIPT REPLACEMENT
# ================================================================

def replace_controller_script(
    html: str,
    controller: str,
    replacement: str,
) -> str:

    needle = (
        f"/static/js/{controller}"
    )

    position = html.rfind(
        needle
    )

    if position == -1:

        raise RuntimeError(
            "Could not locate controller "
            f"{controller} in rendered template"
        )

    start = html.rfind(
        "<script",
        0,
        position,
    )

    end = html.find(
        "</script>",
        position,
    )

    if (
        start == -1
        or
        end == -1
    ):

        raise RuntimeError(
            "Malformed script tag for "
            f"{controller}"
        )

    end += len(
        "</script>"
    )

    return (
        html[:start]
        +
        replacement
        +
        html[end:]
    )


# ================================================================
# RELATIVE ROOT
# ================================================================

def relative_root(
    destination: str,
) -> str:

    path = Path(
        destination
    )

    directory_depth = (
        len(
            path.parts
        )
        -
        1
    )

    return (
        "../" *
        directory_depth
    )


# ================================================================
# COMMON PATH CONVERSION
# ================================================================

def convert_common_paths(
    html: str,
    destination: str,
) -> tuple[str, str]:

    root = relative_root(
        destination
    )

    html = html.replace(
        'href="/static/',
        f'href="{root}static/',
    )

    html = html.replace(
        'src="/static/',
        f'src="{root}static/',
    )

    html = html.replace(
        'href="/"',
        f'href="{root}"',
    )

    return (
        html,
        root,
    )


# ================================================================
# GENERIC STATELESS PAGE
# ================================================================

def pagesify(
    html: str,
    *,
    destination: str,
    controller: str,
) -> str:

    (
        html,
        root,
    ) = convert_common_paths(
        html,
        destination,
    )

    replacement = (
        "<script>\n"
        "window.ETG_PAGES_CONTROLLER = "
        f"{controller!r};\n"
        "</script>\n"
        "<script "
        'type="module" '
        f'src="{root}runtime/'
        'stateless-loader.js">'
        "</script>"
    )

    return replace_controller_script(
        html,
        controller,
        replacement,
    )


# ================================================================
# BACCARAT PAGE
# ================================================================

def pagesify_baccarat(
    html: str,
    destination: str,
) -> str:

    (
        html,
        root,
    ) = convert_common_paths(
        html,
        destination,
    )

    replacement = (
        '<script type="module" '
        f'src="{root}runtime/'
        'baccarat-loader.js">'
        '</script>'
    )

    return replace_controller_script(
        html,
        "baccarat_solo.js",
        replacement,
    )


# ================================================================
# CRAPS PAGE
# ================================================================

def pagesify_craps(
    html: str,
    destination: str,
) -> str:

    (
        html,
        root,
    ) = convert_common_paths(
        html,
        destination,
    )

    replacement = (
        '<script type="module" '
        f'src="{root}runtime/'
        'craps-loader.js">'
        '</script>'
    )

    return replace_controller_script(
        html,
        "craps_solo.js",
        replacement,
    )


# ================================================================
# BLACKJACK PAGE
# ================================================================

def pagesify_blackjack(
    html: str,
    destination: str,
) -> str:

    (
        html,
        root,
    ) = convert_common_paths(
        html,
        destination,
    )

    replacement = (
        '<script type="module" '
        f'src="{root}runtime/'
        'blackjack-loader.js">'
        '</script>'
    )

    return replace_controller_script(
        html,
        "blackjack_solo.js",
        replacement,
    )


# ================================================================
# POKER PAGE
# ================================================================

def pagesify_poker(
    html: str,
    destination: str,
) -> str:

    (
        html,
        root,
    ) = convert_common_paths(
        html,
        destination,
    )

    replacement = (
        '<script type="module" '
        f'src="{root}runtime/'
        'poker-loader.js">'
        '</script>'
    )

    return replace_controller_script(
        html,
        "poker_solo.js",
        replacement,
    )


# ================================================================
# DUELING 8'S PAGE
# ================================================================

def pagesify_dueling_8s(
    html: str,
    destination: str,
) -> str:

    (
        html,
        root,
    ) = convert_common_paths(
        html,
        destination,
    )

    replacement = (
        '<script type="module" '
        f'src="{root}runtime/'
        'dueling-8s-loader.js">'
        '</script>'
    )

    return replace_controller_script(
        html,
        "dueling_8s_solo.js",
        replacement,
    )


# ================================================================
# TEMPLATE RENDERER
# ================================================================

def render_game_page(
    definition: dict,
) -> str:

    context = {
        "game":
            definition[
                "game"
            ],

        "game_name":
            definition.get(
                "game_name",
                definition[
                    "game"
                ],
            ),

        "game_display":
            definition.get(
                "game_display",
                definition.get(
                    "game_name",
                    definition[
                        "game"
                    ],
                ),
            ),

        "game_icon":
            definition.get(
                "game_icon",
                "🎰",
            ),

        "max_bet":
            app.config[
                "MAX_BET"
            ],

        "starting_credits":
            app.config[
                "STARTING_CREDITS"
            ],

        "static_v":
            "pages",
    }

    return render_template(
        definition[
            "template"
        ],
        **context,
    )


# ================================================================
# BUILD
# ================================================================

def build():

    # ------------------------------------------------------------
    # CLEAN PREVIOUS BUILD
    # ------------------------------------------------------------

    if SITE.exists():

        shutil.rmtree(
            SITE
        )

    SITE.mkdir(
        parents=True
    )


    # ------------------------------------------------------------
    # PORTAL
    # ------------------------------------------------------------

    shutil.copy2(
        ROOT /
        "pages" /
        "index.html",

        SITE /
        "index.html",
    )


    # ------------------------------------------------------------
    # PAGES RUNTIME
    # ------------------------------------------------------------

    shutil.copytree(
        ROOT /
        "pages" /
        "runtime",

        SITE /
        "runtime",
    )


    # ------------------------------------------------------------
    # EXISTING FRONTEND ASSETS
    # ------------------------------------------------------------

    shutil.copytree(
        ROOT /
        "static",

        SITE /
        "static",
    )


    # ------------------------------------------------------------
    # AUTHORITATIVE PYTHON GAME ENGINES
    # ------------------------------------------------------------

    shutil.copytree(
        ROOT /
        "game",

        SITE /
        "python" /
        "game",

        ignore=
            shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                ".DS_Store",
            ),
    )


    # ------------------------------------------------------------
    # RENDER STATIC GAME PAGES
    # ------------------------------------------------------------

    with app.test_request_context(
        "/"
    ):


        # ========================================================
        # BACCARAT
        # ========================================================

        for (
            game,
            meta,
        ) in (
            BACCARAT_VARIANTS.items()
        ):

            definition = {
                "game":
                    game,

                "template":
                    "baccarat_game.html",

                "game_name":
                    meta[
                        "name"
                    ],

                "game_display":
                    meta[
                        "name"
                    ],

                "game_icon":
                    meta[
                        "icon"
                    ],
            }

            destination = (
                "games/baccarat/"
                f"{meta['slug']}/"
                "index.html"
            )

            html = render_game_page(
                definition
            )

            html = pagesify_baccarat(
                html,
                destination,
            )

            write_text(
                SITE /
                destination,
                html,
            )


        # ========================================================
        # STATELESS GAMES
        # ========================================================

        for definition in (
            STATELESS_PAGES
        ):

            html = render_game_page(
                definition
            )

            html = pagesify(
                html,

                destination=
                    definition[
                        "destination"
                    ],

                controller=
                    definition[
                        "controller"
                    ],
            )

            write_text(
                SITE /
                definition[
                    "destination"
                ],
                html,
            )


        # ========================================================
        # CRAPS
        # ========================================================

        html = render_game_page(
            CRAPS_PAGE
        )

        html = pagesify_craps(
            html,
            CRAPS_PAGE[
                "destination"
            ],
        )

        write_text(
            SITE /
            CRAPS_PAGE[
                "destination"
            ],
            html,
        )


        # ========================================================
        # BLACKJACK FAMILY
        # ========================================================

        for (
            game,
            meta,
        ) in (
            BLACKJACK_VARIANTS.items()
        ):

            definition = {
                "game":
                    game,

                "template":
                    "blackjack_game.html",

                "game_name":
                    meta[
                        "name"
                    ],

                "game_display":
                    meta[
                        "name"
                    ],

                "game_icon":
                    meta[
                        "icon"
                    ],
            }

            destination = (
                "games/blackjack/"
                f"{meta['slug']}/"
                "index.html"
            )

            html = render_game_page(
                definition
            )

            html = pagesify_blackjack(
                html,
                destination,
            )

            write_text(
                SITE /
                destination,
                html,
            )


        # ========================================================
        # POKER FAMILY
        # ========================================================

        for game in poker_engine.GAMES:

            if game not in POKER_SLUGS:

                raise RuntimeError(
                    "Missing GitHub Pages Poker slug "
                    f"for {game}"
                )

            slug = POKER_SLUGS[
                game
            ]

            name = poker_engine.NAMES[
                game
            ]

            icon = poker_engine.ICONS[
                game
            ]

            definition = {
                "game":
                    game,

                "template":
                    "poker_game.html",

                "game_name":
                    name,

                "game_display":
                    name,

                "game_icon":
                    icon,
            }

            destination = (
                "games/poker/"
                f"{slug}/"
                "index.html"
            )

            html = render_game_page(
                definition
            )

            html = pagesify_poker(
                html,
                destination,
            )

            write_text(
                SITE /
                destination,
                html,
            )

        # ========================================================
        # DUELING 8'S 21+
        # ========================================================

        html = render_game_page(
            DUELING_8S_PAGE
        )

        html = pagesify_dueling_8s(
            html,
            DUELING_8S_PAGE[
                "destination"
            ],
        )

        write_text(
            SITE /
            DUELING_8S_PAGE[
                "destination"
            ],
            html,
        )


    # ------------------------------------------------------------
    # DISABLE JEKYLL PROCESSING
    # ------------------------------------------------------------

    (
        SITE /
        ".nojekyll"
    ).touch()


    print(
        "GitHub Pages build complete:"
    )

    print(
        SITE
    )


if __name__ == "__main__":

    build()