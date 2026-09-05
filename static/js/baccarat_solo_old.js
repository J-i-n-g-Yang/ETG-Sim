/* ================================================================
   baccarat_solo.js
   Dedicated Solo Baccarat UI

   IMPORTANT:
   This file intentionally has NO imports.
   It does not depend on boards.js, solo.js, api.js, or animations.js.
   ================================================================ */

const GAME = window.BACCARAT_GAME;
const MAX_BET = Number(window.BACCARAT_MAX);
const STARTING_CREDITS = Number(window.BACCARAT_START);

const $ = (id) => document.getElementById(id);

const fmt = (value) =>
  Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 1,
  });

const sleep = (ms) =>
  new Promise((resolve) => setTimeout(resolve, ms));

/* ================================================================
   VARIANT CONFIGURATION
   ================================================================ */

const VARIANTS = {
  baccarat_dragon_tiger: {
    payTable: [
      ["Player", "1:1"],
      ["Banker on 6", "1:2"],
      ["Banker otherwise", "1:1"],
      ["Tie", "8:1"],
      ["Dragon Tiger", "30 / 40 / 100:1"],
      ["Small Dragon", "15:1"],
      ["Big Dragon", "30:1"],
      ["Small Tiger", "22:1"],
      ["Big Tiger", "50:1"],
      ["Tiger Tie", "35:1"],
    ],
  },

  baccarat_immortal: {
    payTable: [
      ["Player win on 7", "1:2"],
      ["Player 7 loses to Banker 8/9", "Push"],
      ["Player other win", "1:1"],
      ["Banker on 6", "1:2"],
      ["Banker otherwise", "1:1"],
      ["Tie", "8:1"],
      ["Player Pair", "11:1"],
      ["Banker Pair", "11:1"],
      ["Immortal Dragon", "25:1"],
      ["Dragon Tiger", "30 / 40 / 100:1"],
      ["Small Dragon", "15:1"],
      ["Big Dragon", "30:1"],
      ["Small Tiger", "22:1"],
      ["Big Tiger", "50:1"],
      ["Tiger Tie", "35:1"],
    ],
  },

  baccarat_rising: {
    payTable: [
      ["Player", "1:1"],
      ["Banker on 6", "1:2"],
      ["Banker otherwise", "1:1"],
      ["Tie", "8:1"],
      ["Dragon Tiger", "30 / 40 / 100:1"],
      ["Small Dragon", "15:1"],
      ["Big Dragon", "30:1"],
      ["Small Tiger", "22:1"],
      ["Big Tiger", "50:1"],
      ["Tiger Tie", "35:1"],
      ["Rising Dragon — 4 cards", "4:1"],
      ["Rising Dragon — 5 cards", "6:1"],
      ["Rising Dragon — 6 cards", "4.5:1"],
      ["Rising Tiger — 4 cards", "4:1"],
      ["Rising Tiger — 5 cards", "4.5:1"],
      ["Rising Tiger — 6 cards", "5.5:1"],
    ],
  },
};

const CONFIG = VARIANTS[GAME];

if (!CONFIG) {
  console.error("Unknown Baccarat variant:", GAME);
}

/* ================================================================
   CHIP CONFIGURATION

   Self-contained replacement for boards.js.
   ================================================================ */

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

const CHIP_COLORS = {
  100: {
    idle: ["#3a6080", "#1e3d55"],
    bright: "#4a90d9",
    text: "#aaccee",
  },

  250: {
    idle: ["#3a5a30", "#1e3a14"],
    bright: "#5aaa3a",
    text: "#88cc88",
  },

  500: {
    idle: ["#6a2a2a", "#3a0e0e"],
    bright: "#d94040",
    text: "#ee9999",
  },

  1000: {
    idle: ["#404070", "#20204a"],
    bright: "#7070d9",
    text: "#9999ee",
  },

  2500: {
    idle: ["#604010", "#3a2008"],
    bright: "#c07020",
    text: "#ddaa77",
  },

  5000: {
    idle: ["#2a5a5a", "#0e3a3a"],
    bright: "#30b0b0",
    text: "#88dddd",
  },

  10000: {
    idle: ["#5a2060", "#38103a"],
    bright: "#aa40c0",
    text: "#cc88ee",
  },

  20000: {
    idle: ["#505020", "#303010"],
    bright: "#c0a800",
    text: "#e8d060",
  },
};

function chipLabel(value) {
  if (value >= 1000) {
    return `${value / 1000}K`;
  }

  return String(value);
}

function chipGradient(value, active = false) {
  const color =
    CHIP_COLORS[value] ||
    CHIP_COLORS[100];

  const bright =
    active
      ? color.bright
      : color.idle[0];

  const dark =
    color.idle[1];

  return `
    conic-gradient(
      ${bright} 0deg 30deg,
      ${dark} 30deg 60deg,
      ${bright} 60deg 90deg,
      ${dark} 90deg 120deg,
      ${bright} 120deg 150deg,
      ${dark} 150deg 180deg,
      ${bright} 180deg 210deg,
      ${dark} 210deg 240deg,
      ${bright} 240deg 270deg,
      ${dark} 270deg 300deg,
      ${bright} 300deg 330deg,
      ${dark} 330deg 360deg
    )
  `;
}

/* ================================================================
   STATE
   ================================================================ */

const BALANCE_KEY =
  `etg_bacc_balance_${GAME}`;

const HISTORY_KEY =
  `etg_bacc_history_${GAME}`;

let balance = parseFloat(
  localStorage.getItem(BALANCE_KEY) ??
  String(STARTING_CREDITS)
);

if (!Number.isFinite(balance)) {
  balance = STARTING_CREDITS;
}

let selectedChip = 1000;

let pendingBets = {};

let dealing = false;

/* ================================================================
   BALANCE
   ================================================================ */

function saveBalance() {
  localStorage.setItem(
    BALANCE_KEY,
    String(balance)
  );

  const element =
    $("balanceDisplay");

  if (element) {
    element.textContent =
      fmt(balance);
  }
}

function pendingTotal() {
  return Object.values(
    pendingBets
  ).reduce(
    (sum, amount) =>
      sum + Number(amount),
    0
  );
}

/* ================================================================
   STATUS
   ================================================================ */

function showStatus(
  message,
  type = ""
) {
  const bar =
    $("statusBar");

  if (!bar) {
    return;
  }

  bar.className =
    `status ${type}`;

  bar.innerHTML =
    message;
}

/* ================================================================
   CHIP BAR
   ================================================================ */

function renderChipBar() {
  const container =
    $("chipBar");

  if (!container) {
    console.error(
      "chipBar element not found"
    );

    return;
  }

  container.innerHTML = "";

  CHIPS.forEach((value) => {
    const active =
      value === selectedChip;

    const color =
      CHIP_COLORS[value];

    const chip =
      document.createElement("div");

    chip.className =
      `chip${active ? " active" : ""}`;

    chip.textContent =
      chipLabel(value);

    chip.style.background =
      chipGradient(
        value,
        active
      );

    chip.style.borderColor =
      active
        ? color.bright
        : color.idle[0];

    chip.style.color =
      active
        ? "#ffffff"
        : color.text;

    chip.style.boxShadow =
      active
        ? `0 0 16px ${color.bright}88,
           0 2px 8px rgba(0,0,0,0.4)`
        : "0 2px 8px rgba(0,0,0,0.4)";

    chip.addEventListener(
      "click",
      () => {
        if (dealing) {
          return;
        }

        selectedChip =
          value;

        renderChipBar();
      }
    );

    container.appendChild(
      chip
    );
  });
}

/* ================================================================
   CHIP STACKS ON TABLE
   ================================================================ */

function chipStackHTML(
  totalAmount
) {
  if (
    !totalAmount ||
    totalAmount <= 0
  ) {
    return "";
  }

  const denomOrder = [
    20000,
    10000,
    5000,
    2500,
    1000,
    500,
    250,
    100,
  ];

  const discs = [];

  let remaining =
    totalAmount;

  for (
    const denomination
    of denomOrder
  ) {
    while (
      remaining >= denomination &&
      discs.length < 5
    ) {
      discs.push(
        denomination
      );

      remaining -=
        denomination;
    }

    if (
      discs.length >= 5
    ) {
      break;
    }
  }

  if (
    discs.length === 0
  ) {
    discs.push(100);
  }

  const totalLabel =
    totalAmount >= 1000
      ? (
          totalAmount / 1000
        ).toLocaleString(
          undefined,
          {
            maximumFractionDigits: 1,
          }
        ) + "K"
      : String(totalAmount);

  const discsHTML =
    discs
      .map((value) => {
        const color =
          CHIP_COLORS[value] ||
          CHIP_COLORS[100];

        return `
          <div
            class="cstack-chip"
            style="
              background:${chipGradient(value)};
              border-color:${color.idle[0]};
            "
          >
            ${chipLabel(value)}
          </div>
        `;
      })
      .join("");

  return `
    <div class="chip-stack">
      <span class="cstack-total">
        ${totalLabel}
      </span>

      ${discsHTML}
    </div>
  `;
}

/* ================================================================
   VARIANT VISIBILITY
   ================================================================ */

function configureVariant() {
  /*
   * HTML already hides variant
   * wagers by default.
   *
   * We reinforce it here.
   */

  document
    .querySelectorAll(
      ".variant"
    )
    .forEach((element) => {
      element.style.display =
        "none";
    });

  if (
    GAME ===
    "baccarat_immortal"
  ) {
    document
      .querySelectorAll(
        ".immortal-only"
      )
      .forEach(
        (element) => {
          element.style.display =
            "flex";
        }
      );

    /*
     * MBS Immortal Dragon Tiger No Commission Baccarat V3:
     *
     * - A winning Player hand with 7 pays 1:2.
     * - If Player finishes on 7 and loses to Banker 8 or 9,
     *   the Player wager is a Push.
     *
     * The backend already implements this. This text makes the
     * betting-table UI accurately describe the same rule.
     */
    const playerOdds =
      $("playerOdds");

    if (playerOdds) {
      playerOdds.textContent =
        "PAYS 1 TO 1 · 1 TO 2 ON PLAYER WIN WITH 7 · PLAYER 7 VS BANKER 8/9 PUSHES";
    }
  }

  if (
    GAME ===
    "baccarat_rising"
  ) {
    document
      .querySelectorAll(
        ".rising-only"
      )
      .forEach(
        (element) => {
          element.style.display =
            "flex";
        }
      );
  }

  /*
   * Add betting events to every
   * currently legal/visible wager.
   */

  document
    .querySelectorAll(
      "#wagerGrid [data-wager]"
    )
    .forEach((element) => {
      const hidden =
        window
          .getComputedStyle(
            element
          )
          .display === "none";

      if (hidden) {
        return;
      }

      element.addEventListener(
        "click",
        () => {
          placeBet(
            element.dataset.wager
          );
        }
      );
    });
}

/* ================================================================
   BET PLACEMENT
   ================================================================ */

function placeBet(
  wagerType
) {
  if (dealing) {
    return;
  }

  if (
    balance <
    selectedChip
  ) {
    showStatus(
      "<strong>Not enough credits</strong>",
      "bad"
    );

    return;
  }

  const newTotal =
    pendingTotal() +
    selectedChip;

  if (
    newTotal >
    MAX_BET
  ) {
    showStatus(
      `<strong>Maximum deal stake reached</strong> — ${fmt(
        MAX_BET
      )} credits.`,
      "bad"
    );

    return;
  }

  pendingBets[
    wagerType
  ] =
    (
      pendingBets[
        wagerType
      ] || 0
    ) +
    selectedChip;

  balance -=
    selectedChip;

  saveBalance();

  refreshBets();

  showStatus(
    `<strong>Bet placed</strong> — ${fmt(
      selectedChip
    )} on ${wagerType.replaceAll(
      "_",
      " "
    )}.`,
    "good"
  );
}

/* ================================================================
   REFRESH BETS
   ================================================================ */

function refreshBets() {
  const total =
    pendingTotal();

  const pending =
    $("pendingTotal");

  if (pending) {
    pending.textContent =
      fmt(total);
  }

  const deal =
    $("dealBtn");

  if (deal) {
    deal.disabled =
      dealing ||
      total <= 0;
  }

  const clear =
    $("clearBtn");

  if (clear) {
    clear.disabled =
      dealing ||
      total <= 0;
  }

  document
    .querySelectorAll(
      "#wagerGrid [data-wager]"
    )
    .forEach((spot) => {
      spot
        .querySelectorAll(
          ".chip-stack"
        )
        .forEach(
          (stack) =>
            stack.remove()
        );

      const amount =
        pendingBets[
          spot.dataset.wager
        ] || 0;

      if (
        amount > 0
      ) {
        spot.insertAdjacentHTML(
          "beforeend",
          chipStackHTML(
            amount
          )
        );
      }
    });
}

/* ================================================================
   BACCARAT CARD VALUES
   ================================================================ */

function cardValue(rank) {
  if (rank === "A") {
    return 1;
  }

  if (
    [
      "10",
      "J",
      "Q",
      "K",
    ].includes(rank)
  ) {
    return 0;
  }

  return Number(rank);
}

function handTotal(cards) {
  return (
    cards.reduce(
      (sum, card) =>
        sum +
        cardValue(
          card.rank
        ),
      0
    ) % 10
  );
}

const SUITS = {
  S: "♠",
  H: "♥",
  D: "♦",
  C: "♣",
};

const RED_SUITS =
  new Set([
    "H",
    "D",
  ]);

function cardHTML(card) {
  return `
    <div
      class="card ${
        RED_SUITS.has(
          card.suit
        )
          ? "red"
          : ""
      }"
    >
      <div class="rank">
        ${card.rank}
      </div>

      <div class="suit">
        ${
          SUITS[
            card.suit
          ] ||
          card.suit
        }
      </div>
    </div>
  `;
}

/* ================================================================
   CLEAR TABLE
   ================================================================ */

function clearCards() {
  const p =
    $("playerCards");

  const b =
    $("bankerCards");

  if (p) {
    p.innerHTML = "";
  }

  if (b) {
    b.innerHTML = "";
  }

  if ($("playerScore")) {
    $("playerScore")
      .textContent = "—";
  }

  if ($("bankerScore")) {
    $("bankerScore")
      .textContent = "—";
  }

  const winner =
    $("winner");

  if (winner) {
    winner.textContent = "";
    winner.className =
      "winner";
  }

  const breakdown =
    $("breakdown");

  if (breakdown) {
    breakdown.innerHTML =
      "";
  }
}

/* ================================================================
   DEAL ONE CARD
   ================================================================ */

async function addCard(
  card,
  side,
  shownCards
) {
  const player =
    side === "player";

  const container = $(
    player
      ? "playerCards"
      : "bankerCards"
  );

  if (!container) {
    return;
  }

  container.insertAdjacentHTML(
    "beforeend",
    cardHTML(card)
  );

  const element =
    container.lastElementChild;

  if (element) {
    element.classList.add(
      "deal-in"
    );
  }

  shownCards.push(
    card
  );

  const total =
    handTotal(
      shownCards
    );

  const score = $(
    player
      ? "playerScore"
      : "bankerScore"
  );

  if (score) {
    score.textContent =
      total;
  }

  await sleep(480);
}

/* ================================================================
   DEALING ANIMATION
   ================================================================ */

async function animateOutcome(
  outcome
) {
  clearCards();

  const playerCards =
    outcome.player_cards ||
    [];

  const bankerCards =
    outcome.banker_cards ||
    [];

  const shownPlayer = [];
  const shownBanker = [];

  /*
   * Initial deal:
   *
   * P → B → P → B
   */

  if (playerCards[0]) {
    await addCard(
      playerCards[0],
      "player",
      shownPlayer
    );
  }

  if (bankerCards[0]) {
    await addCard(
      bankerCards[0],
      "banker",
      shownBanker
    );
  }

  if (playerCards[1]) {
    await addCard(
      playerCards[1],
      "player",
      shownPlayer
    );
  }

  if (bankerCards[1]) {
    await addCard(
      bankerCards[1],
      "banker",
      shownBanker
    );
  }

  /*
   * Third cards.
   */

  if (playerCards[2]) {
    await addCard(
      playerCards[2],
      "player",
      shownPlayer
    );
  }

  if (bankerCards[2]) {
    await addCard(
      bankerCards[2],
      "banker",
      shownBanker
    );
  }

  await sleep(200);

  const winner =
    $("winner");

  if (winner) {
    winner.textContent =
      outcome.winner
        .toUpperCase();

    winner.className =
      `winner ${outcome.winner}`;
  }

  await sleep(350);
}

/* ================================================================
   PAY TABLE
   ================================================================ */

function renderPayTable() {
  const area =
    $("payTable");

  if (
    !area ||
    !CONFIG
  ) {
    return;
  }

  area.innerHTML =
    "<b>Pay Table</b>" +
    CONFIG.payTable
      .map(
        ([label, odds]) => `
          <div class="prow">
            <span>
              ${label}
            </span>

            <span class="odds">
              ${odds}
            </span>
          </div>
        `
      )
      .join("");
}

/* ================================================================
   HISTORY
   ================================================================ */

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
        (winner) => `
          <span
            class="hb ${winner}"
          >
            ${winner
              .charAt(0)
              .toUpperCase()}
          </span>
        `
      )
      .join("");
}

function addHistory(
  outcome
) {
  let history =
    JSON.parse(
      localStorage.getItem(
        HISTORY_KEY
      ) || "[]"
    );

  history.push(
    outcome.winner
  );

  history =
    history.slice(-30);

  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(
      history
    )
  );

  renderHistory();
}

/* ================================================================
   RESULT BREAKDOWN
   ================================================================ */

function renderBreakdown(
  response
) {
  const area =
    $("breakdown");

  if (!area) {
    return;
  }

  area.innerHTML =
    response.results
      .map((result) => {
        const net =
          Number(
            result.return
          ) -
          Number(
            result.amount
          );

        let color =
          "#94a3b8";

        if (net > 0) {
          color =
            "#4ade80";
        }

        if (net < 0) {
          color =
            "#f87171";
        }

        return `
          <div class="br">
            <span>
              ${result.wager_type.replaceAll(
                "_",
                " "
              )}
            </span>

            <b
              style="color:${color}"
            >
              ${
                net >= 0
                  ? "+"
                  : ""
              }${fmt(net)}
            </b>
          </div>
        `;
      })
      .join("");
}

/* ================================================================
   DEAL ROUND
   ================================================================ */

async function dealRound() {
  const total =
    pendingTotal();

  if (
    dealing ||
    total <= 0
  ) {
    return;
  }

  dealing = true;

  refreshBets();

  showStatus(
    "<strong>No more bets…</strong>",
    "warn"
  );

  const betsForServer =
    Object.entries(
      pendingBets
    ).map(
      ([
        wager_type,
        amount,
      ]) => ({
        wager_type,
        amount,
      })
    );

  try {
    const response =
      await fetch(
        "/api/solo/spin",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              game: GAME,
              bets:
                betsForServer,
            }),
        }
      );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.error ||
        `HTTP ${response.status}`
      );
    }

    await animateOutcome(
      data.outcome
    );

    /*
     * Bets were already deducted
     * when placed.
     *
     * Server return includes
     * returned stake + winnings.
     */

    balance +=
      Number(
        data.total_return
      );

    saveBalance();

    addHistory(
      data.outcome
    );

    renderBreakdown(
      data
    );

    const net =
      Number(
        data.net
      );

    showStatus(
      `Round done — <strong>${
        net >= 0
          ? "+"
          : ""
      }${fmt(net)} cr</strong>`,
      net >= 0
        ? "good"
        : "bad"
    );

    pendingBets = {};
  } catch (error) {
    /*
     * Bets were deducted locally
     * while they were being placed.
     * If the server fails before
     * settlement, refund them.
     */

    balance +=
      pendingTotal();

    pendingBets = {};

    saveBalance();

    showStatus(
      `<strong>Deal failed</strong> — ${
        error.message ||
        "Unknown error"
      }`,
      "bad"
    );
  }

  dealing = false;

  refreshBets();
}

/* ================================================================
   CLEAR
   ================================================================ */

function clearBets() {
  if (dealing) {
    return;
  }

  /*
   * Bets are deducted immediately
   * on placement, so clearing the
   * table returns those credits.
   */

  balance +=
    pendingTotal();

  pendingBets = {};

  saveBalance();

  refreshBets();

  showStatus(
    "<strong>Bets cleared</strong>",
    "warn"
  );
}

/* ================================================================
   RESET
   ================================================================ */

function resetGame() {
  if (dealing) {
    return;
  }

  if (
    !window.confirm(
      `Reset credits to ${fmt(
        STARTING_CREDITS
      )}?`
    )
  ) {
    return;
  }

  balance =
    STARTING_CREDITS;

  pendingBets = {};

  localStorage.removeItem(
    HISTORY_KEY
  );

  saveBalance();

  renderHistory();

  refreshBets();

  clearCards();

  showStatus(
    `<strong>Credits reset to ${fmt(
      STARTING_CREDITS
    )}</strong>`,
    "good"
  );
}

/* ================================================================
   INITIALISATION
   ================================================================ */

function init() {
  saveBalance();

  renderChipBar();

  configureVariant();

  renderPayTable();

  renderHistory();

  clearCards();

  refreshBets();

  const deal =
    $("dealBtn");

  const clear =
    $("clearBtn");

  const reset =
    $("resetBtn");

  if (deal) {
    deal.addEventListener(
      "click",
      dealRound
    );
  }

  if (clear) {
    clear.addEventListener(
      "click",
      clearBets
    );
  }

  if (reset) {
    reset.addEventListener(
      "click",
      resetGame
    );
  }

  console.log(
    `Baccarat Solo ready: ${GAME}`
  );
}

if (
  document.readyState ===
  "loading"
) {
  document.addEventListener(
    "DOMContentLoaded",
    init
  );
} else {
  init();
}