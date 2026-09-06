import {
  renderChipBar,
} from "./boards.js";


/* ================================================================
   ETG SIM — BACCARAT SOLO

   Supported variants:
   - baccarat_dragon_tiger
   - baccarat_immortal
   - baccarat_rising

   Road TV:
   - Bead Plate
   - Big Road
   - Big Eye Boy
   - Small Road
   - Cockroach Pig
   - Dragon / Tiger Result Road

   IMPORTANT:
   The server remains authoritative for:
   - dealing
   - winner
   - wager settlement
   - payout amounts

   All road displays are presentation/history only.
   ================================================================ */


/* ================================================================
   CONFIG
   ================================================================ */

const GAME =
  window.BACCARAT_GAME;

const MAX_BET =
  Number(
    window.BACCARAT_MAX
  );

const START_CR =
  Number(
    window.BACCARAT_START
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
   STORAGE
   ================================================================ */

const BAL_KEY =
  `etg_baccarat_bal_${GAME}`;

const HIST_KEY =
  `etg_baccarat_hist_${GAME}`;

const ROAD_KEY =
  `etg_baccarat_road_${GAME}`;


/* ================================================================
   VARIANT CONFIG
   ================================================================ */

const VARIANTS = {

  baccarat_dragon_tiger: {

    pays: [
      ["Player", "1:1"],
      ["Banker", "1:1 · ½ on Banker 6"],
      ["Tie", "8:1"],
      ["Small Dragon", "15:1"],
      ["Big Dragon", "30:1"],
      ["Dragon Tiger 2-2", "30:1"],
      ["Dragon Tiger 3-2", "40:1"],
      ["Dragon Tiger 3-3", "100:1"],
      ["Small Tiger", "22:1"],
      ["Big Tiger", "50:1"],
      ["Tiger Tie", "35:1"],
    ],

    note:
      "Dragon Tiger No Commission Baccarat.",
  },


  baccarat_immortal: {

    pays: [
      ["Player win on 7", "1:2"],
      ["Player 7 loses to Banker 8/9", "Push"],
      ["Player other win", "1:1"],
      ["Banker", "1:1 · ½ on Banker 6"],
      ["Tie", "8:1"],
      ["Player Pair", "11:1"],
      ["Banker Pair", "11:1"],
      ["Small Dragon", "15:1"],
      ["Big Dragon", "30:1"],
      ["Dragon Tiger 2-2", "30:1"],
      ["Dragon Tiger 3-2", "40:1"],
      ["Dragon Tiger 3-3", "100:1"],
      ["Small Tiger", "22:1"],
      ["Big Tiger", "50:1"],
      ["Tiger Tie", "35:1"],
      ["Immortal Dragon", "25:1"],
    ],

    note:
      "Immortal Dragon Tiger No Commission Baccarat.",
  },


  baccarat_rising: {

    pays: [
      ["Player", "1:1"],
      ["Banker", "1:1 · ½ on Banker 6"],
      ["Tie", "8:1"],
      ["Small Dragon", "15:1"],
      ["Big Dragon", "30:1"],
      ["Dragon Tiger 2-2", "30:1"],
      ["Dragon Tiger 3-2", "40:1"],
      ["Dragon Tiger 3-3", "100:1"],
      ["Small Tiger", "22:1"],
      ["Big Tiger", "50:1"],
      ["Tiger Tie", "35:1"],
      ["Rising Dragon", "4 / 6 / 4.5:1"],
      ["Rising Tiger", "4 / 4.5 / 5.5:1"],
    ],

    note:
      "Rising Dragon Tiger No Commission Baccarat.",
  },
};


const cfg =
  VARIANTS[
    GAME
  ];


if (!cfg) {

  throw new Error(
    `Unknown Baccarat variant: ${GAME}`
  );
}


/* ================================================================
   LOCAL STATE
   ================================================================ */

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


/*
 * Road record:
 *
 * {
 *   winner: "player" | "banker" | "tie",
 *   playerPair: boolean,
 *   bankerPair: boolean,
 *
 *   dtMarkers: [
 *      {
 *        code: "SD",
 *        label: "Small Dragon",
 *        type: "dragon",
 *        modifier: "small"
 *      }
 *   ]
 * }
 */

let roadHistory =
  loadRoadHistory();


/* ================================================================
   BALANCE
   ================================================================ */

function saveBalance() {

  localStorage.setItem(
    BAL_KEY,
    String(balance)
  );


  const display =
    $("balanceDisplay");


  if (display) {

    display.textContent =
      fmt(
        balance
      );
  }
}


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
   CHIPS
   ================================================================ */

function renderChips() {

  renderChipBar(
    $("chipBar"),
    selectedChip,

    (value) => {

      if (
        dealing
      ) {
        return;
      }


      selectedChip =
        value;


      renderChips();
    }
  );
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


/* ================================================================
   PLACE BET
   ================================================================ */

function placeBet(
  wager
) {

  if (
    dealing
  ) {
    return;
  }


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


  /*
   * Starting a new betting round after a completed result.
   *
   * Clear only the hand/result area.
   * Road TV remains.
   */

  const phase =
    $("phaseLabel");


  if (
    phase &&
    phase.textContent ===
    "COMPLETE"
  ) {

    phase.textContent =
      "BETTING";


    clearTableResult();


    const returned =
      $("returnMetric");


    const net =
      $("netMetric");


    if (returned) {

      returned.textContent =
        "0";
    }


    if (net) {

      net.textContent =
        "0";


      net.className =
        "metric-value";
    }


    status(
      "Place your bets."
    );
  }


  refreshBetting();
}


/* ================================================================
   GOLD WAGER BADGES
   Same style as Dueling 8s.
   ================================================================ */

function refreshWagerBadges() {

  document
    .querySelectorAll(
      ".spot[data-wager]"
    )
    .forEach(
      (spot) => {

        const wager =
          spot.dataset.wager;


        let badge =
          spot.querySelector(
            ".wager-badge"
          );


        const amount =
          Number(
            bets[
              wager
            ] || 0
          );


        if (
          amount <= 0
        ) {

          badge?.remove();

          return;
        }


        if (
          !badge
        ) {

          badge =
            document.createElement(
              "span"
            );


          badge.className =
            "wager-badge";


          spot.appendChild(
            badge
          );
        }


        badge.textContent =
          fmt(
            amount
          );
      }
    );
}


/* ================================================================
   REFRESH BETTING
   ================================================================ */

function refreshBetting() {

  const total =
    pendingTotal();


  const pending =
    $("pendingTotal");


  if (pending) {

    pending.textContent =
      fmt(
        total
      );
  }


  /*
   * While not resolving a hand, Total Stake reflects pending chips.
   */

  const stake =
    $("stakeMetric");


  if (
    stake &&
    !dealing
  ) {

    stake.textContent =
      fmt(
        total
      );
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


  refreshWagerBadges();
}


/* ================================================================
   CLEAR PENDING BETS
   ================================================================ */

function clearBets() {

  if (
    dealing
  ) {
    return;
  }


  balance +=
    pendingTotal();


  bets =
    {};


  saveBalance();


  refreshBetting();


  status(
    "Bets cleared."
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
  animation = ""
) {

  if (
    !cardData
  ) {
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
   BACCARAT OUTCOME HELPERS
   ================================================================ */

function getPlayerCards(
  outcome
) {

  return (
    outcome?.player_cards ||
    outcome?.player ||
    outcome?.player_hand ||
    []
  );
}


function getBankerCards(
  outcome
) {

  return (
    outcome?.banker_cards ||
    outcome?.banker ||
    outcome?.banker_hand ||
    []
  );
}


/* ================================================================
   CARD VALUE
   ================================================================ */

function cardValue(
  cardData
) {

  if (
    !cardData
  ) {
    return 0;
  }


  if (
    cardData.rank ===
    "A"
  ) {

    return 1;
  }


  if (
    [
      "10",
      "J",
      "Q",
      "K",
    ].includes(
      String(
        cardData.rank
      )
    )
  ) {

    return 0;
  }


  return Number(
    cardData.rank
  ) || 0;
}


/* ================================================================
   BACCARAT TOTAL
   ================================================================ */

function baccaratTotal(
  cards
) {

  return (
    cards.reduce(
      (
        total,
        cardData
      ) =>
        total +
        cardValue(
          cardData
        ),
      0
    ) %
    10
  );
}


/* ================================================================
   PLAYER TOTAL
   ================================================================ */

function getPlayerTotal(
  outcome
) {

  const candidates = [

    outcome?.player_total,

    outcome?.player_score,

    outcome?.player_points,
  ];


  for (
    const value
    of candidates
  ) {

    if (
      value !== undefined &&
      value !== null &&
      Number.isFinite(
        Number(
          value
        )
      )
    ) {

      return Number(
        value
      );
    }
  }


  return baccaratTotal(
    getPlayerCards(
      outcome
    )
  );
}


/* ================================================================
   BANKER TOTAL
   ================================================================ */

function getBankerTotal(
  outcome
) {

  const candidates = [

    outcome?.banker_total,

    outcome?.banker_score,

    outcome?.banker_points,
  ];


  for (
    const value
    of candidates
  ) {

    if (
      value !== undefined &&
      value !== null &&
      Number.isFinite(
        Number(
          value
        )
      )
    ) {

      return Number(
        value
      );
    }
  }


  return baccaratTotal(
    getBankerCards(
      outcome
    )
  );
}


/* ================================================================
   WINNER NORMALISATION
   ================================================================ */

function normalizeWinner(
  value
) {

  const text =
    String(
      value || ""
    )
      .trim()
      .toLowerCase();


  if (
    text.includes(
      "player"
    )
  ) {

    return "player";
  }


  if (
    text.includes(
      "banker"
    )
  ) {

    return "banker";
  }


  if (
    text.includes(
      "tie"
    )
  ) {

    return "tie";
  }


  return null;
}


/* ================================================================
   GET WINNER
   ================================================================ */

function getWinner(
  outcome
) {

  const directCandidates = [

    outcome?.winner,

    outcome?.result,

    outcome?.main_result,
  ];


  for (
    const candidate
    of directCandidates
  ) {

    const winner =
      normalizeWinner(
        candidate
      );


    if (
      winner
    ) {

      return winner;
    }
  }


  const player =
    getPlayerTotal(
      outcome
    );


  const banker =
    getBankerTotal(
      outcome
    );


  if (
    player >
    banker
  ) {

    return "player";
  }


  if (
    banker >
    player
  ) {

    return "banker";
  }


  return "tie";
}


/* ================================================================
   PAIR DETECTION
   ================================================================ */

function sameRank(
  a,
  b
) {

  if (
    !a ||
    !b
  ) {

    return false;
  }


  return (
    String(
      a.rank
    ) ===
    String(
      b.rank
    )
  );
}


function detectPlayerPair(
  outcome
) {

  if (
    typeof outcome?.player_pair ===
    "boolean"
  ) {

    return outcome.player_pair;
  }


  if (
    typeof outcome?.playerPair ===
    "boolean"
  ) {

    return outcome.playerPair;
  }


  const cards =
    getPlayerCards(
      outcome
    );


  return (
    cards.length >= 2 &&
    sameRank(
      cards[0],
      cards[1]
    )
  );
}


function detectBankerPair(
  outcome
) {

  if (
    typeof outcome?.banker_pair ===
    "boolean"
  ) {

    return outcome.banker_pair;
  }


  if (
    typeof outcome?.bankerPair ===
    "boolean"
  ) {

    return outcome.bankerPair;
  }


  const cards =
    getBankerCards(
      outcome
    );


  return (
    cards.length >= 2 &&
    sameRank(
      cards[0],
      cards[1]
    )
  );
}


/* ================================================================
   SIDE-BET RESULT HELPERS
   ================================================================ */

/*
 * Because the backend is authoritative, first try to read any
 * explicit boolean/result field it exposes.
 *
 * If that field does not exist, the UI can derive the simple
 * structural conditions from the actual dealt hand.
 */

function truthyOutcomeField(
  outcome,
  ...names
) {

  for (
    const name
    of names
  ) {

    const value =
      outcome?.[
        name
      ];


    if (
      value === true
    ) {

      return true;
    }


    if (
      value &&
      typeof value ===
      "string"
    ) {

      const text =
        value
          .trim()
          .toLowerCase();


      if (
        [
          "win",
          "winner",
          "true",
          "yes",
          "qualified",
          "qualifies",
        ].includes(
          text
        )
      ) {

        return true;
      }
    }
  }


  return false;
}


/* ================================================================
   DRAGON / TIGER DIFFERENCE
   ================================================================ */

function pointDifference(
  outcome
) {

  return Math.abs(
    getPlayerTotal(
      outcome
    )
    -
    getBankerTotal(
      outcome
    )
  );
}


/* ================================================================
   SMALL / BIG DRAGON / TIGER

   These follow the winning margin.

   Dragon = Player wins.
   Tiger  = Banker wins.

   Small = winning margin 4–6.
   Big   = winning margin 7–9.

   Explicit backend result fields take priority where available.
   ================================================================ */

function detectSmallDragon(
  outcome
) {

  if (
    truthyOutcomeField(
      outcome,
      "small_dragon",
      "smallDragon"
    )
  ) {

    return true;
  }


  return (
    getWinner(
      outcome
    ) === "player" &&
    pointDifference(
      outcome
    ) >= 4 &&
    pointDifference(
      outcome
    ) <= 6
  );
}


function detectBigDragon(
  outcome
) {

  if (
    truthyOutcomeField(
      outcome,
      "big_dragon",
      "bigDragon"
    )
  ) {

    return true;
  }


  return (
    getWinner(
      outcome
    ) === "player" &&
    pointDifference(
      outcome
    ) >= 7
  );
}


function detectSmallTiger(
  outcome
) {

  if (
    truthyOutcomeField(
      outcome,
      "small_tiger",
      "smallTiger"
    )
  ) {

    return true;
  }


  return (
    getWinner(
      outcome
    ) === "banker" &&
    pointDifference(
      outcome
    ) >= 4 &&
    pointDifference(
      outcome
    ) <= 6
  );
}


function detectBigTiger(
  outcome
) {

  if (
    truthyOutcomeField(
      outcome,
      "big_tiger",
      "bigTiger"
    )
  ) {

    return true;
  }


  return (
    getWinner(
      outcome
    ) === "banker" &&
    pointDifference(
      outcome
    ) >= 7
  );
}


/* ================================================================
   TIGER TIE

   Existing rules/tests identify Tiger Tie as the special 6-6 tie.
   ================================================================ */

function detectTigerTie(
  outcome
) {

  if (
    truthyOutcomeField(
      outcome,
      "tiger_tie",
      "tigerTie"
    )
  ) {

    return true;
  }


  return (
    getPlayerTotal(
      outcome
    ) === 6 &&
    getBankerTotal(
      outcome
    ) === 6
  );
}


/* ================================================================
   DRAGON TIGER COMBINATION

   Dragon Tiger requires Player 7 defeating Banker 6.

   Final card counts determine the payout category:
   2-2       -> 30:1
   3-2 / 2-3 -> 40:1
   3-3       -> 100:1

   The result marker is recorded regardless of whether Dragon Tiger
   was actually wagered.
   ================================================================ */

function detectDragonTigerCombo(
  outcome
) {

  /*
   * Dragon Tiger wins only when Player wins 7-6.
   * Final card counts select the applicable payout:
   *   2-2 -> 30:1
   *   3-2 / 2-3 -> 40:1
   *   3-3 -> 100:1
   */

  if (
    getWinner(
      outcome
    ) !== "player" ||
    getPlayerTotal(
      outcome
    ) !== 7 ||
    getBankerTotal(
      outcome
    ) !== 6
  ) {

    return null;
  }


  const playerCards =
    getPlayerCards(
      outcome
    );


  const bankerCards =
    getBankerCards(
      outcome
    );


  const p =
    playerCards.length;


  const b =
    bankerCards.length;


  if (
    p === 2 &&
    b === 2
  ) {

    return {
      code:
        "DT22",

      label:
        "Dragon Tiger 2-2",

      type:
        "dragon",

      modifier:
        "combo",
    };
  }


  if (
    (
      p === 3 &&
      b === 2
    ) ||
    (
      p === 2 &&
      b === 3
    )
  ) {

    return {
      code:
        "DT32",

      label:
        "Dragon Tiger 3-2",

      type:
        "dragon",

      modifier:
        "combo",
    };
  }


  if (
    p === 3 &&
    b === 3
  ) {

    return {
      code:
        "DT33",

      label:
        "Dragon Tiger 3-3",

      type:
        "dragon",

      modifier:
        "combo",
    };
  }


  return null;
}


/* ================================================================
   IMMORTAL DRAGON

   Prefer backend's explicit result field.

   We intentionally do NOT invent a fallback condition here if the
   outcome object does not expose enough information. The payout
   module remains authoritative.
   ================================================================ */

function detectImmortalDragon(
  outcome
) {

  if (
    GAME !==
    "baccarat_immortal"
  ) {

    return false;
  }


  return truthyOutcomeField(
    outcome,
    "immortal_dragon",
    "immortalDragon"
  );
}


/* ================================================================
   RISING DRAGON / TIGER

   Prefer explicit backend fields.

   If unavailable, the display derives direction from the winner
   and accepts only a 4-, 5- or 6-card completed Baccarat hand,
   matching the wager's card-count payout table.
   ================================================================ */

function totalCardCount(
  outcome
) {

  return (
    getPlayerCards(
      outcome
    ).length
    +
    getBankerCards(
      outcome
    ).length
  );
}


function detectRisingDragon(
  outcome
) {

  if (
    GAME !==
    "baccarat_rising"
  ) {

    return false;
  }


  if (
    truthyOutcomeField(
      outcome,
      "rising_dragon",
      "risingDragon"
    )
  ) {

    return true;
  }


  const count =
    totalCardCount(
      outcome
    );


  return (
    getWinner(
      outcome
    ) === "player" &&
    [
      4,
      5,
      6,
    ].includes(
      count
    )
  );
}


function detectRisingTiger(
  outcome
) {

  if (
    GAME !==
    "baccarat_rising"
  ) {

    return false;
  }


  if (
    truthyOutcomeField(
      outcome,
      "rising_tiger",
      "risingTiger"
    )
  ) {

    return true;
  }


  const count =
    totalCardCount(
      outcome
    );


  return (
    getWinner(
      outcome
    ) === "banker" &&
    [
      4,
      5,
      6,
    ].includes(
      count
    )
  );
}


/* ================================================================
   BUILD DRAGON / TIGER MARKERS FOR ONE HAND
   ================================================================ */

function buildDragonTigerMarkers(
  outcome
) {

  const markers =
    [];


  if (
    detectSmallDragon(
      outcome
    )
  ) {

    markers.push({
      code:
        "SD",

      label:
        "Small Dragon",

      type:
        "dragon",

      modifier:
        "small",
    });
  }


  if (
    detectBigDragon(
      outcome
    )
  ) {

    markers.push({
      code:
        "BD",

      label:
        "Big Dragon",

      type:
        "dragon",

      modifier:
        "big",
    });
  }


  if (
    detectSmallTiger(
      outcome
    )
  ) {

    markers.push({
      code:
        "ST",

      label:
        "Small Tiger",

      type:
        "tiger",

      modifier:
        "small",
    });
  }


  if (
    detectBigTiger(
      outcome
    )
  ) {

    markers.push({
      code:
        "BT",

      label:
        "Big Tiger",

      type:
        "tiger",

      modifier:
        "big",
    });
  }


  if (
    detectTigerTie(
      outcome
    )
  ) {

    markers.push({
      code:
        "TT",

      label:
        "Tiger Tie",

      type:
        "tie",

      modifier:
        "special",
    });
  }


  const dragonTiger =
    detectDragonTigerCombo(
      outcome
    );


  if (
    dragonTiger
  ) {

    markers.push(
      dragonTiger
    );
  }


  if (
    detectImmortalDragon(
      outcome
    )
  ) {

    markers.push({
      code:
        "ID",

      label:
        "Immortal Dragon",

      type:
        "immortal",

      modifier:
        "special",
    });
  }


  if (
    detectRisingDragon(
      outcome
    )
  ) {

    markers.push({
      code:
        "RD",

      label:
        "Rising Dragon",

      type:
        "rising-dragon",

      modifier:
        "special",
    });
  }


  if (
    detectRisingTiger(
      outcome
    )
  ) {

    markers.push({
      code:
        "RT",

      label:
        "Rising Tiger",

      type:
        "rising-tiger",

      modifier:
        "special",
    });
  }


  return markers;
}


/* ================================================================
   CLEAR TABLE RESULT
   ================================================================ */

function clearTableResult() {

  const playerCards =
    $("playerCards");

  const bankerCards =
    $("bankerCards");

  const playerScore =
    $("playerScore");

  const bankerScore =
    $("bankerScore");

  const winner =
    $("winner");

  const breakdown =
    $("breakdown");


  if (playerCards) {

    playerCards.innerHTML =
      "";
  }


  if (bankerCards) {

    bankerCards.innerHTML =
      "";
  }


  if (playerScore) {

    playerScore.textContent =
      "—";
  }


  if (bankerScore) {

    bankerScore.textContent =
      "—";
  }


  if (winner) {

    winner.textContent =
      "";


    winner.className =
      "winner";
  }


  if (breakdown) {

    breakdown.innerHTML =
      "";
  }
}


/* ================================================================
   CARD DEAL ANIMATION
   ================================================================ */

async function animateCards(
  outcome
) {

  const player =
    getPlayerCards(
      outcome
    );


  const banker =
    getBankerCards(
      outcome
    );


  const playerBox =
    $("playerCards");


  const bankerBox =
    $("bankerCards");


  if (
    !playerBox ||
    !bankerBox
  ) {

    return;
  }


  playerBox.innerHTML =
    "";


  bankerBox.innerHTML =
    "";


  /*
   * Baccarat sequence:
   *
   * Player 1
   * Banker 1
   * Player 2
   * Banker 2
   * Player 3
   * Banker 3
   */

  const sequence =
    [];


  if (
    player[0]
  ) {

    sequence.push({
      side:
        "player",

      card:
        player[0],
    });
  }


  if (
    banker[0]
  ) {

    sequence.push({
      side:
        "banker",

      card:
        banker[0],
    });
  }


  if (
    player[1]
  ) {

    sequence.push({
      side:
        "player",

      card:
        player[1],
    });
  }


  if (
    banker[1]
  ) {

    sequence.push({
      side:
        "banker",

      card:
        banker[1],
    });
  }


  if (
    player[2]
  ) {

    sequence.push({
      side:
        "player",

      card:
        player[2],
    });
  }


  if (
    banker[2]
  ) {

    sequence.push({
      side:
        "banker",

      card:
        banker[2],
    });
  }


  for (
    const item
    of sequence
  ) {

    const target =
      item.side ===
      "player"
        ? playerBox
        : bankerBox;


    target.insertAdjacentHTML(
      "beforeend",

      cardHTML(
        item.card,
        "deal-in"
      )
    );


    await sleep(
      260
    );
  }


  const playerScore =
    $("playerScore");


  const bankerScore =
    $("bankerScore");


  if (
    playerScore
  ) {

    playerScore.textContent =
      String(
        getPlayerTotal(
          outcome
        )
      );
  }


  if (
    bankerScore
  ) {

    bankerScore.textContent =
      String(
        getBankerTotal(
          outcome
        )
      );
  }
}


/* ================================================================
   WINNER DISPLAY
   ================================================================ */

function renderWinner(
  outcome
) {

  const winner =
    getWinner(
      outcome
    );


  const box =
    $("winner");


  if (
    !box
  ) {

    return;
  }


  box.className =
    `winner ${winner}`;


  if (
    winner ===
    "player"
  ) {

    box.textContent =
      "PLAYER WINS";
  }


  else if (
    winner ===
    "banker"
  ) {

    box.textContent =
      "BANKER WINS";
  }


  else {

    box.textContent =
      "TIE";
  }
}


/* ================================================================
   RESULT BREAKDOWN
   ================================================================ */

function renderBreakdown(
  data
) {

  const box =
    $("breakdown");


  if (
    !box
  ) {

    return;
  }


  const results =
    Array.isArray(
      data.results
    )
      ? data.results
      : [];


  if (
    !results.length
  ) {

    box.innerHTML =
      "";

    return;
  }


  box.innerHTML =
    results
      .map(
        (result) => {

          const amount =
            Number(
              result.amount || 0
            );


          const returned =
            Number(
              result.return || 0
            );


          const net =
            returned -
            amount;


          return `
            <div class="br">

              <span>
                ${formatWagerName(
                  result.wager_type
                )}
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
   WAGER NAME
   ================================================================ */

function formatWagerName(
  wager
) {

  const names = {

    player:
      "Player",

    banker:
      "Banker",

    tie:
      "Tie",

    player_pair:
      "Player Pair",

    banker_pair:
      "Banker Pair",

    small_dragon:
      "Small Dragon",

    big_dragon:
      "Big Dragon",

    dragon_tiger:
      "Dragon Tiger",

    small_tiger:
      "Small Tiger",

    big_tiger:
      "Big Tiger",

    tiger_tie:
      "Tiger Tie",

    immortal_dragon:
      "Immortal Dragon",

    rising_dragon:
      "Rising Dragon",

    rising_tiger:
      "Rising Tiger",
  };


  return (
    names[
      wager
    ] ||
    String(
      wager || ""
    )
      .replaceAll(
        "_",
        " "
      )
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      )
  );
}


/* ================================================================
   ROUND HISTORY
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
  winner
) {

  let history =
    loadHistory();


  history.unshift(
    {
      winner,

      at:
        Date.now(),
    }
  );


  history =
    history.slice(
      0,
      30
    );


  localStorage.setItem(
    HIST_KEY,
    JSON.stringify(
      history
    )
  );


  renderHistory();
}


function renderHistory() {

  const box =
    $("history");


  if (
    !box
  ) {

    return;
  }


  const history =
    loadHistory();


  if (
    !history.length
  ) {

    box.innerHTML =
      "No rounds yet";

    return;
  }


  box.innerHTML =
    history
      .map(
        (item) => {

          const winner =
            normalizeWinner(
              item.winner
            ) ||
            "tie";


          const letter =
            winner ===
            "player"
              ? "P"
              : winner ===
                "banker"
                ? "B"
                : "T";


          return `
            <span
              class="hb ${winner}"
            >
              ${letter}
            </span>
          `;
        }
      )
      .join("");
}


/* ================================================================
   PAY TABLE
   ================================================================ */

function renderPayTable() {

  const box =
    $("payTable");


  if (
    !box
  ) {

    return;
  }


  box.innerHTML =
    cfg.pays
      .map(
        (
          [
            name,
            payout,
          ]
        ) => `
          <div class="prow">

            <span>
              ${name}
            </span>

            <span class="odds">
              ${payout}
            </span>

          </div>
        `
      )
      .join("");


  if (
    cfg.note
  ) {

    box.insertAdjacentHTML(
      "beforeend",

      `
        <div
          style="
            grid-column:1/-1;
            padding-top:8px;
            color:#c9d3cb;
            text-align:center;
            line-height:1.45;
          "
        >
          ${cfg.note}
        </div>
      `
    );
  }
}


/* ================================================================
   DEAL
   ================================================================ */

async function dealRound() {

  if (
    dealing ||
    pendingTotal() <= 0
  ) {

    return;
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
        ) => ({

          wager_type,

          amount:
            Number(
              amount
            ),
        })
      );


  dealing =
    true;


  const phase =
    $("phaseLabel");


  if (
    phase
  ) {

    phase.textContent =
      "DEALING";
  }


  status(
    "Dealing Baccarat hand…",
    "playing"
  );


  refreshBetting();


  try {

    const response =
      await fetch(
        "/api/solo/spin",

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
        "Baccarat deal failed"
      );
    }


    /*
     * Server accepted the wagers.
     */

    bets =
      {};


    refreshBetting();


    clearTableResult();


    await animateCards(
      data.outcome
    );


    renderWinner(
      data.outcome
    );


    renderBreakdown(
      data
    );


    const returned =
      Number(
        data.total_return || 0
      );


    balance +=
      returned;


    saveBalance();


    const stakeMetric =
      $("stakeMetric");


    if (
      stakeMetric
    ) {

      stakeMetric.textContent =
        fmt(
          data.total_wager
        );
    }


    const returnMetric =
      $("returnMetric");


    if (
      returnMetric
    ) {

      returnMetric.textContent =
        fmt(
          data.total_return
        );
    }


    const net =
      Number(
        data.net || 0
      );


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
        }${fmt(
          net
        )}`;


      netMetric.className =
        net > 0
          ? "metric-value win"
          : net < 0
            ? "metric-value lose"
            : "metric-value push";
    }


    const winner =
      getWinner(
        data.outcome
      );


    saveHistory(
      winner
    );


    /*
     * Standard roads + Dragon/Tiger result road are updated from
     * the same completed hand.
     */

    addRoadResult(
      data.outcome
    );


    if (
      phase
    ) {

      phase.textContent =
        "COMPLETE";
    }


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


  } catch (error) {

    /*
     * Refund pending wagers if the request failed.
     */

    balance +=
      wagered;


    bets =
      {};


    saveBalance();


    refreshBetting();


    status(
      error.message ||
      "Baccarat deal failed.",
      "bad"
    );


    console.error(
      "[BACCARAT DEAL ERROR]",
      error
    );


    if (
      phase
    ) {

      phase.textContent =
        "BETTING";
    }


  } finally {

    dealing =
      false;


    refreshBetting();
  }
}


/* ================================================================
   RESET CREDITS

   This intentionally DOES NOT clear the Road TV.
   CLEAR ROAD controls the shoe-history display independently.
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


  localStorage.removeItem(
    BAL_KEY
  );


  localStorage.removeItem(
    HIST_KEY
  );


  saveBalance();


  clearTableResult();


  renderHistory();


  const stake =
    $("stakeMetric");


  const returned =
    $("returnMetric");


  const net =
    $("netMetric");


  const phase =
    $("phaseLabel");


  if (
    stake
  ) {

    stake.textContent =
      "0";
  }


  if (
    returned
  ) {

    returned.textContent =
      "0";
  }


  if (
    net
  ) {

    net.textContent =
      "0";


    net.className =
      "metric-value";
  }


  if (
    phase
  ) {

    phase.textContent =
      "BETTING";
  }


  status(
    "Credits reset."
  );


  refreshBetting();
}


/* ================================================================
   ROAD TV STORAGE
   ================================================================ */

function loadRoadHistory() {

  try {

    const parsed =
      JSON.parse(
        localStorage.getItem(
          ROAD_KEY
        ) ||
        "[]"
      );


    if (
      !Array.isArray(
        parsed
      )
    ) {

      return [];
    }


    return parsed
      .map(
        (item) => ({

          winner:
            normalizeWinner(
              item.winner
            ),

          playerPair:
            Boolean(
              item.playerPair
            ),

          bankerPair:
            Boolean(
              item.bankerPair
            ),

          /*
           * Backwards compatible:
           * old Road TV entries have no dtMarkers.
           */

          dtMarkers:
            Array.isArray(
              item.dtMarkers
            )
              ? item.dtMarkers
                  .filter(
                    (marker) =>
                      marker &&
                      marker.code
                  )
                  .map(
                    (marker) => ({

                      code:
                        String(
                          marker.code
                        ),

                      label:
                        String(
                          marker.label ||
                          marker.code
                        ),

                      type:
                        String(
                          marker.type ||
                          "dragon"
                        ),

                      modifier:
                        String(
                          marker.modifier ||
                          ""
                        ),
                    })
                  )
              : [],
        })
      )
      .filter(
        (item) =>
          Boolean(
            item.winner
          )
      );


  } catch {

    return [];
  }
}


/* ================================================================
   SAVE ROAD
   ================================================================ */

function saveRoadHistory() {

  localStorage.setItem(
    ROAD_KEY,

    JSON.stringify(
      roadHistory
    )
  );
}


/* ================================================================
   ADD ROAD RESULT
   ================================================================ */

function addRoadResult(
  outcome
) {

  const winner =
    getWinner(
      outcome
    );


  if (
    !winner
  ) {

    return;
  }


  roadHistory.push(
    {

      winner,

      playerPair:
        detectPlayerPair(
          outcome
        ),

      bankerPair:
        detectBankerPair(
          outcome
        ),

      dtMarkers:
        buildDragonTigerMarkers(
          outcome
        ),
    }
  );


  /*
   * Enough history for a long casino shoe while preventing
   * unlimited localStorage growth.
   */

  roadHistory =
    roadHistory.slice(
      -500
    );


  saveRoadHistory();


  renderRoadTV();
}


/* ================================================================
   CLEAR ROAD
   ================================================================ */

function clearRoad() {

  if (
    dealing
  ) {

    return;
  }


  if (
    !confirm(
      "Clear the Baccarat road history?"
    )
  ) {

    return;
  }


  roadHistory =
    [];


  localStorage.removeItem(
    ROAD_KEY
  );


  renderRoadTV();


  status(
    "Road history cleared."
  );
}


/* ================================================================
   ROAD COLOURS
   ================================================================ */

const ROAD_COLOURS = {

  player:
    "#1671ca",

  banker:
    "#cf3338",

  tie:
    "#299349",

  red:
    "#d02f35",

  blue:
    "#176fc1",

  grid:
    "#c5c5c5",

  background:
    "#f5f2e9",

  text:
    "#1d1d1d",
};


/* ================================================================
   CANVAS SETUP
   ================================================================ */

function setupCanvas(
  canvas,
  cssHeight,
  minWidth = 300
) {

  if (
    !canvas
  ) {

    return null;
  }


  const rect =
    canvas.getBoundingClientRect();


  const cssWidth =
    Math.max(
      minWidth,

      Math.floor(
        rect.width
      )
    );


  const dpr =
    Math.max(
      1,

      window.devicePixelRatio ||
      1
    );


  canvas.width =
    Math.round(
      cssWidth *
      dpr
    );


  canvas.height =
    Math.round(
      cssHeight *
      dpr
    );


  const ctx =
    canvas.getContext(
      "2d"
    );


  ctx.setTransform(
    dpr,
    0,
    0,
    dpr,
    0,
    0
  );


  ctx.clearRect(
    0,
    0,
    cssWidth,
    cssHeight
  );


  ctx.fillStyle =
    ROAD_COLOURS.background;


  ctx.fillRect(
    0,
    0,
    cssWidth,
    cssHeight
  );


  return {

    ctx,

    width:
      cssWidth,

    height:
      cssHeight,
  };
}


/* ================================================================
   GRID DRAWING
   ================================================================ */

function drawGrid(
  ctx,
  width,
  height,
  cell
) {

  ctx.save();


  ctx.strokeStyle =
    ROAD_COLOURS.grid;


  ctx.lineWidth =
    0.6;


  ctx.beginPath();


  for (
    let x = 0;
    x <= width;
    x += cell
  ) {

    ctx.moveTo(
      Math.round(
        x
      ) + 0.5,
      0
    );


    ctx.lineTo(
      Math.round(
        x
      ) + 0.5,
      height
    );
  }


  for (
    let y = 0;
    y <= height;
    y += cell
  ) {

    ctx.moveTo(
      0,
      Math.round(
        y
      ) + 0.5
    );


    ctx.lineTo(
      width,
      Math.round(
        y
      ) + 0.5
    );
  }


  ctx.stroke();


  ctx.restore();
}


/* ================================================================
   BEAD PLATE
   ================================================================ */

function drawBeadPlate() {

  const canvas =
    $("beadPlate");


  const setup =
    setupCanvas(
      canvas,
      220
    );


  if (
    !setup
  ) {

    return;
  }


  const {
    ctx,
    width,
    height,
  } =
    setup;


  const rows =
    6;


  const cell =
    height /
    rows;


  const columns =
    Math.max(
      1,

      Math.floor(
        width /
        cell
      )
    );


  drawGrid(
    ctx,
    width,
    height,
    cell
  );


  const capacity =
    rows *
    columns;


  const visible =
    roadHistory.slice(
      -capacity
    );


  visible.forEach(
    (
      item,
      index
    ) => {

      const col =
        Math.floor(
          index /
          rows
        );


      const row =
        index %
        rows;


      const cx =
        col *
        cell +
        cell / 2;


      const cy =
        row *
        cell +
        cell / 2;


      const radius =
        cell *
        0.36;


      const colour =
        ROAD_COLOURS[
          item.winner
        ];


      ctx.save();


      ctx.fillStyle =
        colour;


      ctx.beginPath();


      ctx.arc(
        cx,
        cy,
        radius,
        0,
        Math.PI * 2
      );


      ctx.fill();


      ctx.fillStyle =
        "#ffffff";


      ctx.font =
        `900 ${
          Math.max(
            9,
            cell * 0.30
          )
        }px Arial`;


      ctx.textAlign =
        "center";


      ctx.textBaseline =
        "middle";


      const label =
        item.winner ===
        "player"
          ? "P"
          : item.winner ===
            "banker"
            ? "B"
            : "T";


      ctx.fillText(
        label,
        cx,
        cy + 0.5
      );


      /*
       * Player Pair = blue upper-left dot.
       */

      if (
        item.playerPair
      ) {

        ctx.fillStyle =
          ROAD_COLOURS.player;


        ctx.beginPath();


        ctx.arc(
          cx -
          radius * 0.68,

          cy -
          radius * 0.68,

          Math.max(
            2.5,
            radius * 0.18
          ),

          0,
          Math.PI * 2
        );


        ctx.fill();
      }


      /*
       * Banker Pair = red lower-right dot.
       */

      if (
        item.bankerPair
      ) {

        ctx.fillStyle =
          ROAD_COLOURS.banker;


        ctx.beginPath();


        ctx.arc(
          cx +
          radius * 0.68,

          cy +
          radius * 0.68,

          Math.max(
            2.5,
            radius * 0.18
          ),

          0,
          Math.PI * 2
        );


        ctx.fill();
      }


      ctx.restore();
    }
  );
}


/* ================================================================
   BIG ROAD BUILDER
   ================================================================ */

function buildBigRoad(
  source
) {

  const rows =
    6;


  const grid =
    new Map();


  const cells =
    [];


  let lastWinner =
    null;


  let lastCell =
    null;


  let currentColumn =
    0;


  let streakOriginColumn =
    0;


  let leadingTies =
    0;


  const key = (
    row,
    col
  ) =>
    `${row}:${col}`;


  for (
    const item
    of source
  ) {

    const winner =
      item.winner;


    /*
     * Ties attach to the preceding Player/Banker cell.
     */

    if (
      winner ===
      "tie"
    ) {

      if (
        lastCell
      ) {

        lastCell.ties =
          Number(
            lastCell.ties || 0
          ) +
          1;


        if (
          item.playerPair
        ) {

          lastCell.playerPair =
            true;
        }


        if (
          item.bankerPair
        ) {

          lastCell.bankerPair =
            true;
        }

      } else {

        leadingTies++;
      }


      continue;
    }


    let row =
      0;


    let col =
      0;


    if (
      !lastCell
    ) {

      row =
        0;


      col =
        0;


      streakOriginColumn =
        0;

    } else if (
      winner !==
      lastWinner
    ) {

      streakOriginColumn++;


      row =
        0;


      col =
        streakOriginColumn;


      while (
        grid.has(
          key(
            row,
            col
          )
        )
      ) {

        col++;
      }


      streakOriginColumn =
        col;

    } else {

      const downRow =
        lastCell.row +
        1;


      const downCol =
        lastCell.col;


      const canMoveDown =
        downRow <
        rows &&
        !grid.has(
          key(
            downRow,
            downCol
          )
        );


      if (
        canMoveDown
      ) {

        row =
          downRow;


        col =
          downCol;

      } else {

        row =
          lastCell.row;


        col =
          lastCell.col +
          1;


        while (
          grid.has(
            key(
              row,
              col
            )
          )
        ) {

          col++;
        }
      }
    }


    const cell = {

      row,

      col,

      winner,

      ties:
        0,

      playerPair:
        Boolean(
          item.playerPair
        ),

      bankerPair:
        Boolean(
          item.bankerPair
        ),
    };


    if (
      !lastCell &&
      leadingTies > 0
    ) {

      cell.ties =
        leadingTies;


      leadingTies =
        0;
    }


    grid.set(
      key(
        row,
        col
      ),
      cell
    );


    cells.push(
      cell
    );


    lastCell =
      cell;


    lastWinner =
      winner;


    currentColumn =
      Math.max(
        currentColumn,
        col
      );
  }


  return {

    cells,

    grid,

    maxColumn:
      currentColumn,
  };
}


/* ================================================================
   BIG ROAD DRAW
   ================================================================ */

function drawBigRoad() {

  const canvas =
    $("bigRoad");


  const setup =
    setupCanvas(
      canvas,
      220,
      500
    );


  if (
    !setup
  ) {

    return;
  }


  const {
    ctx,
    width,
    height,
  } =
    setup;


  const rows =
    6;


  const cell =
    height /
    rows;


  const visibleColumns =
    Math.max(
      1,

      Math.floor(
        width /
        cell
      )
    );


  drawGrid(
    ctx,
    width,
    height,
    cell
  );


  const road =
    buildBigRoad(
      roadHistory
    );


  const startColumn =
    Math.max(
      0,

      road.maxColumn -
      visibleColumns +
      1
    );


  for (
    const item
    of road.cells
  ) {

    const displayCol =
      item.col -
      startColumn;


    if (
      displayCol < 0 ||
      displayCol >=
      visibleColumns
    ) {

      continue;
    }


    const cx =
      displayCol *
      cell +
      cell / 2;


    const cy =
      item.row *
      cell +
      cell / 2;


    const radius =
      cell *
      0.34;


    const colour =
      ROAD_COLOURS[
        item.winner
      ];


    ctx.save();


    ctx.strokeStyle =
      colour;


    ctx.lineWidth =
      Math.max(
        2,
        cell * 0.075
      );


    ctx.beginPath();


    ctx.arc(
      cx,
      cy,
      radius,
      0,
      Math.PI * 2
    );


    ctx.stroke();


    if (
      item.ties >
      0
    ) {

      ctx.fillStyle =
        ROAD_COLOURS.tie;


      ctx.font =
        `900 ${
          Math.max(
            8,
            cell * 0.25
          )
        }px Arial`;


      ctx.textAlign =
        "center";


      ctx.textBaseline =
        "middle";


      ctx.fillText(
        String(
          item.ties
        ),
        cx,
        cy
      );
    }


    if (
      item.playerPair
    ) {

      ctx.fillStyle =
        ROAD_COLOURS.player;


      ctx.beginPath();


      ctx.arc(
        cx -
        radius * 0.66,

        cy -
        radius * 0.66,

        Math.max(
          2,
          radius * 0.16
        ),

        0,
        Math.PI * 2
      );


      ctx.fill();
    }


    if (
      item.bankerPair
    ) {

      ctx.fillStyle =
        ROAD_COLOURS.banker;


      ctx.beginPath();


      ctx.arc(
        cx +
        radius * 0.66,

        cy +
        radius * 0.66,

        Math.max(
          2,
          radius * 0.16
        ),

        0,
        Math.PI * 2
      );


      ctx.fill();
    }


    ctx.restore();
  }
}


/* ================================================================
   DERIVED ROAD HELPERS
   ================================================================ */

function buildBigRoadColumnMap(
  bigRoad
) {

  const columns =
    new Map();


  for (
    const cell
    of bigRoad.cells
  ) {

    if (
      !columns.has(
        cell.col
      )
    ) {

      columns.set(
        cell.col,
        new Set()
      );
    }


    columns
      .get(
        cell.col
      )
      .add(
        cell.row
      );
  }


  return columns;
}


function columnHeight(
  columns,
  col
) {

  const set =
    columns.get(
      col
    );


  if (
    !set ||
    !set.size
  ) {

    return 0;
  }


  return (
    Math.max(
      ...set
    ) +
    1
  );
}


/* ================================================================
   DERIVED COLOUR
   ================================================================ */

function derivedColourForCell(
  cell,
  previousCell,
  columns,
  offset
) {

  /*
   * New streak.
   */

  if (
    cell.row ===
    0
  ) {

    const leftA =
      cell.col -
      1;


    const leftB =
      cell.col -
      1 -
      offset;


    if (
      leftB <
      0
    ) {

      return null;
    }


    return (
      columnHeight(
        columns,
        leftA
      ) ===
      columnHeight(
        columns,
        leftB
      )
    );
  }


  /*
   * Continuing streak.
   */

  const compareCol =
    cell.col -
    offset;


  if (
    compareCol <
    0
  ) {

    return null;
  }


  const compareColumn =
    columns.get(
      compareCol
    );


  const sameRowExists =
    Boolean(
      compareColumn?.has(
        cell.row
      )
    );


  const previousRowExists =
    Boolean(
      compareColumn?.has(
        cell.row -
        1
      )
    );


  if (
    sameRowExists
  ) {

    return true;
  }


  if (
    previousRowExists
  ) {

    return false;
  }


  return true;
}


/* ================================================================
   DERIVED ROAD SEQUENCE
   ================================================================ */

function buildDerivedSequence(
  source,
  offset
) {

  const bigRoad =
    buildBigRoad(
      source
    );


  const columns =
    buildBigRoadColumnMap(
      bigRoad
    );


  const sequence =
    [];


  for (
    let index = 0;
    index <
    bigRoad.cells.length;
    index++
  ) {

    const cell =
      bigRoad.cells[
        index
      ];


    const previous =
      index > 0
        ? bigRoad.cells[
            index - 1
          ]
        : null;


    if (
      cell.col <
      offset
    ) {

      continue;
    }


    const red =
      derivedColourForCell(
        cell,
        previous,
        columns,
        offset
      );


    if (
      red ===
      null
    ) {

      continue;
    }


    sequence.push(
      red
        ? "red"
        : "blue"
    );
  }


  return sequence;
}


/* ================================================================
   GENERIC 6-ROW COLOUR ROAD
   ================================================================ */

function buildColourRoad(
  sequence
) {

  const rows =
    6;


  const grid =
    new Map();


  const cells =
    [];


  const key = (
    row,
    col
  ) =>
    `${row}:${col}`;


  let last =
    null;


  let lastColour =
    null;


  let originColumn =
    0;


  let maxColumn =
    0;


  for (
    const colour
    of sequence
  ) {

    let row =
      0;


    let col =
      0;


    if (
      !last
    ) {

      row =
        0;


      col =
        0;


      originColumn =
        0;

    } else if (
      colour !==
      lastColour
    ) {

      originColumn++;


      row =
        0;


      col =
        originColumn;


      while (
        grid.has(
          key(
            row,
            col
          )
        )
      ) {

        col++;
      }


      originColumn =
        col;

    } else {

      const downRow =
        last.row +
        1;


      const downCol =
        last.col;


      if (
        downRow <
        rows &&
        !grid.has(
          key(
            downRow,
            downCol
          )
        )
      ) {

        row =
          downRow;


        col =
          downCol;

      } else {

        row =
          last.row;


        col =
          last.col +
          1;


        while (
          grid.has(
            key(
              row,
              col
            )
          )
        ) {

          col++;
        }
      }
    }


    const cell = {

      row,

      col,

      colour,
    };


    grid.set(
      key(
        row,
        col
      ),
      cell
    );


    cells.push(
      cell
    );


    last =
      cell;


    lastColour =
      colour;


    maxColumn =
      Math.max(
        maxColumn,
        col
      );
  }


  return {

    cells,

    maxColumn,
  };
}


/* ================================================================
   DRAW DERIVED CIRCLE ROAD
   ================================================================ */

function drawDerivedCircleRoad(
  canvasId,
  sequence,
  filled
) {

  const canvas =
    $(
      canvasId
    );


  const setup =
    setupCanvas(
      canvas,
      105,
      500
    );


  if (
    !setup
  ) {

    return;
  }


  const {
    ctx,
    width,
    height,
  } =
    setup;


  const rows =
    6;


  const cell =
    height /
    rows;


  const visibleColumns =
    Math.max(
      1,

      Math.floor(
        width /
        cell
      )
    );


  drawGrid(
    ctx,
    width,
    height,
    cell
  );


  const road =
    buildColourRoad(
      sequence
    );


  const startColumn =
    Math.max(
      0,

      road.maxColumn -
      visibleColumns +
      1
    );


  for (
    const item
    of road.cells
  ) {

    const displayCol =
      item.col -
      startColumn;


    if (
      displayCol < 0 ||
      displayCol >=
      visibleColumns
    ) {

      continue;
    }


    const cx =
      displayCol *
      cell +
      cell / 2;


    const cy =
      item.row *
      cell +
      cell / 2;


    const radius =
      cell *
      0.29;


    const colour =
      ROAD_COLOURS[
        item.colour
      ];


    ctx.save();


    if (
      filled
    ) {

      ctx.fillStyle =
        colour;


      ctx.beginPath();


      ctx.arc(
        cx,
        cy,
        radius,
        0,
        Math.PI * 2
      );


      ctx.fill();

    } else {

      ctx.strokeStyle =
        colour;


      ctx.lineWidth =
        Math.max(
          1.5,
          cell * 0.10
        );


      ctx.beginPath();


      ctx.arc(
        cx,
        cy,
        radius,
        0,
        Math.PI * 2
      );


      ctx.stroke();
    }


    ctx.restore();
  }
}


/* ================================================================
   COCKROACH PIG
   ================================================================ */

function drawCockroachRoad(
  sequence
) {

  const canvas =
    $("cockroachRoad");


  const setup =
    setupCanvas(
      canvas,
      105,
      500
    );


  if (
    !setup
  ) {

    return;
  }


  const {
    ctx,
    width,
    height,
  } =
    setup;


  const rows =
    6;


  const cell =
    height /
    rows;


  const visibleColumns =
    Math.max(
      1,

      Math.floor(
        width /
        cell
      )
    );


  drawGrid(
    ctx,
    width,
    height,
    cell
  );


  const road =
    buildColourRoad(
      sequence
    );


  const startColumn =
    Math.max(
      0,

      road.maxColumn -
      visibleColumns +
      1
    );


  for (
    const item
    of road.cells
  ) {

    const displayCol =
      item.col -
      startColumn;


    if (
      displayCol < 0 ||
      displayCol >=
      visibleColumns
    ) {

      continue;
    }


    const cx =
      displayCol *
      cell +
      cell / 2;


    const cy =
      item.row *
      cell +
      cell / 2;


    const radius =
      cell *
      0.30;


    const colour =
      ROAD_COLOURS[
        item.colour
      ];


    ctx.save();


    ctx.strokeStyle =
      colour;


    ctx.lineWidth =
      Math.max(
        2,
        cell * 0.12
      );


    ctx.lineCap =
      "round";


    ctx.beginPath();


    ctx.moveTo(
      cx -
      radius,
      cy +
      radius
    );


    ctx.lineTo(
      cx +
      radius,
      cy -
      radius
    );


    ctx.stroke();


    ctx.restore();
  }
}


/* ================================================================
   DRAGON / TIGER ROAD

   Each Baccarat HAND owns one cell.

   If that hand triggered multiple Dragon/Tiger-style results,
   markers are stacked inside the same cell rather than pretending
   that they were separate hands.
   ================================================================ */

function markerClass(
  marker
) {

  const classes = [
    "dt-marker",
  ];


  switch (
    marker.type
  ) {

    case "dragon":

      classes.push(
        "dragon"
      );

      break;


    case "tiger":

      classes.push(
        "tiger"
      );

      break;


    case "tie":

      classes.push(
        "tie"
      );

      break;


    case "immortal":

      classes.push(
        "immortal"
      );

      break;


    case "rising-dragon":

      classes.push(
        "rising-dragon"
      );

      break;


    case "rising-tiger":

      classes.push(
        "rising-tiger"
      );

      break;


    default:

      classes.push(
        "dragon"
      );

      break;
  }


  if (
    marker.modifier
  ) {

    classes.push(
      marker.modifier
    );
  }


  return classes.join(
    " "
  );
}


/* ================================================================
   DRAGON / TIGER MARKER HTML
   ================================================================ */

function dragonTigerMarkerHTML(
  marker
) {

  return `
    <span
      class="${markerClass(
        marker
      )}"
      title="${marker.label}"
    >
      ${marker.code}
    </span>
  `;
}


/* ================================================================
   RENDER DRAGON / TIGER ROAD
   ================================================================ */

function renderDragonTigerRoad() {

  const box =
    $("dragonTigerRoad");


  if (
    !box
  ) {

    return;
  }


  /*
   * Keep only hands that produced at least one Dragon/Tiger
   * side-result marker.
   */

  const qualifying =
    roadHistory.filter(
      (item) =>
        Array.isArray(
          item.dtMarkers
        ) &&
        item.dtMarkers.length >
        0
    );


  if (
    !qualifying.length
  ) {

    box.innerHTML =
      `
        <div
          class="dt-cell"
          style="
            grid-column:1/-1;
            min-height:104px;
            color:#777;
            font-size:10px;
            font-weight:700;
          "
        >
          NO DRAGON / TIGER RESULTS YET
        </div>
      `;


    return;
  }


  /*
   * HTML uses a 12-column × 3-row TV panel on desktop.
   * Keep the newest 36 qualifying hands.
   */

  const visible =
    qualifying.slice(
      -36
    );


  box.innerHTML =
    visible
      .map(
        (
          item,
          index
        ) => {

          const markers =
            item.dtMarkers;


          /*
           * One primary marker is shown large.
           * Additional simultaneous qualifiers are shown as a
           * small +N indicator, while the tooltip contains all
           * descriptions.
           */

          const primary =
            markers[
              0
            ];


          const title =
            markers
              .map(
                (marker) =>
                  marker.label
              )
              .join(
                " · "
              );


          return `
            <div
              class="dt-cell"
              title="${title}"
              data-road-index="${index}"
            >

              ${dragonTigerMarkerHTML(
                primary
              )}

              ${
                markers.length > 1
                  ? `
                      <span
                        class="dt-multi"
                        title="${title}"
                      >
                        +${
                          markers.length -
                          1
                        }
                      </span>
                    `
                  : ""
              }

            </div>
          `;
        }
      )
      .join("");
}


/* ================================================================
   ROAD STATISTICS
   ================================================================ */

function renderRoadStats() {

  let player =
    0;


  let banker =
    0;


  let tie =
    0;


  let playerPair =
    0;


  let bankerPair =
    0;


  for (
    const item
    of roadHistory
  ) {

    if (
      item.winner ===
      "player"
    ) {

      player++;
    }


    else if (
      item.winner ===
      "banker"
    ) {

      banker++;
    }


    else if (
      item.winner ===
      "tie"
    ) {

      tie++;
    }


    if (
      item.playerPair
    ) {

      playerPair++;
    }


    if (
      item.bankerPair
    ) {

      bankerPair++;
    }
  }


  const values = {

    roadHands:
      roadHistory.length,

    roadPlayer:
      player,

    roadBanker:
      banker,

    roadTie:
      tie,

    roadPlayerPair:
      playerPair,

    roadBankerPair:
      bankerPair,
  };


  for (
    const [
      id,
      value,
    ]
    of Object.entries(
      values
    )
  ) {

    const element =
      $(
        id
      );


    if (
      element
    ) {

      element.textContent =
        String(
          value
        );
    }
  }
}


/* ================================================================
   NEXT-RESULT ROAD PREVIEW

   This is NOT a gambling prediction.

   It displays what the derived-road colour would become IF the
   next hand were Player or Banker.
   ================================================================ */

function nextDerivedColours(
  hypotheticalWinner
) {

  const hypothetical =
    [
      ...roadHistory,

      {

        winner:
          hypotheticalWinner,

        playerPair:
          false,

        bankerPair:
          false,

        dtMarkers:
          [],
      },
    ];


  const roads =
    [

      buildDerivedSequence(
        hypothetical,
        1
      ),

      buildDerivedSequence(
        hypothetical,
        2
      ),

      buildDerivedSequence(
        hypothetical,
        3
      ),
    ];


  return roads.map(
    (road) =>
      road.length
        ? road[
            road.length -
            1
          ]
        : null
  );
}


/* ================================================================
   PREDICTION MARK
   ================================================================ */

function predictionMark(
  colour,
  type
) {

  if (
    !colour
  ) {

    return `
      <span
        style="
          width:11px;
          height:11px;
          display:inline-flex;
          align-items:center;
          justify-content:center;
          color:#777;
          font-size:10px;
        "
      >
        —
      </span>
    `;
  }


  const cls =
    colour ===
    "red"
      ? "pred-banker"
      : "pred-player";


  if (
    type ===
    "slash"
  ) {

    return `
      <span
        class="
          pred-slash
          ${cls}
        "
      ></span>
    `;
  }


  return `
    <span
      class="
        pred-dot
        ${cls}
      "
    ></span>
  `;
}


/* ================================================================
   RENDER PREDICTIONS
   ================================================================ */

function renderPredictions() {

  const player =
    nextDerivedColours(
      "player"
    );


  const banker =
    nextDerivedColours(
      "banker"
    );


  const playerBox =
    $("playerPrediction");


  const bankerBox =
    $("bankerPrediction");


  if (
    playerBox
  ) {

    playerBox.innerHTML =
      predictionMark(
        player[0],
        "circle"
      )
      +
      predictionMark(
        player[1],
        "circle"
      )
      +
      predictionMark(
        player[2],
        "slash"
      );
  }


  if (
    bankerBox
  ) {

    bankerBox.innerHTML =
      predictionMark(
        banker[0],
        "circle"
      )
      +
      predictionMark(
        banker[1],
        "circle"
      )
      +
      predictionMark(
        banker[2],
        "slash"
      );
  }
}


/* ================================================================
   RENDER ROAD TV
   ================================================================ */

function renderRoadTV() {

  renderRoadStats();


  drawBeadPlate();


  drawBigRoad();


  const bigEye =
    buildDerivedSequence(
      roadHistory,
      1
    );


  const small =
    buildDerivedSequence(
      roadHistory,
      2
    );


  const cockroach =
    buildDerivedSequence(
      roadHistory,
      3
    );


  drawDerivedCircleRoad(
    "bigEyeRoad",
    bigEye,
    false
  );


  drawDerivedCircleRoad(
    "smallRoad",
    small,
    true
  );


  drawCockroachRoad(
    cockroach
  );


  /*
   * New side-bet result road.
   */

  renderDragonTigerRoad();


  renderPredictions();
}


/* ================================================================
   DOM VERIFICATION
   ================================================================ */

function verifyDOM() {

  const required = [

    "phaseLabel",

    "balanceDisplay",

    "chipBar",

    "resetBtn",

    "stakeMetric",

    "returnMetric",

    "netMetric",

    "history",

    "statusBar",

    "playerScore",

    "bankerScore",

    "playerCards",

    "bankerCards",

    "winner",

    "wagerGrid",

    "pendingTotal",

    "clearBtn",

    "dealBtn",

    "breakdown",

    "payTable",

    "roadHands",

    "roadPlayer",

    "roadBanker",

    "roadTie",

    "roadPlayerPair",

    "roadBankerPair",

    "beadPlate",

    "bigRoad",

    "bigEyeRoad",

    "smallRoad",

    "cockroachRoad",

    /*
     * New Part-1 HTML contract.
     */

    "dragonTigerRoad",

    "playerPrediction",

    "bankerPrediction",

    "clearRoadBtn",
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
      `Baccarat HTML/JS mismatch. Missing: ${missing.join(", ")}`
    );
  }
}


/* ================================================================
   BIND WAGER SPOTS
   ================================================================ */

function bindWagers() {

  document
    .querySelectorAll(
      ".spot[data-wager]"
    )
    .forEach(
      (spot) => {

        spot.addEventListener(
          "click",

          () => {

            placeBet(
              spot.dataset.wager
            );
          }
        );
      }
    );
}


/* ================================================================
   RESIZE ROAD TV
   ================================================================ */

let resizeTimer =
  null;


function onResize() {

  clearTimeout(
    resizeTimer
  );


  resizeTimer =
    setTimeout(
      () => {

        renderRoadTV();

      },
      120
    );
}


/* ================================================================
   INITIALISE
   ================================================================ */

function init() {

  try {

    verifyDOM();


    saveBalance();


    renderChips();


    bindWagers();


    renderHistory();


    renderPayTable();


    renderRoadTV();


    clearTableResult();


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


    $("clearRoadBtn")
      .addEventListener(
        "click",
        clearRoad
      );


    window.addEventListener(
      "resize",
      onResize
    );


    const phase =
      $("phaseLabel");


    if (
      phase
    ) {

      phase.textContent =
        "BETTING";
    }


    const stake =
      $("stakeMetric");


    const returned =
      $("returnMetric");


    const net =
      $("netMetric");


    if (
      stake
    ) {

      stake.textContent =
        "0";
    }


    if (
      returned
    ) {

      returned.textContent =
        "0";
    }


    if (
      net
    ) {

      net.textContent =
        "0";


      net.className =
        "metric-value";
    }


    status(
      "Place your bets — select a chip, tap a wager, then Deal."
    );


    refreshBetting();


    console.log(
      "[BACCARAT]",
      "Frontend initialised:",
      GAME
    );


  } catch (error) {

    console.error(
      "[BACCARAT INIT ERROR]",
      error
    );


    const statusBar =
      $("statusBar");


    if (
      statusBar
    ) {

      statusBar.className =
        "status-bar bad";


      statusBar.textContent =
        `BACCARAT FRONTEND ERROR: ${error.message}`;
    }


    const phase =
      $("phaseLabel");


    if (
      phase
    ) {

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