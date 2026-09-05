import {
  renderChipBar,
  chipStackHTML
} from "./boards.js";

/* ================================================================
   BLACKJACK SOLO
   Interactive UI for:

   - Blackjack Lucky 8 — MBS Version 5
   - Free Bet Blackjack — MBS Version 4
   - King's Bounty Blackjack — MBS
   - Pontoon — MBS Version 6
   ================================================================ */

const GAME = window.BLACKJACK_GAME;
const MAX_BET = Number(window.BLACKJACK_MAX);
const START_CR = Number(window.BLACKJACK_START);

const $ = (id) => document.getElementById(id);

const fmt = (n) =>
  Math.round(Number(n)).toLocaleString();

/* ================================================================
   VARIANT CONFIGURATION
   ================================================================ */

const VARIANTS = {

  blackjack_lucky8: {
    pairKey: "pair",

    left: {
      key: "lucky8",
      label: "Lucky 8",
      cls: "bc-red",
    },

    pays: [
      ["Blackjack", "3:2"],
      ["Regular Win", "1:1"],
      ["Insurance", "2:1"],
      ["Any Pair", "11:1"],
      ["3 suited 8s", "1000:1"],
      ["3 unsuited 8s", "100:1"],
      ["2 suited 8s", "10:1"],
      ["2 unsuited 8s", "5:1"],
      ["Two of a Kind", "3:1"],
    ],

    note:
      "Dealer draws to 16 and stands on hard or soft 17.",
  },

  blackjack_freebet: {
    pairKey: "pair",

    left: {
      key: "busted",
      label: "Busted",
      cls: "bc-red",
    },

    right: {
      key: "potofgold",
      label: "Pot of Gold",
      cls: "bc-green",
    },

    pays: [
      ["Blackjack", "3:2"],
      ["Regular Win", "1:1"],
      ["Insurance", "2:1"],
      ["Any Pair", "11:1"],

      [
        "Busted — Dealer 3/4/5/6/7+ cards",
        "1 / 2 / 6 / 50 / 100:1",
      ],

      [
        "Pot of Gold — 1/2/3/4/5+ markers",
        "3 / 10 / 25 / 50 / 100:1",
      ],
    ],

    note:
      "Dealer draws to soft 17 and stands on hard 17. " +
      "Dealer 22 pushes all non-busted Player hands except Blackjack. " +
      "Free Double is available on hard 9, 10 or 11. " +
      "Free Split applies to equal-value non-10-point cards.",
  },

  blackjack_kingsbounty: {
    topKey: "kingsbounty",
    topLabel: "KING'S BOUNTY",

    left: {
      key: "bettheset",
      label: "Bet the Set",
      cls: "bc-blue",
    },

    right: {
      key: "royalmatch",
      label: "Royal Match",
      cls: "bc-purple",
    },

    pays: [
      ["Blackjack", "6:5"],
      ["Regular Win", "1:1"],
      ["Insurance", "2:1"],

      [
        "2 Kings of Spades + Dealer Blackjack",
        "1000:1",
      ],

      ["2 Kings of Spades", "100:1"],
      ["2 Suited Kings", "30:1"],
      ["2 Suited Q / J / 10", "20:1"],
      ["Suited 20", "9:1"],
      ["2 Kings", "6:1"],
      ["Unsuited 20", "4:1"],

      ["Bet the Set — suited pair", "15:1"],
      ["Bet the Set — unsuited pair", "10:1"],

      ["Royal Match — suited K-Q", "25:1"],
      ["Royal Match — other suited cards", "5:2"],
    ],

    note:
      "Dealer draws to 16 and stands on hard or soft 17.",
  },

  pontoon: {
    pairKey: "pair",

    pays: [
      ["Pontoon", "3:2"],
      ["Regular Win", "1:1"],
      ["Insurance", "2:1"],
      ["Any Pair", "11:1"],

      ["5 cards totaling 21", "3:2"],
      ["6 cards totaling 21", "2:1"],
      ["7+ cards totaling 21", "3:1"],

      ["6-7-8 / 7-7-7 mixed suits", "3:2"],

      [
        "6-7-8 / 7-7-7 same suit except Spades",
        "2:1",
      ],

      [
        "6-7-8 / 7-7-7 all Spades",
        "3:1",
      ],

      [
        "Super Bonus — original wager $10-$99",
        "$1,000",
      ],

      [
        "Super Bonus — original wager $100+",
        "$5,000",
      ],

      [
        "Other original wagers during Super Bonus",
        "+$50",
      ],
    ],

    note:
      "10 cards are removed from the shoe. " +
      "Dealer draws to hard 16 or soft 17 and stands on hard 17. " +
      "Super Bonus requires unsplit, undoubled 7-7-7 of the same suit " +
      "with Dealer showing any 7. " +
      "Pontoon and all other 21 hands are paid immediately.",
  },
};

const cfg = VARIANTS[GAME];

if (!cfg) {
  throw new Error(
    `Unknown Blackjack variant: ${GAME}`
  );
}

/* ================================================================
   CARD DISPLAY
   ================================================================ */

const SUIT = {
  S: "♠",
  H: "♥",
  D: "♦",
  C: "♣",
};

const RED = new Set([
  "H",
  "D",
]);

const sleep = (ms) =>
  new Promise((resolve) =>
    setTimeout(resolve, ms)
  );

function card(
  c,
  down = false,
  anim = ""
) {
  if (down) {
    return `
      <div class="card facedown ${anim}"></div>
    `;
  }

  return `
    <div class="card ${
      RED.has(c.suit)
        ? "red"
        : ""
    } ${anim}">
      <div class="rank">
        ${c.rank}
      </div>

      <div class="suit">
        ${SUIT[c.suit]}
      </div>
    </div>
  `;
}

/* ================================================================
   LOCAL STATE
   ================================================================ */

const BAL_KEY =
  `etg_bj_bal_${GAME}`;

const HIST_KEY =
  `etg_bj_hist_${GAME}`;

let balance =
  parseFloat(
    localStorage.getItem(BAL_KEY) ??
    START_CR
  );

let selectedChip = 1000;

let bets = {};

let dealing = false;

let stateToken = null;

let currentSeat = null;

let currentHand = null;

let activeSeats = [];

let lastView = null;

/* ================================================================
   STATUS / BALANCE
   ================================================================ */

function status(
  text,
  cls = ""
) {
  const el = $("statusBar");

  el.className =
    `status-bar ${cls}`;

  el.innerHTML =
    text;
}

function saveBal() {
  localStorage.setItem(
    BAL_KEY,
    String(balance)
  );

  $("balDisplay").textContent =
    fmt(balance);
}

function pending() {
  return Object
    .values(bets)
    .reduce(
      (a, b) =>
        a + Number(b),
      0
    );
}

/* ================================================================
   CHIPS
   ================================================================ */

function chips() {
  renderChipBar(
    $("chipBar"),
    selectedChip,
    (value) => {
      selectedChip =
        value;

      chips();
    }
  );
}

/* ================================================================
   INITIAL-DEAL ANIMATION
   ================================================================ */

function emptyView() {
  const view = {
    seats: {},
  };

  for (
    let s = 0;
    s < 3;
    s++
  ) {
    view.seats[String(s)] = {
      hands: [],
    };
  }

  return view;
}

function partialInitialView(
  full,
  counts
) {
  const view = {
    seats: {},
  };

  for (
    let s = 0;
    s < 3;
    s++
  ) {
    const seat =
      full.seats?.[
        String(s)
      ];

    if (!seat) {
      view.seats[String(s)] = {
        hands: [],
      };

      continue;
    }

    const source =
      seat.hands[0];

    const count =
      counts[String(s)] || 0;

    view.seats[String(s)] = {
      hands: count
        ? [{
            ...source,

            cards:
              source.cards.slice(
                0,
                count
              ),

            total:
              count === 1
                ? ""
                : source.total,

            status:
              count < 2
                ? "dealing"
                : source.status,

            can_hit: false,
            can_stand: false,
            can_double: false,
            can_split: false,
          }]
        : [],
    };
  }

  return view;
}

async function animateInitialDeal(
  data
) {
  renderDealer(
    null,
    []
  );

  renderSeats(
    emptyView()
  );

  const counts = {};

  data.active_seats.forEach(
    (s) => {
      counts[String(s)] = 0;
    }
  );

  /*
   * MBS initial deal:
   *
   * first card to each active Player
   * Dealer up-card
   * second card to each Player
   * Dealer hole card remains hidden
   */

  for (
    const s
    of data.active_seats
  ) {
    counts[String(s)] = 1;

    renderSeats(
      partialInitialView(
        data,
        counts
      )
    );

    const cardEl =
      document.querySelector(
        `#seat${s} .hand-cards .card:last-child`
      );

    cardEl?.classList.add(
      "deal-in"
    );

    await sleep(380);
  }

  $("dealerHand").innerHTML =
    card(
      data.dealer_up,
      false,
      "deal-in"
    );

  await sleep(380);

  for (
    const s
    of data.active_seats
  ) {
    counts[String(s)] = 2;

    renderSeats(
      partialInitialView(
        data,
        counts
      )
    );

    const cards =
      document.querySelectorAll(
        `#seat${s} .hand-cards .card`
      );

    cards[
      cards.length - 1
    ]?.classList.add(
      "deal-in"
    );

    await sleep(380);
  }

  $("dealerHand")
    .insertAdjacentHTML(
      "beforeend",
      card(
        null,
        true,
        "deal-in"
      )
    );

  $("dealerBadge")
    .textContent = "";

  await sleep(300);

  renderSeats(data);
}

/* ================================================================
   ACTION ANIMATION
   ================================================================ */

async function animateActionTransition(
  before,
  after,
  seat,
  action
) {
  const beforeHands =
    before?.seats?.[
      String(seat)
    ]?.hands || [];

  const afterHands =
    after?.seats?.[
      String(seat)
    ]?.hands || [];

  if (
    action === "split"
  ) {
    renderSeats(after);

    const hands =
      document.querySelectorAll(
        `#seat${seat} .player-hand`
      );

    hands.forEach(
      (hand) =>
        hand
          .querySelectorAll(
            ".card"
          )
          .forEach(
            (c) =>
              c.style.visibility =
                "hidden"
          )
    );

    for (
      const hand
      of hands
    ) {
      for (
        const c
        of hand.querySelectorAll(
          ".card"
        )
      ) {
        c.style.visibility =
          "visible";

        c.classList.add(
          "deal-in"
        );

        await sleep(300);
      }
    }

    return;
  }

  renderSeats(after);

  const beforeIndex =
    before.current_hand ?? 0;

  const afterIndex =
    Math.min(
      beforeIndex,
      afterHands.length - 1
    );

  const oldCount =
    beforeHands[
      beforeIndex
    ]?.cards?.length || 0;

  const newCards =
    afterHands[
      afterIndex
    ]?.cards || [];

  if (
    newCards.length >
    oldCount
  ) {
    const cards =
      document.querySelectorAll(
        `#seat${seat} .player-hand:nth-child(${
          afterIndex + 1
        }) .card`
      );

    cards[
      cards.length - 1
    ]?.classList.add(
      "deal-in"
    );

    await sleep(360);
  }
}

/* ================================================================
   DEALER ANIMATION
   ================================================================ */

async function animateDealer(
  finalCards
) {
  const area =
    $("dealerHand");

  area.innerHTML = "";

  if (
    !finalCards?.length
  ) {
    return;
  }

  area.innerHTML =
    card(
      finalCards[0]
    );

  if (
    finalCards.length > 1
  ) {
    area.insertAdjacentHTML(
      "beforeend",
      card(
        null,
        true
      )
    );
  }

  await sleep(300);

  if (
    finalCards.length > 1
  ) {
    area.children[1]
      .outerHTML =
        card(
          finalCards[1],
          false,
          "flip-in"
        );

    await sleep(380);
  }

  for (
    let i = 2;
    i < finalCards.length;
    i++
  ) {
    area.insertAdjacentHTML(
      "beforeend",
      card(
        finalCards[i],
        false,
        "deal-in"
      )
    );

    await sleep(430);
  }
}

/* ================================================================
   SEATS
   ================================================================ */

function renderSeats(
  view
) {
  const row =
    $("seatsRow");

  row.innerHTML = "";

  for (
    let s = 0;
    s < 3;
    s++
  ) {
    const seat =
      view?.seats?.[
        String(s)
      ];

    const hands =
      seat?.hands || [];

    row.innerHTML += `
      <div
        class="seat ${
          s === currentSeat
            ? "active"
            : ""
        }"
        id="seat${s}"
      >
        <div class="seat-num">
          Seat ${s + 1}
        </div>

        <div class="split-hands">
          ${
            hands
              .map(
                (h, i) => `
                  <div
                    class="player-hand ${
                      s === currentSeat &&
                      i === currentHand
                        ? "current"
                        : ""
                    }"
                  >
                    <div class="hand-label">
                      Hand ${i + 1}
                      ${
                        h.free_marker
                          ? " · FREE"
                          : ""
                      }
                    </div>

                    <div class="hand-cards">
                      ${
                        h.cards
                          .map(
                            (c) =>
                              card(c)
                          )
                          .join("")
                      }
                    </div>

                    <div class="hand-total">
                      ${h.total}
                      ${
                        h.status ===
                        "bust"
                          ? " · BUST"
                          : ""
                      }
                    </div>

                    <div
                      class="seat-result"
                      id="res${s}_${i}"
                    ></div>
                  </div>
                `
              )
              .join("")
          }
        </div>

        <div
          class="action-bar"
          id="ab${s}"
        ></div>

        <div id="tags${s}"></div>
      </div>
    `;
  }
}

/* ================================================================
   BETTING ZONE
   ================================================================ */

function renderBetZone() {
  const zone =
    $("bzSeats");

  zone.innerHTML = "";

  for (
    let s = 0;
    s < 3;
    s++
  ) {
    const top =
      cfg.topKey ||
      cfg.pairKey;

    const left =
      cfg.left;

    const right =
      cfg.right;

    zone.innerHTML += `
      <div class="bz-seat-col">

        <div class="bz-seat-lbl">
          Seat ${s + 1}
        </div>

        <div class="bz-layout-row">

          ${
            left
              ? `
                <div
                  class="bet-spot bz-circle ${left.cls}"
                  data-wager="seat${s}_${left.key}"
                >
                  ${left.label}
                </div>
              `
              : `
                <div class="bz-spacer"></div>
              `
          }

          <div class="bz-centre">

            ${
              top
                ? `
                  <div
                    class="bet-spot bz-pair"
                    data-wager="seat${s}_${top}"
                  >
                    ${
                      cfg.topLabel ||
                      "ANY PAIR"
                    }
                  </div>
                `
                : ""
            }

            <div
              class="bet-spot bz-main ${
                top
                  ? ""
                  : "full-radius"
              }"
              data-wager="seat${s}_main"
            >
              MAIN BET
            </div>

          </div>

          ${
            right
              ? `
                <div
                  class="bet-spot bz-circle ${right.cls}"
                  data-wager="seat${s}_${right.key}"
                >
                  ${right.label}
                </div>
              `
              : `
                <div class="bz-spacer"></div>
              `
          }

        </div>
      </div>
    `;
  }

  zone
    .querySelectorAll(
      "[data-wager]"
    )
    .forEach(
      (el) => {
        el.onclick =
          () =>
            place(
              el.dataset.wager
            );
      }
    );

  refresh();
}

/* ================================================================
   BETTING
   ================================================================ */

function place(
  wagerType
) {
  if (dealing) {
    return;
  }

  if (
    balance <
    selectedChip
  ) {
    return status(
      "Not enough credits",
      "bad"
    );
  }

  if (
    pending() +
      selectedChip >
    MAX_BET
  ) {
    return status(
      "Maximum deal stake reached",
      "bad"
    );
  }

  bets[wagerType] =
    (
      bets[wagerType] ||
      0
    ) +
    selectedChip;

  balance -=
    selectedChip;

  saveBal();

  refresh();
}

function refresh() {
  $("pendingTotal")
    .textContent =
      fmt(
        pending()
      );

  $("dealBtn")
    .disabled =
      dealing ||
      !pending();

  $("clearBtn")
    .disabled =
      dealing ||
      !pending();

  document
    .querySelectorAll(
      "#bzSeats [data-wager]"
    )
    .forEach(
      (el) => {
        el
          .querySelectorAll(
            ".chip-stack"
          )
          .forEach(
            (stack) =>
              stack.remove()
          );

        const amount =
          bets[
            el.dataset.wager
          ] || 0;

        if (amount) {
          el.insertAdjacentHTML(
            "beforeend",
            chipStackHTML(
              amount
            )
          );
        }
      }
    );
}

/* ================================================================
   PAY TABLE
   ================================================================ */

function paytable() {
  $("payTblArea")
    .innerHTML =
      "<b>Pay Table</b>" +

      cfg.pays
        .map(
          ([label, odds]) => `
            <div class="pay-row">
              <span>${label}</span>
              <span class="odds">
                ${odds}
              </span>
            </div>
          `
        )
        .join("") +

      (
        cfg.note
          ? `
            <div class="pay-note">
              ${cfg.note}
            </div>
          `
          : ""
      );
}

/* ================================================================
   HISTORY
   ================================================================ */

function history(
  net = null
) {
  let items =
    JSON.parse(
      localStorage.getItem(
        HIST_KEY
      ) || "[]"
    );

  if (
    net !== null
  ) {
    items.push(
      Math.round(net)
    );

    items =
      items.slice(-30);

    localStorage.setItem(
      HIST_KEY,
      JSON.stringify(
        items
      )
    );
  }

  $("histBadges")
    .innerHTML =
      items
        .slice()
        .reverse()
        .map(
          (n) => `
            <span
              class="h-b ${
                n > 0
                  ? "win"
                  : n < 0
                    ? "lose"
                    : "push"
              }"
            >
              ${
                n > 0
                  ? "+"
                  : ""
              }${fmt(n)}
            </span>
          `
        )
        .join("");
}

/* ================================================================
   DEALER
   ================================================================ */

function renderDealer(
  up,
  final = null
) {
  $("dealerHand")
    .innerHTML =
      final
        ? final
            .map(
              (c) =>
                card(c)
            )
            .join("")
        : card(up) +
          card(
            null,
            true
          );
}

/* ================================================================
   PLAYER ACTIONS
   ================================================================ */

function actions(
  view
) {
  document
    .querySelectorAll(
      ".action-bar"
    )
    .forEach(
      (el) =>
        el.innerHTML = ""
    );

  if (
    view.all_done
  ) {
    return settle();
  }

  if (
    view.decision_phase ===
    "insurance"
  ) {
    const offer =
      view.insurance_offer;

    const bar =
      $(
        `ab${currentSeat}`
      );

    let buttons = `
      <button
        class="act-btn act-insurance"
      >
        Insurance (${fmt(
          offer.amount
        )})
      </button>

      <button
        class="act-btn act-stand"
      >
        No Insurance
      </button>
    `;

    /*
     * Even Money is intentionally supplied
     * by the server only for Blackjack
     * variants, never Pontoon.
     */

    if (
      offer.even_money
    ) {
      buttons += `
        <button
          class="act-btn act-even"
        >
          Even Money
        </button>
      `;
    }

    bar.innerHTML =
      buttons;

    const buttonsList =
      [...bar.children];

    buttonsList[0]
      .onclick =
        () =>
          act(
            "insurance"
          );

    buttonsList[1]
      .onclick =
        () =>
          act(
            "decline_insurance"
          );

    if (
      buttonsList[2]
    ) {
      buttonsList[2]
        .onclick =
          () =>
            act(
              "even_money"
            );
    }

    status(
      `<strong>Seat ${
        currentSeat + 1
      }</strong> — Dealer shows Ace: Insurance${
        offer.even_money
          ? " or Even Money"
          : ""
      }?`,
      "warn"
    );

    return;
  }

  const hand =
    view
      .seats[
        String(
          currentSeat
        )
      ]
      .hands[
        currentHand
      ];

  const bar =
    $(
      `ab${currentSeat}`
    );

  if (
    hand.can_withdraw_double
  ) {
    bar.innerHTML = `
      <button
        class="act-btn act-rescue"
      >
        Withdraw Double
      </button>

      <button
        class="act-btn act-stand"
      >
        Keep Double
      </button>
    `;

    bar.children[0]
      .onclick =
        () =>
          act(
            "withdraw_double"
          );

    bar.children[1]
      .onclick =
        () =>
          act(
            "keep_double"
          );

    status(
      `<strong>Seat ${
        currentSeat + 1
      }, Hand ${
        currentHand + 1
      }</strong> — Pontoon double withdrawal decision`,
      "warn"
    );

    return;
  }

  bar.innerHTML = `
    <button
      class="act-btn act-hit"
    >
      Hit
    </button>

    <button
      class="act-btn act-stand"
    >
      Stand
    </button>

    <button
      class="act-btn act-double"
      ${
        hand.can_double
          ? ""
          : "disabled"
      }
    >
      ${
        hand.free_double
          ? "Free Double"
          : "Double"
      }
    </button>

    <button
      class="act-btn act-split"
      ${
        hand.can_split
          ? ""
          : "disabled"
      }
    >
      ${
        hand.free_split
          ? "Free Split"
          : "Split"
      }
    </button>

    ${
      hand.can_surrender
        ? `
          <button
            class="act-btn act-surrender"
          >
            Surrender
          </button>
        `
        : ""
    }
  `;

  const actionNames = [
    "hit",
    "stand",
    "double",
    "split",
  ].concat(
    hand.can_surrender
      ? ["surrender"]
      : []
  );

  [...bar.children]
    .forEach(
      (button, i) => {
        button.onclick =
          () =>
            act(
              actionNames[i]
            );
      }
    );

  status(
    `<strong>Seat ${
      currentSeat + 1
    }, Hand ${
      currentHand + 1
    }</strong> — choose an action`,
    "warn"
  );
}

/* ================================================================
   DEAL
   ================================================================ */

async function deal() {
  if (
    dealing ||
    !pending()
  ) {
    return;
  }

  dealing = true;

  refresh();

  const list =
    Object.entries(
      bets
    ).map(
      ([
        wager_type,
        amount,
      ]) => ({
        seat:
          +wager_type[4],

        wager_type,

        amount,
      })
    );

  try {
    const response =
      await fetch(
        "/api/solo/blackjack/deal",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              game: GAME,
              bets: list,
            }),
        }
      );

    const data =
      await response.json();

    if (
      !response.ok
    ) {
      throw Error(
        data.error
      );
    }

    stateToken =
      data.state_token;

    activeSeats =
      data.active_seats;

    currentSeat =
      data.current_seat;

    currentHand =
      data.current_hand;

    lastView =
      data;

    /*
     * Pontoon and certain Blackjack
     * interim settlements may return
     * credits before final settlement.
     */

    if (
      data.immediate_return
    ) {
      balance +=
        Number(
          data.immediate_return
        );

      saveBal();
    }

    $("betZoneWrap")
      .classList.add(
        "playing-hidden"
      );

    status(
      "<strong>Dealing…</strong>",
      "warn"
    );

    await animateInitialDeal(
      data
    );

    actions(data);

  } catch (error) {
    dealing = false;

    refresh();

    status(
      error.message,
      "bad"
    );
  }
}

/* ================================================================
   ACTION
   ================================================================ */

async function act(
  action
) {
  const seat =
    currentSeat;

  try {
    const response =
      await fetch(
        "/api/solo/blackjack/action",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              state_token:
                stateToken,

              seat,

              action,
            }),
        }
      );

    const data =
      await response.json();

    if (
      !response.ok
    ) {
      throw Error(
        data.error
      );
    }

    if (
      data.extra_stake
    ) {
      if (
        balance <
        data.extra_stake
      ) {
        throw Error(
          "Not enough credits for this additional wager"
        );
      }

      balance -=
        Number(
          data.extra_stake
        );

      saveBal();
    }

    if (
      data.immediate_return
    ) {
      balance +=
        Number(
          data.immediate_return
        );

      saveBal();

      status(
        `Immediate payout: +${fmt(
          data.immediate_return
        )} credits`,
        "good"
      );

      await sleep(300);
    }

    const before =
      lastView;

    stateToken =
      data.state_token;

    currentSeat =
      data.current_seat;

    currentHand =
      data.current_hand;

    if (
      before?.decision_phase !==
        "insurance" &&
      ![
        "surrender",
        "withdraw_double",
        "keep_double",
      ].includes(action)
    ) {
      await animateActionTransition(
        before,
        data,
        seat,
        action
      );
    } else {
      renderSeats(data);
    }

    lastView =
      data;

    actions(data);

  } catch (error) {
    status(
      error.message,
      "bad"
    );

    actions(
      lastView
    );
  }
}

/* ================================================================
   SETTLEMENT
   ================================================================ */

async function settle() {
  status(
    "Dealer's turn…"
  );

  try {
    const response =
      await fetch(
        "/api/solo/blackjack/settle",
        {
          method: "POST",

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
      throw Error(
        data.error
      );
    }

    await animateDealer(
      data.outcome
        .dealer_cards
    );

    $("dealerBadge")
      .textContent =
        `${data.outcome.dealer_total}${
          data.outcome.dealer_bust
            ? " · BUST"
            : ""
        }`;

    await sleep(250);

    currentSeat = null;
    currentHand = null;

    const view = {
      seats: {},
    };

    for (
      const s
      of data.outcome
        .active_seats
    ) {
      view.seats[
        String(s)
      ] = {
        hands:
          data.outcome
            .seats[s]
            .hands,
      };
    }

    renderSeats(view);

    for (
      const s
      of data.outcome
        .active_seats
    ) {
      data.outcome
        .seats[s]
        .hands
        .forEach(
          (hand, i) => {
            const el =
              $(
                `res${s}_${i}`
              );

            if (!el) {
              return;
            }

            const label =
              {
                paid:
                  "PAID 21",

                surrender:
                  "SURRENDER",

                double_withdrawn:
                  "DOUBLE WITHDRAWN",
              }[
                hand.result
              ] ||
              hand.result
                .toUpperCase();

            el.textContent =
              label;

            el.className =
              `seat-result ${
                [
                  "win",
                  "blackjack",
                  "pontoon",
                  "paid",
                ].includes(
                  hand.result
                )
                  ? "win"
                  : [
                      "push",
                      "double_withdrawn",
                    ].includes(
                      hand.result
                    )
                    ? "push"
                    : "lose"
              }`;
          }
        );
    }

    /*
     * Immediate payouts have already
     * been credited by deal()/act().
     *
     * total_return intentionally
     * contains final settlement only.
     */

    balance +=
      Number(
        data.total_return
      );

    saveBal();

    history(
      data.net
    );

    status(
      `Round done — <strong>${
        data.net >= 0
          ? "+"
          : ""
      }${fmt(
        data.net
      )} cr</strong>`,
      data.net >= 0
        ? "good"
        : "bad"
    );

    bets = {};

    dealing = false;

    stateToken = null;

    $("betZoneWrap")
      .classList.remove(
        "playing-hidden"
      );

    refresh();

  } catch (error) {
    dealing = false;

    status(
      error.message,
      "bad"
    );

    refresh();
  }
}

/* ================================================================
   BUTTONS
   ================================================================ */

$("dealBtn").onclick =
  deal;

$("clearBtn").onclick =
  () => {
    if (dealing) {
      return;
    }

    balance +=
      pending();

    bets = {};

    saveBal();

    refresh();
  };

$("resetBtn").onclick =
  () => {
    if (
      confirm(
        `Reset credits to ${fmt(
          START_CR
        )}?`
      )
    ) {
      balance =
        START_CR;

      bets = {};

      localStorage.removeItem(
        HIST_KEY
      );

      saveBal();

      history();

      refresh();
    }
  };

/* ================================================================
   INITIALISE
   ================================================================ */

saveBal();

chips();

renderBetZone();

paytable();

history();

renderSeats(null);