// ==UserScript==
// @name         WinGo VIP Light Auto-Bot (4-6m Wait + Martingale)
// @namespace    https://wingoauto.getvoroa.com/
// @version      2.0
// @description  Light Theme WinGo 24/7 Auto-Bet Bot with 4-6 min randomized wait on Win & Loss
// @match        *://*/*
// @grant        none
// ==/UserScript==

(function() {
  'use strict';
  if (window.__WINGO_BOT_LOADED__) return;
  window.__WINGO_BOT_LOADED__ = true;

  // State
  let botActive = false;
  let baseBet = 10;
  let currentBet = 10;
  let takeProfit = 350;
  let balance = 0;
  let consecutiveLosses = 0;
  let sleepingUntil = 0;
  let sleepIntervalTimer = null;
  let recentDraws = [];
  let lastBetPeriod = null;
  let lastBetSide = null;

  // Audio cues
  const winAudio = new Audio('https://assets.mixkit.co/active_storage/sfx/2000/2000-preview.mp3');
  const betAudio = new Audio('https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3');

  // Inject Styles (Light Apple VIP Theme)
  const style = document.createElement('style');
  style.textContent = `
    #wingo-light-hud {
      position: fixed;
      top: 60px;
      right: 16px;
      width: 320px;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-radius: 24px;
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.15), 0 0 1px rgba(0, 0, 0, 0.1);
      z-index: 9999999;
      font-family: -apple-system, BlinkMacSystemFont, "Outfit", "Segoe UI", Roboto, sans-serif;
      color: #1e293b;
      overflow: hidden;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    #wingo-light-hud.minimized {
      width: 170px;
      height: 48px;
      overflow: hidden;
    }
    .wlh-header {
      background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: grab;
      user-select: none;
    }
    .wlh-title {
      font-weight: 800;
      font-size: 13px;
      letter-spacing: 0.5px;
      color: #0f172a;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .wlh-pill {
      font-size: 10px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 999px;
      background: #e2e8f0;
      color: #475569;
    }
    .wlh-pill.live {
      background: #dcfce7;
      color: #15803d;
    }
    .wlh-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .wlh-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .wlh-stat-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
    }
    .wlh-stat-label {
      font-size: 10px;
      text-transform: uppercase;
      font-weight: 700;
      color: #64748b;
      letter-spacing: 0.5px;
    }
    .wlh-stat-val {
      font-size: 17px;
      font-weight: 800;
      color: #0f172a;
      font-feature-settings: "tnum";
    }
    .wlh-stat-val.green { color: #16a34a; }
    .wlh-stat-val.purple { color: #7c3aed; }
    .wlh-row {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .wlh-label {
      font-size: 11px;
      font-weight: 700;
      color: #475569;
      display: flex;
      justify-content: space-between;
    }
    .wlh-input {
      background: #ffffff;
      border: 1.5px solid #cbd5e1;
      border-radius: 10px;
      padding: 8px 12px;
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      outline: none;
      transition: border 0.15s;
    }
    .wlh-input:focus {
      border-color: #6366f1;
    }
    .wlh-countdown-card {
      background: linear-gradient(135deg, #ede9fe 0%, #fae8ff 100%);
      border: 1px solid #ddd6fe;
      border-radius: 14px;
      padding: 10px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .wlh-clock {
      font-size: 18px;
      font-weight: 900;
      color: #6d28d9;
      font-family: monospace;
    }
    .wlh-btn {
      width: 100%;
      padding: 12px;
      border-radius: 14px;
      border: none;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.5px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s ease;
    }
    .wlh-btn-start {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: #ffffff;
      box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
    }
    .wlh-btn-start:hover {
      box-shadow: 0 10px 25px rgba(16, 185, 129, 0.45);
      transform: translateY(-1px);
    }
    .wlh-btn-stop {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: #ffffff;
      box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
    }
    .wlh-log {
      font-size: 10px;
      color: #64748b;
      font-family: monospace;
      max-height: 80px;
      overflow-y: auto;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 6px 8px;
    }
  `;
  document.head.appendChild(style);

  // Inject Widget DOM
  const widget = document.createElement('div');
  widget.id = 'wingo-light-hud';
  widget.innerHTML = `
    <div class="wlh-header" id="wlh-drag-handle">
      <div class="wlh-title">
        <span>⚡ WinGo Auto-Bot</span>
        <span class="wlh-pill" id="wlh-status-pill">OFFLINE</span>
      </div>
      <div style="cursor: pointer; font-size: 14px; font-weight: 800; color: #94a3b8;" id="wlh-toggle-btn">−</div>
    </div>
    <div class="wlh-body">
      <div class="wlh-grid">
        <div class="wlh-stat-box">
          <span class="wlh-stat-label">Live Balance</span>
          <span class="wlh-stat-val green" id="wlh-val-bal">₹0.00</span>
        </div>
        <div class="wlh-stat-box">
          <span class="wlh-stat-label">Next Stake</span>
          <span class="wlh-stat-val purple" id="wlh-val-bet">₹10.00</span>
        </div>
      </div>

      <div class="wlh-countdown-card" id="wlh-timer-card" style="display: none;">
        <div>
          <div style="font-size: 10px; font-weight: 800; color: #7c3aed; text-transform: uppercase;">4–6 Min Delay Active</div>
          <div style="font-size: 10px; color: #6b21a8;">Waiting next cycle</div>
        </div>
        <div class="wlh-clock" id="wlh-clock-text">04:30</div>
      </div>

      <div class="wlh-grid">
        <div class="wlh-row">
          <label class="wlh-label">Base Bet</label>
          <input type="number" class="wlh-input" id="wlh-in-base" value="10" step="5">
        </div>
        <div class="wlh-row">
          <label class="wlh-label">Take Profit</label>
          <input type="number" class="wlh-input" id="wlh-in-target" value="350" step="10">
        </div>
      </div>

      <div style="font-size: 10px; color: #94a3b8; font-weight: 600; text-align: center;">
        🛡️ Stop-Loss: <b>NONE</b> (Continuous Martingale) | 4–6m RNG Delay
      </div>

      <button class="wlh-btn wlh-btn-start" id="wlh-action-btn">▶ START AUTO-BET</button>
      <div class="wlh-log" id="wlh-log-box">Auto-Bot initialized. Ready.</div>
    </div>
  `;
  document.body.appendChild(widget);

  // Dragging support
  let isDragging = false, startX, startY, initLeft, initTop;
  const handle = document.getElementById('wlh-drag-handle');
  handle.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    const rect = widget.getBoundingClientRect();
    initLeft = rect.left;
    initTop = rect.top;
  });
  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    widget.style.left = `${initLeft + (e.clientX - startX)}px`;
    widget.style.top = `${initTop + (e.clientY - startY)}px`;
    widget.style.right = 'auto';
  });
  window.addEventListener('mouseup', () => isDragging = false);

  // Toggle minimize
  let isMin = false;
  document.getElementById('wlh-toggle-btn').addEventListener('click', () => {
    isMin = !isMin;
    widget.classList.toggle('minimized', isMin);
    document.getElementById('wlh-toggle-btn').innerText = isMin ? '+' : '−';
  });

  // Logging
  function log(msg) {
    const box = document.getElementById('wlh-log-box');
    const time = new Date().toLocaleTimeString();
    box.innerHTML = `[${time}] ${msg}<br>` + box.innerHTML;
  }

  // Auto-Detect Balance
  function detectBalance() {
    // 1. Check DOM for rupee or dollar amounts
    const walkers = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while (node = walkers.nextNode()) {
      const txt = node.textContent.trim();
      const match = txt.match(/[₹$]\s*([\d,]+\.?\d*)/);
      if (match && parseFloat(match[1].replace(/,/g, '')) > 0) {
        const val = parseFloat(match[1].replace(/,/g, ''));
        if (val !== balance) {
          balance = val;
          document.getElementById('wlh-val-bal').innerText = `₹${balance.toFixed(2)}`;
        }
        break;
      }
    }
  }
  setInterval(detectBalance, 2000);

  // Hook XHR & Fetch to intercept live game responses
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);
    try {
      const clone = response.clone();
      clone.json().then(data => {
        handleGameNetworkData(data);
      }).catch(() => {});
    } catch(e) {}
    return response;
  };

  function handleGameNetworkData(data) {
    if (!data) return;
    // Intercept balance
    if (data.data && (data.data.balance !== undefined || data.data.amount !== undefined)) {
      const b = parseFloat(data.data.balance || data.data.amount);
      if (!isNaN(b)) {
        balance = b;
        document.getElementById('wlh-val-bal').innerText = `₹${balance.toFixed(2)}`;
      }
    }
    // Intercept draw history
    if (data.data && Array.isArray(data.data.list)) {
      recentDraws = data.data.list.slice(0, 15);
      checkLastBetOutcome();
    }
  }

  // Prediction calculation (Titan Quant Logic)
  function getTitanPrediction() {
    if (!recentDraws || recentDraws.length < 3) return "BIG";
    const sizes = recentDraws.map(d => {
      const num = parseInt(d.number !== undefined ? d.number : d.openNumber);
      return num >= 5 ? "BIG" : "SMALL";
    }).reverse();

    const last = sizes[sizes.length - 1];
    // 2-2 Doublet
    if (sizes.length >= 4 && sizes[sizes.length - 1] === sizes[sizes.length - 2] && sizes[sizes.length - 3] === sizes[sizes.length - 4] && sizes[sizes.length - 1] !== sizes[sizes.length - 3]) {
      return last === "BIG" ? "SMALL" : "BIG";
    }
    // Dragon
    let streak = 1;
    for (let i = sizes.length - 2; i >= 0; i--) {
      if (sizes[i] === last) streak++; else break;
    }
    if (streak >= 3 && streak <= 5) return last;
    if (streak > 5) return last === "BIG" ? "SMALL" : "BIG";

    return last === "BIG" ? "SMALL" : "BIG";
  }

  // Check last bet outcome
  function checkLastBetOutcome() {
    if (!lastBetPeriod || !lastBetSide) return;
    const match = recentDraws.find(d => String(d.issueNumber || d.period) === String(lastBetPeriod));
    if (match) {
      const num = parseInt(match.number !== undefined ? match.number : match.openNumber);
      const actualSize = num >= 5 ? "BIG" : "SMALL";
      const won = (actualSize === lastBetSide);
      lastBetPeriod = null;
      lastBetSide = null;

      if (won) {
        log(`✅ WIN on #${match.issueNumber || ''} (${actualSize})! Resetting bet.`);
        consecutiveLosses = 0;
        currentBet = baseBet;
        try { winAudio.play(); } catch(e) {}
      } else {
        consecutiveLosses++;
        currentBet = currentBet * 2;
        log(`❌ LOSS on #${match.issueNumber || ''} (${actualSize})! Next 2x: ₹${currentBet}`);
      }
      document.getElementById('wlh-val-bet').innerText = `₹${currentBet.toFixed(2)}`;

      // Strict 4 to 6 Minute Wait
      start4to6MinWait();
    }
  }

  // 4 to 6 Min Delay Countdown
  function start4to6MinWait() {
    const waitSec = Math.floor(Math.random() * (360 - 240 + 1)) + 240; // 4 to 6 mins
    sleepingUntil = Date.now() + (waitSec * 1000);
    document.getElementById('wlh-timer-card').style.display = 'flex';
    log(`⏳ 4-6m rule: Sleeping ${Math.round(waitSec / 60)} mins...`);

    if (sleepIntervalTimer) clearInterval(sleepIntervalTimer);
    sleepIntervalTimer = setInterval(() => {
      const rem = Math.max(0, Math.floor((sleepingUntil - Date.now()) / 1000));
      const m = Math.floor(rem / 60);
      const s = rem % 60;
      document.getElementById('wlh-clock-text').innerText = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
      if (rem <= 0) {
        clearInterval(sleepIntervalTimer);
        document.getElementById('wlh-timer-card').style.display = 'none';
        log(`🔔 Delay finished. Resuming betting.`);
      }
    }, 1000);
  }

  // Click elements on page
  function clickButtonByText(regex) {
    const elements = Array.from(document.querySelectorAll('button, div, span, a'));
    for (const el of elements) {
      if (regex.test(el.innerText || '')) {
        el.click();
        return true;
      }
    }
    return false;
  }

  // Auto-Bet Tick
  async function runAutoBetTick() {
    if (!botActive) return;
    if (Date.now() < sleepingUntil) return;

    // Check Take Profit
    if (takeProfit && balance >= takeProfit) {
      log(`🎯 TARGET REACHED: ₹${balance.toFixed(2)} >= ₹${takeProfit}! Stopping.`);
      stopBot();
      return;
    }

    // Find countdown timer on screen
    let secondsLeft = 15;
    const timeEls = document.querySelectorAll('.van-count-down, [class*="time"], [class*="countdown"]');
    for (const el of timeEls) {
      const match = (el.innerText || '').match(/(\d+):(\d+)/);
      if (match) {
        secondsLeft = parseInt(match[1]) * 60 + parseInt(match[2]);
        break;
      }
    }

    // Bet between 14s and 6s
    if (secondsLeft > 14 || secondsLeft < 6) return;

    // Check period
    let period = "LIVE";
    const periodEls = document.querySelectorAll('[class*="issue"], [class*="period"]');
    for (const el of periodEls) {
      const pMatch = (el.innerText || '').match(/\d{5,}/);
      if (pMatch) { period = pMatch[0]; break; }
    }

    if (lastBetPeriod === period) return; // Already placed on this period

    const side = getTitanPrediction();
    log(`🎯 Betting ₹${currentBet} on ${side}...`);

    // Click Big or Small on page
    const clickedSide = clickButtonByText(new RegExp(`^\\s*${side}\\s*$`, 'i'));
    if (!clickedSide) {
      log(`Could not find ${side} button on screen.`);
      return;
    }

    await new Promise(r => setTimeout(r, 600));

    // Fill or select amount
    const input = document.querySelector('input[type="number"], .van-field__control');
    if (input) {
      input.value = currentBet;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    await new Promise(r => setTimeout(r, 600));

    // Click confirm / bet
    const confirmed = clickButtonByText(/(confirm|bet|buy|submit)/i);
    if (confirmed) {
      lastBetPeriod = period;
      lastBetSide = side;
      try { betAudio.play(); } catch(e) {}
      log(`✅ Placed ₹${currentBet} on ${side} for #${period}`);
    }
  }

  setInterval(runAutoBetTick, 2000);

  // UI Handlers
  const actionBtn = document.getElementById('wlh-action-btn');
  function startBot() {
    baseBet = parseFloat(document.getElementById('wlh-in-base').value) || 10;
    currentBet = baseBet;
    takeProfit = parseFloat(document.getElementById('wlh-in-target').value) || 350;
    botActive = true;
    actionBtn.className = 'wlh-btn wlh-btn-stop';
    actionBtn.innerText = '⏹ STOP AUTO-BET';
    const pill = document.getElementById('wlh-status-pill');
    pill.className = 'wlh-pill live';
    pill.innerText = 'RUNNING';
    log(`🚀 Auto-Bet started. Base: ₹${baseBet}, Target: ₹${takeProfit}`);
  }

  function stopBot() {
    botActive = false;
    actionBtn.className = 'wlh-btn wlh-btn-start';
    actionBtn.innerText = '▶ START AUTO-BET';
    const pill = document.getElementById('wlh-status-pill');
    pill.className = 'wlh-pill';
    pill.innerText = 'OFFLINE';
    log(`🛑 Auto-Bet stopped.`);
  }

  actionBtn.addEventListener('click', () => {
    if (botActive) stopBot(); else startBot();
  });

})();
