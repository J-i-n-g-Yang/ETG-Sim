/**
 * projector.js — read-only projector screen.
 * Handles all 3 game animations: baccarat cards, roulette wheel, sic bo dice.
 */

import { StateManager } from "./state.js";
import {
  renderAnimation, renderBaccarat, renderRoulette, renderSicbo,
  buildDieFaceHTML, buildHistDieHTML,
  SUIT_SYMBOLS, RED_SUITS, FACE_RANKS,
  WHEEL_SEQ, RED_SET, DOT_LAYOUTS,
} from "./animations.js";

const $ = (id) => document.getElementById(id);
const fmtN = (n) => Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });

let lastPhase   = null;
let lastGame    = null;
let lastOutcome = null;
let countdownTimer = null;
let animatedRoundId = null;

// ---------------------------------------------------------------- //
// Main state handler                                                 //
// ---------------------------------------------------------------- //
function onState(state) {
  renderHeader(state);
  handlePhaseTransition(state);
  refreshDistribution(state);
  lastPhase = state.phase;
  lastGame  = state.game;
}

function renderHeader(state) {
  const el = $("gameRoundLabel");
  if (el) {
    const g = state.game ? state.game.charAt(0).toUpperCase() + state.game.slice(1) : "—";
    el.textContent = state.round_number
      ? `${g} — Round ${state.round_number}/8`
      : g;
  }
  const ph = $("phaseLabel");
  if (ph) ph.textContent = state.phase;
}

function handlePhaseTransition(state) {
  if (state.phase === "BETTING_OPEN") {
    showSection("bettingSection");
    startCountdown(state.betting_ends_at, state.server_time);
  } else if (state.phase === "BETTING_LOCKED") {
    showSection("lockedSection");
    clearInterval(countdownTimer);
  } else if ((state.phase === "SETTLING" || state.phase === "SETTLED") && state.outcome) {
    showSection("resultSection");
    if (animatedRoundId !== state.round_id) {
      animatedRoundId = state.round_id;
      renderAnimation(state.game, state.outcome, $("animationArea"));
      updateHistory(state.game);
    }
  } else if (state.phase === "GAME_OVER") {
    showSection("gameOverSection");
    refreshLeaderboard();
  } else {
    showSection("idleSection");
  }
}

function showSection(id) {
  ["bettingSection","lockedSection","resultSection","gameOverSection","idleSection"]
    .forEach(s => { const el = $(s); if (el) el.style.display = s === id ? "" : "none"; });
}

// ---------------------------------------------------------------- //
// Countdown                                                          //
// ---------------------------------------------------------------- //
function startCountdown(endsAtStr, serverTimeStr) {
  clearInterval(countdownTimer);
  const endsAt   = new Date(endsAtStr).getTime();
  const serverMs = new Date(serverTimeStr).getTime();
  const offset   = serverMs - Date.now();

  function tick() {
    const rem = Math.max(0, endsAt - (Date.now() + offset));
    const el  = $("countdown");
    if (el) el.textContent = Math.ceil(rem / 1000);
    if (rem <= 0) clearInterval(countdownTimer);
  }
  tick();
  countdownTimer = setInterval(tick, 200);
}

// ---------------------------------------------------------------- //
// Distribution                                                       //
// ---------------------------------------------------------------- //
async function refreshDistribution(state) {
  if (!state.round_id || state.phase === "IDLE") return;
  try {
    const r = await fetch(`api/distribution?round_id=${state.round_id}`);
    const d = await r.json();
    d.game = state.game;   // inject game type so renderDistribution can pick the right layout
    renderDistribution(d);
  } catch (_) {}
}

// ---------------------------------------------------------------- //
// Distribution — chip stacks on a felt board                        //
// ---------------------------------------------------------------- //

// Same colour identity as player.js chip bar
const CHIP_COLORS_PROJ = {
  100:   ["#3a6080","#1e3d55"], 250:   ["#3a5a30","#1e3a14"],
  500:   ["#6a2a2a","#3a0e0e"], 1000:  ["#404070","#20204a"],
  2500:  ["#604010","#3a2008"], 5000:  ["#2a5a5a","#0e3a3a"],
  10000: ["#5a2060","#38103a"], 20000: ["#505020","#303010"],
};
function _projChipLabel(v) { return v >= 1000 ? (v/1000)+"K" : String(v); }
function _projChipStackHTML(total) {
  if (!total || total <= 0) return "";
  const order = [20000,10000,5000,2500,1000,500,250,100];
  const discs = []; let rem = total;
  for (const d of order) {
    while (rem >= d && discs.length < 5) { discs.push(d); rem -= d; }
    if (discs.length >= 5) break;
  }
  if (!discs.length) discs.push(100);
  const lbl = total >= 1000
    ? (total % 1000 === 0 ? (total/1000)+"K" : (total/1000).toFixed(1)+"K")
    : String(total);
  const chipHTML = discs.map(d => {
    const [c0,c1] = CHIP_COLORS_PROJ[d] || CHIP_COLORS_PROJ[100];
    const bg = `conic-gradient(${c0} 0deg 30deg,${c1} 30deg 60deg,${c0} 60deg 90deg,${c1} 90deg 120deg,${c0} 120deg 150deg,${c1} 150deg 180deg,${c0} 180deg 210deg,${c1} 210deg 240deg,${c0} 240deg 270deg,${c1} 270deg 300deg,${c0} 300deg 330deg,${c1} 330deg 360deg)`;
    return `<div class="proj-cstack-chip" style="background:${bg};border-color:${c0};">${_projChipLabel(d)}</div>`;
  }).join("");
  return `<div class="proj-chip-stack"><span class="proj-cstack-total">${lbl}</span>${chipHTML}</div>`;
}

function _dzone(wager, cls, label, totals) {
  const amt = totals[wager] || 0;
  return `<div class="proj-dzone ${cls}" data-wager="${wager}">${label}${_projChipStackHTML(amt)}</div>`;
}

// Roulette constants (same as player.js)
const PROJ_RED = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);

function renderDistribution(d) {
  const el = $("distribution");
  if (!el) return;
  const totals = d.totals || {};
  const total  = Object.values(totals).reduce((s,v) => s+v, 0);
  if (!d.game && !total) { el.innerHTML = "<div class='muted'>No bets yet</div>"; return; }

  const game = d.game || lastGame;

  let feltHTML = "";

  if (game === "baccarat") {
    feltHTML = `
      <div class="proj-dist-bacc-main">
        ${_dzone("player", "player", "Player<br><small style='font-size:10px;font-weight:400;opacity:0.8'>Pays 1:1</small>", totals)}
        ${_dzone("tie",    "tie",    "Tie<br><small style='font-size:10px;font-weight:400;opacity:0.8'>8:1</small>",    totals)}
        ${_dzone("banker", "banker", "Banker<br><small style='font-size:10px;font-weight:400;opacity:0.8'>Pays 1:1 (½ on 6)</small>", totals)}
      </div>
      <div class="proj-dist-bacc-dt">
        ${_dzone("dragon_tiger", "proj-dzone-dt", "Dragon Tiger<br><small style='font-size:10px;font-weight:400;opacity:0.7'>Player 7 beats Banker 6 — up to 100:1</small>", totals)}
      </div>
      <div class="proj-dist-bacc-sides">
        ${_dzone("small_dragon",   "dark", "Small Dragon<br><small style='color:var(--gold-soft)'>15:1</small>",   totals)}
        ${_dzone("big_dragon",     "dark", "Big Dragon<br><small style='color:var(--gold-soft)'>30:1</small>",     totals)}
        ${_dzone("tiger_tie",      "dark", "Tiger Tie<br><small style='color:var(--gold-soft)'>35:1</small>",      totals)}
        ${_dzone("small_tiger",    "dark", "Small Tiger<br><small style='color:var(--gold-soft)'>22:1</small>",    totals)}
        ${_dzone("big_tiger",      "dark", "Big Tiger<br><small style='color:var(--gold-soft)'>50:1</small>",      totals)}
        ${_dzone("immortal_dragon","dark", "Immortal Dragon<br><small style='color:var(--gold-soft)'>25:1</small>",totals)}
      </div>`;

  } else if (game === "sicbo") {
    // Full RWS layout: Top row + Totals + Combos + Singles + Odd/Even
    const PROJ_TOTAL_PAY = { 4:60,17:60, 5:30,16:30, 6:17,15:17, 7:12,14:12, 8:8,13:8, 9:6,12:6, 10:6,11:6 };

    // Helper: small die HTML for projector (reuse DOT_LAYOUTS)
    function _projDie(val) {
      const layouts = {1:[[1,1]],2:[[0,0],[2,2]],3:[[0,0],[1,1],[2,2]],4:[[0,0],[0,2],[2,0],[2,2]],5:[[0,0],[0,2],[1,1],[2,0],[2,2]],6:[[0,0],[0,2],[1,0],[1,2],[2,0],[2,2]]};
      const cells = Array(9).fill('<div></div>');
      (layouts[val]||[]).forEach(([r,c])=>{ cells[r*3+c]='<div style="width:4px;height:4px;border-radius:50%;background:#222;align-self:center;justify-self:center;"></div>'; });
      return `<div style="width:14px;height:14px;background:#f5f0e0;border-radius:3px;display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,1fr);padding:2px;flex-shrink:0;">${cells.join('')}</div>`;
    }

    // Top row sub-columns
    const triplesLeft  = [1,2,3].map(n=>`<div class="proj-dzone-sub" data-wager="triple_${n}">${_projDie(n)}${_projDie(n)}${_projDie(n)}${_projChipStackHTML(totals[`triple_${n}`]||0)}</div>`).join('');
    const triplesRight = [4,5,6].map(n=>`<div class="proj-dzone-sub" data-wager="triple_${n}">${_projDie(n)}${_projDie(n)}${_projDie(n)}${_projChipStackHTML(totals[`triple_${n}`]||0)}</div>`).join('');
    const doublesLeft  = [1,2,3].map(n=>`<div class="proj-dzone-sub" data-wager="double_${n}">${_projDie(n)}${_projDie(n)}${_projChipStackHTML(totals[`double_${n}`]||0)}</div>`).join('');
    const doublesRight = [4,5,6].map(n=>`<div class="proj-dzone-sub" data-wager="double_${n}">${_projDie(n)}${_projDie(n)}${_projChipStackHTML(totals[`double_${n}`]||0)}</div>`).join('');

    const totalCells = [4,5,6,7,8,9,10,11,12,13,14,15,16,17]
      .map(n => `<div class="proj-dzone dark" data-wager="total_${n}" style="flex-direction:column;gap:1px;">${n}<span style="font-size:8px;opacity:0.6">${PROJ_TOTAL_PAY[n]}:1</span>${_projChipStackHTML(totals[`total_${n}`]||0)}</div>`).join('');

    const comboCells = [];
    for (let a=1;a<=6;a++) for (let b=a+1;b<=6;b++) {
      comboCells.push(`<div class="proj-dzone dark" data-wager="combo_${a}${b}" style="flex-direction:column;gap:1px;">${_projDie(a)}${_projDie(b)}${_projChipStackHTML(totals[`combo_${a}${b}`]||0)}</div>`);
    }

    const singleLabels = ['ONE','TWO','THREE','FOUR','FIVE','SIX'];
    const singleCells = [1,2,3,4,5,6].map((n,i)=>
      `<div class="proj-dzone dark" data-wager="single_${n}" style="flex-direction:column;gap:1px;"><span style="font-size:8px">${singleLabels[i]}</span>${_projDie(n)}${_projChipStackHTML(totals[`single_${n}`]||0)}</div>`
    ).join('');

    feltHTML = `
      <div class="proj-dist-sicbo-top">
        <div class="proj-dzone gold-sm" data-wager="small" style="flex-direction:column;gap:2px;align-items:center;justify-content:center;">
          <span style="font-size:11px;font-weight:900;">SMALL</span>
          <span style="font-size:8px;opacity:0.7">4–10</span>
          ${_projChipStackHTML(totals['small']||0)}
        </div>
        <div class="proj-dzone-col">${doublesLeft}</div>
        <div class="proj-dzone-col">${triplesLeft}</div>
        <div class="proj-dzone gold" data-wager="any_triple" style="flex-direction:column;gap:2px;">
          <span style="font-size:10px;font-weight:900;line-height:1.2;">ANY<br>TRIPLE</span>
          <span style="font-size:8px;opacity:0.7">30:1</span>
          ${_projChipStackHTML(totals['any_triple']||0)}
        </div>
        <div class="proj-dzone-col">${triplesRight}</div>
        <div class="proj-dzone-col">${doublesRight}</div>
        <div class="proj-dzone gold-sm" data-wager="big" style="flex-direction:column;gap:2px;align-items:center;justify-content:center;">
          <span style="font-size:11px;font-weight:900;">BIG</span>
          <span style="font-size:8px;opacity:0.7">11–17</span>
          ${_projChipStackHTML(totals['big']||0)}
        </div>
      </div>
      <div class="proj-dist-sicbo-totals">${totalCells}</div>
      <div class="proj-dist-sicbo-combos" style="display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-bottom:5px;">${comboCells.join('')}</div>
      <div class="proj-dist-sicbo-singles" style="display:grid;grid-template-columns:repeat(6,1fr);gap:4px;margin-bottom:5px;">${singleCells}</div>
      <div class="proj-dist-sicbo-oddeven" style="display:grid;grid-template-columns:1fr 1fr;gap:5px;">
        ${_dzone("odd",  "dark", "ODD",  totals)}
        ${_dzone("even", "dark", "EVEN", totals)}
      </div>`;

  } else if (game === "roulette") {
    // Compact version of the player roulette grid — numbers + outside bets
    const numCol = (c) => 3 + 2*(c-1);
    const numEnd = numCol(12) + 1;
    const cells  = [];

    // Zero
    cells.push(`<div class="proj-dzone green-n" data-wager="straight_0" style="grid-column:1;grid-row:1/6;">0${_projChipStackHTML(totals["straight_0"]||0)}</div>`);

    for (let c=1; c<=12; c++) {
      const top=3*c, mid=3*c-1, bot=3*c-2, col=numCol(c);
      cells.push(`<div class="proj-dzone ${PROJ_RED.has(top)?"red-n":"black-n"}" data-wager="straight_${top}" style="grid-column:${col};grid-row:1;">${top}${_projChipStackHTML(totals[`straight_${top}`]||0)}</div>`);
      cells.push(`<div class="proj-dzone ${PROJ_RED.has(mid)?"red-n":"black-n"}" data-wager="straight_${mid}" style="grid-column:${col};grid-row:3;">${mid}${_projChipStackHTML(totals[`straight_${mid}`]||0)}</div>`);
      cells.push(`<div class="proj-dzone ${PROJ_RED.has(bot)?"red-n":"black-n"}" data-wager="straight_${bot}" style="grid-column:${col};grid-row:5;">${bot}${_projChipStackHTML(totals[`straight_${bot}`]||0)}</div>`);
    }
    // Dozens (boxed, same as the even-money row below)
    cells.push(`<div class="proj-dzone dark" data-wager="dozen1" style="grid-column:${numCol(1)}/${numCol(5)};grid-row:8;">1st 12${_projChipStackHTML(totals["dozen1"]||0)}</div>`);
    cells.push(`<div class="proj-dzone dark" data-wager="dozen2" style="grid-column:${numCol(5)}/${numCol(9)};grid-row:8;">2nd 12${_projChipStackHTML(totals["dozen2"]||0)}</div>`);
    cells.push(`<div class="proj-dzone dark" data-wager="dozen3" style="grid-column:${numCol(9)}/${numEnd};grid-row:8;">3rd 12${_projChipStackHTML(totals["dozen3"]||0)}</div>`);
    // Even money
    const emW = (numEnd - numCol(1)) / 6;
    [["low","1-18",""],["even","EVEN",""],["red","RED","red-spot"],["black","BLACK","black-spot"],["odd","ODD",""],["high","19-36",""]].forEach(([w,lbl,cls],i) => {
      const s = Math.round(numCol(1) + i*emW), e = i<5 ? Math.round(numCol(1)+(i+1)*emW) : numEnd;
      cells.push(`<div class="proj-dzone dark ${cls}" data-wager="${w}" style="grid-column:${s}/${e};grid-row:9;">${lbl}${_projChipStackHTML(totals[w]||0)}</div>`);
    });
    // Column bets (Col1/Col2/Col3) — same grid, same size as a number cell,
    // right next to the 34/35/36 column (rows 1/3/5 only — not spanning
    // down through the street/dozens/even-money rows).
    const colBetCol = numCol(12) + 2;
    cells.push(`<div class="proj-dzone dark" data-wager="col3" style="grid-column:${colBetCol};grid-row:1;">Col3<br><span style="opacity:0.7">2:1</span>${_projChipStackHTML(totals["col3"]||0)}</div>`);
    cells.push(`<div class="proj-dzone dark" data-wager="col2" style="grid-column:${colBetCol};grid-row:3;">Col2<br><span style="opacity:0.7">2:1</span>${_projChipStackHTML(totals["col2"]||0)}</div>`);
    cells.push(`<div class="proj-dzone dark" data-wager="col1" style="grid-column:${colBetCol};grid-row:5;">Col1<br><span style="opacity:0.7">2:1</span>${_projChipStackHTML(totals["col1"]||0)}</div>`);

    feltHTML = `<div class="proj-dist-roul-grid">${cells.join("")}</div>`;

  } else {
    // Fallback: simple list for unknown game types
    const items = Object.entries(totals).sort((a,b) => b[1]-a[1]);
    feltHTML = items.map(([k,v]) => `<div class="dark" style="margin:3px 0;padding:6px;">${k.replace(/_/g," ")} — ${v}${_projChipStackHTML(v)}</div>`).join("");
  }

  const grandTotal = total >= 1000
    ? (total % 1000 === 0 ? (total/1000)+"K" : (total/1000).toFixed(1)+"K") + " credits"
    : total + " credits";

  el.innerHTML = `
    <div class="proj-dist-felt">${feltHTML}</div>
    <div class="dist-total-bar">${d.bet_count} bets · ${grandTotal} wagered</div>`;
}

// ---------------------------------------------------------------- //
// History                                                             //
// ---------------------------------------------------------------- //
async function updateHistory(game) {
  try {
    const r = await fetch(`api/history?game=${game}&limit=20`);
    const d = await r.json();
    renderHistory(game, d.results);
  } catch (_) {}
}

function renderHistory(game, results) {
  const el = $("historyDisplay");
  if (!el) return;
  el.innerHTML = results.slice().reverse().map(r => {
    const o = r.outcome;
    if (game === "baccarat") {
      const cls = o.winner === "player" ? "blue" : o.winner === "banker" ? "red" : "green";
      return `<span class="hist-badge ${cls}">${o.winner[0].toUpperCase()}</span>`;
    }
    if (game === "roulette") {
      const cls = o.color;
      return `<span class="hist-badge ${cls}" title="${o.number}">${o.number}</span>`;
    }
    if (game === "sicbo") {
      return `<span class="hist-badge dice" title="Total ${o.total}">${o.dice.map(buildHistDieHTML).join("")}</span>`;
    }
    return "";
  }).join("");
}

// ---------------------------------------------------------------- //
// Leaderboard                                                        //
// ---------------------------------------------------------------- //
async function refreshLeaderboard() {
  try {
    const r = await fetch("api/leaderboard?top=10");
    const d = await r.json();
    const el = $("leaderboard");
    if (!el) return;
    el.innerHTML = d.players.map((p, i) =>
      `<div class="lb-row ${i === 0 ? "gold" : i === 1 ? "silver" : i === 2 ? "bronze" : ""}">
        <span class="lb-rank">${i + 1}</span>
        <span class="lb-name">${p.display_name}</span>
        <span class="lb-credits">${fmtN(p.credits)}</span>
      </div>`
    ).join("");
  } catch (_) {}
}

// Boot                                                                //
// ---------------------------------------------------------------- //
document.addEventListener("DOMContentLoaded", () => {
  const sm = new StateManager();
  sm.on("state",               onState);
  sm.on("phase_change",        onState);
  sm.on("settled",             onState);
  sm.on("reveal",              (d) => {
    fetch("api/state").then(r => r.json()).then(onState);
  });
  sm.on("distribution_update", (d) => { d.game = lastGame; renderDistribution(d); });
  sm.on("leaderboard_update",  refreshLeaderboard);
  sm.start();

  fetch("api/state").then(r => r.json()).then(onState).catch(() => {});
  setInterval(refreshLeaderboard, 5000);
});
