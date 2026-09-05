/**
 * animations.js — shared cinematic animations for baccarat, roulette, and sic bo.
 *
 * All three functions write directly into a container element you supply.
 * Nothing here knows about rounds, SSE, credits, or the server — it only
 * turns an `outcome` dict (same shape as game/*.py resolve()) into a
 * self-contained visual sequence.
 *
 * Exports:
 *   renderAnimation(game, outcome, container)  — top-level dispatcher
 *   renderBaccarat(area, outcome)
 *   renderRoulette(area, outcome)
 *   renderSicbo(area, outcome)
 */

// ---------------------------------------------------------------- //
// Shared constants                                                   //
// ---------------------------------------------------------------- //
export const SUIT_SYMBOLS = { S: "♠", H: "♥", D: "♦", C: "♣" };
export const RED_SUITS    = new Set(["H", "D"]);
export const FACE_RANKS   = new Set(["J", "Q", "K", "A"]);
export const WHEEL_SEQ    = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
export const RED_SET      = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);

export const DOT_LAYOUTS = {
  1: [[1,1]],
  2: [[0,0],[2,2]],
  3: [[0,0],[1,1],[2,2]],
  4: [[0,0],[0,2],[2,0],[2,2]],
  5: [[0,0],[0,2],[1,1],[2,0],[2,2]],
  6: [[0,0],[0,2],[1,0],[1,2],[2,0],[2,2]],
};

// ---------------------------------------------------------------- //
// Top-level dispatcher                                               //
// ---------------------------------------------------------------- //
/**
 * Run the appropriate animation for the given game into `container`.
 * If container is null/undefined the call is a no-op.
 * Returns a Promise that resolves once the animation has completed,
 * so callers can await it before showing the result breakdown.
 */
export function renderAnimation(game, outcome, container) {
  if (!container) return Promise.resolve();
  if (game === "baccarat") return renderBaccarat(container, outcome);
  if (game === "roulette") return renderRoulette(container, outcome);
  if (game === "sicbo")    return renderSicbo(container, outcome);
  return Promise.resolve();
}

// ---------------------------------------------------------------- //
// Baccarat                                                           //
// ---------------------------------------------------------------- //
function _cardVal(rank) {
  if (rank === "A") return 1;
  if (["10","J","Q","K"].includes(rank)) return 0;
  return parseInt(rank, 10);
}
function _handTotal(cards) {
  return cards.reduce((s, c) => s + _cardVal(c.rank), 0) % 10;
}

const DEAL_STAGGER_MS = 480;

function buildCard(c, delayMs) {
  const suitSym  = SUIT_SYMBOLS[c.suit] || c.suit;
  const isRed    = RED_SUITS.has(c.suit);
  const isFace   = FACE_RANKS.has(c.rank);
  const colorCls = isRed ? "red" : "black";
  const faceCls  = isFace ? " face-card" : "";
  const style    = delayMs != null ? ` style="animation-delay:${delayMs}ms"` : "";
  return `
    <div class="proj-card deal-in ${colorCls}${faceCls}"${style}>
      <div class="card-rank">${c.rank}</div>
      <div class="card-suit-lg">${suitSym}</div>
    </div>`;
}

export function renderBaccarat(area, o) {
  const pCards = o.player_cards || [];
  const bCards = o.banker_cards || [];

  const playerCards = pCards.map((c, i) => buildCard(c, (i * 2)     * DEAL_STAGGER_MS)).join("");
  const bankerCards = bCards.map((c, i) => buildCard(c, (i * 2 + 1) * DEAL_STAGGER_MS)).join("");

  const lastCardCount = pCards.length + bCards.length;
  const badgeDelay    = lastCardCount * DEAL_STAGGER_MS + 200;

  area.innerHTML = `
    <div class="proj-baccarat-table">
      <div class="proj-hand">
        <div class="proj-hand-label player">Player</div>
        <div class="proj-hand-score player" id="anim_scoreP">—</div>
        <div class="proj-cards">${playerCards}</div>
      </div>
      <div class="proj-winner-badge ${o.winner} deal-in" style="animation-delay:${badgeDelay}ms">${o.winner.toUpperCase()}</div>
      <div class="proj-hand">
        <div class="proj-hand-label banker">Banker</div>
        <div class="proj-hand-score banker" id="anim_scoreB">—</div>
        <div class="proj-cards">${bankerCards}</div>
      </div>
    </div>`;

  const CARD_LAND_MS = DEAL_STAGGER_MS + 420;
  const seq = [];
  const maxCards = Math.max(pCards.length, bCards.length);
  for (let i = 0; i < maxCards; i++) {
    if (i < pCards.length) seq.push({ hand: "p", idx: i });
    if (i < bCards.length) seq.push({ hand: "b", idx: i });
  }

  seq.forEach(({ hand, idx }, slotIdx) => {
    const delay = slotIdx * DEAL_STAGGER_MS + CARD_LAND_MS;
    setTimeout(() => {
      const cards = hand === "p" ? pCards.slice(0, idx + 1) : bCards.slice(0, idx + 1);
      const score = _handTotal(cards);
      const el = document.getElementById(hand === "p" ? "anim_scoreP" : "anim_scoreB");
      if (el) {
        el.textContent = score;
        el.classList.remove("score-bump");
        void el.offsetWidth;
        el.classList.add("score-bump");
      }
    }, delay);
  });

  const totalDuration = badgeDelay + 500;
  return new Promise(resolve => setTimeout(resolve, totalDuration));
}

// ---------------------------------------------------------------- //
// Roulette                                                           //
// ---------------------------------------------------------------- //
export function renderRoulette(area, o) {
  area.innerHTML = `
    <div class="proj-roulette-wrap">
      <canvas id="animWheelCanvas" width="280" height="280"></canvas>
      <div class="proj-roulette-result ${o.color}" id="animRouletteResult" style="visibility:hidden; opacity:0;">
        <div class="proj-roulette-number">${o.number}</div>
        <div class="proj-roulette-label">${o.color.toUpperCase()}</div>
        ${o.lightning && o.lightning[String(o.number)]
          ? `<div class="proj-lightning-badge">⚡ ${o.lightning[String(o.number)]}:1</div>`
          : ""}
      </div>
    </div>`;

  const canvas = document.getElementById("animWheelCanvas");
  return new Promise(resolve => {
    if (!canvas) { resolve(); return; }
    drawRouletteWheel(canvas, o.number, () => {
      const resultEl = document.getElementById("animRouletteResult");
      if (resultEl) {
        resultEl.style.transition = "opacity 0.4s ease";
        resultEl.style.visibility = "visible";
        requestAnimationFrame(() => { resultEl.style.opacity = "1"; });
      }
      setTimeout(resolve, 600);
    });
  });
}

export function drawRouletteWheel(canvas, winNumber, onSettled) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2, R = Math.min(W, H) / 2 - 8;
  const n = WHEEL_SEQ.length;
  const sliceA = (2 * Math.PI) / n;

  const winIdx       = WHEEL_SEQ.indexOf(winNumber);
  const baseAngle    = -Math.PI / 2;
  const totalWheelRot = 5 * 2 * Math.PI + (baseAngle - winIdx * sliceA);
  const duration     = 4200;
  const start        = performance.now();

  const ballTotalRot  = -(9 * 2 * Math.PI);
  const ballStartAngle = baseAngle - ballTotalRot;

  function easeOut(t) { return 1 - Math.pow(1 - t, 4); }

  function frame(now) {
    const t = Math.min((now - start) / duration, 1);
    const e = easeOut(t);
    const wheelAngle = e * totalWheelRot;
    const ballAngle  = ballStartAngle + e * ballTotalRot;
    const ballRadiusT = 0.96 - 0.10 * e;

    ctx.clearRect(0, 0, W, H);

    // Outer wooden rim
    const rimGrad = ctx.createRadialGradient(cx, cy, R, cx, cy, R + 8);
    rimGrad.addColorStop(0, "#5a3a10");
    rimGrad.addColorStop(0.5, "#8b6020");
    rimGrad.addColorStop(1, "#3a2208");
    ctx.beginPath();
    ctx.arc(cx, cy, R + 8, 0, Math.PI * 2);
    ctx.fillStyle = rimGrad;
    ctx.fill();

    // Pockets
    for (let i = 0; i < n; i++) {
      const num = WHEEL_SEQ[i];
      const sA = wheelAngle + i * sliceA - sliceA / 2;
      const eA = sA + sliceA;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, R, sA, eA);
      ctx.closePath();
      ctx.fillStyle = num === 0 ? "#1a6b35"
        : RED_SET.has(num) ? "#c01820" : "#111118";
      ctx.fill();
      ctx.strokeStyle = "#c9a84c";
      ctx.lineWidth = 0.8;
      ctx.stroke();

      const midA  = sA + sliceA / 2;
      const textR = R * 0.78;
      const tx    = cx + Math.cos(midA) * textR;
      const ty    = cy + Math.sin(midA) * textR;
      ctx.save();
      ctx.translate(tx, ty);
      ctx.rotate(midA + Math.PI / 2);
      ctx.fillStyle = "#fff";
      ctx.font = `bold ${Math.max(6, R * 0.068)}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(num), 0, 0);
      ctx.restore();
    }

    // Ball
    const ballR = R * ballRadiusT;
    const bx = cx + Math.cos(ballAngle) * ballR;
    const by = cy + Math.sin(ballAngle) * ballR;
    ctx.beginPath();
    ctx.arc(bx, by, R * 0.045, 0, Math.PI * 2);
    const bg = ctx.createRadialGradient(bx - 2, by - 2, 0, bx, by, R * 0.045);
    bg.addColorStop(0, "#fff");
    bg.addColorStop(1, "#bbb");
    ctx.fillStyle = bg;
    ctx.shadowColor = "rgba(255,255,255,0.5)";
    ctx.shadowBlur = 4;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Center hub
    const hg = ctx.createRadialGradient(cx - 4, cy - 4, 0, cx, cy, R * 0.15);
    hg.addColorStop(0, "#ece090");
    hg.addColorStop(0.6, "#c9a84c");
    hg.addColorStop(1, "#7a5a10");
    ctx.beginPath();
    ctx.arc(cx, cy, R * 0.15, 0, Math.PI * 2);
    ctx.fillStyle = hg;
    ctx.fill();
    ctx.strokeStyle = "#8b6020";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    if (t < 1) {
      requestAnimationFrame(frame);
    } else {
      // Gold highlight on winning pocket
      const wA = wheelAngle + winIdx * sliceA - sliceA / 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, R, wA, wA + sliceA);
      ctx.closePath();
      ctx.fillStyle = "rgba(240,208,80,0.45)";
      ctx.fill();
      if (typeof onSettled === "function") onSettled();
    }
  }

  requestAnimationFrame(frame);
}

// ---------------------------------------------------------------- //
// Sic Bo                                                              //
// ---------------------------------------------------------------- //
export function buildDieFaceHTML(value, dotClass = "die-dot") {
  const dots  = DOT_LAYOUTS[value] || [];
  const cells = Array(9).fill('<div></div>');
  dots.forEach(([r, c]) => {
    cells[r * 3 + c] = `<div class="${dotClass}"></div>`;
  });
  return cells.join('');
}

export function buildHistDieHTML(value) {
  return `<div class="hist-die">${buildDieFaceHTML(value, "hist-die-dot")}</div>`;
}

function _dieFaceGrid(val) {
  return `style="display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,1fr);"`;
}

export function renderSicbo(area, o) {
  const diceHTML = o.dice.map((d, i) =>
    `<div class="proj-die" style="animation-delay:${i * 120}ms" data-val="${d}">
      <div class="proj-die-inner" id="animDie${i}">
        <div class="die-face front"  ${_dieFaceGrid(d)}>${buildDieFaceHTML(d)}</div>
        <div class="die-face back"   ${_dieFaceGrid(d)}>${buildDieFaceHTML(7 - d)}</div>
        <div class="die-face right"  ${_dieFaceGrid(d)}>${buildDieFaceHTML(d === 6 ? 5 : d + 1)}</div>
        <div class="die-face left"   ${_dieFaceGrid(d)}>${buildDieFaceHTML(d === 1 ? 2 : d - 1)}</div>
        <div class="die-face top"    ${_dieFaceGrid(d)}>${buildDieFaceHTML(d <= 3 ? d + 2 : d - 2)}</div>
        <div class="die-face bottom" ${_dieFaceGrid(d)}>${buildDieFaceHTML(d <= 2 ? d + 3 : d - 3)}</div>
      </div>
    </div>`
  ).join("");

  area.innerHTML = `
    <div class="proj-sicbo-wrap">
      <div class="proj-dice">${diceHTML}</div>
      <div class="proj-sicbo-result" id="animSicboResult" style="opacity:0; transition:opacity 0.4s ease;">
        Total: <b>${o.total}</b>${o.triple ? " — <span class='triple-badge'>✦ TRIPLE! ✦</span>" : ""}
      </div>
    </div>`;

  const SPIN_DURATION = 1500;
  o.dice.forEach((val, i) => {
    setTimeout(() => animateDie(`animDie${i}`, val, i), i * 160);
  });

  // Fade in the total after all dice have landed
  const lastDieStart = (o.dice.length - 1) * 160;
  const totalDelay   = lastDieStart + SPIN_DURATION + 200;
  return new Promise(resolve => {
    setTimeout(() => {
      const resultEl = document.getElementById("animSicboResult");
      if (resultEl) resultEl.style.opacity = "1";
      setTimeout(resolve, 400);
    }, totalDelay);
  });
}

export function animateDie(id, targetFace, dieIndex = 0) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.transition = "none";
  el.style.transform  = "rotateX(0deg) rotateY(0deg)";
  void el.offsetHeight;
  const spinsX = 2 + (dieIndex % 3);
  const spinsY = 3 + ((dieIndex + 1) % 3);
  el.style.transition = "transform 1.5s cubic-bezier(0.2,0.8,0.3,1)";
  el.style.transform  = `rotateX(${spinsX * 360}deg) rotateY(${spinsY * 360}deg)`;
}

// ─────────────────────────────────────────────────────────────────────────────
// CRAPS  — two dice roll animation with event banner
// ─────────────────────────────────────────────────────────────────────────────
export function renderCraps(area, o) {
  const EVENT_LABELS = {
    natural:   { text: "NATURAL!",   cls: "craps-win"  },
    craps:     { text: "CRAPS!",     cls: "craps-lose" },
    point_set: { text: `POINT: ${o.total}`, cls: "craps-point" },
    point_hit: { text: "POINT HIT!", cls: "craps-win"  },
    seven_out: { text: "SEVEN OUT!", cls: "craps-lose" },
    rolling:   { text: `ROLLED: ${o.total}`, cls: "craps-neutral" },
  };
  const ev = EVENT_LABELS[o.event] || { text: `TOTAL: ${o.total}`, cls: "craps-neutral" };

  const diceHTML = o.dice.map((d, i) =>
    `<div class="proj-die" style="animation-delay:${i * 200}ms" data-val="${d}">
      <div class="proj-die-inner" id="animCrapsDie${i}">
        <div class="die-face front"  ${_dieFaceGrid(d)}>${buildDieFaceHTML(d)}</div>
        <div class="die-face back"   ${_dieFaceGrid(d)}>${buildDieFaceHTML(7 - d)}</div>
        <div class="die-face right"  ${_dieFaceGrid(d)}>${buildDieFaceHTML(d === 6 ? 5 : d + 1)}</div>
        <div class="die-face left"   ${_dieFaceGrid(d)}>${buildDieFaceHTML(d === 1 ? 2 : d - 1)}</div>
        <div class="die-face top"    ${_dieFaceGrid(d)}>${buildDieFaceHTML(d <= 3 ? d + 2 : d - 2)}</div>
        <div class="die-face bottom" ${_dieFaceGrid(d)}>${buildDieFaceHTML(d <= 2 ? d + 3 : d - 3)}</div>
      </div>
    </div>`
  ).join("");

  const pointBadge = o.point_out != null
    ? `<div class="craps-point-badge">Point locked: <b>${o.point_out}</b></div>`
    : (o.point_in != null && o.event === "point_hit")
      ? `<div class="craps-point-badge craps-point-cleared">Point cleared!</div>`
      : "";

  area.innerHTML = `
    <div class="proj-craps-wrap">
      <div class="proj-dice craps-dice">${diceHTML}</div>
      <div class="proj-craps-result ${ev.cls}" id="animCrapsResult" style="opacity:0;transition:opacity 0.4s ease;">
        <div class="proj-craps-total">${o.total}</div>
        <div class="proj-craps-event">${ev.text}</div>
        ${pointBadge}
      </div>
    </div>`;

  const SPIN_DURATION = 1600;
  o.dice.forEach((val, i) => {
    setTimeout(() => animateDie(`animCrapsDie${i}`, val, i), i * 200);
  });

  const totalDelay = (o.dice.length - 1) * 200 + SPIN_DURATION + 150;
  return new Promise(resolve => {
    setTimeout(() => {
      const el = document.getElementById("animCrapsResult");
      if (el) el.style.opacity = "1";
      setTimeout(resolve, 500);
    }, totalDelay);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// GREAT FORTUNE DICE — four dice roll animation
// ─────────────────────────────────────────────────────────────────────────────
export function renderGFD(area, o) {
  const diceHTML = o.dice.map((d, i) =>
    `<div class="proj-die" style="animation-delay:${i * 120}ms" data-val="${d}">
      <div class="proj-die-inner" id="animGFDDie${i}">
        <div class="die-face front"  ${_dieFaceGrid(d)}>${buildDieFaceHTML(d)}</div>
        <div class="die-face back"   ${_dieFaceGrid(d)}>${buildDieFaceHTML(7 - d)}</div>
        <div class="die-face right"  ${_dieFaceGrid(d)}>${buildDieFaceHTML(d === 6 ? 5 : d + 1)}</div>
        <div class="die-face left"   ${_dieFaceGrid(d)}>${buildDieFaceHTML(d === 1 ? 2 : d - 1)}</div>
        <div class="die-face top"    ${_dieFaceGrid(d)}>${buildDieFaceHTML(d <= 3 ? d + 2 : d - 2)}</div>
        <div class="die-face bottom" ${_dieFaceGrid(d)}>${buildDieFaceHTML(d <= 2 ? d + 3 : d - 3)}</div>
      </div>
    </div>`
  ).join("");

  // Special combos to call out
  const maxCount = Math.max(...Object.values(o.counts || {}));
  let callout = "";
  if (maxCount === 4) callout = `<span class="triple-badge">✦ QUADRUPLE! ✦</span>`;
  else if (maxCount >= 3) callout = `<span class="triple-badge">✦ TRIPLE! ✦</span>`;

  const sorted = [...o.dice].sort((a,b)=>a-b);
  if (!callout) {
    if ([1,2,3,4].join() === sorted.join() ||
        [2,3,4,5].join() === sorted.join() ||
        [3,4,5,6].join() === sorted.join()) {
      callout = `<span class="triple-badge">✦ STRAIGHT! ✦</span>`;
    }
  }

  area.innerHTML = `
    <div class="proj-sicbo-wrap">
      <div class="proj-dice" style="gap:12px;">${diceHTML}</div>
      <div class="proj-sicbo-result" id="animGFDResult" style="opacity:0;transition:opacity 0.4s ease;">
        Total: <b>${o.total}</b>${callout ? " — " + callout : ""}
      </div>
    </div>`;

  const SPIN_DURATION = 1500;
  o.dice.forEach((val, i) => {
    setTimeout(() => animateDie(`animGFDDie${i}`, val, i), i * 140);
  });

  const lastDieStart = (o.dice.length - 1) * 140;
  const totalDelay   = lastDieStart + SPIN_DURATION + 200;
  return new Promise(resolve => {
    setTimeout(() => {
      const el = document.getElementById("animGFDResult");
      if (el) el.style.opacity = "1";
      setTimeout(resolve, 400);
    }, totalDelay);
  });
}
