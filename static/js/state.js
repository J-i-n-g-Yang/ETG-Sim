/**
 * state.js — SSE subscription + polling fallback.
 *
 * Usage:
 *   import { StateManager } from "./state.js";
 *   const sm = new StateManager();
 *   sm.on("phase_change", (data) => { ... });
 *   sm.on("reveal",       (data) => { ... });
 *   sm.start();
 */

// Derive app root from this module's URL — works under any sub-path.
const _BASE = new URL(import.meta.url).pathname.replace(/\/static\/js\/state\.js$/, "");

export class StateManager extends EventTarget {
  constructor() {
    super();
    this._es        = null;
    this._pollTimer = null;
    this._connected = false;
  }

  start() {
    this._connectSSE();
  }

  stop() {
    if (this._es)        { this._es.close(); this._es = null; }
    if (this._pollTimer) { clearInterval(this._pollTimer); this._pollTimer = null; }
  }

  // ---------------------------------------------------------------- //
  // SSE                                                                //
  // ---------------------------------------------------------------- //

  _connectSSE() {
    if (this._es) this._es.close();
    this._es = new EventSource(_BASE + "/api/events");

    const events = ["state", "phase_change", "distribution_update", "reveal", "settled", "leaderboard_update", "event_reset"];
    events.forEach(name => {
      this._es.addEventListener(name, (e) => {
        const data = JSON.parse(e.data);
        this._connected = true;
        this._stopPolling();
        this._emit(name, data);
      });
    });

    this._es.onerror = () => {
      this._connected = false;
      this._es.close();
      this._startPolling();
      // Reconnect SSE after 3 s
      setTimeout(() => this._connectSSE(), 3000);
    };
  }

  // ---------------------------------------------------------------- //
  // Polling fallback                                                    //
  // ---------------------------------------------------------------- //

  _startPolling() {
    if (this._pollTimer) return;
    this._poll();
    this._pollTimer = setInterval(() => this._poll(), 1000);
  }

  _stopPolling() {
    if (this._pollTimer) { clearInterval(this._pollTimer); this._pollTimer = null; }
  }

  async _poll() {
    try {
      const r = await fetch(_BASE + "/api/state");
      if (!r.ok) return;
      const data = await r.json();
      this._emit("state", data);
    } catch (_) {}
  }

  // ---------------------------------------------------------------- //
  // Emit helper                                                         //
  // ---------------------------------------------------------------- //

  _emit(name, data) {
    this.dispatchEvent(Object.assign(new Event(name), { detail: data }));
  }

  on(name, fn) {
    this.addEventListener(name, (e) => fn(e.detail));
    return this;
  }
}
