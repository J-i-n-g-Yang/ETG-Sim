/* ================================================================
   ETG SIM — CRAPS SOLO

   Dedicated stateful Craps frontend.

   Backend:
   POST /api/solo/dice/roll
   POST /api/solo/dice/craps/action

   Craps differs from Sic Bo / Great Fortune Dice because wagers
   can persist across multiple rolls.
   ================================================================ */

const GAME = "craps";

const MAX_BET =
  Number(window.DICE_MAX);

const STARTING_CREDITS =
  Number(window.DICE_START);

const $ = (id) =>
  document.getElementById(id);

const fmt = (value) =>
  Number(value || 0).toLocaleString(
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
  "etg_dice_bal_craps";

const STATE_KEY =
  "etg_dice_state_craps";

const HISTORY_KEY =
  "etg_dice_history_craps";


/* ================================================================
   STATE
   ================================================================ */

let selectedChip = 1000;

let pendingBets = {};

let busy = false;

let rollingAnimationTimer =
  null;


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


let gameState = {};

try {
  gameState =
    JSON.parse(
      localStorage.getItem(
        STATE_KEY
      ) || "{}"
    );
} catch {
  gameState = {};
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


/* ================================================================
   GENERAL HELPERS
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


function sleep(ms) {
  return new Promise(
    (resolve) =>
      setTimeout(
        resolve,
        ms
      )
  );
}


function pendingTotal() {
  return Object
    .values(
      pendingBets
    )
    .reduce(
      (
        total,
        value
      ) =>
        total +
        Number(value),
      0
    );
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


function saveState() {
  localStorage.setItem(
    STATE_KEY,
    JSON.stringify(
      gameState || {}
    )
  );

  renderPoint();
}


function saveHistory() {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(
      history
    )
  );
}


/* ================================================================
   CSS
   ================================================================ */

function installCrapsStyles() {
  if (
    document.getElementById(
      "etgCrapsStyles"
    )
  ) {
    return;
  }

  const style =
    document.createElement(
      "style"
    );

  style.id =
    "etgCrapsStyles";

  style.textContent = `

    /* ============================================================
       PHYSICAL DICE
       ============================================================ */

    .physical-die {
      --die-size: 62px;

      position: relative;

      width: var(--die-size);
      height: var(--die-size);

      flex:
        0 0
        var(--die-size);

      border-radius: 13px;

      background:
        linear-gradient(
          145deg,
          #ffffff 0%,
          #f5f0df 58%,
          #d7d0bc 100%
        );

      border:
        1px solid
        rgba(
          0,
          0,
          0,
          .55
        );

      box-shadow:
        inset
        3px 3px 7px
        rgba(
          255,
          255,
          255,
          .95
        ),

        inset
        -4px -5px 8px
        rgba(
          0,
          0,
          0,
          .18
        ),

        0 8px 12px
        rgba(
          0,
          0,
          0,
          .48
        );

      transform-origin:
        center center;

      user-select: none;
    }


    .physical-die.mini {
      --die-size: 28px;

      border-radius: 6px;

      box-shadow:
        inset
        1px 1px 3px
        rgba(
          255,
          255,
          255,
          .95
        ),

        inset
        -2px -2px 3px
        rgba(
          0,
          0,
          0,
          .18
        ),

        0 2px 4px
        rgba(
          0,
          0,
          0,
          .35
        );
    }


    .physical-die.micro {
      --die-size: 22px;

      border-radius: 5px;

      box-shadow:
        inset
        1px 1px 2px
        rgba(
          255,
          255,
          255,
          .9
        ),

        inset
        -1px -1px 2px
        rgba(
          0,
          0,
          0,
          .18
        ),

        0 1px 3px
        rgba(
          0,
          0,
          0,
          .35
        );
    }


    .die-pip {
      position: absolute;

      width:
        calc(
          var(--die-size) * .145
        );

      height:
        calc(
          var(--die-size) * .145
        );

      border-radius: 50%;

      background:
        radial-gradient(
          circle at 35% 30%,
          #343434 0%,
          #080808 65%,
          #000 100%
        );
    }


    .die-pip.red {
      background:
        radial-gradient(
          circle at 35% 30%,
          #e33c37 0%,
          #a00f0c 65%,
          #650604 100%
        );
    }


    .pip-tl {
      left: 20%;
      top: 20%;
    }

    .pip-tc {
      left: 42.75%;
      top: 20%;
    }

    .pip-tr {
      right: 20%;
      top: 20%;
    }

    .pip-ml {
      left: 20%;
      top: 42.75%;
    }

    .pip-mc {
      left: 42.75%;
      top: 42.75%;
    }

    .pip-mr {
      right: 20%;
      top: 42.75%;
    }

    .pip-bl {
      left: 20%;
      bottom: 20%;
    }

    .pip-bc {
      left: 42.75%;
      bottom: 20%;
    }

    .pip-br {
      right: 20%;
      bottom: 20%;
    }


    .dice-visual-row {
      display: flex;

      align-items: center;
      justify-content: center;

      gap: 4px;

      min-height: 30px;
    }


    /* ============================================================
       ANIMATION
       ============================================================ */

    .physical-die.rolling {
      animation:
        etg-dice-tumble
        .34s
        linear
        infinite;
    }


    .physical-die.rolling:nth-child(2) {
      animation-delay: -.09s;
    }


    @keyframes etg-dice-tumble {

      0% {
        transform:
          translate(0, 0)
          rotate(0deg)
          scale(1);
      }

      20% {
        transform:
          translate(-7px, -9px)
          rotate(70deg)
          scale(.96);
      }

      40% {
        transform:
          translate(6px, -3px)
          rotate(145deg)
          scale(1.05);
      }

      60% {
        transform:
          translate(-3px, 7px)
          rotate(220deg)
          scale(.98);
      }

      80% {
        transform:
          translate(7px, -5px)
          rotate(300deg)
          scale(1.04);
      }

      100% {
        transform:
          translate(0, 0)
          rotate(360deg)
          scale(1);
      }
    }


    .dice-result-shaking {
      animation:
        etg-dome-shake
        .16s
        linear
        infinite;
    }


    @keyframes etg-dome-shake {

      0% {
        transform: translateX(0);
      }

      25% {
        transform: translateX(-3px);
      }

      50% {
        transform: translateX(3px);
      }

      75% {
        transform: translateX(-2px);
      }

      100% {
        transform: translateX(0);
      }
    }


    .physical-die.settling {
      animation:
        etg-dice-settle
        .34s
        ease-out;
    }


    @keyframes etg-dice-settle {

      0% {
        transform:
          translateY(-12px)
          rotate(35deg)
          scale(1.08);
      }

      55% {
        transform:
          translateY(4px)
          rotate(-7deg)
          scale(.97);
      }

      75% {
        transform:
          translateY(-2px)
          rotate(3deg)
          scale(1.02);
      }

      100% {
        transform:
          translateY(0)
          rotate(0deg)
          scale(1);
      }
    }


    /* ============================================================
       CRAPS TABLE
       ============================================================ */

    .craps-table {
      display: grid;

      grid-template-columns:
        minmax(760px, 5fr)
        minmax(230px, 1.35fr);

      gap: 6px;
    }


    .craps-layout {
      border:
        2px solid
        #c9a63b;

      border-radius: 10px;

      padding: 6px;

      background:
        #07502f;
    }


    .craps-box-row {
      display: grid;

      grid-template-columns:
        110px
        repeat(6, 1fr);

      gap: 3px;
    }


    .craps-box-number {
      position: relative;

      min-height: 118px;

      border:
        1px solid
        #c6a543;

      border-radius: 5px;

      padding: 4px;

      text-align: center;
    }


    .craps-number-title {
      font-size: 29px;
      font-weight: 900;

      color:
        #f4e5a1;

      line-height: 1;

      margin-bottom: 4px;
    }


    .craps-number-bets {
      display: grid;

      grid-template-columns:
        repeat(3, 1fr);

      gap: 2px;
    }


    .craps-number-bets .bet {
      min-height: 61px;

      padding: 3px;

      font-size: 11px;
    }


    .craps-puck {
      position: absolute;

      width: 34px;
      height: 34px;

      border-radius: 50%;

      right: 4px;
      top: 4px;

      display: none;

      align-items: center;
      justify-content: center;

      background:
        #f4f1dc;

      color: #111;

      border:
        2px solid
        #111;

      font-size: 9px;
      font-weight: 900;

      box-shadow:
        0 3px 5px
        #0008;

      z-index: 5;
    }


    .craps-puck.active {
      display: flex;
    }


    .craps-off-puck {
      min-height: 118px;

      display: flex;

      align-items: center;
      justify-content: center;
    }


    .craps-off-puck span {
      width: 58px;
      height: 58px;

      border-radius: 50%;

      display: flex;

      align-items: center;
      justify-content: center;

      background: #111;

      color: #fff;

      border:
        3px solid
        #eee;

      font-weight: 900;
      font-size: 12px;

      box-shadow:
        0 4px 8px
        #0008;
    }


    .craps-off-puck.point-on span {
      opacity: .25;
    }


    .craps-come {
      margin-top: 4px;

      min-height: 92px;
    }


    .craps-come > .bet {
      min-height: 92px;

      font-size: 28px;
      font-weight: 900;
    }


    .craps-dont-come-row {
      display: grid;

      grid-template-columns:
        1fr 3fr;

      gap: 4px;

      margin-top: 4px;
    }


    .craps-dont-come-row .bet {
      min-height: 72px;
    }


    .craps-field-box {
      margin-top: 4px;

      border:
        1px solid
        #c6a543;

      border-radius: 6px;

      padding: 4px;
    }


    .craps-field-numbers {
      display: grid;

      grid-template-columns:
        repeat(7, 1fr);

      gap: 3px;
    }


    .craps-field-numbers > div {
      text-align: center;

      padding: 5px 2px;

      font-size: 20px;
      font-weight: 900;

      color:
        #f4e5a1;
    }


    .craps-field-main {
      min-height: 72px;

      margin-top: 3px;
    }


    .craps-line-row {
      display: grid;

      grid-template-columns:
        1fr 4fr;

      gap: 4px;

      margin-top: 4px;
    }


    .craps-line-row .bet {
      min-height: 67px;
    }


    .craps-pass-line {
      margin-top: 4px;

      min-height: 68px;
    }


    .craps-pass-line.bet {
      font-size: 25px;
      font-weight: 900;
    }


    .craps-prop-panel {
      border:
        2px solid
        #c9a63b;

      border-radius: 10px;

      padding: 6px;

      background:
        #063c25;
    }


    .craps-prop-title {
      text-align: center;

      color:
        #f1dc82;

      font-weight: 900;

      letter-spacing: 1px;

      margin:
        4px 0 6px;
    }


    .craps-hard-grid,
    .craps-one-roll-grid,
    .craps-horn-grid {
      display: grid;

      grid-template-columns:
        repeat(2, 1fr);

      gap: 3px;
    }


    .craps-hard-grid .bet {
      min-height: 78px;
    }


    .craps-one-roll-grid .bet,
    .craps-horn-grid .bet {
      min-height: 62px;
    }


    .craps-horn-grid {
      margin-top: 3px;
    }


    /* ============================================================
       ACTIVE TABLE WAGERS
       ============================================================ */

    .craps-active-panel {
      margin-top: 7px;

      border:
        1px solid
        #a9872e;

      border-radius: 7px;

      padding: 6px;

      background:
        #031f15;
    }


    .craps-active-title {
      color:
        #f1dc82;

      font-weight: 900;

      margin-bottom: 5px;
    }


    .craps-active-row {
      display: grid;

      grid-template-columns:
        1fr auto;

      gap: 5px;

      align-items: center;

      padding: 5px 0;

      border-bottom:
        1px solid
        #ffffff12;

      font-size: 12px;
    }


    .craps-active-actions {
      display: flex;

      gap: 3px;
    }


    .craps-action-btn {
      border:
        1px solid
        #b89635;

      background:
        #143a2a;

      color:
        #eee4b7;

      border-radius: 4px;

      padding:
        3px 6px;

      cursor: pointer;

      font-size: 10px;
    }


    .craps-action-btn:hover {
      background:
        #20563e;
    }


    .craps-active-chip {
      display: inline-block;

      padding:
        2px 6px;

      margin-left: 4px;

      border-radius: 10px;

      background:
        #a92727;

      color: white;

      font-weight: 800;
    }


    .craps-come-point {
      border-top:
        1px dashed
        #d6b34c;

      margin-top: 3px;

      padding-top: 3px;

      font-size: 10px;

      color:
        #f1dc82;
    }


    .craps-existing-badge {
      position: absolute;

      left: 4px;
      bottom: 4px;

      border-radius: 12px;

      padding:
        2px 6px;

      background:
        #b32929;

      color: white;

      border:
        1px solid
        #ffdca1;

      font-size: 10px;
      font-weight: 900;

      z-index: 4;
    }

  `;

  document.head.appendChild(
    style
  );
}


/* ================================================================
   DICE
   ================================================================ */

const PIP_MAP = {

  1: [
    "mc",
  ],

  2: [
    "tl",
    "br",
  ],

  3: [
    "tl",
    "mc",
    "br",
  ],

  4: [
    "tl",
    "tr",
    "bl",
    "br",
  ],

  5: [
    "tl",
    "tr",
    "mc",
    "bl",
    "br",
  ],

  6: [
    "tl",
    "tr",
    "ml",
    "mr",
    "bl",
    "br",
  ],

};


function physicalDieHTML(
  value,
  size = "main",
  extraClass = ""
) {
  const safeValue =
    Math.min(
      6,
      Math.max(
        1,
        Number(value) || 1
      )
    );

  const sizeClass =
    size === "mini"
      ? "mini"
      : size === "micro"
        ? "micro"
        : "";

  const pips =
    PIP_MAP[
      safeValue
    ]
      .map(
        (position) => {

          const red =
            (
              safeValue === 1 &&
              position === "mc"
            ) ||
            (
              safeValue === 5 &&
              position === "mc"
            );

          return `
            <span
              class="
                die-pip
                pip-${position}
                ${
                  red
                    ? "red"
                    : ""
                }
              "
            ></span>
          `;
        }
      )
      .join("");

  return `
    <div
      class="
        physical-die
        ${sizeClass}
        ${extraClass}
      "
    >
      ${pips}
    </div>
  `;
}


function diceVisual(
  values,
  size = "mini"
) {
  return `
    <div
      class="
        dice-visual-row
      "
    >
      ${
        values
          .map(
            value =>
              physicalDieHTML(
                value,
                size
              )
          )
          .join("")
      }
    </div>
  `;
}


function dicePair(
  first,
  second
) {
  return diceVisual(
    [
      first,
      second,
    ],
    "mini"
  );
}


/* ================================================================
   BET CELL
   ================================================================ */

function betCell(
  wager,
  main,
  sub = "",
  extraClass = ""
) {
  return `
    <div
      class="
        bet
        ${extraClass}
      "
      data-wager="${wager}"
    >

      ${main}

      ${
        sub
          ? `
            <small>
              ${sub}
            </small>
          `
          : ""
      }

    </div>
  `;
}


/* ================================================================
   CRAPS STATE HELPERS
   ================================================================ */

function crapsStateBets() {
  return (
    gameState.bets ||
    {}
  );
}


function pointData(
  bucket,
  number
) {
  return Number(
    (
      gameState[
        bucket
      ] || {}
    )[
      String(number)
    ] || 0
  );
}


function hasActiveCrapsBets() {

  const direct =
    Object
      .values(
        gameState.bets ||
        {}
      )
      .some(
        amount =>
          Number(amount) > 0
      );

  if (direct) {
    return true;
  }


  for (
    const bucketName of [
      "come",
      "dont_come",
      "come_odds",
      "dont_come_odds",
    ]
  ) {

    const bucket =
      gameState[
        bucketName
      ] || {};

    if (
      Object
        .values(
          bucket
        )
        .some(
          amount =>
            Number(amount) > 0
        )
    ) {
      return true;
    }
  }

  return false;
}


function crapsDisplayName(
  wager
) {
  return String(
    wager
  )
    .replace(
      /_/g,
      " "
    )
    .replace(
      /\b\w/g,
      char =>
        char.toUpperCase()
    );
}


/* ================================================================
   CRAPS TABLE
   ================================================================ */

function renderCrapsBoard() {

  const point =
    Number(
      gameState.point
    ) || null;


  const numbers = [
    4,
    5,
    6,
    8,
    9,
    10,
  ];


  function numberBox(
    number
  ) {

    const come =
      pointData(
        "come",
        number
      );

    const dontCome =
      pointData(
        "dont_come",
        number
      );

    const comeOdds =
      pointData(
        "come_odds",
        number
      );

    const dontComeOdds =
      pointData(
        "dont_come_odds",
        number
      );


    return `
      <div
        class="
          craps-box-number
        "
      >

        <div
          class="
            craps-puck
            ${
              point === number
                ? "active"
                : ""
            }
          "
        >
          ON
        </div>


        <div
          class="
            craps-number-title
          "
        >
          ${number}
        </div>


        <div
          class="
            craps-number-bets
          "
        >

          ${betCell(
            `place_${number}`,

            "PLACE",

            number === 4 ||
            number === 10
              ? "9:5"
              : number === 5 ||
                number === 9
                ? "7:5"
                : "7:6"
          )}


          ${betCell(
            `buy_${number}`,

            "BUY",

            "TRUE ODDS + 5% VIG"
          )}


          ${betCell(
            `lay_${number}`,

            "LAY",

            "TRUE ODDS + VIG"
          )}

        </div>


        ${
          come > 0
            ? `
              <div
                class="
                  craps-come-point
                "
              >

                COME

                <span
                  class="
                    craps-active-chip
                  "
                >
                  ${fmt(come)}
                </span>

                ${
                  comeOdds > 0
                    ? `
                      ODDS

                      <span
                        class="
                          craps-active-chip
                        "
                      >
                        ${fmt(
                          comeOdds
                        )}
                      </span>
                    `
                    : ""
                }

              </div>
            `
            : ""
        }


        ${
          dontCome > 0
            ? `
              <div
                class="
                  craps-come-point
                "
              >

                DON'T COME

                <span
                  class="
                    craps-active-chip
                  "
                >
                  ${fmt(
                    dontCome
                  )}
                </span>

                ${
                  dontComeOdds > 0
                    ? `
                      ODDS

                      <span
                        class="
                          craps-active-chip
                        "
                      >
                        ${fmt(
                          dontComeOdds
                        )}
                      </span>
                    `
                    : ""
                }

              </div>
            `
            : ""
        }

      </div>
    `;
  }


  const hardways =
    [
      [4, 2],
      [6, 3],
      [8, 4],
      [10, 5],
    ]
      .map(
        (
          [
            total,
            face,
          ]
        ) =>
          betCell(
            `hard_${total}`,

            `
              ${dicePair(
                face,
                face
              )}

              <strong>
                HARD ${total}
              </strong>
            `,

            total === 4 ||
            total === 10
              ? "7:1"
              : "9:1"
          )
      )
      .join("");


  $("bettingArea")
    .innerHTML = `

      <div
        class="
          craps-table
        "
      >

        <div
          class="
            craps-layout
          "
        >

          <!-- BOX NUMBERS -->

          <div
            class="
              craps-box-row
            "
          >

            <div
              class="
                craps-off-puck
                ${
                  point
                    ? "point-on"
                    : ""
                }
              "
            >
              <span>
                OFF
              </span>
            </div>


            ${
              numbers
                .map(
                  numberBox
                )
                .join("")
            }

          </div>


          <!-- COME -->

          <div
            class="
              craps-come
            "
          >

            ${betCell(
              "come",

              `
                <strong>
                  COME
                </strong>
              `,

              point
                ? "7 / 11 WIN · 2 / 3 / 12 LOSE"
                : "AVAILABLE AFTER POINT"
            )}

          </div>


          <!-- DON'T COME -->

          <div
            class="
              craps-dont-come-row
            "
          >

            ${betCell(
              "dont_come",

              `
                <strong>
                  DON'T COME
                </strong>
              `,

              point
                ? "2 / 3 WIN · 12 PUSH"
                : "AVAILABLE AFTER POINT"
            )}

            <div></div>

          </div>


          <!-- FIELD -->

          <div
            class="
              craps-field-box
            "
          >

            <div
              class="
                craps-field-numbers
              "
            >
              <div>2</div>
              <div>3</div>
              <div>4</div>
              <div>9</div>
              <div>10</div>
              <div>11</div>
              <div>12</div>
            </div>


            ${betCell(
              "field",

              `
                <strong>
                  FIELD
                </strong>
              `,

              "3 / 4 / 9 / 10 / 11 PAY 1:1 · 2 / 12 PAY 2:1",

              "craps-field-main"
            )}

          </div>


          <!-- DON'T PASS -->

          <div
            class="
              craps-line-row
            "
          >

            ${betCell(
              "dont_pass",

              `
                <strong>
                  DON'T PASS
                </strong>
              `,

              point
                ? `POINT ${point}`
                : "2 / 3 WIN · 12 PUSH"
            )}


            ${betCell(
              "dont_pass_odds",

              `
                <strong>
                  DON'T PASS ODDS
                </strong>
              `,

              point
                ? `TRUE ODDS ON ${point}`
                : "POINT REQUIRED"
            )}

          </div>


          <!-- PASS LINE -->

          ${betCell(
            "pass_line",

            `
              <strong>
                PASS LINE
              </strong>
            `,

            point
              ? `POINT ${point}`
              : "COME OUT · 7 / 11 WIN · 2 / 3 / 12 LOSE",

            "craps-pass-line"
          )}


          ${
            point
              ? betCell(
                  "pass_odds",

                  `
                    <strong>
                      PASS LINE ODDS
                    </strong>
                  `,

                  `TRUE ODDS ON ${point}`
                )
              : ""
          }

        </div>


        <!-- PROPOSITIONS -->

        <div
          class="
            craps-prop-panel
          "
        >

          <div
            class="
              craps-prop-title
            "
          >
            HARDWAYS
          </div>


          <div
            class="
              craps-hard-grid
            "
          >
            ${hardways}
          </div>


          <div
            class="
              craps-prop-title
            "
          >
            ONE ROLL
          </div>


          <div
            class="
              craps-one-roll-grid
            "
          >

            ${betCell(
              "any_seven",
              "ANY 7",
              "4:1"
            )}

            ${betCell(
              "any_craps",
              "ANY CRAPS",
              "7:1"
            )}

            ${betCell(
              "two_crap",
              dicePair(1, 1),
              "2 · 30:1"
            )}

            ${betCell(
              "three_crap",
              dicePair(1, 2),
              "3 · 15:1"
            )}

            ${betCell(
              "eleven",
              dicePair(5, 6),
              "11 · 15:1"
            )}

            ${betCell(
              "twelve_crap",
              dicePair(6, 6),
              "12 · 30:1"
            )}

            ${betCell(
              "craps_eleven",
              "C & E",
              "CRAPS / ELEVEN"
            )}

          </div>


          <div
            class="
              craps-prop-title
            "
          >
            HORN
          </div>


          <div
            class="
              craps-horn-grid
            "
          >

            ${betCell(
              "horn",
              "HORN",
              "2 · 3 · 11 · 12"
            )}

            ${betCell(
              "horn_high_2",
              "HORN HIGH 2",
              "5 UNITS"
            )}

            ${betCell(
              "horn_high_3",
              "HORN HIGH 3",
              "5 UNITS"
            )}

            ${betCell(
              "horn_high_11",
              "HORN HIGH 11",
              "5 UNITS"
            )}

            ${betCell(
              "horn_high_12",
              "HORN HIGH 12",
              "5 UNITS"
            )}

          </div>


          <div
            id="crapsActivePanel"
            class="
              craps-active-panel
            "
          ></div>

        </div>

      </div>
    `;


  bindWagers();

  renderPersistentCrapsBets();

  renderCrapsActivePanel();

  renderPoint();
}


/* ================================================================
   PERSISTENT BET BADGES
   ================================================================ */

function renderPersistentCrapsBets() {

  document
    .querySelectorAll(
      ".craps-existing-badge"
    )
    .forEach(
      badge =>
        badge.remove()
    );


  Object
    .entries(
      crapsStateBets()
    )
    .forEach(
      (
        [
          wager,
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


        document
          .querySelectorAll(
            `[data-wager="${wager}"]`
          )
          .forEach(
            element => {

              const badge =
                document.createElement(
                  "span"
                );

              badge.className =
                "craps-existing-badge";

              badge.textContent =
                fmt(amount);

              element.appendChild(
                badge
              );
            }
          );
      }
    );
}


/* ================================================================
   ACTIVE BET PANEL
   ================================================================ */

function renderCrapsActivePanel() {

  const panel =
    $("crapsActivePanel");

  if (!panel) {
    return;
  }


  const rows = [];


  Object
    .entries(
      gameState.bets ||
      {}
    )
    .forEach(
      (
        [
          wager,
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


        const working =
          (
            gameState.working ||
            {}
          )[wager];


        rows.push(
          crapsActiveRow(
            wager,
            amount,
            working
          )
        );
      }
    );


  for (
    const number of [
      4,
      5,
      6,
      8,
      9,
      10,
    ]
  ) {

    const key =
      String(number);


    const come =
      Number(
        (
          gameState.come ||
          {}
        )[key] || 0
      );


    const dontCome =
      Number(
        (
          gameState.dont_come ||
          {}
        )[key] || 0
      );


    const comeOdds =
      Number(
        (
          gameState.come_odds ||
          {}
        )[key] || 0
      );


    const dontOdds =
      Number(
        (
          gameState.dont_come_odds ||
          {}
        )[key] || 0
      );


    if (
      come > 0
    ) {
      rows.push(
        crapsActiveRow(
          `come_point_${number}`,
          come
        )
      );
    }


    if (
      comeOdds > 0
    ) {
      rows.push(
        crapsActiveRow(
          `come_odds_${number}`,
          comeOdds
        )
      );
    }


    if (
      dontCome > 0
    ) {
      rows.push(
        crapsActiveRow(
          `dont_come_point_${number}`,
          dontCome
        )
      );
    }


    if (
      dontOdds > 0
    ) {
      rows.push(
        crapsActiveRow(
          `dont_come_odds_${number}`,
          dontOdds
        )
      );
    }
  }


  panel.innerHTML = `

    <div
      class="
        craps-active-title
      "
    >
      TABLE WAGERS
    </div>


    ${
      rows.length
        ? rows.join("")
        : `
          <div
            style="
              opacity:.6;
              font-size:11px;
            "
          >
            No persistent wagers.
          </div>
        `
    }

  `;
}


function crapsActiveRow(
  wager,
  amount,
  working = undefined
) {

  const isPass =
    wager ===
    "pass_line";


  const canToggle =
    wager.startsWith(
      "place_"
    ) ||
    wager.startsWith(
      "buy_"
    ) ||
    wager.startsWith(
      "lay_"
    ) ||
    wager.startsWith(
      "hard_"
    ) ||
    wager.startsWith(
      "come_odds_"
    ) ||
    wager.startsWith(
      "dont_come_odds_"
    );


  return `
    <div
      class="
        craps-active-row
      "
    >

      <div>

        ${crapsDisplayName(
          wager
        )}

        <span
          class="
            craps-active-chip
          "
        >
          ${fmt(amount)}
        </span>


        ${
          working === false
            ? " · OFF"
            : working === true
              ? " · ON"
              : ""
        }

      </div>


      <div
        class="
          craps-active-actions
        "
      >

        ${
          canToggle
            ? `
              <button
                type="button"
                class="
                  craps-action-btn
                "
                data-craps-action="on"
                data-craps-wager="${wager}"
              >
                ON
              </button>

              <button
                type="button"
                class="
                  craps-action-btn
                "
                data-craps-action="off"
                data-craps-wager="${wager}"
              >
                OFF
              </button>
            `
            : ""
        }


        ${
          !isPass
            ? `
              <button
                type="button"
                class="
                  craps-action-btn
                "
                data-craps-action="take_down"
                data-craps-wager="${wager}"
              >
                TAKE
              </button>
            `
            : ""
        }

      </div>

    </div>
  `;
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

  bar.innerHTML = "";


  CHIPS.forEach(
    value => {

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

function bindWagers() {

  document
    .querySelectorAll(
      "[data-wager]"
    )
    .forEach(
      element => {

        element.addEventListener(
          "click",
          () =>
            placeBet(
              element.dataset.wager
            )
        );
      }
    );


  document
    .querySelectorAll(
      "[data-craps-action]"
    )
    .forEach(
      button => {

        button.addEventListener(
          "click",
          event => {

            event.stopPropagation();

            crapsAction(
              button.dataset.crapsWager,
              button.dataset.crapsAction
            );
          }
        );
      }
    );
}


function placeBet(
  wagerType
) {

  if (busy) {
    return;
  }


  const point =
    Number(
      gameState.point
    ) || null;


  if (
    (
      wagerType === "come" ||
      wagerType === "dont_come"
    ) &&
    !point
  ) {
    return;
  }


  if (
    (
      wagerType === "pass_odds" ||
      wagerType ===
        "dont_pass_odds"
    ) &&
    !point
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

  refresh();
}


/* ================================================================
   REFRESH
   ================================================================ */

function refresh() {

  const pending =
    pendingTotal();


  if (
    $("pendingTotal")
  ) {
    $("pendingTotal")
      .textContent =
        fmt(pending);
  }


  if (
    $("stakeMetric")
  ) {
    $("stakeMetric")
      .textContent =
        `NEW ${fmt(
          pending
        )}`;
  }


  if (
    $("rollBtn")
  ) {
    $("rollBtn")
      .disabled =
        busy ||
        (
          pending <= 0 &&
          !hasActiveCrapsBets()
        );
  }


  if (
    $("clearBtn")
  ) {
    $("clearBtn")
      .disabled =
        busy ||
        pending <= 0;
  }


  document
    .querySelectorAll(
      "[data-wager]"
    )
    .forEach(
      element => {

        const amount =
          pendingBets[
            element.dataset.wager
          ] || 0;


        let badge =
          element.querySelector(
            ".badge"
          );


        if (!amount) {

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
}


/* ================================================================
   CLEAR PENDING BETS
   ================================================================ */

function clearBets() {

  if (busy) {
    return;
  }


  balance +=
    pendingTotal();


  pendingBets = {};


  saveBalance();

  refresh();
}


/* ================================================================
   CRAPS ACTIONS
   ================================================================ */

async function crapsAction(
  wagerType,
  action
) {

  if (busy) {
    return;
  }


  busy = true;

  refresh();


  try {

    const response =
      await fetch(
        "/api/solo/dice/craps/action",
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              state:
                gameState,

              wager_type:
                wagerType,

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
        "Craps action failed"
      );
    }


    gameState =
      data.state || {};


    balance +=
      Number(
        data.refund || 0
      );


    saveBalance();

    saveState();


    renderCrapsBoard();


  } catch (error) {

    console.error(
      error
    );

  } finally {

    busy = false;

    refresh();
  }
}


/* ================================================================
   RESULT DICE
   ================================================================ */

function renderResultDice(
  dice,
  extraClass = ""
) {

  const area =
    $("diceResult");

  if (!area) {
    return;
  }


  area.innerHTML =
    dice
      .map(
        value =>
          physicalDieHTML(
            value,
            "main",
            extraClass
          )
      )
      .join("");
}


function renderFinalRoll(
  dice
) {

  const area =
    $("diceResult");


  area.classList.remove(
    "dice-result-shaking"
  );


  renderResultDice(
    dice,
    "settling"
  );


  if (
    $("currentRoll")
  ) {
    $("currentRoll")
      .textContent =
        dice.join("-");
  }
}


/* ================================================================
   ROLL ANIMATION
   ================================================================ */

function startRollingAnimation() {

  const area =
    $("diceResult");


  area.classList.add(
    "dice-result-shaking"
  );


  const initial =
    [
      1 +
      Math.floor(
        Math.random() * 6
      ),

      1 +
      Math.floor(
        Math.random() * 6
      ),
    ];


  renderResultDice(
    initial,
    "rolling"
  );


  rollingAnimationTimer =
    window.setInterval(
      () => {

        renderResultDice(
          [
            1 +
            Math.floor(
              Math.random() * 6
            ),

            1 +
            Math.floor(
              Math.random() * 6
            ),
          ],
          "rolling"
        );

      },
      115
    );
}


function stopRollingAnimation() {
  if (rollingAnimationTimer !== null) {
    window.clearInterval(rollingAnimationTimer);
    rollingAnimationTimer = null;
  }

  const area = $("diceResult");

  if (area) {
    area.classList.remove("dice-result-shaking");

    area
      .querySelectorAll(".physical-die")
      .forEach((die) => {
        die.classList.remove("rolling");
      });
  }
}


/* ================================================================
   HISTORY
   ================================================================ */

function historyDiceHTML(
  dice
) {

  return `
    <span
      style="
        display:inline-flex;
        gap:3px;
        vertical-align:middle;
      "
    >

      ${
        dice
          .map(
            value =>
              physicalDieHTML(
                value,
                "micro"
              )
          )
          .join("")
      }

    </span>
  `;
}


function addHistory(
  data
) {

  history.unshift({

    dice:
      data.outcome.dice,

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
}


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
        item => `

          <div
            style="
              display:flex;
              align-items:center;
              justify-content:space-between;
              gap:5px;
              padding:7px 0;
              border-bottom:
                1px solid
                #ffffff12;
            "
          >

            ${historyDiceHTML(
              item.dice
            )}


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
   THROW DICE
   ================================================================ */

async function rollDice() {

  const pending =
    pendingTotal();


  if (busy) {
    return;
  }


  /*
   * Craps is allowed to roll without adding another wager as long
   * as a persistent table wager remains active.
   */

  if (
    pending <= 0 &&
    !hasActiveCrapsBets()
  ) {
    return;
  }


  const wagered =
    pending;


  const bets =
    Object
      .entries(
        pendingBets
      )
      .map(
        (
          [
            wager_type,
            amount,
          ]
        ) => ({
          wager_type,
          amount,
        })
      );


  busy = true;


  if (
    $("phaseLabel")
  ) {
    $("phaseLabel")
      .textContent =
        "ROLLING";
  }


  refresh();

  startRollingAnimation();


  const animationStarted =
    performance.now();


  try {

    const response =
      await fetch(
        "/api/solo/dice/roll",
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

              state:
                gameState,

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
        "Roll failed"
      );
    }


    const elapsed =
      performance.now() -
      animationStarted;


    const minimumAnimation =
      1250;


    if (
      elapsed <
      minimumAnimation
    ) {

      await sleep(
        minimumAnimation -
        elapsed
      );
    }


    stopRollingAnimation();


    renderFinalRoll(
      data.outcome.dice
    );


    /*
     * The pending wager amount has already been deducted from the
     * browser balance when chips were placed.
     *
     * Craps Buy/Lay wagers can also create server-side placement
     * vig. new_wager therefore represents the actual new outlay.
     */

    const serverOutlay =
      Number(
        data.new_wager ??
        data.total_wager ??
        wagered
      );


    const extraCharge =
      Math.max(
        0,
        serverOutlay -
        wagered
      );


    balance -=
      extraCharge;


    balance +=
      Number(
        data.total_return || 0
      );


    gameState =
      data.state || {};


    pendingBets = {};


    saveBalance();

    saveState();


    if (
      $("returnMetric")
    ) {
      $("returnMetric")
        .textContent =
          fmt(
            data.total_return
          );
    }


    if (
      $("netMetric")
    ) {

      $("netMetric")
        .textContent =
          `${
            Number(data.net) > 0
              ? "+"
              : ""
          }${fmt(
            data.net
          )}`;
    }


    addHistory(
      data
    );


    renderCrapsBoard();


  } catch (error) {

    stopRollingAnimation();


    const diceResult =
      $("diceResult");


    if (
      diceResult
    ) {
      diceResult
        .classList
        .remove(
          "dice-result-shaking"
        );
    }


    /*
     * Only pending browser wagers were deducted before the request.
     * Existing persistent table wagers remain server state and must
     * not be refunded here.
     */

    balance +=
      wagered;


    pendingBets = {};


    saveBalance();


    console.error(
      error
    );


    } finally {
    stopRollingAnimation();

    busy = false;

    $("phaseLabel").textContent = "READY";

    refresh();
  }
}


/* ================================================================
   POINT DISPLAY
   ================================================================ */

function renderPoint() {

  const point =
    $("pointLabel");


  if (!point) {
    return;
  }


  point.textContent =
    gameState.point
      ? gameState.point
      : "OFF";
}


/* ================================================================
   RULES
   ================================================================ */

function renderRules() {

  if (
    $("rulesTitle")
  ) {
    $("rulesTitle")
      .textContent =
        "CRAPS RULES";
  }


  const rules = [

    "Pass Line wins on 7 or 11 during the come-out roll and loses on 2, 3 or 12.",

    "A roll of 4, 5, 6, 8, 9 or 10 establishes the table point.",

    "After a point is established, Pass Line wins when the point repeats and loses on 7.",

    "Don't Pass wins on 2 or 3 during the come-out roll and pushes on 12.",

    "Come and Don't Come wagers become available after the table point is established.",

    "Place, Buy, Lay and other persistent wagers can remain on the table between throws.",

    "Working status can be changed for supported persistent wagers.",

    "Persistent wagers may be taken down when permitted by the backend rules.",

    "Pass and Come odds pay true odds.",

    "Buy and Lay wagers may include vigorish.",

    "Field and proposition bets settle on a single throw.",

    "Hardways remain active until they win, lose, or are removed.",

  ];


  const columns = [
    [],
    [],
    [],
    [],
  ];


  rules.forEach(
    (
      rule,
      index
    ) => {

      columns[
        index % 4
      ].push(
        rule
      );
    }
  );


  if (
    $("rulesBox")
  ) {

    $("rulesBox")
      .innerHTML =
        columns
          .map(
            column => `
              <div>

                ${
                  column
                    .map(
                      rule => `
                        <div
                          style="
                            margin-bottom:
                              7px;
                          "
                        >
                          • ${rule}
                        </div>
                      `
                    )
                    .join("")
                }

              </div>
            `
          )
          .join("");
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

  gameState = {};

  history = [];


  localStorage.removeItem(
    BALANCE_KEY
  );

  localStorage.removeItem(
    STATE_KEY
  );

  localStorage.removeItem(
    HISTORY_KEY
  );


  saveBalance();

  saveState();

  saveHistory();


  renderCrapsBoard();


  if (
    $("currentRoll")
  ) {
    $("currentRoll")
      .textContent =
        "—";
  }


  if (
    $("returnMetric")
  ) {
    $("returnMetric")
      .textContent =
        "0";
  }


  if (
    $("netMetric")
  ) {
    $("netMetric")
      .textContent =
        "0";
  }


  renderResultDice(
    [
      1,
      1,
    ]
  );


  renderHistory();

  refresh();
}


/* ================================================================
   INITIALISE
   ================================================================ */

function init() {

  installCrapsStyles();


  if (
    $("diceCount")
  ) {
    $("diceCount")
      .textContent =
        "2";
  }


  saveBalance();

  saveState();


  renderCrapsBoard();

  renderChips();

  renderHistory();

  renderRules();


  if (
    $("clearBtn")
  ) {
    $("clearBtn")
      .onclick =
        clearBets;
  }


  if (
    $("rollBtn")
  ) {

    $("rollBtn")
      .onclick =
        rollDice;

    $("rollBtn")
      .innerHTML =
        "🎲 THROW";
  }


  if (
    $("resetBtn")
  ) {
    $("resetBtn")
      .onclick =
        resetCredits;
  }


  renderResultDice(
    [
      1,
      1,
    ]
  );


  refresh();
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