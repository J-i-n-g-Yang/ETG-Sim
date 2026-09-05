"""Game registry — maps stateless games to modules. Stateful Poker uses game.poker_engine."""
import importlib
_MODULES = {
    "baccarat": "game.baccarat",
    "baccarat_dragon_tiger": "game.baccarat_dragon_tiger",
    "baccarat_immortal": "game.baccarat_immortal",
    "baccarat_rising": "game.baccarat_rising",
    "sicbo": "game.sicbo",
    "roulette": "game.roulette",
    "craps": "game.craps",
    "great_fortune_dice": "game.great_fortune_dice",
    "blackjack_lucky8": "game.blackjack_lucky8",
    "blackjack_freebet": "game.blackjack_freebet",
    "blackjack_kingsbounty": "game.blackjack_kingsbounty",
    "pontoon": "game.pontoon",
}
POKER_MODULES = {
    "poker_mississippi": "game.poker_mississippi_stud",
    "poker_singapore_stud": "game.poker_singapore_stud",
    "poker_texas_bonus": "game.poker_texas_holdem_bonus",
    "poker_three_card_xtreme": "game.poker_three_card_xtreme",
    "poker_ultimate_texas": "game.poker_ultimate_texas",
    "poker_fortune_pai_gow": "game.poker_fortune_pai_gow",
}
def get_module(game):
    path=_MODULES.get(game) or POKER_MODULES.get(game)
    if not path: raise ValueError(f"Unknown game: {game!r}")
    return importlib.import_module(path)
def wager_options(game):
    try: return list(get_module(game).WAGER_TYPES)
    except Exception: return []
def validate_wager(game,wager_type):
    try: return wager_type in get_module(game).WAGER_TYPES
    except Exception: return False
