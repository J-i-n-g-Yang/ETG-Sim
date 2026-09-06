/* ================================================================
   ETG SIM — DUELING 8'S 21+ SOLO

   Three-seat frontend.

   Each seat:
   - Main
   - 6-7-8
   - Superb 8s
   - Tie on 18
   - 21+

   Gameplay:
   - Shared Dealer
   - Permanent 8♠ for Dealer
   - Permanent 8♠ for every active Player seat
   - Up to 3 active seats
   - Up to 4 hands per seat after splitting
   - Only 8s may be split
   - Partial double supported

   Presentation:
   - Sequential initial card distribution
   - Animated player action cards
   - Sequential Dealer draw reveal
   ================================================================ */

const GAME =
  window.DUELING8_GAME ||
  "dueling_8s_21";

const MAX_BET =
  Number(
    window.DUELING8_MAX
  );

const STARTING_CREDITS =
  Number(
    window.DUELING8_START
  );

const $ = (id) =>
  document.getElementById(id);

const fmt = (value) =>
  Number(
    value || 0
  ).toLocaleString(
    undefined,
    {
      maximumFractionDigits: 2,
    }
  );

const sleep = (ms) =>
  new Promise(
    (resolve) =>
      setTimeout(
        resolve,
        ms
      )
  );


/* ================================================================
   ANIMATION TIMING
   ================================================================ */

const INITIAL_DEAL_DELAY =
  360;

const ACTION_DEAL_DELAY =
  300;

const DEALER_DEAL_DELAY =
  390;


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
  "etg_dueling8_balance";

const HISTORY_KEY =
  "etg_dueling8_history";


/* ================================================================
   STATE
   ================================================================ */

let selectedChip =
  1000;

let pendingBets = {
  "0": {},
  "1": {},
  "2": {},
};

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

let history = [];

try {
  history =
    JSON.parse(
      localStorage.getItem(
        HISTORY_KEY
      ) || "[]"
    );
} catch {
  history = [];
}

let stateToken =
  null;

let roundState =
  null;

let busy =
  false;


/* ================================================================
   DEBUG
   ================================================================ */

const D8_DEBUG =
  false;


function d8Log(
  label,
  data = undefined
) {
  if (!D8_DEBUG) {
    return;
  }

  const time =
    performance
      .now()
      .toFixed(1);

  if (
    data === undefined
  ) {
    console.log(
      `[D8 ${time}ms] ${label}`
    );

    return;
  }

  console.log(
    `[D8 ${time}ms] ${label}`,
    data
  );
}


d8Log(
  "CONTROLLER LOADED",
  {
    src:
      import.meta.url,

    href:
      window.location.href,

    initialDealDelay:
      INITIAL_DEAL_DELAY,

    actionDealDelay:
      ACTION_DEAL_DELAY,

    dealerDealDelay:
      DEALER_DEAL_DELAY,
  }
);


/* ================================================================
   BASIC HELPERS
   ================================================================ */

function chipLabel(
  value
) {
  return (
    value >= 1000
      ? `${value / 1000}K`
      : String(value)
  );
}


function message(
  text = ""
) {
  const element =
    $("message");

  if (element) {
    element.textContent =
      text;
  }
}


function saveBalance() {
  localStorage.setItem(
    BALANCE_KEY,
    String(balance)
  );

  const display =
    $("balanceDisplay");

  if (display) {
    display.textContent =
      fmt(balance);
  }
}


function saveHistory() {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(
      history
    )
  );
}


function resetPendingBets() {
  pendingBets = {
    "0": {},
    "1": {},
    "2": {},
  };
}


function pendingSeatTotal(
  seat
) {
  return Object
    .values(
      pendingBets[
        String(seat)
      ] || {}
    )
    .reduce(
      (
        total,
        amount
      ) =>
        total +
        Number(amount),
      0
    );
}


function pendingTotal() {
  return (
    pendingSeatTotal(0) +
    pendingSeatTotal(1) +
    pendingSeatTotal(2)
  );
}


function activePendingSeats() {
  const seats = [];

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {
    if (
      Number(
        pendingBets[
          String(seat)
        ]?.main || 0
      ) > 0
    ) {
      seats.push(
        seat
      );
    }
  }

  return seats;
}


/* ================================================================
   BROWSER PAINT HELPER
   ================================================================ */

function nextPaint() {
  return new Promise(
    (resolve) => {
      requestAnimationFrame(
        () => {
          requestAnimationFrame(
            resolve
          );
        }
      );
    }
  );
}


/* ================================================================
   CARDS
   ================================================================ */

function suitSymbol(
  suit
) {
  return (
    {
      S: "♠",
      H: "♥",
      D: "♦",
      C: "♣",
    }[
      suit
    ] || suit
  );
}


function cardHTML(
  card,
  extraClass = ""
) {
  if (!card) {
    return "";
  }

  const red =
    card.suit === "H" ||
    card.suit === "D";

  return `
    <div
      class="
        card
        ${red ? "red" : ""}
        ${
          card.permanent
            ? "permanent"
            : ""
        }
        ${extraClass}
      "
    >
      <div>
        ${card.rank}
      </div>

      <div class="suit">
        ${suitSymbol(
          card.suit
        )}
      </div>
    </div>
  `;
}


function renderCards(
  cards
) {
  return (
    cards || []
  )
    .map(
      (card) =>
        cardHTML(
          card
        )
    )
    .join("");
}


/* ================================================================
   DEAL ANIMATION CSS
   ================================================================ */

function installDealAnimationStyles() {
  if (
    document.getElementById(
      "dueling8DealAnimationStyles"
    )
  ) {
    return;
  }

  const style =
    document.createElement(
      "style"
    );

  style.id =
    "dueling8DealAnimationStyles";

  style.textContent = `
    @keyframes dueling8DealIn {
      0% {
        opacity: 0;
        transform:
          translate3d(44px, -58px, 0)
          rotate(9deg)
          scale(.82);
      }

      68% {
        opacity: 1;
        transform:
          translate3d(-3px, 4px, 0)
          rotate(-1.5deg)
          scale(1.025);
      }

      100% {
        opacity: 1;
        transform:
          translate3d(0, 0, 0)
          rotate(0deg)
          scale(1);
      }
    }

    .card.deal-in {
      animation:
        dueling8DealIn
        320ms
        cubic-bezier(.2,.8,.2,1)
        both;

      transform-origin:
        50% 50%;

      will-change:
        transform,
        opacity;
    }
  `;

  document.head.appendChild(
    style
  );
}


/* ================================================================
   CHIPS
   ================================================================ */

function renderChips() {
  const bar =
    $("chipBar");

  if (!bar) {
    return;
  }

  bar.innerHTML =
    "";

  CHIPS.forEach(
    (value) => {
      const button =
        document.createElement(
          "button"
        );

      button.className =
        `chip${
          selectedChip ===
          value
            ? " active"
            : ""
        }`;

      button.textContent =
        chipLabel(
          value
        );

      button.style.background =
        `radial-gradient(
          circle at 35% 30%,
          ${CHIP_COLORS[value]},
          #111
        )`;

      button.onclick = () => {
        if (
          busy ||
          stateToken
        ) {
          return;
        }

        selectedChip =
          value;

        renderChips();
      };

      bar.appendChild(
        button
      );
    }
  );
}


/* ================================================================
   BETTING
   ================================================================ */

function placeBet(
  seat,
  wager
) {
  if (
    busy ||
    stateToken
  ) {
    return;
  }

  seat =
    Number(seat);

  if (
    ![
      0,
      1,
      2,
    ].includes(seat)
  ) {
    return;
  }

  /*
   * Side wagers require a Main wager.
   */

  if (
    wager !== "main" &&
    Number(
      pendingBets[
        String(seat)
      ]?.main || 0
    ) <= 0
  ) {
    message(
      `Place Seat ${
        seat + 1
      } Main first.`
    );

    return;
  }

  if (
    balance <
    selectedChip
  ) {
    message(
      "Insufficient balance."
    );

    return;
  }

  if (
    pendingTotal() +
      selectedChip >
    MAX_BET
  ) {
    message(
      `Maximum total table stake is ${fmt(
        MAX_BET
      )}.`
    );

    return;
  }

  const seatKey =
    String(seat);

  pendingBets[
    seatKey
  ][
    wager
  ] =
    Number(
      pendingBets[
        seatKey
      ][
        wager
      ] || 0
    ) +
    selectedChip;

  balance -=
    selectedChip;

  saveBalance();

  message("");

  refresh();
}


function bindBets() {
  document
    .querySelectorAll(
      "[data-seat][data-wager]"
    )
    .forEach(
      (element) => {
        element.onclick =
          () => {
            placeBet(
              Number(
                element.dataset.seat
              ),
              element.dataset.wager
            );
          };
      }
    );
}


/* ================================================================
   CLEAR BETS
   ================================================================ */

function clearBets() {
  if (
    busy ||
    stateToken
  ) {
    return;
  }

  balance +=
    pendingTotal();

  resetPendingBets();

  saveBalance();

  message("");

  refresh();
}


/* ================================================================
   BUILD SERVER BET ARRAY
   ================================================================ */

function buildBetArray() {
  const bets = [];

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {
    const seatBets =
      pendingBets[
        String(seat)
      ] || {};

    Object
      .entries(
        seatBets
      )
      .forEach(
        (
          [
            wager_type,
            amount,
          ]
        ) => {
          amount =
            Number(amount);

          if (
            amount <= 0
          ) {
            return;
          }

          bets.push({
            seat,
            wager_type,
            amount,
          });
        }
      );
  }

  return bets;
}


/* ================================================================
   REFRESH BETTING UI
   ================================================================ */

function refresh() {
  const pending =
    pendingTotal();

  const pendingDisplay =
    $("pendingTotal");

  if (pendingDisplay) {
    pendingDisplay.textContent =
      fmt(pending);
  }

  const stake =
    $("stakeMetric");

  if (stake) {
    stake.textContent =
      stateToken &&
      roundState
        ? fmt(
            roundState.total_wager ||
            0
          )
        : fmt(
            pending
          );
  }

  const dealButton =
    $("dealBtn");

  if (dealButton) {
    dealButton.disabled =
      busy ||
      !!stateToken ||
      activePendingSeats()
        .length === 0;
  }

  const clearButton =
    $("clearBtn");

  if (clearButton) {
    clearButton.disabled =
      busy ||
      !!stateToken ||
      pending <= 0;
  }

  document
    .querySelectorAll(
      "[data-seat][data-wager]"
    )
    .forEach(
      (element) => {
        const seat =
          String(
            element.dataset.seat
          );

        const wager =
          element.dataset.wager;

        const amount =
          Number(
            pendingBets[
              seat
            ]?.[
              wager
            ] || 0
          );

        let badge =
          element.querySelector(
            ".badge"
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
            "badge";

          element.appendChild(
            badge
          );
        }

        badge.textContent =
          fmt(amount);
      }
    );

  updateActions();
}


/* ================================================================
   CURRENT HAND
   ================================================================ */

function currentSeatState() {
  if (
    !roundState ||
    roundState.current_seat ===
      null ||
    roundState.current_seat ===
      undefined
  ) {
    return null;
  }

  return (
    roundState.seats?.[
      String(
        roundState.current_seat
      )
    ] || null
  );
}


function currentHandState() {
  const seat =
    currentSeatState();

  if (!seat) {
    return null;
  }

  return (
    seat.hands?.[
      roundState.current_hand
    ] || null
  );
}


/* ================================================================
   ACTION BUTTONS
   ================================================================ */

function updateActions() {
  const hand =
    currentHandState();

  const actionSet =
    new Set(
      hand?.available_actions ||
      []
    );

  const mapping = {
    hitBtn:
      "hit",

    standBtn:
      "stand",

    doubleBtn:
      "double",

    splitBtn:
      "split",

    surrenderBtn:
      "surrender",
  };

  Object
    .entries(
      mapping
    )
    .forEach(
      (
        [
          id,
          actionName,
        ]
      ) => {
        const button =
          $(id);

        if (!button) {
          return;
        }

        button.disabled =
          busy ||
          !actionSet.has(
            actionName
          );
      }
    );

  if (
    !actionSet.has(
      "double"
    )
  ) {
    $("doubleBox")
      ?.classList
      .remove(
        "active"
      );
  }
}


/* ================================================================
   INITIAL SEAT PLACEHOLDER
   ================================================================ */

function initialSeatHTML(
  seat
) {
  return `
    <div class="hand">
      <div
        style="
          opacity:.65;
          padding:14px 4px;
        "
      >
        ${
          Number(
            pendingBets[
              String(seat)
            ]?.main || 0
          ) > 0
            ? "Ready to deal"
            : "Place Main to activate"
        }
      </div>
    </div>
  `;
}


/* ================================================================
   RENDER ROUND
   ================================================================ */

function renderRound() {
  const dealerCards =
    $("dealerCards");

  const dealerTotal =
    $("dealerTotal");

  if (!roundState) {
    if (dealerCards) {
      dealerCards.innerHTML =
        cardHTML({
          rank:
            "8",

          suit:
            "S",

          permanent:
            true,
        });
    }

    if (dealerTotal) {
      dealerTotal.textContent =
        "Dealer total —";
    }

    for (
      let seat = 0;
      seat < 3;
      seat++
    ) {
      const area =
        $(
          `seat${seat}Hands`
        );

      if (area) {
        area.innerHTML =
          initialSeatHTML(
            seat
          );
      }

      $(
        `seat${seat}`
      )?.classList.remove(
        "active-seat"
      );
    }

    refresh();

    return;
  }


  /*
   * Dealer.
   */

  if (dealerCards) {
    dealerCards.innerHTML =
      renderCards(
        roundState.dealer_cards ||
        roundState.outcome
          ?.dealer_cards ||
        []
      );
  }

  if (dealerTotal) {
    if (
      roundState.outcome
    ) {
      dealerTotal.textContent =
        `Dealer total ${
          roundState.outcome
            .dealer_total
        }${
          roundState.outcome
            .dealer_bust
            ? " · BUST"
            : ""
        }`;
    } else {
      dealerTotal.textContent =
        "Dealer showing 8";
    }
  }


  /*
   * Player seats.
   */

  for (
    let seat = 0;
    seat < 3;
    seat++
  ) {
    const seatElement =
      $(
        `seat${seat}`
      );

    const handArea =
      $(
        `seat${seat}Hands`
      );

    if (
      !seatElement ||
      !handArea
    ) {
      continue;
    }

    seatElement.classList.remove(
      "active-seat"
    );

    const isActiveSeat =
      !roundState.outcome &&
      Number(
        roundState.current_seat
      ) === seat;

    if (isActiveSeat) {
      seatElement.classList.add(
        "active-seat"
      );
    }

    const seatData =
      roundState.seats?.[
        String(seat)
      ];

    const settledSeat =
      roundState.outcome
        ?.hands_by_seat?.[
          String(seat)
        ];

    const hands =
      settledSeat?.hands ||
      seatData?.hands ||
      [];

    if (!hands.length) {
      handArea.innerHTML =
        `
          <div class="hand">
            <div
              style="
                opacity:.5;
                padding:14px 4px;
              "
            >
              Not in round
            </div>
          </div>
        `;

      continue;
    }

    handArea.innerHTML =
      hands
        .map(
          (
            hand,
            index
          ) => {
            const active =
              isActiveSeat &&
              index ===
                Number(
                  roundState
                    .current_hand
                );

            const total =
              Number(
                hand.total ?? 0
              );

            const result =
              hand.result
                ? ` · ${String(
                    hand.result
                  ).toUpperCase()}`
                : "";

            const split =
              hand.from_split
                ? " · SPLIT"
                : "";

            const doubled =
              Number(
                hand.double_extra ||
                0
              ) > 0
                ? " · DOUBLE"
                : "";

            return `
              <div
                class="
                  hand
                  ${
                    active
                      ? "active"
                      : ""
                  }
                  ${
                    hand.status &&
                    hand.status !==
                      "playing"
                      ? "done"
                      : ""
                  }
                "
              >
                <div>
                  <strong>
                    HAND ${
                      index + 1
                    }
                  </strong>

                  ${split}
                  ${doubled}
                </div>

                <div class="cards">
                  ${renderCards(
                    hand.cards
                  )}
                </div>

                <div class="hand-total">
                  TOTAL ${total}

                  ${
                    hand.bust
                      ? " · BUST"
                      : ""
                  }

                  ${result}
                </div>

                <div
                  style="
                    font-size:12px;
                    margin-top:5px;
                  "
                >
                  STAKE
                  ${fmt(
                    hand.stake || 0
                  )}
                </div>
              </div>
            `;
          }
        )
        .join("");
  }

  refresh();
}

/* ================================================================
   INITIAL DEAL ANIMATION

   IMPORTANT:
   During this function roundState remains null.

   We directly control the card DOM so the complete backend state
   cannot accidentally render all cards at once.

   Distribution order:

       Seat 1 permanent 8♠
       Seat 2 permanent 8♠
       Seat 3 permanent 8♠
       Dealer permanent 8♠
       Seat 1 random card
       Seat 2 random card
       Seat 3 random card

   Only active seats participate.
   ================================================================ */

async function animateInitialDeal(
  data
) {
  d8Log(
    "INITIAL DEAL START",
    data
  );

  const activeSeats =
    Array.isArray(
      data.active_seats
    )
      ? data.active_seats
          .map(
            Number
          )
          .filter(
            Number.isInteger
          )
      : [];

  d8Log(
    "ACTIVE SEATS",
    activeSeats
  );


  const dealerCards =
    $("dealerCards");

  const dealerTotal =
    $("dealerTotal");


  /*
   * CRITICAL:
   *
   * Keep the authoritative backend state away from renderRound()
   * until every initial card has physically been presented.
   */

  roundState =
    null;


  /* ============================================================
     CLEAR TABLE
     ============================================================ */

  if (dealerCards) {
    dealerCards.innerHTML =
      "";
  }

  if (dealerTotal) {
    dealerTotal.textContent =
      "DEALING";
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

    const area =
      $(
        `seat${seat}Hands`
      );

    seatElement
      ?.classList
      .remove(
        "active-seat"
      );

    if (!area) {
      continue;
    }


    /*
     * Inactive seat.
     */

    if (
      !activeSeats.includes(
        seat
      )
    ) {
      area.innerHTML =
        `
          <div class="hand">
            <div
              style="
                opacity:.5;
                padding:14px 4px;
              "
            >
              Not in round
            </div>
          </div>
        `;

      continue;
    }


    /*
     * Active seat.
     *
     * Create a completely empty card container.
     */

    const hand =
      data.seats?.[
        String(seat)
      ]?.hands?.[0];


    area.innerHTML =
      `
        <div class="hand">

          <div>
            <strong>
              HAND 1
            </strong>
          </div>

          <div
            class="cards"
            id="seat${seat}DealCards"
          ></div>

          <div
            class="hand-total"
            id="seat${seat}DealTotal"
          >
            DEALING
          </div>

          <div
            style="
              font-size:12px;
              margin-top:5px;
            "
            id="seat${seat}DealStake"
          >
            ${
              hand
                ? `STAKE ${fmt(
                    hand.stake || 0
                  )}`
                : ""
            }
          </div>

        </div>
      `;
  }


  /*
   * Make sure the EMPTY table reaches the screen before any card
   * is inserted.
   */

  await nextPaint();

  await sleep(
    80
  );

  d8Log(
    "EMPTY TABLE PAINTED"
  );


  /* ============================================================
     PASS 1 — PLAYER PERMANENT 8♠
     ============================================================ */

  for (
    const seat
    of activeSeats
  ) {
    const hand =
      data.seats?.[
        String(seat)
      ]?.hands?.[0];

    const card =
      hand?.cards?.[0];

    const container =
      $(
        `seat${seat}DealCards`
      );


    if (
      !card ||
      !container
    ) {
      continue;
    }


    d8Log(
      `PLAYER ${seat + 1} CARD 1`,
      card
    );


    /*
     * Insert exactly ONE card.
     */

    container.insertAdjacentHTML(
      "beforeend",
      cardHTML(
        card,
        "deal-in"
      )
    );


    /*
     * Force the inserted card to paint before sleeping.
     */

    await nextPaint();


    /*
     * Leave enough time for the player to visibly see this card
     * arrive before the next card is inserted.
     */

    await sleep(
      INITIAL_DEAL_DELAY
    );
  }


  /* ============================================================
     DEALER PERMANENT 8♠
     ============================================================ */

  const dealerPermanent =
    data.dealer_cards?.[0] ||
    data.dealer_up ||
    {
      rank:
        "8",

      suit:
        "S",

      permanent:
        true,
    };


  d8Log(
    "DEALER CARD 1",
    dealerPermanent
  );


  if (dealerCards) {
    dealerCards.insertAdjacentHTML(
      "beforeend",
      cardHTML(
        dealerPermanent,
        "deal-in"
      )
    );
  }


  if (dealerTotal) {
    dealerTotal.textContent =
      "Dealer showing 8";
  }


  await nextPaint();

  await sleep(
    INITIAL_DEAL_DELAY
  );


  /* ============================================================
     PASS 2 — PLAYER RANDOM CARDS
     ============================================================ */

  for (
    const seat
    of activeSeats
  ) {
    const hand =
      data.seats?.[
        String(seat)
      ]?.hands?.[0];

    const card =
      hand?.cards?.[1];

    const container =
      $(
        `seat${seat}DealCards`
      );


    if (
      !card ||
      !container
    ) {
      continue;
    }


    d8Log(
      `PLAYER ${seat + 1} CARD 2`,
      card
    );


    /*
     * Insert exactly ONE second card.
     */

    container.insertAdjacentHTML(
      "beforeend",
      cardHTML(
        card,
        "deal-in"
      )
    );


    /*
     * Do NOT renderRound() here.
     *
     * Doing so would reveal the entire authoritative hand.
     */

    await nextPaint();


    /*
     * Only now reveal the hand total.
     */

    const total =
      $(
        `seat${seat}DealTotal`
      );

    if (total) {
      total.textContent =
        `TOTAL ${Number(
          hand.total ?? 0
        )}${
          hand.bust
            ? " · BUST"
            : ""
        }`;
    }


    await sleep(
      INITIAL_DEAL_DELAY
    );
  }


  /*
   * Hold the completed physical deal briefly.
   */

  await sleep(
    180
  );


  /* ============================================================
     HAND CONTROL BACK TO AUTHORITATIVE STATE
     ============================================================ */

  roundState =
    data;

  renderRound();


  d8Log(
    "INITIAL DEAL COMPLETE"
  );
}


/* ================================================================
   PLAYER ACTION TRANSITION

   Hit / Double:
       animate the newly received card.

   Split:
       animate the newly dealt card on each split hand.
   ================================================================ */

async function animateActionTransition(
  before,
  after
) {
  const seat =
    Number(
      before?.current_seat
    );

  const handIndex =
    Number(
      before?.current_hand
    );


  if (
    !Number.isInteger(
      seat
    ) ||
    !Number.isInteger(
      handIndex
    )
  ) {
    roundState =
      after;

    renderRound();

    return;
  }


  const beforeHands =
    before?.seats?.[
      String(seat)
    ]?.hands ||
    [];

  const afterHands =
    after?.seats?.[
      String(seat)
    ]?.hands ||
    [];


  const beforeCount =
    beforeHands[
      handIndex
    ]?.cards?.length ||
    0;

  const afterCount =
    afterHands[
      handIndex
    ]?.cards?.length ||
    0;


  /*
   * Install authoritative post-action state.
   */

  roundState =
    after;

  renderRound();

  await nextPaint();


  /* ============================================================
     HIT / DOUBLE
     ============================================================ */

  if (
    afterCount >
    beforeCount
  ) {
    const handArea =
      $(
        `seat${seat}Hands`
      );

    const handElements =
      handArea
        ?.querySelectorAll(
          ".hand"
        );

    const cards =
      handElements?.[
        handIndex
      ]?.querySelectorAll(
        ".card"
      );

    const newest =
      cards?.[
        cards.length - 1
      ];


    if (newest) {
      /*
       * Restart animation reliably even if this DOM element
       * already inherited the class.
       */

      newest.classList.remove(
        "deal-in"
      );

      void newest.offsetWidth;

      newest.classList.add(
        "deal-in"
      );
    }


    await sleep(
      ACTION_DEAL_DELAY
    );

    return;
  }


  /* ============================================================
     SPLIT
     ============================================================ */

  if (
    afterHands.length >
    beforeHands.length
  ) {
    const handArea =
      $(
        `seat${seat}Hands`
      );

    const handElements =
      handArea
        ?.querySelectorAll(
          ".hand"
        );


    /*
     * The original hand was replaced by two hands.
     *
     * Animate the newly drawn second card of each resulting hand.
     */

    for (
      let index =
        handIndex;
      index <=
        handIndex + 1;
      index++
    ) {
      const cards =
        handElements?.[
          index
        ]?.querySelectorAll(
          ".card"
        );

      const newest =
        cards?.[
          cards.length - 1
        ];


      if (!newest) {
        continue;
      }


      newest.classList.remove(
        "deal-in"
      );

      void newest.offsetWidth;

      newest.classList.add(
        "deal-in"
      );


      await sleep(
        ACTION_DEAL_DELAY
      );
    }
  }
}


/* ================================================================
   DEALER ANIMATION

   Settlement already contains the final Dealer hand.

   Do NOT render the settlement immediately. Instead rebuild the
   Dealer hand card-by-card, then install the final result.
   ================================================================ */

async function animateDealer(
  cards
) {
  const area =
    $("dealerCards");

  const total =
    $("dealerTotal");


  if (!area) {
    return;
  }


  const dealerCards =
    Array.isArray(
      cards
    )
      ? cards
      : [];


  /*
   * Completely clear Dealer display first.
   */

  area.innerHTML =
    "";


  if (total) {
    total.textContent =
      "Dealer drawing...";
  }


  await nextPaint();


  /* ============================================================
     PERMANENT DEALER 8♠
     ============================================================ */

  const permanent =
    dealerCards[0] ||
    {
      rank:
        "8",

      suit:
        "S",

      permanent:
        true,
    };


  area.insertAdjacentHTML(
    "beforeend",
    cardHTML(
      permanent,
      "deal-in"
    )
  );


  if (total) {
    total.textContent =
      "Dealer showing 8";
  }


  await nextPaint();

  await sleep(
    DEALER_DEAL_DELAY
  );


  /* ============================================================
     REMAINING DEALER CARDS
     ============================================================ */

  for (
    let index = 1;
    index < dealerCards.length;
    index++
  ) {
    area.insertAdjacentHTML(
      "beforeend",
      cardHTML(
        dealerCards[
          index
        ],
        "deal-in"
      )
    );


    if (total) {
      total.textContent =
        "Dealer drawing...";
    }


    await nextPaint();

    await sleep(
      DEALER_DEAL_DELAY
    );
  }


  await sleep(
    160
  );
}


/* ================================================================
   JSON POST
   ================================================================ */

async function jsonPost(
  url,
  body
) {
  const response =
    await fetch(
      url,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify(
            body
          ),
      }
    );


  let data;


  try {
    data =
      await response.json();

  } catch {
    throw new Error(
      `Server returned HTTP ${response.status}`
    );
  }


  if (
    !response.ok
  ) {
    throw new Error(
      data.error ||
      "Request failed"
    );
  }


  return data;
}


/* ================================================================
   DEAL
   ================================================================ */

async function deal() {
  if (
    busy ||
    stateToken
  ) {
    return;
  }


  if (
    activePendingSeats()
      .length === 0
  ) {
    message(
      "Place a Main wager on at least one seat."
    );

    return;
  }


  const wagered =
    pendingTotal();

  const bets =
    buildBetArray();


  d8Log(
    "DEAL BUTTON EXECUTION",
    {
      bets,
      wagered,
    }
  );


  busy =
    true;


  const phaseLabel =
    $("phaseLabel");

  if (phaseLabel) {
    phaseLabel.textContent =
      "DEALING";
  }


  refresh();

  message("");


  try {
    d8Log(
      "SENDING DEAL REQUEST"
    );


    const data =
      await jsonPost(
        "/api/solo/dueling-8s/deal",
        {
          game:
            GAME,

          bets,
        }
      );


    d8Log(
      "DEAL RESPONSE RECEIVED",
      {
        active_seats:
          data.active_seats,

        current_seat:
          data.current_seat,

        current_hand:
          data.current_hand,

        all_done:
          data.all_done,

        dealer_cards:
          data.dealer_cards,

        seats:
          data.seats,
      }
    );


    /*
     * Save only the opaque backend state token here.
     *
     * DO NOT:
     *
     *     roundState = data;
     *
     * before animateInitialDeal().
     *
     * Doing so would allow another renderer to expose the entire
     * backend response before the sequential deal is finished.
     */

    stateToken =
      data.state_token;


    resetPendingBets();


    d8Log(
      "CALLING INITIAL DEAL ANIMATION"
    );


    await animateInitialDeal(
      data
    );


    d8Log(
      "INITIAL DEAL ANIMATION RETURNED"
    );


    /*
     * It is possible for the initial state to already have no
     * decisions remaining.
     */

    if (
      data.all_done
    ) {
      await settle();

      return;
    }


    if (phaseLabel) {
      phaseLabel.textContent =
        `SEAT ${
          Number(
            data.current_seat
          ) + 1
        }`;
    }


    message(
      `Seat ${
        Number(
          data.current_seat
        ) + 1
      }, Hand ${
        Number(
          data.current_hand
        ) + 1
      }: choose an action.`
    );

  } catch (error) {
    /*
     * Deal failed.
     *
     * Pending wagers had already been deducted locally, therefore
     * restore them.
     */

    balance +=
      wagered;


    resetPendingBets();

    saveBalance();


    stateToken =
      null;

    roundState =
      null;


    message(
      error.message
    );


    console.error(
      error
    );


    if (phaseLabel) {
      phaseLabel.textContent =
        "BETTING";
    }


    renderRound();

  } finally {
    busy =
      false;


    refresh();


    d8Log(
      "DEAL FUNCTION FINISHED"
    );
  }
}


/* ================================================================
   PLAYER ACTION
   ================================================================ */

async function action(
  name,
  extra = {}
) {
  if (
    busy ||
    !stateToken ||
    !roundState
  ) {
    return;
  }


  const seat =
    Number(
      roundState.current_seat
    );

  const handIndex =
    Number(
      roundState.current_hand
    );


  if (
    !Number.isInteger(
      seat
    ) ||
    !Number.isInteger(
      handIndex
    )
  ) {
    return;
  }


  const before =
    roundState;


  busy =
    true;


  const phaseLabel =
    $("phaseLabel");

  if (phaseLabel) {
    phaseLabel.textContent =
      `SEAT ${seat + 1}`;
  }


  refresh();

  message("");


  try {
    const data =
      await jsonPost(
        "/api/solo/dueling-8s/action",
        {
          state_token:
            stateToken,

          seat,

          hand_index:
            handIndex,

          action:
            name,

          ...extra,
        }
      );


    const extraStake =
      Number(
        data.extra_stake ||
        0
      );


    if (
      extraStake >
      balance
    ) {
      throw new Error(
        "Insufficient balance for additional stake."
      );
    }


    balance -=
      extraStake;


    saveBalance();


    stateToken =
      data.state_token;


    $("doubleBox")
      ?.classList
      .remove(
        "active"
      );


    /*
     * Animate the state transition before allowing another action.
     */

    await animateActionTransition(
      before,
      data
    );


    if (
      data.all_done
    ) {
      await settle();

      return;
    }


    if (phaseLabel) {
      phaseLabel.textContent =
        `SEAT ${
          Number(
            data.current_seat
          ) + 1
        }`;
    }


    message(
      `Seat ${
        Number(
          data.current_seat
        ) + 1
      }, Hand ${
        Number(
          data.current_hand
        ) + 1
      }: choose an action.`
    );

  } catch (error) {
    message(
      error.message
    );


    console.error(
      error
    );

  } finally {
    busy =
      false;

    refresh();
  }
}


/* ================================================================
   SETTLE
   ================================================================ */

async function settle() {
  if (
    !stateToken
  ) {
    return;
  }


  const phaseLabel =
    $("phaseLabel");


  if (phaseLabel) {
    phaseLabel.textContent =
      "DEALER";
  }


  message(
    "Dealer drawing..."
  );


  const data =
    await jsonPost(
      "/api/solo/dueling-8s/settle",
      {
        state_token:
          stateToken,
      }
    );


  /*
   * IMPORTANT:
   *
   * The response already contains every Dealer card.
   * Do not assign it to roundState yet.
   *
   * Keep the current player table visible while the Dealer cards
   * are presented sequentially.
   */

  await animateDealer(
    data.outcome
      ?.dealer_cards ||
    []
  );


  /*
   * Settlement animation is complete.
   *
   * Apply monetary result.
   */

  balance +=
    Number(
      data.total_return ||
      0
    );


  saveBalance();


  const returnMetric =
    $("returnMetric");


  if (returnMetric) {
    returnMetric.textContent =
      fmt(
        data.total_return
      );
  }


  const netMetric =
    $("netMetric");


  if (netMetric) {
    netMetric.textContent =
      `${
        Number(
          data.net
        ) > 0
          ? "+"
          : ""
      }${fmt(
        data.net
      )}`;
  }


  /*
   * Only NOW expose the complete settlement.
   */

  roundState = {
    ...data,

    dealer_cards:
      data.outcome
        ?.dealer_cards ||
      [],

    seats:
      {},

    current_seat:
      null,

    current_hand:
      null,

    outcome:
      data.outcome,
  };


  renderRound();


  /* ============================================================
     HISTORY
     ============================================================ */

  history.unshift({
    dealer:
      data.outcome
        ?.dealer_total,

    seats:
      Object.keys(
        data.outcome
          ?.hands_by_seat ||
        {}
      ).length,

    net:
      Number(
        data.net
      ),
  });


  history =
    history.slice(
      0,
      12
    );


  saveHistory();

  renderHistory();


  /*
   * Unlock table for the next round.
   */

  stateToken =
    null;


  if (phaseLabel) {
    phaseLabel.textContent =
      "BETTING";
  }


  message(
    `Round complete · ${
      Number(
        data.net
      ) >= 0
        ? "+"
        : ""
    }${fmt(
      data.net
    )}`
  );


  refresh();
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
              gap:5px;
              padding:7px 0;
              border-bottom:
                1px solid
                #ffffff12;
            "
          >
            <span>
              Dealer ${
                item.dealer ??
                "—"
              }

              ${
                item.seats
                  ? ` · ${item.seats} seat${
                      item.seats === 1
                        ? ""
                        : "s"
                    }`
                  : ""
              }
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
   DOUBLE UI
   ================================================================ */

function openDoubleBox() {
  if (
    !roundState
  ) {
    return;
  }


  const hand =
    currentHandState();


  if (!hand) {
    return;
  }


  const original =
    Number(
      hand.original_stake ||
      hand.stake ||
      0
    );


  const maximum =
    Math.min(
      original,
      balance
    );


  const input =
    $("doubleAmount");


  if (!input) {
    return;
  }


  input.min =
    "1";


  input.max =
    String(
      maximum
    );


  input.value =
    String(
      maximum
    );


  $("doubleBox")
    ?.classList
    .add(
      "active"
    );
}


function confirmDouble() {
  const input =
    $("doubleAmount");


  if (!input) {
    return;
  }


  const amount =
    Number(
      input.value
    );


  const hand =
    currentHandState();


  if (!hand) {
    return;
  }


  const original =
    Number(
      hand.original_stake ||
      hand.stake ||
      0
    );


  if (
    !Number.isFinite(
      amount
    ) ||
    amount <= 0
  ) {
    message(
      "Enter a valid double amount."
    );

    return;
  }


  if (
    amount >
    original
  ) {
    message(
      `Double cannot exceed the original wager of ${fmt(
        original
      )}.`
    );

    return;
  }


  if (
    amount >
    balance
  ) {
    message(
      "Insufficient balance."
    );

    return;
  }


  action(
    "double",
    {
      amount,
    }
  );
}


/* ================================================================
   SPLIT BALANCE GUARD
   ================================================================ */

function splitCurrentHand() {
  const hand =
    currentHandState();


  if (!hand) {
    return;
  }


  const required =
    Number(
      hand.original_stake ||
      hand.stake ||
      0
    );


  if (
    balance <
    required
  ) {
    message(
      `Splitting requires ${fmt(
        required
      )} additional credits.`
    );

    return;
  }


  action(
    "split"
  );
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


  resetPendingBets();


  stateToken =
    null;


  roundState =
    null;


  history =
    [];


  localStorage.removeItem(
    BALANCE_KEY
  );


  localStorage.removeItem(
    HISTORY_KEY
  );


  saveBalance();

  saveHistory();


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
  }


  const phaseLabel =
    $("phaseLabel");


  if (phaseLabel) {
    phaseLabel.textContent =
      "BETTING";
  }


  message("");


  renderRound();

  renderHistory();

  refresh();
}


/* ================================================================
   INITIALISE
   ================================================================ */

function init() {
  d8Log(
    "INIT START"
  );


  installDealAnimationStyles();


  saveBalance();


  renderChips();


  bindBets();


  renderHistory();


  renderRound();


  const clearButton =
    $("clearBtn");

  if (clearButton) {
    clearButton.onclick =
      clearBets;
  }


  const dealButton =
    $("dealBtn");

  if (dealButton) {
    dealButton.onclick =
      deal;
  }


  const resetButton =
    $("resetBtn");

  if (resetButton) {
    resetButton.onclick =
      resetCredits;
  }


  const hitButton =
    $("hitBtn");

  if (hitButton) {
    hitButton.onclick =
      () =>
        action(
          "hit"
        );
  }


  const standButton =
    $("standBtn");

  if (standButton) {
    standButton.onclick =
      () =>
        action(
          "stand"
        );
  }


  const splitButton =
    $("splitBtn");

  if (splitButton) {
    splitButton.onclick =
      splitCurrentHand;
  }


  const surrenderButton =
    $("surrenderBtn");

  if (surrenderButton) {
    surrenderButton.onclick =
      () =>
        action(
          "surrender"
        );
  }


  const doubleButton =
    $("doubleBtn");

  if (doubleButton) {
    doubleButton.onclick =
      openDoubleBox;
  }


  const confirmDoubleButton =
    $("confirmDoubleBtn");

  if (confirmDoubleButton) {
    confirmDoubleButton.onclick =
      confirmDouble;
  }


  refresh();


  d8Log(
    "INIT COMPLETE"
  );
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
    init,
    {
      once:
        true,
    }
  );

} else {
  init();
}