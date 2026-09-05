"""Shared metadata/helpers for the dedicated Solo Dice family.

Phase 1 intentionally reuses the existing, working variant modules.
Their rules will be audited and migrated one game at a time.
"""

GAMES = ("sicbo", "craps", "great_fortune_dice")

NAMES = {
    "sicbo": "Sic Bo",
    "craps": "Craps",
    "great_fortune_dice": "Great Fortune Dice",
}

ICONS = {
    "sicbo": "🎲",
    "craps": "🎰",
    "great_fortune_dice": "🎲",
}

DICE_COUNTS = {
    "sicbo": 3,
    "craps": 2,
    "great_fortune_dice": 4,
}

FELT_TEMPLATES = {
    "sicbo": "felt_sicbo.html",
    "craps": "felt_craps.html",
    "great_fortune_dice": "felt_gfd.html",
}


def display_name(game):
    return NAMES[game]


def icon(game):
    return ICONS[game]
