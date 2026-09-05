"""MBS Fortune Pai Gow Poker — dedicated Solo rules metadata."""

GAME_ID = "poker_fortune_pai_gow"
NAME = "Fortune Pai Gow Poker"
ICON = "🀄"

DECK_SIZE = 53
JOKER = True

INITIAL_WAGERS = (
    "ante",
    "fortune_bonus",
)

COMMISSION = 0.05

FORTUNE_PAYS = {
    "seven_card_straight_flush_no_joker": 2500,
    "royal_match": 1000,
    "seven_card_straight_flush_with_joker": 500,
    "five_aces": 250,
    "royal_flush": 100,
    "straight_flush": 50,
    "four_kind": 20,
    "full_house": 5,
    "flush": 4,
    "three_kind": 3,
    "straight": 2,
}

ENVY_PAYS = {
    "seven_card_straight_flush_no_joker": 250,
    "royal_match": 50,
}


def legal_actions(stage, blind=False):
    # Blind hands and Dealer are always House Way.
    # The viewed-hand manual-setting UI is added after backend tests.
    return ("houseway",)
