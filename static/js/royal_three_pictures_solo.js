/* ================================================================
   ETG SIM — ROYAL THREE PICTURES SOLO

   3 betting positions:
   - Hand 1 viewed
   - Hands 2 / 3 blind

   Bets:
   - Main
   - Tie
   - Royal Pictures
   ================================================================ */

const GAME = window.RTP_GAME;
const MAX_BET = Number(window.RTP_MAX);
const STARTING_CREDITS = Number(window.RTP_START);

const $ = (id) => document.getElementById(id);

const fmt = (value) =>
  Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 2,
  });


/* ================================================================
   CHIPS
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
  100: "#315b7b",
  250: "#315d2b",
  500: "#8c2929",
  1000: "#49449a",
  2500: "#87520d",
  5000: "#1d6969",
  10000: "#762176",
  20000: "#746b1c",
};


/* ================================================================
   STORAGE
   ================================================================ */

const BALANCE_KEY =
  "etg_royal_three_pictures_balance";

const HISTORY_KEY =
  "etg_royal_three_pictures_history";


/* ================================================================
   STATE
   ================================================================ */

let selectedChip = 1000;

let pendingBets = {};

let busy = false;

let balance = Number(
  localStorage.getItem(BALANCE_KEY) ??
  STARTING_CREDITS
);

if (!Number.isFinite(balance)) {
  balance = STARTING_CREDITS;
}

let history = [];

try {
  history = JSON.parse(
    localStorage.getItem(HISTORY_KEY) ||
    "[]"
  );
} catch {
  history = [];
}


/* ================================================================
   HELPERS
   ================================================================ */

function betKey(seat, wager) {
  return `${seat}:${wager}`;
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

function activeSeats() {
  const seats = [];

  for (let seat = 0; seat < 3; seat++) {
    if (
      Number(
        pendingBets[
          betKey(seat, "main")
        ] || 0
      ) > 0
    ) {
      seats.push(seat);
    }
  }

  return seats;
}

function chipLabel(value) {
  return value >= 1000
    ? `${value / 1000}K`
    : String(value);
}

function saveBalance() {
  localStorage.setItem(
    BALANCE_KEY,
    String(balance)
  );

  $("balanceDisplay").textContent =
    fmt(balance);
}

function saveHistory() {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(history)
  );
}


/* ================================================================
   CARDS
   ================================================================ */

function suitSymbol(suit) {
  const map = {
    S: "♠",
    H: "♥",
    D: "♦",
    C: "♣",
  };

  return map[suit] || suit;
}

function cardHTML(card) {
  if (!card) {
    return "";
  }

  const suit =
    suitSymbol(
      card.suit
    );

  const red =
    card.suit === "H" ||
    card.suit === "D";

  return `
    <div
      class="
        card
        ${red ? "red" : ""}
      "
    >

      <div class="card-corner">

        <div class="card-rank">
          ${card.rank}
        </div>

        <div class="card-suit">
          ${suit}
        </div>

      </div>


      <div class="card-center">
        ${suit}
      </div>

    </div>
  `;
}

function cardBackHTML() {
  return `
    <div class="card back"></div>
  `;
}

function renderCards(
  target,
  cards,
  hidden = false
) {
  const area = $(target);

  if (!area) {
    return;
  }

  if (
    !cards ||
    !cards.length
  ) {
    area.innerHTML = "";
    return;
  }

  if (hidden) {
    area.innerHTML =
      cards
        .map(() => cardBackHTML())
        .join("");

    return;
  }

  area.innerHTML =
    cards
      .map(cardHTML)
      .join("");
}


/* ================================================================
   CHIPS
   ================================================================ */

function renderChips() {
  const bar = $("chipBar");

  bar.innerHTML = "";

  CHIPS.forEach(
    (value) => {
      const button =
        document.createElement(
          "button"
        );

      button.className =
        `chip${
          selectedChip === value
            ? " active"
            : ""
        }`;

      button.textContent =
        chipLabel(value);

      button.style.background =
        `radial-gradient(
          circle at 35% 30%,
          ${CHIP_COLORS[value]},
          #111
        )`;

      button.onclick = () => {
        if (busy) {
          return;
        }

        selectedChip = value;

        renderChips();
      };

      bar.appendChild(button);
    }
  );
}


/* ================================================================
   BETTING
   ================================================================ */

function bindBets() {
  document
    .querySelectorAll(
      "[data-seat][data-wager]"
    )
    .forEach(
      (element) => {
        element.addEventListener(
          "click",
          () => {
            const seat =
              Number(
                element.dataset.seat
              );

            const wager =
              element.dataset.wager;

            placeBet(
              seat,
              wager
            );
          }
        );
      }
    );
}

function placeBet(
  seat,
  wager
) {
  if (busy) {
    return;
  }

  /*
   * Side wagers require that the position
   * has a Main wager.
   *
   * This also prevents accidentally activating
   * a seat using only Tie/Royal Pictures.
   */

  if (
    wager !== "main" &&
    Number(
      pendingBets[
        betKey(
          seat,
          "main"
        )
      ] || 0
    ) <= 0
  ) {
    return;
  }

  if (
    balance <
    selectedChip
  ) {
    return;
  }

  if (
    pendingTotal() +
    selectedChip >
    MAX_BET
  ) {
    return;
  }

  const key =
    betKey(
      seat,
      wager
    );

  pendingBets[key] =
    Number(
      pendingBets[key] || 0
    ) +
    selectedChip;

  balance -=
    selectedChip;

  saveBalance();

  refresh();
}


/* ================================================================
   REFRESH
   ================================================================ */

function refresh() {
  const total =
    pendingTotal();

  const seats =
    activeSeats();

  $("pendingTotal").textContent =
    fmt(total);

  $("stakeMetric").textContent =
    fmt(total);

  $("activeMetric").textContent =
    seats.length;

  $("dealBtn").disabled =
    busy ||
    total <= 0 ||
    seats.length <= 0;

  $("clearBtn").disabled =
    busy ||
    total <= 0;


  /*
   * Seat highlight.
   */

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {
    const element =
      $(`seat${seat}`);

    if (!element) {
      continue;
    }

    element.classList.toggle(
      "active-seat",
      seats.includes(seat)
    );
  }


  /*
   * Bet badges.
   */

  document
    .querySelectorAll(
      "[data-seat][data-wager]"
    )
    .forEach(
      (element) => {
        const seat =
          Number(
            element.dataset.seat
          );

        const wager =
          element.dataset.wager;

        const amount =
          Number(
            pendingBets[
              betKey(
                seat,
                wager
              )
            ] || 0
          );

        let badge =
          element.querySelector(
            ":scope > .bet-badge"
          );

        if (
          amount <= 0
        ) {
          if (badge) {
            badge.remove();
          }

          return;
        }

        if (!badge) {
          badge =
            document.createElement(
              "span"
            );

          badge.className =
            "bet-badge";

          element.appendChild(
            badge
          );
        }

        badge.textContent =
          fmt(amount);
      }
    );
}


/* ================================================================
   CLEAR
   ================================================================ */

function clearBets() {
  if (busy) {
    return;
  }

  balance +=
    pendingTotal();

  pendingBets = {};

  saveBalance();

  clearTable();

  refresh();
}


/* ================================================================
   BUILD API BETS
   ================================================================ */

function buildBets() {
  const bets = [];

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {
    for (
      const wager of [
        "main",
        "tie",
        "royal_pictures",
      ]
    ) {
      const amount =
        Number(
          pendingBets[
            betKey(
              seat,
              wager
            )
          ] || 0
        );

      if (
        amount > 0
      ) {
        bets.push({
          seat,
          wager_type:
            wager,
          amount,
        });
      }
    }
  }

  return bets;
}


/* ================================================================
   TABLE DISPLAY
   ================================================================ */

function clearTable() {
  renderCards(
    "dealerCards",
    []
  );

  $("dealerSummary").textContent =
    "Waiting for deal";

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {
    renderCards(
      `seat${seat}Cards`,
      []
    );

    $(
      `seat${seat}Summary`
    ).textContent =
      Number(
        pendingBets[
          betKey(
            seat,
            "main"
          )
        ] || 0
      ) > 0
        ? "Ready"
        : "Place a Main wager to activate";
  }
}


/* ================================================================
   RESULT TEXT
   ================================================================ */

function mainResultText(
  result
) {
  if (
    result === "win"
  ) {
    return `
      <span class="result-win">
        MAIN WIN
      </span>
    `;
  }

  if (
    result === "standoff"
  ) {
    return `
      <span class="result-push">
        STANDOFF
      </span>
    `;
  }

  return `
    <span class="result-lose">
      MAIN LOSS
    </span>
  `;
}

function royalLabel(
  category
) {
  const labels = {
    three_kings:
      "THREE KINGS",

    three_queens:
      "THREE QUEENS",

    three_jacks:
      "THREE JACKS",

    three_pictures:
      "THREE PICTURES",

    any_picture_pair:
      "PICTURE PAIR",

    any_king:
      "ANY KING",
  };

  return (
    labels[category] ||
    ""
  );
}


/* ================================================================
   REVEAL ANIMATION
   ================================================================ */

function sleep(ms) {
  return new Promise(
    (resolve) =>
      setTimeout(
        resolve,
        ms
      )
  );
}

async function revealResults(data) {
  /*
   * Start with all active hands and Banker
   * represented by card backs.
   */

  const active =
    data.active_seats || [];

  active.forEach(
    (seat) => {
      renderCards(
        `seat${seat}Cards`,
        [{}, {}, {}],
        true
      );

      $(
        `seat${seat}Summary`
      ).textContent =
        seat === active[0]
          ? "Viewed hand"
          : "Blind hand";
    }
  );

  renderCards(
    "dealerCards",
    [{}, {}, {}],
    true
  );

  $("dealerSummary")
    .textContent =
      "Banker hand";

  await sleep(350);


  /*
   * Reveal the viewed position first.
   */

  if (
    active.length
  ) {
    const viewed =
      active[0];

    const info =
      data.outcome.seats[
        String(viewed)
      ];

    renderCards(
      `seat${viewed}Cards`,
      info.cards
    );

    $(
      `seat${viewed}Summary`
    ).innerHTML =
      `
        ${info.hand_name}
        · ${info.point_total} points
        · ${info.picture_count} picture${
          info.picture_count === 1
            ? ""
            : "s"
        }
      `;

    await sleep(500);
  }


  /*
   * Reveal Banker.
   */

  renderCards(
    "dealerCards",
    data.dealer.cards
  );

  $("dealerSummary")
    .textContent =
      `${data.dealer.hand_name}
       · ${data.dealer.point_total} points
       · ${data.dealer.picture_count} picture${
         data.dealer.picture_count === 1
           ? ""
           : "s"
       }`;

  await sleep(500);


  /*
   * Reveal blind hands afterwards.
   */

  for (
    let i = 1;
    i < active.length;
    i++
  ) {
    const seat =
      active[i];

    const info =
      data.outcome.seats[
        String(seat)
      ];

    renderCards(
      `seat${seat}Cards`,
      info.cards
    );

    $(
      `seat${seat}Summary`
    ).innerHTML =
      `
        ${info.hand_name}
        · ${info.point_total} points
        · ${info.picture_count} picture${
          info.picture_count === 1
            ? ""
            : "s"
        }
      `;

    await sleep(400);
  }


  /*
   * Final settlement labels.
   */

  active.forEach(
    (seat) => {
      const info =
        data.outcome.seats[
          String(seat)
        ];

      const royal =
        royalLabel(
          info.royal_pictures
        );

      $(
        `seat${seat}Summary`
      ).innerHTML =
        `
          <div>
            ${info.hand_name}
            · ${info.point_total} points
            · ${info.picture_count} picture${
              info.picture_count === 1
                ? ""
                : "s"
            }
          </div>

          <div style="margin-top:5px">
            ${mainResultText(
              info.main_result
            )}

            ${
              info.tie
                ? `
                  ·
                  <span class="result-win">
                    TIE
                  </span>
                `
                : ""
            }

            ${
              royal
                ? `
                  ·
                  <span class="result-win">
                    ${royal}
                  </span>
                `
                : ""
            }
          </div>
        `;
    }
  );
}


/* ================================================================
   HISTORY
   ================================================================ */

function addHistory(data) {
  history.unshift({
    dealer:
      data.dealer.hand_name,

    net:
      Number(
        data.net
      ),
  });

  history =
    history.slice(
      0,
      15
    );

  saveHistory();

  renderHistory();
}

function renderHistory() {
  const area =
    $("history");

  if (
    !history.length
  ) {
    area.innerHTML =
      "<br>No rounds yet";

    return;
  }

  area.innerHTML =
    history
      .map(
        (item) => `
          <div
            style="
              display:flex;
              justify-content:space-between;
              gap:8px;
              padding:7px 0;
              border-bottom:
                1px solid #ffffff12;
            "
          >
            <span>
              ${item.dealer}
            </span>

            <span
              style="
                color:${
                  item.net >= 0
                    ? "#65ef8a"
                    : "#ff8d8d"
                };
              "
            >
              ${
                item.net > 0
                  ? "+"
                  : ""
              }${fmt(
                item.net
              )}
            </span>
          </div>
        `
      )
      .join("");
}


/* ================================================================
   DEAL
   ================================================================ */

async function dealRound() {
  if (
    busy ||
    pendingTotal() <= 0
  ) {
    return;
  }

  const wagered =
    pendingTotal();

  const bets =
    buildBets();

  busy = true;

  $("phaseLabel").textContent =
    "DEALING";

  refresh();

  try {
    const response =
      await fetch(
        "/api/solo/royal-three-pictures/deal",
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

              bets,
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
        "Royal Three Pictures deal failed"
      );
    }

    $("phaseLabel").textContent =
      "REVEALING";

    await revealResults(
      data
    );

    balance +=
      Number(
        data.total_return
      );

    saveBalance();

    $("stakeMetric").textContent =
      fmt(
        data.total_wager
      );

    $("returnMetric").textContent =
      fmt(
        data.total_return
      );

    $("netMetric").textContent =
      `${
        Number(
          data.net
        ) > 0
          ? "+"
          : ""
      }${fmt(
        data.net
      )}`;

    addHistory(
      data
    );

    pendingBets = {};

  } catch (error) {
    /*
     * Backend rejected / failed before settlement.
     * Restore locally deducted wagers.
     */

    balance +=
      wagered;

    pendingBets = {};

    saveBalance();

    console.error(
      error
    );

    alert(
      error.message ||
      "Royal Three Pictures failed"
    );

  } finally {
    busy = false;

    $("phaseLabel").textContent =
      "READY";

    refresh();
  }
}


/* ================================================================
   RESET
   ================================================================ */

function resetCredits() {
  if (busy) {
    return;
  }

  if (
    !confirm(
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

  history = [];

  localStorage.removeItem(
    BALANCE_KEY
  );

  localStorage.removeItem(
    HISTORY_KEY
  );

  saveBalance();
  saveHistory();

  $("returnMetric").textContent =
    "0";

  $("netMetric").textContent =
    "0";

  clearTable();

  renderHistory();

  refresh();
}


/* ================================================================
   INITIALISE
   ================================================================ */

function init() {
  saveBalance();

  renderChips();

  bindBets();

  renderHistory();

  clearTable();

  $("clearBtn").onclick =
    clearBets;

  $("dealBtn").onclick =
    dealRound;

  $("resetBtn").onclick =
    resetCredits;

  refresh();
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
    init
  );
} else {
  init();
}