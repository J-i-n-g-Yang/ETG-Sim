import {
  renderChipBar,
} from "./boards.js";


/* ================================================================
   ETG SIM — BLACKJACK SOLO

   Variants:
   - blackjack_lucky8
   - blackjack_freebet
   - blackjack_kingsbounty
   - pontoon

   Matched DOM contract:
   - seat0 / seat1 / seat2
   - .seat-hands
   - dealerHand
   - dealerBadge
   - actionBar
   - bzSeats
   - history
   - rulesBox
   ================================================================ */


const GAME =
  window.BLACKJACK_GAME;

const MAX_BET =
  Number(
    window.BLACKJACK_MAX
  );

const START_CR =
  Number(
    window.BLACKJACK_START
  );


const $ = (id) =>
  document.getElementById(
    id
  );


const fmt = (value) =>
  Math.round(
    Number(value) || 0
  ).toLocaleString();


const sleep = (ms) =>
  new Promise(
    (resolve) =>
      setTimeout(
        resolve,
        ms
      )
  );


/* ================================================================
   VARIANT CONFIGURATION
   ================================================================ */

const VARIANTS = {

  blackjack_lucky8: {

    title:
      "BLACKJACK LUCKY 8 RULES",

    top: {
      key:
        "pair",

      label:
        "ANY PAIR",

      cls:
        "",
    },

    left: {
      key:
        "lucky8",

      label:
        "LUCKY 8",

      cls:
        "bc-red",
    },

    right:
      null,

    pays: [
      [
        "Blackjack",
        "3:2",
      ],

      [
        "Regular Win",
        "1:1",
      ],

      [
        "Insurance",
        "2:1",
      ],

      [
        "Any Pair",
        "11:1",
      ],

      [
        "3 suited 8s",
        "1000:1",
      ],

      [
        "3 unsuited 8s",
        "100:1",
      ],

      [
        "2 suited 8s",
        "10:1",
      ],

      [
        "2 unsuited 8s",
        "5:1",
      ],

      [
        "Two of a Kind",
        "3:1",
      ],
    ],

    note:
      "Dealer draws to 16 and stands on hard or soft 17.",
  },


  blackjack_freebet: {

    title:
      "FREE BET BLACKJACK RULES",

    top: {
      key:
        "pair",

      label:
        "ANY PAIR",

      cls:
        "",
    },

    left: {
      key:
        "busted",

      label:
        "BUSTED",

      cls:
        "bc-red",
    },

    right: {
      key:
        "potofgold",

      label:
        "POT OF GOLD",

      cls:
        "bc-green",
    },

    pays: [
      [
        "Blackjack",
        "3:2",
      ],

      [
        "Regular Win",
        "1:1",
      ],

      [
        "Insurance",
        "2:1",
      ],

      [
        "Any Pair",
        "11:1",
      ],

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

    title:
      "KING'S BOUNTY BLACKJACK RULES",

    top: {
      key:
        "kingsbounty",

      label:
        "KING'S BOUNTY",

      cls:
        "",
    },

    left: {
      key:
        "bettheset",

      label:
        "BET THE SET",

      cls:
        "bc-blue",
    },

    right: {
      key:
        "royalmatch",

      label:
        "ROYAL MATCH",

      cls:
        "bc-purple",
    },

    pays: [
      [
        "Blackjack",
        "6:5",
      ],

      [
        "Regular Win",
        "1:1",
      ],

      [
        "Insurance",
        "2:1",
      ],

      [
        "2 Kings of Spades + Dealer Blackjack",
        "1000:1",
      ],

      [
        "2 Kings of Spades",
        "100:1",
      ],

      [
        "2 Suited Kings",
        "30:1",
      ],

      [
        "2 Suited Q / J / 10",
        "20:1",
      ],

      [
        "Suited 20",
        "9:1",
      ],

      [
        "2 Kings",
        "6:1",
      ],

      [
        "Unsuited 20",
        "4:1",
      ],

      [
        "Bet the Set — suited pair",
        "15:1",
      ],

      [
        "Bet the Set — unsuited pair",
        "10:1",
      ],

      [
        "Royal Match — suited K-Q",
        "25:1",
      ],

      [
        "Royal Match — other suited cards",
        "5:2",
      ],
    ],

    note:
      "Dealer draws to 16 and stands on hard or soft 17.",
  },


  pontoon: {

    title:
      "PONTOON RULES",

    top: {
      key:
        "pair",

      label:
        "ANY PAIR",

      cls:
        "",
    },

    left:
      null,

    right:
      null,

    pays: [
      [
        "Pontoon",
        "3:2",
      ],

      [
        "Regular Win",
        "1:1",
      ],

      [
        "Insurance",
        "2:1",
      ],

      [
        "Any Pair",
        "11:1",
      ],

      [
        "5 cards totaling 21",
        "3:2",
      ],

      [
        "6 cards totaling 21",
        "2:1",
      ],

      [
        "7+ cards totaling 21",
        "3:1",
      ],

      [
        "6-7-8 / 7-7-7 mixed suits",
        "3:2",
      ],

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
      "with Dealer showing any 7. Pontoon and all other 21 hands are " +
      "paid immediately.",
  },
};


const cfg =
  VARIANTS[
    GAME
  ];


if (!cfg) {
  throw new Error(
    `Unknown Blackjack variant: ${GAME}`
  );
}


/* ================================================================
   CARDS
   ================================================================ */

const SUITS = {
  S:
    "♠",

  H:
    "♥",

  D:
    "♦",

  C:
    "♣",
};


const RED_SUITS =
  new Set([
    "H",
    "D",
  ]);


function cardHTML(
  cardData,
  facedown = false,
  animation = ""
) {

  if (facedown) {
    return `
      <div
        class="
          card
          facedown
          ${animation}
        "
      ></div>
    `;
  }


  if (!cardData) {
    return "";
  }


  const red =
    RED_SUITS.has(
      cardData.suit
    );


  return `
    <div
      class="
        card
        ${red ? "red" : ""}
        ${animation}
      "
    >

      <div class="rank">
        ${cardData.rank}
      </div>

      <div class="suit">
        ${
          SUITS[
            cardData.suit
          ] ||
          cardData.suit ||
          ""
        }
      </div>

    </div>
  `;
}


/* ================================================================
   STORAGE / STATE
   ================================================================ */

const BAL_KEY =
  `etg_bj_bal_${GAME}`;

const HIST_KEY =
  `etg_bj_hist_${GAME}`;


let balance =
  Number(
    localStorage.getItem(
      BAL_KEY
    ) ??
    START_CR
  );


if (
  !Number.isFinite(
    balance
  )
) {
  balance =
    START_CR;
}


let selectedChip =
  1000;

let bets =
  {};

let dealing =
  false;

let stateToken =
  null;

let currentSeat =
  null;

let currentHand =
  null;

let lastView =
  null;


/* ================================================================
   STATUS
   ================================================================ */

function status(
  message,
  cls = ""
) {
  const element =
    $("statusBar");

  if (!element) {
    return;
  }

  element.className =
    `status-bar ${cls}`;

  element.innerHTML =
    message;
}


/* ================================================================
   BALANCE
   ================================================================ */

function saveBalance() {

  localStorage.setItem(
    BAL_KEY,
    String(balance)
  );


  const display =
    $("balDisplay");

  if (display) {
    display.textContent =
      fmt(balance);
  }
}


/* ================================================================
   BET HELPERS
   ================================================================ */

function wagerId(
  seat,
  key
) {
  return (
    `seat${seat}_${key}`
  );
}


function pendingTotal() {

  return Object
    .values(
      bets
    )
    .reduce(
      (
        total,
        amount
      ) =>
        total +
        Number(
          amount
        ),
      0
    );
}


function mainBet(
  seat
) {
  return Number(
    bets[
      wagerId(
        seat,
        "main"
      )
    ] || 0
  );
}


/* ================================================================
   CHIPS
   ================================================================ */

function renderChips() {

  renderChipBar(
    $("chipBar"),
    selectedChip,

    (value) => {

      if (dealing) {
        return;
      }

      selectedChip =
        value;

      renderChips();
    }
  );
}


/* ================================================================
   BET SPOT HTML
   ================================================================ */

function betSpotHTML(
  seat,
  key,
  label,
  classes
) {

  const wager =
    wagerId(
      seat,
      key
    );


  return `
    <div
      class="
        bet-spot
        ${classes}
      "
      data-wager="${wager}"
    >

      <span class="bet-spot-label">
        ${label}
      </span>

      <div
        class="bet-chip-layer"
        id="amt_${wager}"
      ></div>

    </div>
  `;
}


/* ================================================================
   BETTING ZONE
   ================================================================ */

function renderBetZone() {

  const zone =
    $("bzSeats");


  if (!zone) {
    return;
  }


  zone.innerHTML =
    "";


  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    const top =
      cfg.top;

    const left =
      cfg.left;

    const right =
      cfg.right;


    const topHTML =
      top
        ? betSpotHTML(
            seat,
            top.key,
            top.label,
            `bz-top ${top.cls || ""}`
          )
        : `
            <div
              style="
                grid-column:2;
                grid-row:1;
              "
            ></div>
          `;


    const leftHTML =
      left
        ? betSpotHTML(
            seat,
            left.key,
            left.label,
            `bz-circle bz-left ${left.cls || ""}`
          )
        : `
            <div
              class="
                bz-empty
                bz-left
              "
              aria-hidden="true"
            ></div>
          `;


    const rightHTML =
      right
        ? betSpotHTML(
            seat,
            right.key,
            right.label,
            `bz-circle bz-right ${right.cls || ""}`
          )
        : `
            <div
              class="
                bz-empty
                bz-right
              "
              aria-hidden="true"
            ></div>
          `;


    const mainHTML =
      betSpotHTML(
        seat,
        "main",
        "MAIN BET",
        "bz-main"
      );


    zone.insertAdjacentHTML(
      "beforeend",

      `
        <div class="bz-seat-col">

          <div class="bz-seat-lbl">
            SEAT ${seat + 1}
          </div>

          <div class="bz-casino-layout">

            ${topHTML}

            ${leftHTML}

            ${mainHTML}

            ${rightHTML}

          </div>

        </div>
      `
    );
  }


  zone
    .querySelectorAll(
      "[data-wager]"
    )
    .forEach(
      (element) => {

        element.addEventListener(
          "click",

          () => {
            placeBet(
              element.dataset.wager
            );
          }
        );
      }
    );


  refresh();
}


/* ================================================================
   PLACE BET
   ================================================================ */

function placeBet(
  wager
) {

  if (
    dealing ||
    stateToken
  ) {
    return;
  }


  prepareBettingTable();


  if (
    balance <
    selectedChip
  ) {
    status(
      "Not enough credits.",
      "bad"
    );

    return;
  }


  if (
    pendingTotal() +
    selectedChip >
    MAX_BET
  ) {
    status(
      `Table maximum is ${fmt(
        MAX_BET
      )} credits.`,
      "bad"
    );

    return;
  }


  bets[
    wager
  ] =
    Number(
      bets[
        wager
      ] || 0
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


  const pendingDisplay =
    $("pendingTotal");

  if (pendingDisplay) {
    pendingDisplay.textContent =
      fmt(total);
  }


  /*
   * During betting, Total Stake displays pending wagers.
   *
   * During a live/completed round the API updates this separately.
   */

  if (!stateToken) {

    const stakeMetric =
      $("stakeMetric");

    if (stakeMetric) {
      stakeMetric.textContent =
        fmt(total);
    }
  }


  let activeCount =
    0;


  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    if (
      mainBet(
        seat
      ) > 0
    ) {
      activeCount++;
    }
  }


  if (!stateToken) {

    const activeMetric =
      $("activeMetric");

    if (activeMetric) {
      activeMetric.textContent =
        String(
          activeCount
        );
    }
  }


  const dealButton =
    $("dealBtn");

  if (dealButton) {

    dealButton.disabled =
      dealing ||
      Boolean(
        stateToken
      ) ||
      total <= 0;
  }


  const clearButton =
    $("clearBtn");

  if (clearButton) {

    clearButton.disabled =
      dealing ||
      Boolean(
        stateToken
      ) ||
      total <= 0;
  }


  document
    .querySelectorAll(
      ".bet-chip-layer"
    )
    .forEach(
      (layer) => {

        const wager =
          layer.id.replace(
            /^amt_/,
            ""
          );

        const amount =
          Number(
            bets[
              wager
            ] || 0
          );

        layer.innerHTML =
          amount > 0
            ? `
                <span class="badge">
                  ${fmt(amount)}
                </span>
              `
            : "";
      }
    );
}

/* ================================================================
   EMPTY PLAYER VIEW
   ================================================================ */

function emptyView() {

  return {
    seats: {
      "0": {
        hands: [],
      },

      "1": {
        hands: [],
      },

      "2": {
        hands: [],
      },
    },

    current_seat:
      null,

    current_hand:
      null,
  };
}


/* ================================================================
   PLAYER SEATS
   ================================================================ */

function renderSeats(
  view
) {

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    const seatElement =
      $(
        `seat${seat}`
      );


    if (!seatElement) {
      continue;
    }


    seatElement
      .classList
      .remove(
        "active-seat",
        "current-seat"
      );


    const handArea =
      seatElement.querySelector(
        ".seat-hands"
      );


    if (!handArea) {
      continue;
    }


    const seatData =
      view?.seats?.[
        String(seat)
      ];


    if (
      !seatData ||
      !Array.isArray(
        seatData.hands
      ) ||
      !seatData.hands.length
    ) {

      handArea.innerHTML =
        `
          <div class="seat-empty">
            Place a Main wager to activate
          </div>
        `;

      continue;
    }


    seatElement
      .classList
      .add(
        "active-seat"
      );


    if (
      Number(
        view.current_seat
      ) === seat
    ) {

      seatElement
        .classList
        .add(
          "current-seat"
        );
    }


    handArea.innerHTML =
      seatData.hands
        .map(
          (
            hand,
            index
          ) => {

            const isCurrent =
              Number(
                view.current_seat
              ) === seat &&
              Number(
                view.current_hand
              ) === index;


            return `
              <div
                class="
                  player-hand
                  ${
                    isCurrent
                      ? "current"
                      : ""
                  }
                "
              >

                <div class="hand-title">
                  HAND ${index + 1}
                </div>


                <div class="hand-cards">

                  ${
                    (
                      hand.cards ||
                      []
                    )
                      .map(
                        (cardData) =>
                          cardHTML(
                            cardData
                          )
                      )
                      .join("")
                  }

                </div>


                <div class="hand-total">

                  ${
                    hand.total === "" ||
                    hand.total === null ||
                    hand.total === undefined
                      ? ""
                      : `TOTAL ${hand.total}`
                  }

                  ${
                    hand.free_marker
                      ? " · FREE"
                      : ""
                  }

                </div>


                <div
                  class="seat-result"
                  id="res${seat}_${index}"
                ></div>

              </div>
            `;
          }
        )
        .join("");
  }
}


/* ================================================================
   PARTIAL INITIAL VIEW
   ================================================================ */

function partialInitialView(
  fullView,
  cardCounts
) {

  const view =
    emptyView();


  view.current_seat =
    fullView.current_seat;

  view.current_hand =
    fullView.current_hand;


  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    const seatData =
      fullView.seats?.[
        String(seat)
      ];


    if (
      !seatData ||
      !seatData.hands?.length
    ) {
      continue;
    }


    const source =
      seatData.hands[
        0
      ];


    const count =
      Number(
        cardCounts[
          String(seat)
        ] || 0
      );


    if (
      count <= 0
    ) {
      continue;
    }


    view.seats[
      String(seat)
    ] = {
      hands: [
        {
          ...source,

          cards:
            source.cards.slice(
              0,
              count
            ),

          total:
            count >= 2
              ? source.total
              : "",

          can_hit:
            false,

          can_stand:
            false,

          can_double:
            false,

          can_split:
            false,

          can_surrender:
            false,
        },
      ],
    };
  }


  return view;
}


/* ================================================================
   DEALER
   ================================================================ */

function renderDealer(
  upCard = null,
  cards = null
) {

  const hand =
    $("dealerHand");


  if (!hand) {
    return;
  }


  if (
    Array.isArray(
      cards
    ) &&
    cards.length
  ) {

    hand.innerHTML =
      cards
        .map(
          (cardData) =>
            cardHTML(
              cardData
            )
        )
        .join("");

    return;
  }


  if (upCard) {

    hand.innerHTML =
      cardHTML(
        upCard
      ) +
      cardHTML(
        null,
        true
      );

    return;
  }


  hand.innerHTML =
    "";
}


/* ================================================================
   INITIAL DEAL ANIMATION
   ================================================================ */

async function animateInitialDeal(
  data
) {

  renderDealer();

  renderSeats(
    emptyView()
  );


  const counts =
    {};


  for (
    const seat
    of data.active_seats
  ) {
    counts[
      String(seat)
    ] = 0;
  }


  /*
   * First player card.
   */

  for (
    const seat
    of data.active_seats
  ) {

    counts[
      String(seat)
    ] = 1;


    renderSeats(
      partialInitialView(
        data,
        counts
      )
    );


    const cards =
      document.querySelectorAll(
        `#seat${seat} .card`
      );


    cards[
      cards.length - 1
    ]?.classList.add(
      "deal-in"
    );


    await sleep(
      300
    );
  }


  /*
   * Dealer up-card.
   */

  const dealerHand =
    $("dealerHand");


  if (dealerHand) {

    dealerHand.innerHTML =
      cardHTML(
        data.dealer_up,
        false,
        "deal-in"
      );
  }


  await sleep(
    300
  );


  /*
   * Second player card.
   */

  for (
    const seat
    of data.active_seats
  ) {

    counts[
      String(seat)
    ] = 2;


    renderSeats(
      partialInitialView(
        data,
        counts
      )
    );


    const cards =
      document.querySelectorAll(
        `#seat${seat} .card`
      );


    cards[
      cards.length - 1
    ]?.classList.add(
      "deal-in"
    );


    await sleep(
      300
    );
  }


  /*
   * Dealer hole card.
   */

  if (dealerHand) {

    dealerHand.insertAdjacentHTML(
      "beforeend",

      cardHTML(
        null,
        true,
        "deal-in"
      )
    );
  }


  await sleep(
    250
  );


  renderSeats(
    data
  );
}


/* ================================================================
   ACTION TRANSITION
   ================================================================ */

async function animateActionTransition(
  before,
  after,
  seat,
  action
) {

  const oldHandIndex =
    Number(
      before?.current_hand ?? 0
    );


  const beforeHands =
    before?.seats?.[
      String(seat)
    ]?.hands || [];


  const afterHands =
    after?.seats?.[
      String(seat)
    ]?.hands || [];


  renderSeats(
    after
  );


  if (
    action ===
    "split"
  ) {

    const cards =
      document.querySelectorAll(
        `#seat${seat} .card`
      );


    for (
      const element
      of cards
    ) {

      element.classList.add(
        "split-in"
      );

      await sleep(
        90
      );
    }

    return;
  }


  const beforeCount =
    beforeHands[
      oldHandIndex
    ]?.cards?.length || 0;


  const afterCount =
    afterHands[
      oldHandIndex
    ]?.cards?.length || 0;


  if (
    afterCount >
    beforeCount
  ) {

    const targetHand =
      document.querySelectorAll(
        `#seat${seat} .player-hand`
      )[
        oldHandIndex
      ];


    const cards =
      targetHand?.querySelectorAll(
        ".card"
      );


    cards?.[
      cards.length - 1
    ]?.classList.add(
      "deal-in"
    );


    await sleep(
      300
    );
  }
}


/* ================================================================
   DEALER ANIMATION
   ================================================================ */

async function animateDealer(
  cards
) {

  const hand =
    $("dealerHand");


  if (!hand) {
    return;
  }


  hand.innerHTML =
    "";


  for (
    let index = 0;
    index < cards.length;
    index++
  ) {

    hand.insertAdjacentHTML(
      "beforeend",

      cardHTML(
        cards[
          index
        ],
        false,
        "deal-in"
      )
    );


    await sleep(
      index < 2
        ? 300
        : 380
    );
  }
}


/* ================================================================
   ACTION BUTTONS
   ================================================================ */

function actionButton(
  action,
  label,
  cls = ""
) {

  return `
    <button
      type="button"
      class="
        action-btn
        ${cls}
      "
      data-action="${action}"
    >
      ${label}
    </button>
  `;
}


function clearActionBar() {

  const bar =
    $("actionBar");


  if (!bar) {
    return;
  }


  bar.innerHTML =
    `
      <div class="action-placeholder">
        Actions will appear here during play
      </div>
    `;
}


/* ================================================================
   ACTION RENDERING
   ================================================================ */

function renderActions(
  view
) {

  const bar =
    $("actionBar");


  if (!bar) {
    return;
  }


  if (
    !view ||
    view.all_done
  ) {

    clearActionBar();

    return;
  }


  /*
   * Insurance phase.
   */

  if (
    view.decision_phase ===
    "insurance"
  ) {

    const offer =
      view.insurance_offer;


    if (!offer) {

      clearActionBar();

      return;
    }


    let buttons =
      actionButton(
        "insurance",
        `INSURANCE ${fmt(
          offer.amount
        )}`,
        "insurance"
      );


    if (
      offer.even_money
    ) {

      buttons +=
        actionButton(
          "even_money",
          "EVEN MONEY",
          "even-money"
        );
    }


    buttons +=
      actionButton(
        "decline_insurance",
        "NO INSURANCE",
        "secondary"
      );


    bar.innerHTML =
      `
        <div class="action-context">
          SEAT ${offer.seat + 1}
          · INSURANCE DECISION
        </div>

        <div class="action-buttons">
          ${buttons}
        </div>
      `;


    bindActionButtons(
      view
    );

    return;
  }


  const seat =
    view.current_seat;

  const handIndex =
    view.current_hand;


  if (
    seat === null ||
    seat === undefined ||
    handIndex === null ||
    handIndex === undefined
  ) {

    clearActionBar();

    return;
  }


  const hand =
    view.seats?.[
      String(seat)
    ]?.hands?.[
      handIndex
    ];


  if (!hand) {

    clearActionBar();

    return;
  }


  let buttons =
    "";


  if (
    hand.can_hit
  ) {

    buttons +=
      actionButton(
        "hit",
        "HIT",
        "hit"
      );
  }


  if (
    hand.can_stand
  ) {

    buttons +=
      actionButton(
        "stand",
        "STAND",
        "stand"
      );
  }


  if (
    hand.can_double
  ) {

    buttons +=
      actionButton(
        "double",

        hand.free_double
          ? "FREE DOUBLE"
          : "DOUBLE",

        hand.free_double
          ? "free-action"
          : "double"
      );
  }


  if (
    hand.can_split
  ) {

    buttons +=
      actionButton(
        "split",

        hand.free_split
          ? "FREE SPLIT"
          : "SPLIT",

        hand.free_split
          ? "free-action"
          : "split"
      );
  }


  if (
    hand.can_surrender
  ) {

    buttons +=
      actionButton(
        "surrender",
        "SURRENDER",
        "surrender"
      );
  }


  /*
   * Pontoon Double Rescue.
   */

  if (
    hand.can_withdraw_double
  ) {

    buttons =
      actionButton(
        "keep_double",
        "KEEP DOUBLE",
        "stand"
      )
      +
      actionButton(
        "withdraw_double",
        "WITHDRAW DOUBLE",
        "surrender"
      );
  }


  bar.innerHTML =
    `
      <div class="action-context">

        SEAT ${seat + 1}
        · HAND ${handIndex + 1}
        · TOTAL ${hand.total}

        ${
          hand.can_withdraw_double
            ? " · DOUBLE RESCUE"
            : ""
        }

      </div>

      <div class="action-buttons">
        ${buttons}
      </div>
    `;


  bindActionButtons(
    view
  );
}


function bindActionButtons(
  view
) {

  document
    .querySelectorAll(
      "#actionBar [data-action]"
    )
    .forEach(
      (button) => {

        button.addEventListener(
          "click",

          () => {

            performAction(
              button.dataset.action,
              view
            );
          }
        );
      }
    );
}


/* ================================================================
   DEAL ROUND
   ================================================================ */

async function dealRound() {

  if (
    dealing ||
    stateToken ||
    pendingTotal() <= 0
  ) {
    return;
  }


  const activeSeats =
    [];


  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    if (
      mainBet(
        seat
      ) > 0
    ) {

      activeSeats.push(
        seat
      );
    }
  }


  if (
    !activeSeats.length
  ) {

    status(
      "At least one Main wager is required.",
      "bad"
    );

    return;
  }


  /*
   * No side-bet-only seats.
   */

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    const prefix =
      `seat${seat}_`;


    const seatTotal =
      Object.entries(
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


    if (
      seatTotal > 0 &&
      mainBet(
        seat
      ) <= 0
    ) {

      status(
        `Seat ${seat + 1} requires a Main wager.`,
        "bad"
      );

      return;
    }
  }


  const wagered =
    pendingTotal();


  const payloadBets =
    Object.entries(
      bets
    )
      .filter(
        (
          [, amount]
        ) =>
          Number(
            amount
          ) > 0
      )
      .map(
        (
          [
            wager_type,
            amount,
          ]
        ) => {

          const match =
            wager_type.match(
              /^seat(\d+)_/
            );


          return {
            seat:
              Number(
                match?.[1]
              ),

            wager_type,

            amount:
              Number(
                amount
              ),
          };
        }
      );


  dealing =
    true;


  const phase =
    $("phaseLabel");


  if (phase) {
    phase.textContent =
      "DEALING";
  }


  status(
    "Dealing cards…",
    "playing"
  );


  clearActionBar();

  refresh();


  try {

    const response =
      await fetch(
        "/api/solo/blackjack/deal",

        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(
              {
                game:
                  GAME,

                bets:
                  payloadBets,
              }
            ),
        }
      );


    const data =
      await response.json();


    if (
      !response.ok
    ) {

      throw new Error(
        data.error ||
        "Blackjack deal failed"
      );
    }


    stateToken =
      data.state_token;


    currentSeat =
      data.current_seat;


    currentHand =
      data.current_hand;


    lastView =
      data;


    /*
     * Betting chips disappear once accepted by the table.
     */

    bets =
      {};


    refresh();


    await animateInitialDeal(
      data
    );


    renderDealer(
      data.dealer_up
    );


    renderSeats(
      data
    );


    renderActions(
      data
    );


    const activeMetric =
      $("activeMetric");


    if (activeMetric) {

      activeMetric.textContent =
        String(
          data.active_seats?.length ||
          activeSeats.length
        );
    }


    const stakeMetric =
      $("stakeMetric");


    if (stakeMetric) {

      stakeMetric.textContent =
        fmt(
          data.total_wager ??
          wagered
        );
    }


    /*
     * Pontoon immediate payout.
     */

    const immediate =
      Number(
        data.immediate_return || 0
      );


    if (
      immediate > 0
    ) {

      balance +=
        immediate;


      saveBalance();


      const returnMetric =
        $("returnMetric");


      if (returnMetric) {

        returnMetric.textContent =
          fmt(
            immediate
          );
      }
    }


    if (
      data.all_done
    ) {

      dealing =
        false;


      await settleRound();

      return;
    }


    if (
      data.decision_phase ===
      "insurance"
    ) {

      status(
        `Seat ${
          data.current_seat + 1
        } · Insurance decision`,
        "playing"
      );


      if (phase) {
        phase.textContent =
          "INSURANCE";
      }

    } else {

      status(
        `Seat ${
          data.current_seat + 1
        } · Hand ${
          data.current_hand + 1
        }`,
        "playing"
      );


      if (phase) {
        phase.textContent =
          "PLAYER TURN";
      }
    }


  } catch (error) {

    /*
     * The deal did not become a valid active round.
     * Restore the initial chips.
     */

    balance +=
      wagered;


    saveBalance();


    stateToken =
      null;


    lastView =
      null;


    status(
      error.message ||
      "Deal failed.",
      "bad"
    );


    console.error(
      error
    );


    if (phase) {
      phase.textContent =
        "READY";
    }

  } finally {

    dealing =
      false;


    refresh();
  }
}


/* ================================================================
   PLAYER ACTION
   ================================================================ */

async function performAction(
  action,
  view
) {

  if (
    dealing ||
    !stateToken
  ) {
    return;
  }


  const seat =
    view.current_seat;


  const handIndex =
    view.current_hand;


  if (
    seat === null ||
    seat === undefined
  ) {
    return;
  }


  const hand =
    view.seats?.[
      String(seat)
    ]?.hands?.[
      handIndex
    ];


  /*
   * Local affordability checks.
   *
   * Backend remains authoritative for the actual extra stake.
   */

  if (
    action ===
    "double" &&
    !hand?.free_double
  ) {

    const expected =
      Number(
        hand?.stake ||
        hand?.original_stake ||
        0
      );


    if (
      balance <
      expected
    ) {

      status(
        "Not enough credits to Double.",
        "bad"
      );

      return;
    }
  }


  if (
    action ===
    "split" &&
    !hand?.free_split
  ) {

    const expected =
      Number(
        hand?.stake ||
        hand?.original_stake ||
        0
      );


    if (
      balance <
      expected
    ) {

      status(
        "Not enough credits to Split.",
        "bad"
      );

      return;
    }
  }


  if (
    action ===
    "insurance"
  ) {

    const amount =
      Number(
        view
          .insurance_offer
          ?.amount || 0
      );


    if (
      balance <
      amount
    ) {

      status(
        "Not enough credits for Insurance.",
        "bad"
      );

      return;
    }
  }


  dealing =
    true;


  const phase =
    $("phaseLabel");


  if (phase) {
    phase.textContent =
      "ACTION";
  }


  status(
    `${action
      .replaceAll(
        "_",
        " "
      )
      .toUpperCase()}…`,
    "playing"
  );


  document
    .querySelectorAll(
      "#actionBar button"
    )
    .forEach(
      (button) => {

        button.disabled =
          true;
      }
    );


  try {

    const before =
      lastView;


    const response =
      await fetch(
        "/api/solo/blackjack/action",

        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(
              {
                state_token:
                  stateToken,

                seat,

                action,
              }
            ),
        }
      );


    const data =
      await response.json();


    if (
      !response.ok
    ) {

      throw new Error(
        data.error ||
        "Blackjack action failed"
      );
    }


    /*
     * Backend tells us exactly how much extra money was wagered.
     */

    const extra =
      Number(
        data.extra_stake || 0
      );


    if (
      extra > 0
    ) {

      if (
        balance <
        extra
      ) {

        throw new Error(
          "Insufficient local balance for additional wager."
        );
      }


      balance -=
        extra;


      saveBalance();
    }


    /*
     * Pontoon immediate payout / Even Money / rescue.
     */

    const immediate =
      Number(
        data.immediate_return || 0
      );


    if (
      immediate > 0
    ) {

      balance +=
        immediate;


      saveBalance();
    }


    stateToken =
      data.state_token;


    currentSeat =
      data.current_seat;


    currentHand =
      data.current_hand;


    await animateActionTransition(
      before,
      data,
      seat,
      action
    );


    lastView =
      data;


    renderSeats(
      data
    );


    renderActions(
      data
    );


    /*
     * The API exposes cumulative extra_wager through its encoded
     * state only indirectly, but each action exposes extra_stake.
     * Increment the displayed stake using that authoritative value.
     */

    if (
      extra > 0
    ) {

      const stakeMetric =
        $("stakeMetric");


      if (stakeMetric) {

        const previous =
          Number(
            stakeMetric
              .textContent
              .replaceAll(
                ",",
                ""
              )
          ) || 0;


        stakeMetric.textContent =
          fmt(
            previous +
            extra
          );
      }
    }


    if (
      immediate > 0
    ) {

      const returnMetric =
        $("returnMetric");


      if (returnMetric) {

        const previous =
          Number(
            returnMetric
              .textContent
              .replaceAll(
                ",",
                ""
              )
          ) || 0;


        returnMetric.textContent =
          fmt(
            previous +
            immediate
          );
      }
    }


    if (
      data.all_done
    ) {

      dealing =
        false;


      await settleRound();

      return;
    }


    if (
      data.decision_phase ===
      "insurance"
    ) {

      status(
        `Seat ${
          data.current_seat + 1
        } · Insurance decision`,
        "playing"
      );


      if (phase) {
        phase.textContent =
          "INSURANCE";
      }

    } else {

      status(
        `Seat ${
          data.current_seat + 1
        } · Hand ${
          data.current_hand + 1
        }`,
        "playing"
      );


      if (phase) {
        phase.textContent =
          "PLAYER TURN";
      }
    }


  } catch (error) {

    status(
      error.message ||
      "Action failed.",
      "bad"
    );


    console.error(
      error
    );


    renderActions(
      lastView
    );


  } finally {

    dealing =
      false;


    refresh();
  }
}


/* ================================================================
   RESULT LABELS
   ================================================================ */

function resultLabel(
  result
) {

  const labels = {

    win:
      "WIN",

    lose:
      "LOSE",

    push:
      "PUSH",

    blackjack:
      "BLACKJACK",

    pontoon:
      "PONTOON",

    surrender:
      "SURRENDER",

    paid:
      "PAID",

    paid21:
      "21 PAID",

    paid_even_money:
      "EVEN MONEY",

    double_withdrawn:
      "DOUBLE WITHDRAWN",
  };


  return (
    labels[
      result
    ] ||
    String(
      result || ""
    ).toUpperCase()
  );
}


function resultClass(
  result
) {

  if (
    [
      "win",
      "blackjack",
      "pontoon",
      "paid",
      "paid21",
      "paid_even_money",
    ].includes(
      result
    )
  ) {

    return "win";
  }


  if (
    result ===
    "push"
  ) {

    return "push";
  }


  return "lose";
}


/* ================================================================
   SETTLEMENT
   ================================================================ */

async function settleRound() {

  if (
    !stateToken
  ) {
    return;
  }


  dealing =
    true;


  clearActionBar();


  const phase =
    $("phaseLabel");


  if (phase) {
    phase.textContent =
      "DEALER";
  }


  status(
    "Dealer completing hand…",
    "playing"
  );


  try {

    const response =
      await fetch(
        "/api/solo/blackjack/settle",

        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(
              {
                state_token:
                  stateToken,
              }
            ),
        }
      );


    const data =
      await response.json();


    if (
      !response.ok
    ) {

      throw new Error(
        data.error ||
        "Settlement failed"
      );
    }


    const outcome =
      data.outcome;


    await animateDealer(
      outcome.dealer_cards
    );


    const dealerBadge =
      $("dealerBadge");


    if (dealerBadge) {

      if (
        outcome.dealer_bust
      ) {

        dealerBadge.textContent =
          `BUST · ${outcome.dealer_total}`;

      } else if (
        outcome.dealer_blackjack
      ) {

        dealerBadge.textContent =
          GAME === "pontoon"
            ? "PONTOON"
            : "BLACKJACK";

      } else {

        dealerBadge.textContent =
          `TOTAL ${outcome.dealer_total}`;
      }
    }


    /*
     * Render final hands exactly from settlement.
     */

    for (
      const seat
      of outcome.active_seats
    ) {

      const seatData =
        outcome.seats?.[
          String(seat)
        ] ??
        outcome.seats?.[
          seat
        ];


      if (!seatData) {
        continue;
      }


      const seatElement =
        $(
          `seat${seat}`
        );


      const target =
        seatElement
          ?.querySelector(
            ".seat-hands"
          );


      if (!target) {
        continue;
      }


      seatElement
        .classList
        .remove(
          "current-seat"
        );


      seatElement
        .classList
        .add(
          "active-seat"
        );


      target.innerHTML =
        seatData.hands
          .map(
            (
              hand,
              index
            ) => `
              <div class="player-hand">

                <div class="hand-title">
                  HAND ${index + 1}
                </div>


                <div class="hand-cards">

                  ${
                    hand.cards
                      .map(
                        (cardData) =>
                          cardHTML(
                            cardData
                          )
                      )
                      .join("")
                  }

                </div>


                <div class="hand-total">

                  TOTAL ${hand.total}

                  ${
                    hand.free_marker
                      ? " · FREE"
                      : ""
                  }

                </div>


                <div
                  class="
                    seat-result
                    ${resultClass(
                      hand.result
                    )}
                  "
                >
                  ${resultLabel(
                    hand.result
                  )}
                </div>

              </div>
            `
          )
          .join("");
    }


    /*
     * Immediate Pontoon payouts have already been credited during
     * play. Therefore only settlement total_return is added now.
     */

    const settlementReturn =
      Number(
        data.total_return || 0
      );


    balance +=
      settlementReturn;


    saveBalance();


    const economicReturn =
      Number(
        data.total_wager || 0
      )
      +
      Number(
        data.net || 0
      );


    const returnMetric =
      $("returnMetric");


    if (returnMetric) {

      returnMetric.textContent =
        fmt(
          economicReturn
        );
    }


    const stakeMetric =
      $("stakeMetric");


    if (stakeMetric) {

      stakeMetric.textContent =
        fmt(
          data.total_wager
        );
    }


    const net =
      Number(
        data.net || 0
      );


    const netMetric =
      $("netMetric");


    if (netMetric) {

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


    saveHistory(
      net
    );


    status(
      net > 0
        ? `Round complete · +${fmt(net)}`
        : net < 0
          ? `Round complete · ${fmt(net)}`
          : "Round complete · Push",

      net > 0
        ? "good"
        : net < 0
          ? "bad"
          : ""
    );


    if (phase) {
      phase.textContent =
        "COMPLETE";
    }


    stateToken =
      null;


    currentSeat =
      null;


    currentHand =
      null;


    lastView =
      null;


  } catch (error) {

    status(
      error.message ||
      "Settlement failed.",
      "bad"
    );


    console.error(
      error
    );


    if (phase) {
      phase.textContent =
        "ERROR";
    }


  } finally {

    dealing =
      false;


    refresh();
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
          HIST_KEY
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


function saveHistory(
  net
) {

  let items =
    loadHistory();


  items.unshift(
    {
      net:
        Number(net),

      at:
        Date.now(),
    }
  );


  items =
    items.slice(
      0,
      12
    );


  localStorage.setItem(
    HIST_KEY,
    JSON.stringify(
      items
    )
  );


  renderHistory();
}


function renderHistory() {

  const box =
    $("history");


  if (!box) {
    return;
  }


  const items =
    loadHistory();


  if (
    !items.length
  ) {

    box.innerHTML =
      "<br>No rounds yet";

    return;
  }


  box.innerHTML =
    items
      .map(
        (item) => {

          const net =
            Number(
              item.net || 0
            );


          return `
            <div class="history-row">

              <span>
                Round
              </span>

              <strong
                class="${
                  net > 0
                    ? "win"
                    : net < 0
                      ? "lose"
                      : "push"
                }"
              >
                ${
                  net > 0
                    ? "+"
                    : ""
                }${fmt(net)}
              </strong>

            </div>
          `;
        }
      )
      .join("");
}


/* ================================================================
   RULES
   ================================================================ */

function renderRules() {

  const title =
    $("rulesTitle");


  if (title) {

    title.textContent =
      cfg.title;
  }


  const box =
    $("rulesBox");


  if (!box) {
    return;
  }


  box.innerHTML =
    `
      <div class="rules-grid">

        ${
          cfg.pays
            .map(
              (
                [
                  name,
                  payout,
                ]
              ) => `
                <div class="rule-row">

                  <span>
                    ${name}
                  </span>

                  <strong>
                    ${payout}
                  </strong>

                </div>
              `
            )
            .join("")
        }

      </div>


      <div class="rule-note">
        ${cfg.note}
      </div>
    `;
}


/* ================================================================
   CLEAR BETS
   ================================================================ */

function clearBets() {

  if (
    dealing ||
    stateToken
  ) {
    return;
  }


  balance +=
    pendingTotal();


  bets =
    {};


  saveBalance();


  status(
    "Bets cleared."
  );


  refresh();
}


/* ================================================================
   RESET
   ================================================================ */

function resetCredits() {

  if (
    dealing
  ) {
    return;
  }


  if (
    !confirm(
      `Reset credits to ${fmt(
        START_CR
      )}?`
    )
  ) {
    return;
  }


  balance =
    START_CR;


  bets =
    {};


  stateToken =
    null;


  currentSeat =
    null;


  currentHand =
    null;


  lastView =
    null;


  localStorage.removeItem(
    BAL_KEY
  );


  localStorage.removeItem(
    HIST_KEY
  );


  saveBalance();


  renderDealer();


  renderSeats(
    emptyView()
  );


  clearActionBar();


  const dealerBadge =
    $("dealerBadge");


  if (dealerBadge) {
    dealerBadge.textContent =
      "";
  }


  const activeMetric =
    $("activeMetric");


  if (activeMetric) {
    activeMetric.textContent =
      "0";
  }


  const stakeMetric =
    $("stakeMetric");


  if (stakeMetric) {
    stakeMetric.textContent =
      "0";
  }


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


  const phase =
    $("phaseLabel");


  if (phase) {
    phase.textContent =
      "READY";
  }


  renderHistory();


  status(
    "Credits reset."
  );


  refresh();
}


/* ================================================================
   NEW BETTING ROUND
   ================================================================ */

function prepareBettingTable() {

  if (
    stateToken
  ) {
    return;
  }


  const phase =
    $("phaseLabel");


  if (
    phase &&
    phase.textContent ===
    "COMPLETE"
  ) {

    phase.textContent =
      "READY";


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


    status(
      "Place your bets."
    );
  }
}


/* ================================================================
   DOM CONTRACT CHECK

   If this ever fails again, the error will be explicit instead of
   silently rendering an empty Blackjack screen.
   ================================================================ */

function verifyDOM() {

  const requiredIds = [
    "phaseLabel",
    "balDisplay",
    "chipBar",
    "resetBtn",
    "activeMetric",
    "stakeMetric",
    "returnMetric",
    "netMetric",
    "history",
    "statusBar",
    "dealerHand",
    "dealerBadge",
    "seat0",
    "seat1",
    "seat2",
    "actionBar",
    "betZoneWrap",
    "bzSeats",
    "pendingTotal",
    "clearBtn",
    "dealBtn",
    "rulesTitle",
    "rulesBox",
  ];


  const missing =
    requiredIds.filter(
      (id) =>
        !$(id)
    );


  if (
    missing.length
  ) {

    throw new Error(
      `Blackjack HTML/JS mismatch. Missing elements: ${missing.join(", ")}`
    );
  }


  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {

    const seatElement =
      $(
        `seat${seat}`
      );


    if (
      !seatElement.querySelector(
        ".seat-hands"
      )
    ) {

      throw new Error(
        `Blackjack HTML/JS mismatch: seat${seat} has no .seat-hands container`
      );
    }
  }
}


/* ================================================================
   INITIALISE
   ================================================================ */

function init() {

  try {

    verifyDOM();


    saveBalance();


    renderChips();


    renderBetZone();


    renderDealer();


    renderSeats(
      emptyView()
    );


    renderRules();


    renderHistory();


    clearActionBar();


    const phase =
      $("phaseLabel");


    phase.textContent =
      "READY";


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


    $("clearBtn")
      .addEventListener(
        "click",
        clearBets
      );


    $("dealBtn")
      .addEventListener(
        "click",
        dealRound
      );


    $("resetBtn")
      .addEventListener(
        "click",
        resetCredits
      );


    status(
      "Place your bets."
    );


    refresh();


    console.log(
      "[BLACKJACK]",
      "Frontend initialised:",
      GAME
    );


  } catch (error) {

    console.error(
      "[BLACKJACK INIT ERROR]",
      error
    );


    /*
     * Make initialization failures visible directly on the page.
     */

    const statusElement =
      $("statusBar");


    if (statusElement) {

      statusElement.className =
        "status-bar bad";


      statusElement.textContent =
        `BLACKJACK FRONTEND ERROR: ${error.message}`;
    }


    const phase =
      $("phaseLabel");


    if (phase) {

      phase.textContent =
        "ERROR";
    }
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
    init
  );

} else {

  init();
}