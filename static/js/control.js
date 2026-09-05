/**
 * control.js — operator control panel.
 */

import api from "./api.js";
import { StateManager } from "./state.js";

const $ = (id) => document.getElementById(id);
const fmtN = (n) => Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });

let pin = localStorage.getItem("etg_control_pin") || "";
let countdownTimer = null;

// ---------------------------------------------------------------- //
// PIN gate                                                          //
// ---------------------------------------------------------------- //
function checkPin() {
  pin = ($("pinInput")?.value || "").trim();
  if (!pin) { showMsg("bad", "Enter PIN first"); return false; }
  return true;
}

// ---------------------------------------------------------------- //
// Actions                                                            //
// ---------------------------------------------------------------- //
async function doAction(fn, label) {
  if (!checkPin()) return;
  try {
    const r = await fn(pin);
    showMsg("good", `${label}: OK`);
  } catch (err) {
    showMsg("bad", `${label} failed: ${err.message}`);
  }
}

// ---------------------------------------------------------------- //
// State rendering                                                    //
// ---------------------------------------------------------------- //
function renderState(state) {
  const el = $("stateDisplay");
  if (!el) return;

  const phase = state.phase || "IDLE";
  el.innerHTML = `
    <div class="ctrl-state-row">
      <span class="ctrl-label">Game</span>
      <span class="ctrl-val">${(state.game || "—").toUpperCase()}</span>
    </div>
    <div class="ctrl-state-row">
      <span class="ctrl-label">Round</span>
      <span class="ctrl-val">${state.round_number || "—"} / 8</span>
    </div>
    <div class="ctrl-state-row">
      <span class="ctrl-label">Phase</span>
      <span class="ctrl-val phase-${phase.toLowerCase()}">${phase}</span>
    </div>`;

  // Enable/disable buttons based on phase
  const btns = {
    "btnOpen":   ["IDLE", "SETTLED"],
    "btnLock":   ["BETTING_OPEN"],
    "btnReveal": ["BETTING_LOCKED"],
    "btnExtend": ["BETTING_OPEN"],
    "btnVoid":   ["BETTING_OPEN", "BETTING_LOCKED", "REVEALING", "SETTLED"],
  };
  Object.entries(btns).forEach(([id, validPhases]) => {
    const el = $(id);
    if (el) el.disabled = !validPhases.includes(phase);
  });

  // Countdown
  if (phase === "BETTING_OPEN" && state.betting_ends_at) {
    const endsAt = new Date(state.betting_ends_at).getTime();
    const srvMs = new Date(state.server_time).getTime();
    const offset = srvMs - Date.now();
    clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
      const rem = Math.max(0, endsAt - (Date.now() + offset));
      const el = $("ctrlCountdown");
      if (el) el.textContent = `${Math.ceil(rem / 1000)}s`;
      if (rem <= 0) clearInterval(countdownTimer);
    }, 200);
  } else {
    clearInterval(countdownTimer);
    const el = $("ctrlCountdown");
    if (el) el.textContent = "—";
  }
}

async function refreshStatus() {
  if (!pin) return;
  try {
    const r = await api.ctrl.status(pin);
    const el = $("liveStats");
    if (el) {
      el.innerHTML = `
        <div class="ctrl-stat"><b>${r.players}</b> players</div>
        <div class="ctrl-stat"><b>${r.bet_count}</b> bets — <b>${fmtN(r.total_wagered)}</b> credits wagered</div>
        <div class="ctrl-stat"><b>${r.sse_clients}</b> SSE clients</div>`;
    }
    renderState(r.state);
  } catch (_) {}
}

// ---------------------------------------------------------------- //
// Message bar                                                        //
// ---------------------------------------------------------------- //
function showMsg(type, msg) {
  const el = $("ctrlMsg");
  if (!el) return;
  el.className = `status ${type}`;
  el.textContent = msg;
  clearTimeout(showMsg._t);
  showMsg._t = setTimeout(() => { el.textContent = ""; el.className = "status"; }, 4000);
}

// ---------------------------------------------------------------- //
// Game toggle                                                       //
// ---------------------------------------------------------------- //
function updateToggleUI(game) {
  if (!game) return;
  ["baccarat", "roulette", "sicbo"].forEach(g => {
    const btn = $(`toggle${g.charAt(0).toUpperCase() + g.slice(1)}`);
    if (btn) btn.classList.toggle("active", g === game);
  });
}

async function setGame(game) {
  if (!checkPin()) return;
  const note = $("toggleNote");
  try {
    await api.ctrl.setGame(pin, game);
    updateToggleUI(game);
    if (note) {
      note.textContent = `✓ Switched to ${game.toUpperCase()} — takes effect next Open Betting.`;
      note.style.color = "#9be8ac";
    }
  } catch (err) {
    if (note) {
      note.textContent = `✗ ${err.message}`;
      note.style.color = "#ff9b9b";
    }
  }
  setTimeout(() => {
    if (note) { note.textContent = "Select a game — takes effect on the next Open Betting."; note.style.color = ""; }
  }, 3500);
}

// ---------------------------------------------------------------- //
// Boot                                                               //
// ---------------------------------------------------------------- //
document.addEventListener("DOMContentLoaded", () => {
  // Restore PIN
  const pinInput = $("pinInput");
  if (pinInput && pin) pinInput.value = pin;

  $("btnOpen")?.addEventListener("click",   () => doAction(api.ctrl.open,   "Open Betting"));
  $("btnLock")?.addEventListener("click",   () => doAction(api.ctrl.lock,   "Lock"));
  $("btnReveal")?.addEventListener("click", () => doAction(api.ctrl.reveal, "Reveal"));
  $("btnExtend")?.addEventListener("click", () => {
    const s = parseInt($("extendSecs")?.value || "10");
    doAction(p => api.ctrl.extend(p, s), "Extend Timer");
  });
  $("btnVoid")?.addEventListener("click", () => {
    if (!confirm("Void this round and refund all stakes?")) return;
    doAction(api.ctrl.void, "Void Round");
  });
  $("btnReset")?.addEventListener("click", () => {
    // NOTE: `!prompt(...) === "RESET"` (the old check) always evaluates to
    // false, because !prompt(...) is a boolean and can never strictly equal
    // the string "RESET" — so the `return` never ran and the reset always
    // proceeded, no matter what (or whether) the operator typed anything.
    if (prompt("Type RESET to confirm full event reset:") !== "RESET") return;
    doAction(api.ctrl.reset, "Reset Event");
  });

  // Game toggle
  ["baccarat", "roulette", "sicbo"].forEach(g => {
    const id  = `toggle${g.charAt(0).toUpperCase() + g.slice(1)}`;
    const btn = $(id);
    if (btn) btn.addEventListener("click", () => setGame(g));
  });

  pinInput?.addEventListener("change", () => {
    pin = pinInput.value.trim();
    localStorage.setItem("etg_control_pin", pin);
    refreshStatus();
  });

  // SSE — also update toggle when state changes
  const sm = new StateManager();
  sm.on("state",        (s) => { renderState(s); updateToggleUI(s.game); });
  sm.on("phase_change", (s) => { renderState(s); updateToggleUI(s.game); });
  sm.on("settled",      (s) => { renderState(s); updateToggleUI(s.game); });
  sm.start();

  refreshStatus();
  setInterval(refreshStatus, 3000);
});
