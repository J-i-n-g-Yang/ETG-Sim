/* ================================================================
   ETG SIM — POKER SOLO

   Standardised ETG card-table frontend.

   Games:
   - Three Card Poker Xtreme
   - Singapore Stud Poker
   - Texas Hold'em Bonus
   - Ultimate Texas Hold'em
   - Mississippi Stud Poker
   - Fortune Pai Gow Poker

   Seat model:
   - Seat 1 = VIEWED
   - Seat 2 = BLIND
   - Seat 3 = BLIND

   API:
   - POST /api/solo/poker/deal
   - POST /api/solo/poker/action
   - POST /api/solo/poker/settle
   ================================================================ */


/* ================================================================
   CONFIG
   ================================================================ */

const GAME =
  window.POKER_GAME;

const MAX_BET =
  Number(
    window.POKER_MAX
  );

const STARTING_CREDITS =
  Number(
    window.POKER_START
  );


const $ = (id) =>
  document.getElementById(
    id
  );


const fmt = (value) =>
  Number(
    value || 0
  ).toLocaleString(
    undefined,
    {
      maximumFractionDigits: 1,
    }
  );


/* ================================================================
   CARD / CHIP CONSTANTS
   ================================================================ */

const SUITS = {
  S: "♠",
  H: "♥",
  D: "♦",
  C: "♣",
  X: "★",
};


const RED_SUITS =
  new Set([
    "H",
    "D",
  ]);


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

  100: {
    idle: [
      "#3a6080",
      "#1e3d55",
    ],

    bright:
      "#4a90d9",

    text:
      "#aaccee",
  },


  250: {
    idle: [
      "#3a5a30",
      "#1e3a14",
    ],

    bright:
      "#5aaa3a",

    text:
      "#88cc88",
  },


  500: {
    idle: [
      "#6a2a2a",
      "#3a0e0e",
    ],

    bright:
      "#d94040",

    text:
      "#ee9999",
  },


  1000: {
    idle: [
      "#404070",
      "#20204a",
    ],

    bright:
      "#7070d9",

    text:
      "#9999ee",
  },


  2500: {
    idle: [
      "#604010",
      "#3a2008",
    ],

    bright:
      "#c07020",

    text:
      "#ddaa77",
  },


  5000: {
    idle: [
      "#2a5a5a",
      "#0e3a3a",
    ],

    bright:
      "#30b0b0",

    text:
      "#88dddd",
  },


  10000: {
    idle: [
      "#5a2060",
      "#38103a",
    ],

    bright:
      "#aa40c0",

    text:
      "#cc88ee",
  },


  20000: {
    idle: [
      "#505020",
      "#303010",
    ],

    bright:
      "#c0a800",

    text:
      "#e8d060",
  },
};


/* ================================================================
   GAME CONFIGURATION
   ================================================================ */

const GAME_CONFIG = {


  /* ==============================================================
     THREE CARD POKER XTREME
     ============================================================== */

  poker_three_card_xtreme: {

    note:
      "Play = 1× Ante. Dealer qualifies Queen-high or better. " +
      "Pair Plus and Six Card Bonus remain in play after Fold. " +
      "Pair Plus and/or Six Card Bonus may be played without Ante. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards:
      3,

    communityCards:
      2,

    communityLabel:
      "COMMUNITY CARDS",

    allowSideOnly:
      true,

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


  /* ==============================================================
     SINGAPORE STUD
     ============================================================== */

  poker_singapore_stud: {

    note:
      "Bet = 2× Ante. Dealer qualifies with A-K high or better. " +
      "If Dealer does not qualify, Ante pays 1:1 and Bet pushes. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards:
      5,

    communityCards:
      0,

    communityLabel:
      "",

    allowSideOnly:
      false,

    sideBets:
      [],

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


  /* ==============================================================
     TEXAS HOLD'EM BONUS
     ============================================================== */

  poker_texas_bonus: {

    note:
      "Flop = 2× Ante. Turn and River are optional 1× Ante wagers. " +
      "A Player who folds loses Ante and Bonus. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards:
      2,

    communityCards:
      5,

    communityLabel:
      "COMMUNITY CARDS · FLOP / TURN / RIVER",

    allowSideOnly:
      false,

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


  /* ==============================================================
     ULTIMATE TEXAS HOLD'EM
     ============================================================== */

  poker_ultimate_texas: {

    note:
      "Ante and Blind must be equal. " +
      "Pre-flop Play = 3× or 4×; after Flop = 2×; River = 1×. " +
      "Dealer qualifies for Ante with Pair or better. " +
      "Trips remains independent of the Dealer result. " +
      "Progressive Jackpot system is currently unavailable.",

    dealerCards:
      2,

    communityCards:
      5,

    communityLabel:
      "COMMUNITY CARDS · FLOP / TURN / RIVER",

    allowSideOnly:
      false,

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


  /* ==============================================================
     MISSISSIPPI STUD
     ============================================================== */

  poker_mississippi: {

    note:
      "At 3rd, 4th and 5th Street choose Fold or wager " +
      "1×, 2× or 3× Ante. Progressive Jackpot is currently unavailable. " +
      "Three Card Bonus will be enabled after its PDF pay-table " +
      "image is separately verified.",

    dealerCards:
      0,

    communityCards:
      3,

    communityLabel:
      "COMMUNITY CARDS · 3RD / 4TH / 5TH STREET",

    allowSideOnly:
      false,

    sideBets:
      [],

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


  /* ==============================================================
     FORTUNE PAI GOW
     ============================================================== */

  poker_fortune_pai_gow: {

    note:
      "Seat 1 is viewed and may be manually set. Select exactly " +
      "2 cards for the Low Hand; the remaining 5 become the High Hand. " +
      "Seat 2, Seat 3 and Dealer use House Way. " +
      "A foul viewed hand is reset to House Way. " +
      "Standard wins pay 1:1 less 5% commission.",

    dealerCards:
      7,

    communityCards:
      0,

    communityLabel:
      "",

    allowSideOnly:
      false,

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
  GAME_CONFIG[
    GAME
  ];


if (!CONFIG) {
  throw new Error(
    `Unknown Poker game: ${GAME}`
  );
}


/* ================================================================
   STORAGE
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

let selectedChip =
  1000;

let bets =
  {};

let stateToken =
  null;

let busy =
  false;

let currentState =
  null;

let paiGowLowSelection =
  [];


/*
 * The accepted initial wager amount is kept separately after Deal.
 *
 * This lets the new sidebar continue showing the proper stake after
 * the pending betting chips are cleared.
 */

let roundInitialStake =
  0;

let roundExtraStake =
  0;


/* ================================================================
   PHASE
   ================================================================ */

function setPhase(
  text
) {
  const phase =
    $("phaseLabel");

  if (phase) {
    phase.textContent =
      text;
  }
}


/* ================================================================
   STATUS
   ================================================================ */

function showStatus(
  message
) {
  const element =
    $("status");

  if (element) {
    element.innerHTML =
      message;
  }
}


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


/* ================================================================
   BET HELPERS
   ================================================================ */

function pendingTotal() {

  return Object
    .values(
      bets
    )
    .reduce(
      (
        sum,
        amount
      ) =>
        sum +
        Number(
          amount
        ),
      0
    );
}


function seatPendingTotal(
  seat
) {

  const prefix =
    `seat${seat}_`;


  return Object
    .entries(
      bets
    )
    .filter(
      ([key]) =>
        key.startsWith(
          prefix
        )
    )
    .reduce(
      (
        total,
        [, amount]
      ) =>
        total +
        Number(
          amount
        ),
      0
    );
}


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


  /*
   * Three Card Poker explicitly permits Pair Plus and/or
   * Six Card Bonus without an Ante.
   */

  if (
    GAME ===
    "poker_three_card_xtreme"
  ) {

    return (
      Number(
        bets[
          `seat${seat}_pair_plus`
        ] || 0
      ) > 0
      ||
      Number(
        bets[
          `seat${seat}_six_card_bonus`
        ] || 0
      ) > 0
    );
  }


  return false;
}


function activeSeatCountFromBets() {

  let count =
    0;


  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    if (
      seatHasValidInitialBet(
        seat
      )
    ) {
      count++;
    }
  }


  return count;
}


function activeSeatCountFromState() {

  if (
    !currentState?.seats
  ) {
    return 0;
  }


  return Object
    .keys(
      currentState.seats
    )
    .length;
}


/* ================================================================
   METRICS
   ================================================================ */

function updateMetrics() {

  const activeMetric =
    $("activeMetric");

  const stakeMetric =
    $("stakeMetric");


  if (activeMetric) {

    activeMetric.textContent =
      String(
        stateToken
          ? activeSeatCountFromState()
          : activeSeatCountFromBets()
      );
  }


  if (stakeMetric) {

    if (
      stateToken
    ) {

      stakeMetric.textContent =
        fmt(
          roundInitialStake +
          roundExtraStake
        );

    } else if (
      roundInitialStake > 0 &&
      currentState?.settled
    ) {

      /*
       * Preserve completed-round metrics until a fresh wager
       * begins.
       */

    } else {

      stakeMetric.textContent =
        fmt(
          pendingTotal()
        );
    }
  }
}


/* ================================================================
   CHIP LABEL
   ================================================================ */

function chipLabel(
  value
) {

  if (
    value >= 1000
  ) {

    const thousands =
      value / 1000;


    return Number.isInteger(
      thousands
    )
      ? `${thousands}K`
      : `${thousands.toFixed(1)}K`;
  }


  return String(
    value
  );
}


/* ================================================================
   CHIP BAR
   ================================================================ */

function renderChips() {

  const container =
    $("chipBar");


  if (!container) {
    return;
  }


  container.innerHTML =
    "";


  CHIPS.forEach(
    (value) => {

      const style =
        CHIP_STYLE[
          value
        ];


      const active =
        value ===
        selectedChip;


      const outer =
        active
          ? style.bright
          : style.idle[0];


      const inner =
        style.idle[1];


      const sectors =
        `conic-gradient(
          ${outer} 0deg 30deg,
          ${inner} 30deg 60deg,
          ${outer} 60deg 90deg,
          ${inner} 90deg 120deg,
          ${outer} 120deg 150deg,
          ${inner} 150deg 180deg,
          ${outer} 180deg 210deg,
          ${inner} 210deg 240deg,
          ${outer} 240deg 270deg,
          ${inner} 270deg 300deg,
          ${outer} 300deg 330deg,
          ${inner} 330deg 360deg
        )`;


      const button =
        document.createElement(
          "button"
        );


      button.type =
        "button";


      button.className =
        active
          ? "chip active"
          : "chip";


      button.style.background =
        sectors;


      button.style.borderColor =
        active
          ? style.bright
          : style.idle[0];


      button.style.color =
        active
          ? "#fff"
          : style.text;


      button.style.boxShadow =
        active
          ? `0 0 16px ${style.bright}88, 0 2px 8px rgba(0,0,0,.4)`
          : "0 2px 8px rgba(0,0,0,.4)";


      button.textContent =
        chipLabel(
          value
        );


      button.addEventListener(
        "click",
        () => {

          if (
            busy ||
            stateToken
          ) {
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

  if (
    faceDown
  ) {

    return `
      <div
        class="
          card
          down
          ${extraClass}
        "
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


  const suit =
    SUITS[
      card.suit
    ] || "";


  return `
    <div
      class="
        card
        ${
          red
            ? "red"
            : ""
        }
        ${extraClass}
      "
      ${attributes}
    >

      <div>
        ${rank}
      </div>

      <div>
        ${suit}
      </div>

    </div>
  `;
}


function emptySlots(
  count
) {

  return Array(
    Math.max(
      0,
      count
    )
  )
    .fill(
      '<div class="card-slot"></div>'
    )
    .join("");
}


/* ================================================================
   GOLD WAGER BADGE
   Same convention as Dueling 8s / Blackjack.
   ================================================================ */

function wagerBadgeHTML(
  amount
) {

  amount =
    Number(
      amount || 0
    );


  if (
    amount <= 0
  ) {
    return "";
  }


  return `
    <span class="chip-stack">
      ${chipLabel(amount)}
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
    Number(
      bets[
        wagerKey
      ] || 0
    );


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

      <span>
        ${name}
      </span>

      ${
        wagerBadgeHTML(
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
    isPaiGow()
    &&
    seat === 0
    &&
    view.current_seat === 0
    &&
    seatData
    &&
    seatData.manual_set_allowed ===
      true
    &&
    Array.isArray(
      seatData.cards
    )
    &&
    seatData.cards.length ===
      7
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
      .indexOf(
        index
      );


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
    (a, b) =>
      a - b
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
      "The remaining five cards form the High Hand. " +
      "Press Confirm Set."
    );

  } else {

    const remaining =
      2 -
      paiGowLowSelection.length;


    showStatus(
      `<strong>Select ${remaining} more card${
        remaining === 1
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
    !Array.isArray(
      cards
    ) ||
    cards.length !==
      7
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
        lowSet.has(
          index
        )
    );


  const high =
    cards.filter(
      (
        _,
        index
      ) =>
        !lowSet.has(
          index
        )
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
          low
            .map(
              (card) =>
                cardHTML(
                  card
                )
            )
            .join("")
        }

        ${
          emptySlots(
            2 -
            low.length
          )
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
                cardHTML(
                  card
                )
            )
            .join("")
        }

        ${
          emptySlots(
            5 -
            high.length
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
        type="button"
        class="
          action
          primary
          paigow-confirm
        "
        ${
          ready
            ? ""
            : "disabled"
        }
      >
        Confirm Set
      </button>


      <button
        type="button"
        class="
          action
          secondary
          paigow-houseway
        "
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
                color:#ff9b9b;
                font-weight:900;
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
                cardHTML(
                  card
                )
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
                cardHTML(
                  card
                )
            )
            .join("")
        }
      </div>

    </div>
  `;
}


/* ================================================================
   ACTION LABELS
   ================================================================ */

function actionLabel(
  action
) {

  const labels = {

    fold:
      "FOLD",

    play:
      "PLAY",

    check:
      "CHECK",

    flop:
      "FLOP · 2×",

    turn:
      "TURN · 1×",

    river:
      "RIVER · 1×",

    play1:
      "PLAY · 1×",

    play2:
      "PLAY · 2×",

    play3:
      "PLAY · 3×",

    play4:
      "PLAY · 4×",

    bet1:
      "BET · 1×",

    bet2:
      "BET · 2×",

    bet3:
      "BET · 3×",

    set_hand:
      "SET HAND",

    houseway:
      "HOUSE WAY",
  };


  return (
    labels[
      action
    ] ||
    String(
      action
    ).toUpperCase()
  );
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


          let cardsHTML =
            "";


          if (
            seatData
          ) {

            if (
              Array.isArray(
                seatData.cards
              ) &&
              seatData.cards.length
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

                          `data-paigow-card="${index}"`
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
                    .card_count || 0
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


          let actionsHTML =
            "";


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

              const actions =
                (
                  view.actions ||
                  []
                )
                  .filter(
                    (action) =>
                      action !==
                      "set_hand"
                  );


              actionsHTML =
                actions.length
                  ? `
                    <div class="actions">

                      ${
                        actions
                          .map(
                            (action) => `
                              <button
                                type="button"

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
                  `
                  : "";
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


          const sideHTML =
            CONFIG
              .sideBets
              .map(
                (definition) =>
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
              .join("");


          const mainHTML =
            CONFIG
              .mainBets
              .map(
                (definition) =>
                  wagerHTML(
                    seat,
                    definition,
                    "rect"
                  )
              )
              .join("");


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
                        margin:8px 0 4px;
                        opacity:.8;
                      "
                    >
                      SELECT EXACTLY 2 CARDS FOR LOW HAND
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

                ${
                  CONFIG.sideBets.length
                    ? `
                      <div class="side-row">
                        ${sideHTML}
                      </div>
                    `
                    : ""
                }


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
                  ${mainHTML}
                </div>

              </div>


              ${
                seatData?.result
                  ? `
                    <div
                      style="
                        margin-top:8px;
                        color:#f4dc83;
                        font-family:system-ui,sans-serif;
                        font-size:12px;
                        font-weight:900;
                      "
                    >
                      ${
                        String(
                          seatData.result
                        ).toUpperCase()
                      }
                    </div>
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
     INITIAL WAGERS
     -------------------------------------------------------------- */

  container
    .querySelectorAll(
      ".wager[data-initial='1']"
    )
    .forEach(
      (element) => {

        element.addEventListener(
          "click",
          () => {

            placeInitialWager(
              Number(
                element.dataset.seat
              ),

              element.dataset.key
            );
          }
        );
      }
    );


  /* --------------------------------------------------------------
     ACTIONS
     -------------------------------------------------------------- */

  container
    .querySelectorAll(
      ".action[data-action]"
    )
    .forEach(
      (element) => {

        element.addEventListener(
          "click",
          () => {

            performAction(
              element.dataset.action
            );
          }
        );
      }
    );


  /* --------------------------------------------------------------
     PAI GOW CARD SELECTION
     -------------------------------------------------------------- */

  container
    .querySelectorAll(
      "[data-paigow-card]"
    )
    .forEach(
      (element) => {

        element.addEventListener(
          "click",
          () => {

            togglePaiGowLowCard(
              Number(
                element.dataset
                  .paigowCard
              )
            );
          }
        );
      }
    );


  /* --------------------------------------------------------------
     PAI GOW CONFIRM
     -------------------------------------------------------------- */

  const confirm =
    container.querySelector(
      ".paigow-confirm"
    );


  if (confirm) {

    confirm.addEventListener(
      "click",
      confirmPaiGowSet
    );
  }


  /* --------------------------------------------------------------
     PAI GOW HOUSE WAY
     -------------------------------------------------------------- */

  const houseWay =
    container.querySelector(
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


  if (
    isPaiGow() &&
    (
      view.current_seat !== 0 ||
      !view.seats?.["0"]
        ?.manual_set_allowed
    )
  ) {

    paiGowLowSelection =
      [];
  }


  /* --------------------------------------------------------------
     DEALER
     -------------------------------------------------------------- */

  const dealerTitle =
    $("dealerTitle");


  if (dealerTitle) {

    dealerTitle.textContent =
      CONFIG.dealerCards > 0
        ? `DEALER · ${
            CONFIG.dealerCards
          } CARD${
            CONFIG.dealerCards === 1
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
            cardHTML(
              card
            )
        )
        .join("")
      +
      emptySlots(
        CONFIG.dealerCards -
        dealerCards.length
      );
  }


  /* --------------------------------------------------------------
     COMMUNITY
     -------------------------------------------------------------- */

  const communityTitle =
    $("communityTitle");


  if (communityTitle) {

    communityTitle.textContent =
      CONFIG.communityLabel;
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
            cardHTML(
              card
            )
        )
        .join("")
      +
      emptySlots(
        CONFIG.communityCards -
        community.length
      );
  }


  renderSeats(
    view
  );


  updateMetrics();


  /* --------------------------------------------------------------
     STATUS / PHASE
     -------------------------------------------------------------- */

  if (
    view.current_seat !== null &&
    view.current_seat !== undefined
  ) {

    const seatData =
      view.seats?.[
        String(
          view.current_seat
        )
      ];


    if (
      isPaiGow() &&
      view.current_seat === 0 &&
      seatData
        ?.manual_set_allowed
    ) {

      setPhase(
        "SET HAND"
      );


      showStatus(
        "<strong>Seat 1 — set your Pai Gow hand.</strong> " +
        "Select exactly 2 cards for the Low Hand, then Confirm Set, " +
        "or choose House Way."
      );

    } else {

      setPhase(
        seatData?.blind_mode
          ? "BLIND PLAY"
          : "PLAYER TURN"
      );


      showStatus(
        `<strong>Seat ${
          view.current_seat + 1
        }</strong> — ${
          seatData?.blind_mode
            ? "Blind Betting"
            : "choose an action"
        }.`
      );
    }
  }
}


/* ================================================================
   PREPARE NEW BETTING ROUND
   ================================================================ */

function prepareNewBettingRound() {

  if (
    stateToken
  ) {
    return;
  }


  if (
    currentState?.settled
  ) {

    currentState =
      {
        seats: {},
        community: [],
        dealer_cards: [],
        current_seat: null,
        actions: [],
      };


    roundInitialStake =
      0;


    roundExtraStake =
      0;


    const returnMetric =
      $("returnMetric");


    if (returnMetric) {
      returnMetric.textContent =
        "0";
    }


    const netMetric =
      $("netMetric");


    if (netMetric) {

      netMetric.textContent =
        "0";


      netMetric.className =
        "metric-value";
    }


    renderTable(
      currentState
    );


    setPhase(
      "BETTING"
    );


    showStatus(
      "Place your initial wagers."
    );
  }
}


/* ================================================================
   PLACE INITIAL WAGER
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


  prepareNewBettingRound();


  /*
   * Every optional initial wager except the Three Card side wagers
   * requires the primary wager first.
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
   * Ultimate:
   * Ante automatically places the same amount on Blind.
   */

  if (
    key === "ante" &&
    GAME ===
      "poker_ultimate_texas"
  ) {

    cost *=
      2;
  }


  if (
    balance <
    cost
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


  bets[
    wagerKey
  ] =
    Number(
      bets[
        wagerKey
      ] || 0
    )
    +
    selectedChip;


  if (
    key === "ante" &&
    GAME ===
      "poker_ultimate_texas"
  ) {

    const blindKey =
      `seat${seat}_blind`;


    bets[
      blindKey
    ] =
      Number(
        bets[
          blindKey
        ] || 0
      )
      +
      selectedChip;
  }


  balance -=
    cost;


  saveBalance();


  renderSeats(
    currentState || {
      seats: {},
      current_seat: null,
      actions: [],
    }
  );


  updateMetrics();


  refreshControls();
}


/* ================================================================
   CONTROLS
   ================================================================ */

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
      stateToken !== null ||
      !valid;
  }


  const clear =
    $("clear");


  if (clear) {

    clear.disabled =
      busy ||
      stateToken !== null ||
      pendingTotal() <= 0;
  }


  updateMetrics();
}


/* ================================================================
   BUILD INITIAL SERVER BETS
   ================================================================ */

function buildInitialBets() {

  const result =
    [];


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


    const prefix =
      `seat${seat}_`;


    Object.entries(
      bets
    ).forEach(
      ([
        wagerType,
        amount,
      ]) => {

        if (
          !wagerType.startsWith(
            prefix
          )
        ) {
          return;
        }


        if (
          Number(
            amount
          ) <= 0
        ) {
          return;
        }


        result.push({
          seat,

          wager_type:
            wagerType,

          amount:
            Number(
              amount
            ),
        });
      }
    );
  }


  return result;
}


/* ================================================================
   DEAL ROUND
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
    !serverBets.length
  ) {

    showStatus(
      "<strong>Place a valid wager first.</strong>"
    );

    return;
  }


  const acceptedStake =
    pendingTotal();


  busy =
    true;


  paiGowLowSelection =
    [];


  setPhase(
    "DEALING"
  );


  showStatus(
    "<strong>No more bets — dealing…</strong>"
  );


  refreshControls();


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
              game:
                GAME,

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
        `HTTP ${response.status}`
      );
    }


    roundInitialStake =
      Number(
        data.total_wager ??
        acceptedStake
      );


    roundExtraStake =
      0;


    stateToken =
      data.state_token;


    /*
     * The accepted betting chips no longer need to remain in the
     * local pending-bet object.
     */

    bets =
      {};


    renderTable(
      data
    );


    busy =
      false;


    refreshControls();


    if (
      data.all_done
    ) {

      await settleRound();
    }


  } catch (error) {

    /*
     * Deal failed. The chips had only been deducted locally, so
     * refund the pending amount.
     */

    balance +=
      acceptedStake;


    bets =
      {};


    roundInitialStake =
      0;


    roundExtraStake =
      0;


    stateToken =
      null;


    paiGowLowSelection =
      [];


    saveBalance();


    setPhase(
      "BETTING"
    );


    showStatus(
      `<strong>Deal failed:</strong> ${
        error.message
      }`
    );


    busy =
      false;


    renderSeats({
      seats: {},
      current_seat: null,
      actions: [],
    });


    refreshControls();
  }
}


/* ================================================================
   PERFORM ACTION
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


  if (
    action ===
    "set_hand"
  ) {

    await confirmPaiGowSet();

    return;
  }


  busy =
    true;


  setPhase(
    "ACTION"
  );


  showStatus(
    `<strong>${actionLabel(
      action
    )}</strong>…`
  );


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
        `HTTP ${response.status}`
      );
    }


    const extra =
      Number(
        data.extra_stake || 0
      );


    /*
     * This should normally be caught before the action is sent,
     * but the backend remains authoritative.
     */

    if (
      extra >
      balance
    ) {

      throw new Error(
        "Not enough credits for this action."
      );
    }


    if (
      extra > 0
    ) {

      balance -=
        extra;


      roundExtraStake +=
        extra;


      saveBalance();
    }


    stateToken =
      data.state_token;


    renderTable(
      data
    );


    busy =
      false;


    refreshControls();


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


    busy =
      false;


    if (
      currentState?.current_seat !==
        null &&
      currentState?.current_seat !==
        undefined
    ) {

      setPhase(
        "PLAYER TURN"
      );
    }


    refreshControls();
  }
}


/* ================================================================
   PAI GOW CONFIRM SET
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


  busy =
    true;


  setPhase(
    "SET HAND"
  );


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
                0,

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
        `HTTP ${response.status}`
      );
    }


    stateToken =
      data.state_token;


    paiGowLowSelection =
      [];


    renderTable(
      data
    );


    busy =
      false;


    refreshControls();


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


    setPhase(
      "SET HAND"
    );


    busy =
      false;


    refreshControls();
  }
}


/* ================================================================
   HISTORY
   ================================================================ */

function loadHistory() {

  try {

    const parsed =
      JSON.parse(
        localStorage.getItem(
          HISTORY_KEY
        ) ||
        "[]"
      );


    return Array.isArray(
      parsed
    )
      ? parsed
      : [];


  } catch {

    return [];
  }
}


function addHistory(
  net
) {

  let history =
    loadHistory();


  history.push(
    Number(
      net
    )
  );


  history =
    history.slice(
      -25
    );


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
    loadHistory();


  if (
    !history.length
  ) {

    area.innerHTML =
      "<span style='opacity:.7'>No rounds yet</span>";

    return;
  }


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
            cls =
              "win";
          }


          if (
            net < 0
          ) {
            cls =
              "loss";
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


  busy =
    true;


  setPhase(
    "DEALER"
  );


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
        `HTTP ${response.status}`
      );
    }


    const totalReturn =
      Number(
        data.total_return || 0
      );


    balance +=
      totalReturn;


    saveBalance();


    const finalState = {

      seats:
        {},

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

      actions:
        [],

      settled:
        true,
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


    currentState =
      finalState;


    stateToken =
      null;


    paiGowLowSelection =
      [];


    renderTable(
      finalState
    );


    const totalWager =
      Number(
        data.total_wager ??
        (
          roundInitialStake +
          roundExtraStake
        )
      );


    const net =
      Number(
        data.net || 0
      );


    /*
     * Metrics.
     */

    const stakeMetric =
      $("stakeMetric");


    if (
      stakeMetric
    ) {

      stakeMetric.textContent =
        fmt(
          totalWager
        );
    }


    const returnMetric =
      $("returnMetric");


    if (
      returnMetric
    ) {

      returnMetric.textContent =
        fmt(
          totalReturn
        );
    }


    const netMetric =
      $("netMetric");


    if (
      netMetric
    ) {

      netMetric.textContent =
        `${
          net > 0
            ? "+"
            : ""
        }${fmt(net)}`;


      netMetric.className =
        net > 0
          ? "metric-value win"
          : net < 0
            ? "metric-value lose"
            : "metric-value push";
    }


    const activeMetric =
      $("activeMetric");


    if (
      activeMetric
    ) {

      activeMetric.textContent =
        String(
          Object.keys(
            finalState.seats
          ).length
        );
    }


    addHistory(
      net
    );


    setPhase(
      "COMPLETE"
    );


    showStatus(
      net > 0
        ? `Round complete — <strong>+${fmt(
            net
          )} cr</strong>`
        : net < 0
          ? `Round complete — <strong>${fmt(
              net
            )} cr</strong>`
          : "Round complete — <strong>Push</strong>"
    );


    bets =
      {};


    busy =
      false;


    refreshControls();


  } catch (error) {

    showStatus(
      `<strong>Settlement failed:</strong> ${
        error.message
      }`
    );


    setPhase(
      "ERROR"
    );


    busy =
      false;


    refreshControls();
  }
}


/* ================================================================
   CLEAR INITIAL BETS
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


  bets =
    {};


  paiGowLowSelection =
    [];


  saveBalance();


  renderSeats(
    currentState || {
      seats: {},
      current_seat: null,
      actions: [],
    }
  );


  updateMetrics();


  refreshControls();


  showStatus(
    "Initial wagers cleared."
  );
}


/* ================================================================
   RESET
   ================================================================ */

function resetCredits() {

  if (
    busy
  ) {
    return;
  }


  const confirmed =
    window.confirm(
      `Reset credits to ${fmt(
        STARTING_CREDITS
      )}?`
    );


  if (
    !confirmed
  ) {
    return;
  }


  balance =
    STARTING_CREDITS;


  bets =
    {};


  stateToken =
    null;


  currentState =
    null;


  paiGowLowSelection =
    [];


  roundInitialStake =
    0;


  roundExtraStake =
    0;


  localStorage.removeItem(
    BALANCE_KEY
  );


  localStorage.removeItem(
    HISTORY_KEY
  );


  saveBalance();


  renderHistory();


  renderTable({
    seats: {},
    community: [],
    dealer_cards: [],
    current_seat: null,
    actions: [],
  });


  const activeMetric =
    $("activeMetric");


  if (
    activeMetric
  ) {
    activeMetric.textContent =
      "0";
  }


  const stakeMetric =
    $("stakeMetric");


  if (
    stakeMetric
  ) {
    stakeMetric.textContent =
      "0";
  }


  const returnMetric =
    $("returnMetric");


  if (
    returnMetric
  ) {
    returnMetric.textContent =
      "0";
  }


  const netMetric =
    $("netMetric");


  if (
    netMetric
  ) {

    netMetric.textContent =
      "0";


    netMetric.className =
      "metric-value";
  }


  setPhase(
    "BETTING"
  );


  refreshControls();


  showStatus(
    `<strong>Credits reset to ${fmt(
      STARTING_CREDITS
    )}.</strong>`
  );
}


/* ================================================================
   RULES
   ================================================================ */

function renderRules() {

  const note =
    $("rulesNote");


  if (
    note
  ) {

    note.textContent =
      CONFIG.note;
  }


  const pay =
    $("pay");


  if (
    pay
  ) {

    pay.innerHTML =
      CONFIG
        .payTable
        .map(
          (
            [
              name,
              payout,
            ]
          ) => `
            <div class="pay-row">

              <span>
                ${name}
              </span>

              <span>
                ${payout}
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


  if (
    deal
  ) {

    deal.addEventListener(
      "click",
      dealRound
    );
  }


  if (
    clear
  ) {

    clear.addEventListener(
      "click",
      clearInitialBets
    );
  }


  if (
    reset
  ) {

    reset.addEventListener(
      "click",
      resetCredits
    );
  }
}


/* ================================================================
   DOM CHECK
   ================================================================ */

function verifyDOM() {

  const required =
    [
      "phaseLabel",
      "balance",
      "chipBar",
      "reset",
      "activeMetric",
      "stakeMetric",
      "returnMetric",
      "netMetric",
      "history",
      "status",
      "dealerTitle",
      "dealerCards",
      "communityTitle",
      "community",
      "seats",
      "pending",
      "clear",
      "deal",
      "rulesNote",
      "pay",
    ];


  const missing =
    required.filter(
      (id) =>
        !$(id)
    );


  if (
    missing.length
  ) {

    throw new Error(
      `Poker HTML/JS mismatch. Missing: ${
        missing.join(
          ", "
        )
      }`
    );
  }
}


/* ================================================================
   INITIALISE
   ================================================================ */

function initPoker() {

  try {

    verifyDOM();


    saveBalance();


    renderChips();


    renderRules();


    renderHistory();


    bindButtons();


    currentState = {
      seats: {},
      community: [],
      dealer_cards: [],
      current_seat: null,
      actions: [],
    };


    renderTable(
      currentState
    );


    $("activeMetric")
      .textContent =
        "0";


    $("stakeMetric")
      .textContent =
        "0";


    $("returnMetric")
      .textContent =
        "0";


    $("netMetric")
      .textContent =
        "0";


    setPhase(
      "BETTING"
    );


    showStatus(
      "Place your initial wagers. " +
      "Seat 1 is viewed; Seats 2–3 follow Blind Betting / House Way."
    );


    refreshControls();


    console.log(
      "[POKER]",
      "Frontend initialised:",
      GAME
    );


  } catch (error) {

    console.error(
      "[POKER INIT ERROR]",
      error
    );


    const status =
      $("status");


    if (
      status
    ) {

      status.innerHTML =
        `<strong>POKER FRONTEND ERROR:</strong> ${
          error.message
        }`;
    }


    setPhase(
      "ERROR"
    );
  }
}


/* ================================================================
   START
   ================================================================ */

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