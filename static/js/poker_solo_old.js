/* ================================================================
   ETG Sim Poker Solo

   HOUSE-BANKED POKER
   ---------------------------------------------------------------
   - Three Card Poker Xtreme
   - Singapore Stud Poker
   - Texas Hold'em Bonus
   - Ultimate Texas Hold'em
   - Mississippi Stud Poker
   - Fortune Pai Gow Poker

   Fortune Pai Gow:
   - Seat 1 / VIEWED may manually set the hand
   - Select exactly 2 cards for the Low Hand
   - Remaining 5 cards become the High Hand
   - House Way is also available
   - Blind seats use House Way automatically

   Progressive Jackpot wagering remains unavailable until ETG Sim
   has a real jackpot-pool model.
   ================================================================ */

const GAME = window.POKER_GAME;
const MAX_BET = Number(window.POKER_MAX);
const STARTING_CREDITS = Number(window.POKER_START);

const $ = (id) =>
  document.getElementById(id);

const fmt = (value) =>
  Number(value).toLocaleString(
    undefined,
    {
      maximumFractionDigits: 1,
    }
  );

/* ================================================================
   CARDS / CHIPS
   ================================================================ */

const SUITS = {
  S: "♠",
  H: "♥",
  D: "♦",
  C: "♣",
  X: "★",
};

const RED_SUITS =
  new Set(["H", "D"]);

const CHIPS = [
  100,
  250,
  500,
  1000,
  2500,
  5000,
  10000,
  20000,
];

const CHIP_STYLE = {
  100: [
    "#315b7b",
    "#b9d9ee",
  ],

  250: [
    "#315d2b",
    "#b9e6a9",
  ],

  500: [
    "#7b2929",
    "#ffc0c0",
  ],

  1000: [
    "#49449a",
    "#d4d0ff",
  ],

  2500: [
    "#87520d",
    "#ffd39a",
  ],

  5000: [
    "#1d6969",
    "#a8eeee",
  ],

  10000: [
    "#762176",
    "#efb1ef",
  ],

  20000: [
    "#746b1c",
    "#fff08b",
  ],
};

/* ================================================================
   GAME CONFIGURATION
   ================================================================ */

const GAME_CONFIG = {

  /* --------------------------------------------------------------
     THREE CARD POKER XTREME
     -------------------------------------------------------------- */

  poker_three_card_xtreme: {
    note:
      "Play = 1× Ante. Dealer qualifies Queen-high or better. " +
      "Pair Plus and Six Card Bonus remain in play after Fold. " +
      "Pair Plus and/or Six Card Bonus may be played without Ante. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards: 3,
    communityCards: 2,

    communityLabel:
      "COMMUNITY CARDS",

    allowSideOnly: true,

    sideBets: [
      [
        "pair_plus",
        "PAIR PLUS",
      ],

      [
        "six_card_bonus",
        "SIX CARD BONUS",
      ],
    ],

    mainBets: [
      [
        "ante",
        "ANTE",
        true,
      ],

      [
        "play",
        "PLAY",
        false,
      ],
    ],

    payTable: [
      [
        "Ante / Play",
        "1:1",
      ],

      [
        "Ante Bonus — SF / Trips / Straight",
        "5 / 4 / 1:1",
      ],

      [
        "Pair Plus — SF / Trips / Straight / Flush / Pair",
        "40 / 30 / 5 / 4 / 1:1",
      ],

      [
        "Six Card — Royal / SF / Quads / FH / Flush / Straight / Trips",
        "500 / 100 / 50 / 20 / 15 / 10 / 7:1",
      ],

      [
        "Progressive Jackpot",
        "Unavailable",
      ],
    ],
  },

  /* --------------------------------------------------------------
     SINGAPORE STUD
     -------------------------------------------------------------- */

  poker_singapore_stud: {
    note:
      "Bet = 2× Ante. Dealer qualifies with A-K high or better. " +
      "If Dealer does not qualify, Ante pays 1:1 and Bet pushes. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards: 5,
    communityCards: 0,

    communityLabel: "",

    allowSideOnly: false,

    sideBets: [],

    mainBets: [
      [
        "ante",
        "ANTE",
        true,
      ],

      [
        "play",
        "BET · 2× ANTE",
        false,
      ],
    ],

    payTable: [
      [
        "Ante",
        "1:1",
      ],

      [
        "Bet — Royal / Straight Flush",
        "250 / 50:1",
      ],

      [
        "Bet — Quads / Full House",
        "20 / 7:1",
      ],

      [
        "Bet — Flush / Straight / Trips / Two Pair / Pair or Lower",
        "5 / 4 / 3 / 2 / 1:1",
      ],

      [
        "Progressive Jackpot",
        "Unavailable",
      ],
    ],
  },

  /* --------------------------------------------------------------
     TEXAS HOLD'EM BONUS
     -------------------------------------------------------------- */

  poker_texas_bonus: {
    note:
      "Flop = 2× Ante. Turn and River are optional 1× Ante wagers. " +
      "A Player who folds loses Ante and Bonus. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards: 2,
    communityCards: 5,

    communityLabel:
      "COMMUNITY CARDS · FLOP / TURN / RIVER",

    allowSideOnly: false,

    sideBets: [
      [
        "bonus",
        "BONUS",
      ],
    ],

    mainBets: [
      [
        "ante",
        "ANTE",
        true,
      ],

      [
        "flop",
        "FLOP / TURN / RIVER",
        false,
      ],
    ],

    payTable: [
      [
        "Flop / Turn / River wins",
        "1:1",
      ],

      [
        "Ante on Straight+ Player win",
        "1:1",
      ],

      [
        "Ante on lower Player win",
        "Push",
      ],

      [
        "Bonus — AA Player + Dealer",
        "1000:1",
      ],

      [
        "Bonus — AA Player",
        "30:1",
      ],

      [
        "Bonus — AK suited",
        "25:1",
      ],

      [
        "Bonus — AQ/AJ suited",
        "20:1",
      ],

      [
        "Bonus — AK unsuited",
        "15:1",
      ],

      [
        "Bonus — KK/QQ/JJ",
        "10:1",
      ],

      [
        "Bonus — AQ/AJ unsuited",
        "5:1",
      ],

      [
        "Bonus — 10-10 through 2-2",
        "3:1",
      ],

      [
        "Progressive Jackpot",
        "Unavailable",
      ],
    ],
  },

  /* --------------------------------------------------------------
     ULTIMATE TEXAS HOLD'EM
     -------------------------------------------------------------- */

  poker_ultimate_texas: {
    note:
      "Ante and Blind must be equal. " +
      "Pre-flop Play = 3× or 4×; after Flop = 2×; River = 1×. " +
      "Dealer qualifies for Ante with Pair or better. " +
      "Trips remains independent of the Dealer result. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards: 2,
    communityCards: 5,

    communityLabel:
      "COMMUNITY CARDS · FLOP / TURN / RIVER",

    allowSideOnly: false,

    sideBets: [
      [
        "trips",
        "TRIPS",
      ],
    ],

    mainBets: [
      [
        "ante",
        "ANTE",
        true,
      ],

      [
        "blind",
        "BLIND",
        false,
      ],

      [
        "play",
        "PLAY",
        false,
      ],
    ],

    payTable: [
      [
        "Play",
        "1:1",
      ],

      [
        "Ante — Dealer Pair+",
        "1:1",
      ],

      [
        "Blind — Royal / SF / Quads",
        "500 / 50 / 10:1",
      ],

      [
        "Blind — Full House / Flush / Straight",
        "3 / 1.5 / 1:1",
      ],

      [
        "Blind — below Straight",
        "Push",
      ],

      [
        "Trips — Royal / SF / Quads",
        "100 / 40 / 30:1",
      ],

      [
        "Trips — Full House / Flush / Straight / Trips",
        "8 / 7 / 4 / 3:1",
      ],

      [
        "Progressive Jackpot",
        "Unavailable",
      ],
    ],
  },

  /* --------------------------------------------------------------
     MISSISSIPPI STUD
     -------------------------------------------------------------- */

  poker_mississippi: {
    note:
      "At 3rd, 4th and 5th Street choose Fold or wager " +
      "1×, 2× or 3× Ante. " +
      "Progressive Jackpot is currently unavailable. " +
      "Three Card Bonus will be enabled after its PDF pay-table " +
      "image is separately verified.",

    dealerCards: 0,
    communityCards: 3,

    communityLabel:
      "COMMUNITY CARDS · 3RD / 4TH / 5TH STREET",

    allowSideOnly: false,

    sideBets: [],

    mainBets: [
      [
        "ante",
        "ANTE",
        true,
      ],
    ],

    payTable: [
      [
        "Royal / Straight Flush",
        "500 / 100:1",
      ],

      [
        "Quads / Full House",
        "40 / 10:1",
      ],

      [
        "Flush / Straight / Trips / Two Pair",
        "6 / 4 / 3 / 2:1",
      ],

      [
        "Pair Jacks or Better",
        "1:1",
      ],

      [
        "Pair 6s–10s",
        "Push",
      ],

      [
        "Pair 5s or Lower / High Card",
        "Lose",
      ],

      [
        "Progressive Jackpot",
        "Unavailable",
      ],
    ],
  },

  /* --------------------------------------------------------------
     FORTUNE PAI GOW
     -------------------------------------------------------------- */

  poker_fortune_pai_gow: {
    note:
      "Seat 1 is viewed and may be manually set. Select exactly " +
      "2 cards for the Low Hand; the remaining 5 become the High Hand. " +
      "Seat 2, Seat 3 and Dealer use House Way. " +
      "A foul viewed hand is reset to House Way. " +
      "Standard wins pay 1:1 less 5% commission.",

    dealerCards: 7,
    communityCards: 0,

    communityLabel: "",

    allowSideOnly: false,

    sideBets: [
      [
        "fortune_bonus",
        "FORTUNE BONUS",
      ],
    ],

    mainBets: [
      [
        "ante",
        "STANDARD",
        true,
      ],
    ],

    payTable: [
      [
        "Standard win",
        "1:1 less 5% commission",
      ],

      [
        "Copy hands",
        "Dealer wins",
      ],

      [
        "7-Card Straight Flush · no Joker",
        "2500:1",
      ],

      [
        "Royal Match",
        "1000:1",
      ],

      [
        "7-Card Straight Flush · Joker",
        "500:1",
      ],

      [
        "Five Aces",
        "250:1",
      ],

      [
        "Royal Flush",
        "100:1",
      ],

      [
        "Straight Flush",
        "50:1",
      ],

      [
        "Four of a Kind",
        "20:1",
      ],

      [
        "Full House",
        "5:1",
      ],

      [
        "Flush",
        "4:1",
      ],

      [
        "Three of a Kind",
        "3:1",
      ],

      [
        "Straight",
        "2:1",
      ],

      [
        "Envy · 7-Card SF / Royal Match",
        "250 / 50 credits",
      ],
    ],
  },
};

const CONFIG =
  GAME_CONFIG[GAME];

if (!CONFIG) {
  throw new Error(
    `Unknown Poker game: ${GAME}`
  );
}

/* ================================================================
   LOCAL STORAGE
   ================================================================ */

const BALANCE_KEY =
  `etg_poker_bal_${GAME}`;

const HISTORY_KEY =
  `etg_poker_history_${GAME}`;

let balance =
  Number(
    localStorage.getItem(
      BALANCE_KEY
    ) ??
    STARTING_CREDITS
  );

if (
  !Number.isFinite(
    balance
  )
) {
  balance =
    STARTING_CREDITS;
}

/* ================================================================
   ROUND STATE
   ================================================================ */

let selectedChip = 1000;

let bets = {};

let stateToken = null;

let busy = false;

let currentState = null;

/*
 * Pai Gow only.
 *
 * These are zero-based indices into Seat 1's original seven-card
 * array. Exactly two indices represent the Low Hand.
 */
let paiGowLowSelection = [];

/* ================================================================
   BALANCE
   ================================================================ */

function saveBalance() {
  localStorage.setItem(
    BALANCE_KEY,
    String(balance)
  );

  const display =
    $("balance");

  if (display) {
    display.textContent =
      fmt(balance);
  }
}

function pendingTotal() {
  return Object
    .values(bets)
    .reduce(
      (sum, amount) =>
        sum +
        Number(amount),
      0
    );
}

/* ================================================================
   STATUS
   ================================================================ */

function showStatus(
  message
) {
  const status =
    $("status");

  if (status) {
    status.innerHTML =
      message;
  }
}

/* ================================================================
   CHIP HELPERS
   ================================================================ */

function chipLabel(
  value
) {
  if (
    value >= 1000
  ) {
    return `${
      value / 1000
    }K`;
  }

  return String(value);
}

function renderChips() {
  const container =
    $("chipBar");

  if (!container) {
    return;
  }

  container.innerHTML = "";

  CHIPS.forEach(
    (value) => {
      const [
        background,
        foreground,
      ] =
        CHIP_STYLE[value];

      const button =
        document.createElement(
          "button"
        );

      button.className =
        "chip";

      if (
        value ===
        selectedChip
      ) {
        button.classList.add(
          "active"
        );
      }

      button.textContent =
        chipLabel(value);

      button.style.background =
        `radial-gradient(
          circle at 35% 30%,
          ${background} 0%,
          ${background} 55%,
          #111 100%
        )`;

      button.style.color =
        foreground;

      button.addEventListener(
        "click",
        () => {
          if (busy) {
            return;
          }

          selectedChip =
            value;

          renderChips();
        }
      );

      container.appendChild(
        button
      );
    }
  );
}

/* ================================================================
   CARDS
   ================================================================ */

function cardHTML(
  card,
  faceDown = false,
  extraClass = "",
  attributes = ""
) {
  if (faceDown) {
    return `
      <div
        class="card down ${extraClass}"
        ${attributes}
      ></div>
    `;
  }

  if (!card) {
    return "";
  }

  const red =
    RED_SUITS.has(
      card.suit
    );

  const rank =
    card.rank ===
    "JOKER"
      ? "★"
      : card.rank;

  return `
    <div
      class="
        card
        ${
          red ? "red" : ""
        }
        ${extraClass}
      "
      ${attributes}
    >
      <div>
        ${rank}
      </div>

      <div>
        ${
          SUITS[
            card.suit
          ] || ""
        }
      </div>
    </div>
  `;
}

function emptySlots(
  count
) {
  return Array(count)
    .fill(
      '<div class="card-slot"></div>'
    )
    .join("");
}

/* ================================================================
   CHIP STACK
   ================================================================ */

function chipStackHTML(
  value
) {
  if (!value) {
    return "";
  }

  const denomination =
    [...CHIPS]
      .reverse()
      .find(
        (candidate) =>
          candidate <= value
      ) || 100;

  const [
    background,
  ] =
    CHIP_STYLE[
      denomination
    ];

  return `
    <span
      class="chip-stack"
      style="
        background:${background};
      "
    >
      ${chipLabel(value)}
    </span>
  `;
}

/* ================================================================
   WAGER HTML
   ================================================================ */

function wagerHTML(
  seat,
  definition,
  shape
) {
  const [
    key,
    name,
    initial = true,
  ] =
    definition;

  const wagerKey =
    `seat${seat}_${key}`;

  const amount =
    bets[wagerKey] || 0;

  const locked =
    !initial ||
    stateToken !== null;

  return `
    <div
      class="
        wager
        ${shape}
        ${
          locked
            ? "locked"
            : ""
        }
      "

      data-seat="${seat}"
      data-key="${key}"
      data-initial="${
        initial
          ? "1"
          : "0"
      }"
    >
      ${name}

      <span class="amt">
        ${
          amount
            ? fmt(amount)
            : ""
        }
      </span>

      ${
        chipStackHTML(
          amount
        )
      }
    </div>
  `;
}

/* ================================================================
   PAI GOW HELPERS
   ================================================================ */

function isPaiGow() {
  return (
    GAME ===
    "poker_fortune_pai_gow"
  );
}

function paiGowManualActive(
  view,
  seat,
  seatData
) {
  return (
    isPaiGow() &&
    seat === 0 &&
    view.current_seat === 0 &&
    seatData &&
    seatData.manual_set_allowed ===
      true &&
    Array.isArray(
      seatData.cards
    ) &&
    seatData.cards.length === 7
  );
}

function togglePaiGowLowCard(
  index
) {
  if (
    busy ||
    !isPaiGow() ||
    !currentState ||
    currentState.current_seat !==
      0
  ) {
    return;
  }

  const seatData =
    currentState
      .seats?.["0"];

  if (
    !seatData ||
    !seatData
      .manual_set_allowed
  ) {
    return;
  }

  const existing =
    paiGowLowSelection
      .indexOf(index);

  if (
    existing >= 0
  ) {
    paiGowLowSelection.splice(
      existing,
      1
    );
  } else {
    if (
      paiGowLowSelection
        .length >= 2
    ) {
      showStatus(
        "<strong>Low Hand can contain exactly 2 cards.</strong> " +
        "Deselect one card before choosing another."
      );

      return;
    }

    paiGowLowSelection.push(
      index
    );
  }

  paiGowLowSelection.sort(
    (a, b) => a - b
  );

  renderSeats(
    currentState
  );

  if (
    paiGowLowSelection
      .length === 2
  ) {
    showStatus(
      "<strong>Low Hand selected.</strong> " +
      "The other five cards form the High Hand. " +
      "Press Confirm Set."
    );
  } else {
    showStatus(
      `<strong>Select ${
        2 -
        paiGowLowSelection.length
      } more card${
        2 -
          paiGowLowSelection.length ===
        1
          ? ""
          : "s"
      }</strong> for the Low Hand.`
    );
  }
}

function paiGowPreviewHTML(
  cards
) {
  if (
    !Array.isArray(cards) ||
    cards.length !== 7
  ) {
    return "";
  }

  const lowSet =
    new Set(
      paiGowLowSelection
    );

  const low =
    cards.filter(
      (
        _,
        index
      ) =>
        lowSet.has(index)
    );

  const high =
    cards.filter(
      (
        _,
        index
      ) =>
        !lowSet.has(index)
    );

  return `
    <div
      class="paigow-set-preview"
      style="
        margin-top:12px;
        padding:10px;
        border:1px solid rgba(255,255,255,.15);
        border-radius:10px;
      "
    >
      <div
        style="
          font-size:12px;
          opacity:.75;
          margin-bottom:6px;
        "
      >
        LOW HAND · 2 CARDS
      </div>

      <div
        class="hand-cards"
        style="margin-bottom:10px;"
      >
        ${
          low.length
            ? low
                .map(
                  (card) =>
                    cardHTML(card)
                )
                .join("")
            : emptySlots(2)
        }

        ${
          low.length === 1
            ? emptySlots(1)
            : ""
        }
      </div>

      <div
        style="
          font-size:12px;
          opacity:.75;
          margin-bottom:6px;
        "
      >
        HIGH HAND · 5 CARDS
      </div>

      <div class="hand-cards">
        ${
          high
            .map(
              (card) =>
                cardHTML(card)
            )
            .join("")
        }

        ${
          emptySlots(
            Math.max(
              0,
              5 -
                high.length
            )
          )
        }
      </div>
    </div>
  `;
}

function paiGowSetActionsHTML() {
  const ready =
    paiGowLowSelection
      .length === 2;

  return `
    <div class="actions">

      <button
        class="action primary paigow-confirm"
        ${
          ready
            ? ""
            : "disabled"
        }
      >
        Confirm Set
      </button>

      <button
        class="action secondary paigow-houseway"
      >
        House Way
      </button>

    </div>
  `;
}

function paiGowFinalSetHTML(
  seatData
) {
  if (
    !isPaiGow() ||
    !seatData
  ) {
    return "";
  }

  const low =
    seatData.low || [];

  const high =
    seatData.high || [];

  if (
    low.length !== 2 ||
    high.length !== 5
  ) {
    return "";
  }

  return `
    <div
      class="paigow-final-set"
      style="
        margin-top:12px;
        padding:10px;
        border:1px solid rgba(255,255,255,.15);
        border-radius:10px;
      "
    >
      ${
        seatData.foul
          ? `
            <div
              style="
                margin-bottom:8px;
                font-weight:700;
              "
            >
              FOUL SET RESET TO HOUSE WAY
            </div>
          `
          : ""
      }

      <div
        style="
          font-size:12px;
          opacity:.75;
          margin-bottom:6px;
        "
      >
        LOW HAND
      </div>

      <div
        class="hand-cards"
        style="margin-bottom:10px;"
      >
        ${
          low
            .map(
              (card) =>
                cardHTML(card)
            )
            .join("")
        }
      </div>

      <div
        style="
          font-size:12px;
          opacity:.75;
          margin-bottom:6px;
        "
      >
        HIGH HAND
      </div>

      <div class="hand-cards">
        ${
          high
            .map(
              (card) =>
                cardHTML(card)
            )
            .join("")
        }
      </div>
    </div>
  `;
}

/* ================================================================
   SEATS
   ================================================================ */

function renderSeats(
  view = {
    seats: {},
    current_seat: null,
    actions: [],
  }
) {
  const container =
    $("seats");

  if (!container) {
    return;
  }

  container.innerHTML =
    [0, 1, 2]
      .map(
        (seat) => {
          const seatData =
            view.seats
              ? view.seats[
                  String(
                    seat
                  )
                ]
              : null;

          const manualPaiGow =
            paiGowManualActive(
              view,
              seat,
              seatData
            );

          let cardsHTML = "";

          if (seatData) {
            if (
              seatData.cards &&
              seatData.cards
                .length
            ) {
              cardsHTML =
                seatData.cards
                  .map(
                    (
                      card,
                      index
                    ) => {
                      if (
                        manualPaiGow
                      ) {
                        const selected =
                          paiGowLowSelection
                            .includes(
                              index
                            );

                        return cardHTML(
                          card,
                          false,
                          `paigow-selectable ${
                            selected
                              ? "paigow-low-selected"
                              : ""
                          }`,
                          `
                            data-paigow-card="${index}"
                            style="
                              cursor:pointer;
                              ${
                                selected
                                  ? "transform:translateY(-10px); outline:3px solid #f0c85a;"
                                  : ""
                              }
                            "
                          `
                        );
                      }

                      return cardHTML(
                        card
                      );
                    }
                  )
                  .join("");
            } else {
              cardsHTML =
                Array(
                  seatData
                    .card_count ||
                  0
                )
                  .fill(0)
                  .map(
                    () =>
                      cardHTML(
                        null,
                        true
                      )
                  )
                  .join("");
            }
          }

          let actionsHTML = "";

          if (
            view.current_seat ===
            seat
          ) {
            if (
              manualPaiGow
            ) {
              actionsHTML =
                paiGowSetActionsHTML();
            } else {
              actionsHTML = `
                <div class="actions">
                  ${
                    (
                      view.actions ||
                      []
                    )
                      .filter(
                        (action) =>
                          action !==
                          "set_hand"
                      )
                      .map(
                        (action) => `
                          <button
                            class="
                              action
                              ${
                                action ===
                                "fold"
                                  ? "secondary"
                                  : "primary"
                              }
                            "

                            data-action="${action}"
                          >
                            ${
                              actionLabel(
                                action
                              )
                            }
                          </button>
                        `
                      )
                      .join("")
                  }
                </div>
              `;
            }
          }

          const paiGowPreview =
            manualPaiGow
              ? paiGowPreviewHTML(
                  seatData.cards
                )
              : "";

          const paiGowFinal =
            !manualPaiGow
              ? paiGowFinalSetHTML(
                  seatData
                )
              : "";

          return `
            <div
              class="
                seat

                ${
                  view.current_seat ===
                  seat
                    ? "active"
                    : ""
                }

                ${
                  seat > 0
                    ? "blind"
                    : ""
                }
              "
            >

              <div class="seat-title">
                SEAT ${seat + 1}
                ·
                ${
                  seat > 0
                    ? "BLIND"
                    : "VIEWED"
                }
              </div>

              ${
                manualPaiGow
                  ? `
                    <div
                      style="
                        font-size:12px;
                        margin:6px 0 10px;
                        opacity:.8;
                      "
                    >
                      Select exactly 2 cards for LOW HAND
                    </div>
                  `
                  : ""
              }

              <div class="hand-cards">
                ${cardsHTML}
              </div>

              ${paiGowPreview}

              ${paiGowFinal}

              <div class="bet-layout">

                <div class="side-row">
                  ${
                    CONFIG
                      .sideBets
                      .map(
                        (
                          definition
                        ) =>
                          wagerHTML(
                            seat,
                            [
                              definition[0],
                              definition[1],
                              true,
                            ],
                            "circle"
                          )
                      )
                      .join("")
                  }
                </div>

                <div
                  class="
                    main-row
                    cols-${
                      CONFIG
                        .mainBets
                        .length
                    }
                  "
                >
                  ${
                    CONFIG
                      .mainBets
                      .map(
                        (
                          definition
                        ) =>
                          wagerHTML(
                            seat,
                            definition,
                            "rect"
                          )
                      )
                      .join("")
                  }
                </div>

              </div>

              ${
                seatData &&
                seatData.result
                  ? `
                    <b>
                      ${
                        String(
                          seatData
                            .result
                        )
                          .toUpperCase()
                      }
                    </b>
                  `
                  : ""
              }

              ${actionsHTML}

            </div>
          `;
        }
      )
      .join("");

  /* --------------------------------------------------------------
     Initial wager listeners
     -------------------------------------------------------------- */

  container
    .querySelectorAll(
      ".wager[data-initial='1']"
    )
    .forEach(
      (element) => {
        element
          .addEventListener(
            "click",
            () => {
              placeInitialWager(
                Number(
                  element
                    .dataset
                    .seat
                ),

                element
                  .dataset
                  .key
              );
            }
          );
      }
    );

  /* --------------------------------------------------------------
     Generic action listeners
     -------------------------------------------------------------- */

  container
    .querySelectorAll(
      ".action[data-action]"
    )
    .forEach(
      (element) => {
        element
          .addEventListener(
            "click",
            () => {
              performAction(
                element
                  .dataset
                  .action
              );
            }
          );
      }
    );

  /* --------------------------------------------------------------
     Pai Gow card selection
     -------------------------------------------------------------- */

  container
    .querySelectorAll(
      "[data-paigow-card]"
    )
    .forEach(
      (element) => {
        element
          .addEventListener(
            "click",
            () => {
              togglePaiGowLowCard(
                Number(
                  element
                    .dataset
                    .paigowCard
                )
              );
            }
          );
      }
    );

  /* --------------------------------------------------------------
     Pai Gow Confirm Set
     -------------------------------------------------------------- */

  const confirm =
    container
      .querySelector(
        ".paigow-confirm"
      );

  if (confirm) {
    confirm.addEventListener(
      "click",
      () => {
        confirmPaiGowSet();
      }
    );
  }

  /* --------------------------------------------------------------
     Pai Gow House Way
     -------------------------------------------------------------- */

  const houseWay =
    container
      .querySelector(
        ".paigow-houseway"
      );

  if (houseWay) {
    houseWay.addEventListener(
      "click",
      () => {
        performAction(
          "houseway"
        );
      }
    );
  }
}

/* ================================================================
   TABLE
   ================================================================ */

function renderTable(
  view = {
    seats: {},
    community: [],
    dealer_cards: [],
    current_seat: null,
    actions: [],
  }
) {
  currentState =
    view;

  /*
   * Clear a stale Pai Gow selection once Seat 1 is no longer the
   * active manual-setting seat.
   */
  if (
    isPaiGow() &&
    (
      view.current_seat !== 0 ||
      !view.seats?.["0"]
        ?.manual_set_allowed
    )
  ) {
    paiGowLowSelection = [];
  }

  const dealerTitle =
    $("dealerTitle");

  if (dealerTitle) {
    dealerTitle.textContent =
      CONFIG.dealerCards > 0
        ? `DEALER · ${
            CONFIG
              .dealerCards
          } CARD${
            CONFIG
              .dealerCards ===
            1
              ? ""
              : "S"
          }`
        : "NO DEALER HAND";
  }

  const dealerArea =
    $("dealerCards");

  if (dealerArea) {
    const dealerCards =
      view.dealer_cards ||
      [];

    dealerArea.innerHTML =
      dealerCards
        .map(
          (card) =>
            cardHTML(card)
        )
        .join("") +

      emptySlots(
        Math.max(
          0,

          CONFIG
            .dealerCards -
          dealerCards.length
        )
      );
  }

  const communityTitle =
    $("communityTitle");

  if (communityTitle) {
    communityTitle
      .textContent =
        CONFIG
          .communityLabel;
  }

  const communityArea =
    $("community");

  if (communityArea) {
    const community =
      view.community ||
      [];

    communityArea.innerHTML =
      community
        .map(
          (card) =>
            cardHTML(card)
        )
        .join("") +

      emptySlots(
        Math.max(
          0,

          CONFIG
            .communityCards -
          community.length
        )
      );
  }

  renderSeats(view);

  if (
    view.current_seat !==
      null &&
    view.current_seat !==
      undefined
  ) {
    const seatData =
      view.seats
        ? view.seats[
            String(
              view
                .current_seat
            )
          ]
        : null;

    if (
      isPaiGow() &&
      view.current_seat ===
        0 &&
      seatData
        ?.manual_set_allowed
    ) {
      showStatus(
        "<strong>Seat 1 — set your Pai Gow hand.</strong> " +
        "Select exactly 2 cards for the Low Hand, then Confirm Set, " +
        "or choose House Way."
      );
    } else {
      showStatus(
        `<strong>Seat ${
          view.current_seat +
          1
        }</strong> — ${
          seatData &&
          seatData.blind_mode
            ? "Blind Betting"
            : "choose an action"
        }.`
      );
    }
  }
}

/* ================================================================
   INITIAL WAGERS
   ================================================================ */

function placeInitialWager(
  seat,
  key
) {
  if (
    busy ||
    stateToken !== null
  ) {
    return;
  }

  /*
   * Every optional wager except:
   *
   * - Three Card Xtreme Pair Plus / Six Card Bonus
   *
   * requires the main Ante / Standard wager first.
   */

  if (
    key !== "ante" &&
    GAME !==
      "poker_three_card_xtreme"
  ) {
    const ante =
      Number(
        bets[
          `seat${seat}_ante`
        ] || 0
      );

    if (
      ante <= 0
    ) {
      showStatus(
        isPaiGow()
          ? "<strong>Place the Standard wager first.</strong>"
          : "<strong>Place the Ante first.</strong>"
      );

      return;
    }
  }

  let cost =
    selectedChip;

  /*
   * Ultimate Texas:
   * placing Ante automatically creates an equal Blind.
   */

  if (
    key === "ante" &&
    GAME ===
      "poker_ultimate_texas"
  ) {
    cost *= 2;
  }

  if (
    balance < cost
  ) {
    showStatus(
      "<strong>Not enough credits.</strong>"
    );

    return;
  }

  if (
    pendingTotal() +
      cost >
    MAX_BET
  ) {
    showStatus(
      `<strong>Maximum initial stake is ${fmt(
        MAX_BET
      )} credits.</strong>`
    );

    return;
  }

  const wagerKey =
    `seat${seat}_${key}`;

  bets[wagerKey] =
    (
      bets[wagerKey] ||
      0
    ) +
    selectedChip;

  if (
    key === "ante" &&
    GAME ===
      "poker_ultimate_texas"
  ) {
    const blindKey =
      `seat${seat}_blind`;

    bets[blindKey] =
      (
        bets[blindKey] ||
        0
      ) +
      selectedChip;
  }

  balance -=
    cost;

  saveBalance();

  renderSeats(
    currentState || {
      seats: {},
    }
  );

  refreshControls();
}

/* ================================================================
   CONTROLS
   ================================================================ */

function seatHasValidInitialBet(
  seat
) {
  const ante =
    Number(
      bets[
        `seat${seat}_ante`
      ] || 0
    );

  if (
    ante > 0
  ) {
    return true;
  }

  if (
    GAME ===
    "poker_three_card_xtreme"
  ) {
    return (
      Number(
        bets[
          `seat${seat}_pair_plus`
        ] || 0
      ) > 0 ||

      Number(
        bets[
          `seat${seat}_six_card_bonus`
        ] || 0
      ) > 0
    );
  }

  return false;
}

function refreshControls() {
  const pending =
    $("pending");

  if (pending) {
    pending.textContent =
      fmt(
        pendingTotal()
      );
  }

  const deal =
    $("deal");

  if (deal) {
    const valid =
      [0, 1, 2]
        .some(
          (seat) =>
            seatHasValidInitialBet(
              seat
            )
        );

    deal.disabled =
      busy ||
      stateToken !==
        null ||
      !valid;
  }

  const clear =
    $("clear");

  if (clear) {
    clear.disabled =
      busy ||
      stateToken !==
        null ||
      pendingTotal() <= 0;
  }
}

/* ================================================================
   ACTION LABELS
   ================================================================ */

function actionLabel(
  action
) {
  const labels = {
    fold: "Fold",
    play: "Play",
    check: "Check",

    flop:
      "Flop 2×",

    turn:
      "Turn 1×",

    river:
      "River 1×",

    play1:
      "Play 1×",

    play2:
      "Play 2×",

    play3:
      "Play 3×",

    play4:
      "Play 4×",

    bet1:
      "Bet 1×",

    bet2:
      "Bet 2×",

    bet3:
      "Bet 3×",

    set_hand:
      "Set Hand",

    houseway:
      "House Way",
  };

  return (
    labels[action] ||
    action
  );
}

/* ================================================================
   BUILD SERVER BETS
   ================================================================ */

function buildInitialBets() {
  const result = [];

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {
    if (
      !seatHasValidInitialBet(
        seat
      )
    ) {
      continue;
    }

    /*
     * Send every initial wager actually placed on this seat.
     */

    Object.entries(
      bets
    ).forEach(
      ([
        wagerType,
        amount,
      ]) => {
        if (
          !wagerType
            .startsWith(
              `seat${seat}_`
            )
        ) {
          return;
        }

        if (
          Number(amount) <= 0
        ) {
          return;
        }

        result.push({
          seat,

          wager_type:
            wagerType,

          amount:
            Number(amount),
        });
      }
    );
  }

  return result;
}

/* ================================================================
   DEAL
   ================================================================ */

async function dealRound() {
  if (
    busy ||
    stateToken !== null
  ) {
    return;
  }

  const serverBets =
    buildInitialBets();

  if (
    serverBets.length ===
    0
  ) {
    return;
  }

  busy = true;

  paiGowLowSelection = [];

  refreshControls();

  showStatus(
    "<strong>No more bets…</strong>"
  );

  try {
    const response =
      await fetch(
        "/api/solo/poker/deal",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              game: GAME,

              bets:
                serverBets,
            }),
        }
      );

    const data =
      await response.json();

    if (
      !response.ok
    ) {
      throw new Error(
        data.error ||
        `HTTP ${
          response.status
        }`
      );
    }

    stateToken =
      data.state_token;

    renderTable(
      data
    );

    busy = false;

    if (
      data.all_done
    ) {
      await settleRound();
    }

  } catch (error) {
    /*
     * Initial bets were already deducted locally.
     */

    balance +=
      pendingTotal();

    bets = {};

    paiGowLowSelection = [];

    saveBalance();

    showStatus(
      `<strong>Deal failed:</strong> ${
        error.message
      }`
    );

    busy = false;
  }

  refreshControls();
}

/* ================================================================
   GENERIC ACTION
   ================================================================ */

async function performAction(
  action
) {
  if (
    busy ||
    !stateToken ||
    !currentState
  ) {
    return;
  }

  /*
   * Manual Pai Gow setting has its own function because the backend
   * requires low_indices.
   */
  if (
    action === "set_hand"
  ) {
    await confirmPaiGowSet();
    return;
  }

  busy = true;

  try {
    const response =
      await fetch(
        "/api/solo/poker/action",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              state_token:
                stateToken,

              seat:
                currentState
                  .current_seat,

              action,
            }),
        }
      );

    const data =
      await response.json();

    if (
      !response.ok
    ) {
      throw new Error(
        data.error ||
        `HTTP ${
          response.status
        }`
      );
    }

    const extra =
      Number(
        data.extra_stake ||
        0
      );

    if (
      extra > balance
    ) {
      throw new Error(
        "Not enough credits for this action."
      );
    }

    balance -=
      extra;

    saveBalance();

    stateToken =
      data.state_token;

    renderTable(
      data
    );

    busy = false;

    if (
      data.all_done
    ) {
      await settleRound();
    }

  } catch (error) {
    showStatus(
      `<strong>Action failed:</strong> ${
        error.message
      }`
    );

    busy = false;
  }

  refreshControls();
}

/* ================================================================
   PAI GOW MANUAL SET ACTION
   ================================================================ */

async function confirmPaiGowSet() {
  if (
    busy ||
    !isPaiGow() ||
    !stateToken ||
    !currentState ||
    currentState.current_seat !==
      0
  ) {
    return;
  }

  if (
    paiGowLowSelection
      .length !== 2
  ) {
    showStatus(
      "<strong>Select exactly 2 cards for the Low Hand.</strong>"
    );

    return;
  }

  busy = true;

  try {
    const response =
      await fetch(
        "/api/solo/poker/action",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              state_token:
                stateToken,

              seat: 0,

              action:
                "set_hand",

              low_indices:
                [
                  ...paiGowLowSelection,
                ],
            }),
        }
      );

    const data =
      await response.json();

    if (
      !response.ok
    ) {
      throw new Error(
        data.error ||
        `HTTP ${
          response.status
        }`
      );
    }

    stateToken =
      data.state_token;

    paiGowLowSelection = [];

    renderTable(
      data
    );

    busy = false;

    if (
      data.all_done
    ) {
      await settleRound();
    }

  } catch (error) {
    showStatus(
      `<strong>Pai Gow set failed:</strong> ${
        error.message
      }`
    );

    busy = false;
  }

  refreshControls();
}

/* ================================================================
   HISTORY
   ================================================================ */

function addHistory(
  net
) {
  let history =
    JSON.parse(
      localStorage.getItem(
        HISTORY_KEY
      ) || "[]"
    );

  history.push(
    net
  );

  history =
    history.slice(-25);

  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(
      history
    )
  );

  renderHistory();
}

function renderHistory() {
  const area =
    $("history");

  if (!area) {
    return;
  }

  const history =
    JSON.parse(
      localStorage.getItem(
        HISTORY_KEY
      ) || "[]"
    );

  area.innerHTML =
    history
      .slice()
      .reverse()
      .map(
        (net) => {
          let cls =
            "push";

          if (
            net > 0
          ) {
            cls = "win";
          }

          if (
            net < 0
          ) {
            cls = "loss";
          }

          return `
            <span
              class="hist ${cls}"
            >
              ${
                net > 0
                  ? "+"
                  : ""
              }${fmt(net)}
            </span>
          `;
        }
      )
      .join("");
}

/* ================================================================
   SETTLEMENT
   ================================================================ */

async function settleRound() {
  if (
    busy ||
    !stateToken
  ) {
    return;
  }

  busy = true;

  showStatus(
    "<strong>Dealer resolving the round…</strong>"
  );

  try {
    const response =
      await fetch(
        "/api/solo/poker/settle",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              state_token:
                stateToken,
            }),
        }
      );

    const data =
      await response.json();

    if (
      !response.ok
    ) {
      throw new Error(
        data.error ||
        `HTTP ${
          response.status
        }`
      );
    }

    balance +=
      Number(
        data.total_return ||
        0
      );

    saveBalance();

    const finalState = {
      seats: {},

      community:
        data.outcome
          ?.community ||
        [],

      dealer_cards:
        data.outcome
          ?.dealer_cards ||
        [],

      current_seat:
        null,

      actions: [],
    };

    const outcomeSeats =
      data.outcome
        ?.seats ||
      {};

    for (
      const [
        seat,
        hand,
      ]
      of Object.entries(
        outcomeSeats
      )
    ) {
      finalState.seats[
        seat
      ] = {
        ...hand,

        cards:
          hand.cards ||
          [],

        card_count:
          (
            hand.cards ||
            []
          ).length,

        result:
          hand.result,
      };
    }

    renderTable(
      finalState
    );

    const net =
      Number(
        data.net ||
        0
      );

    addHistory(
      net
    );

    showStatus(
      `Round done — <strong>${
        net >= 0
          ? "+"
          : ""
      }${fmt(net)} cr</strong>`
    );

    bets = {};

    stateToken = null;

    paiGowLowSelection = [];

    currentState =
      finalState;

    busy = false;

    renderSeats(
      finalState
    );

    refreshControls();

  } catch (error) {
    showStatus(
      `<strong>Settlement failed:</strong> ${
        error.message
      }`
    );

    busy = false;

    refreshControls();
  }
}

/* ================================================================
   CLEAR
   ================================================================ */

function clearInitialBets() {
  if (
    busy ||
    stateToken !== null
  ) {
    return;
  }

  balance +=
    pendingTotal();

  bets = {};

  paiGowLowSelection = [];

  saveBalance();

  renderSeats(
    currentState || {
      seats: {},
    }
  );

  refreshControls();

  showStatus(
    "Initial wagers cleared."
  );
}

/* ================================================================
   RESET
   ================================================================ */

function resetCredits() {
  if (busy) {
    return;
  }

  const confirmed =
    window.confirm(
      `Reset credits to ${fmt(
        STARTING_CREDITS
      )}?`
    );

  if (!confirmed) {
    return;
  }

  balance =
    STARTING_CREDITS;

  bets = {};

  stateToken = null;

  currentState = null;

  paiGowLowSelection = [];

  localStorage.removeItem(
    BALANCE_KEY
  );

  localStorage.removeItem(
    HISTORY_KEY
  );

  saveBalance();

  renderHistory();

  renderTable();

  refreshControls();

  showStatus(
    `<strong>Credits reset to ${fmt(
      STARTING_CREDITS
    )}.</strong>`
  );
}

/* ================================================================
   RULES / PAY TABLE
   ================================================================ */

function renderRules() {
  const note =
    $("rulesNote");

  if (note) {
    note.textContent =
      CONFIG.note;
  }

  const pay =
    $("pay");

  if (pay) {
    pay.innerHTML =
      "<b>RULES / PAY TABLE</b>" +

      CONFIG.payTable
        .map(
          (row) => `
            <div class="pay-row">

              <span>
                ${row[0]}
              </span>

              <span>
                ${row[1]}
              </span>

            </div>
          `
        )
        .join("");
  }
}

/* ================================================================
   BUTTONS
   ================================================================ */

function bindButtons() {
  const deal =
    $("deal");

  const clear =
    $("clear");

  const reset =
    $("reset");

  if (deal) {
    deal.addEventListener(
      "click",
      dealRound
    );
  }

  if (clear) {
    clear.addEventListener(
      "click",
      clearInitialBets
    );
  }

  if (reset) {
    reset.addEventListener(
      "click",
      resetCredits
    );
  }
}

/* ================================================================
   INITIALISE
   ================================================================ */

function initPoker() {
  saveBalance();

  renderChips();

  renderRules();

  renderHistory();

  bindButtons();

  renderTable({
    seats: {},
    community: [],
    dealer_cards: [],
    current_seat:
      null,
    actions: [],
  });

  refreshControls();

  console.log(
    `Poker Solo ready: ${GAME}`
  );
}

if (
  document.readyState ===
  "loading"
) {
  document.addEventListener(
    "DOMContentLoaded",
    initPoker
  );
} else {
  initPoker();
}