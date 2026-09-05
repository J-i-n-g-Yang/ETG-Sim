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

/*
 * Pending wagers:
 *
 * {
 *   "0": {
 *     main: 1000,
 *     superb_8s: 100
 *   },
 *
 *   "1": {
 *     main: 500
 *   }
 * }
 */

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
  card
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
      cardHTML
    )
    .join("");
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
   *
   * This prevents an otherwise inactive seat
   * from being sent to the backend with only
   * side wagers.
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
    hitBtn: "hit",
    standBtn: "stand",
    doubleBtn: "double",
    splitBtn: "split",
    surrenderBtn: "surrender",
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
    <div
      class="
        hand
      "
    >
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
  /*
   * Dealer.
   */

  const dealerCards =
    $("dealerCards");

  const dealerTotal =
    $("dealerTotal");

  if (!roundState) {
    if (dealerCards) {
      dealerCards.innerHTML =
        cardHTML({
          rank: "8",
          suit: "S",
          permanent: true,
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
   * Dealer during player decisions only exposes
   * the permanent 8♠.
   *
   * Settlement returns the complete dealer hand.
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
   * Seats.
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

    /*
     * Settlement uses hands_by_seat.
     */

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

                <div
                  class="
                    hand-total
                  "
                >
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

  busy =
    true;

  $("phaseLabel")
    .textContent =
      "DEALING";

  refresh();

  message("");

  try {
    const data =
      await jsonPost(
        "/api/solo/dueling-8s/deal",
        {
          game:
            GAME,

          bets,
        }
      );

    stateToken =
      data.state_token;

    roundState =
      data;

    resetPendingBets();

    renderRound();

    if (
      data.all_done
    ) {
      await settle();
    } else {
      $("phaseLabel")
        .textContent =
          `SEAT ${
            Number(
              data.current_seat
            ) + 1
          }`;

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
    }

  } catch (error) {
    /*
     * Deal failed before settlement.
     *
     * Restore all locally deducted
     * initial wagers.
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

    $("phaseLabel")
      .textContent =
        "BETTING";

  } finally {
    busy =
      false;

    renderRound();

    refresh();
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

  busy =
    true;

  $("phaseLabel")
    .textContent =
      `SEAT ${seat + 1}`;

  refresh();

  message("");

  try {
    /*
     * For paid Split, the additional wager
     * equals the original Main stake.
     *
     * For Double, the user chooses the
     * additional amount.
     *
     * The server tells us exactly how much
     * was added via extra_stake.
     */

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
      /*
       * This normally should have been
       * prevented before sending the request.
       *
       * Retain this as a final UI guard.
       */

      throw new Error(
        "Insufficient balance for additional stake."
      );
    }

    balance -=
      extraStake;

    saveBalance();

    stateToken =
      data.state_token;

    roundState =
      data;

    $("doubleBox")
      ?.classList
      .remove(
        "active"
      );

    renderRound();

    if (
      data.all_done
    ) {
      await settle();

      return;
    }

    $("phaseLabel")
      .textContent =
        `SEAT ${
          Number(
            data.current_seat
          ) + 1
        }`;

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

  $("phaseLabel")
    .textContent =
      "DEALER";

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
   * Keep a settlement-shaped roundState
   * for display.
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


  /* ------------------------------------------------------------
     HISTORY
     ------------------------------------------------------------ */

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
   * Unlock table for next round.
   */

  stateToken =
    null;

  $("phaseLabel")
    .textContent =
      "BETTING";

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

  /*
   * Backend rules permit a partial Double
   * from table minimum up to original wager.
   */

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

  $("phaseLabel")
    .textContent =
      "BETTING";

  message("");

  renderRound();

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

  renderRound();


  $("clearBtn")
    .onclick =
      clearBets;

  $("dealBtn")
    .onclick =
      deal;

  $("resetBtn")
    .onclick =
      resetCredits;


  $("hitBtn")
    .onclick =
      () =>
        action(
          "hit"
        );

  $("standBtn")
    .onclick =
      () =>
        action(
          "stand"
        );

  $("splitBtn")
    .onclick =
      splitCurrentHand;

  $("surrenderBtn")
    .onclick =
      () =>
        action(
          "surrender"
        );

  $("doubleBtn")
    .onclick =
      openDoubleBox;

  $("confirmDoubleBtn")
    .onclick =
      confirmDouble;


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