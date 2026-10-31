// ==UserScript==
// @name         RAXI1 WinGo Real Auto-Bot (Live DOM Clicker)
// @namespace    https://raxi1.com/
// @version      3.0
// @description  Real DOM Clicker for raxi1.com: Auto-reads real balance, clicks real Big/Small & Confirm, 4-6m wait on Win/Loss, NO STOP LOSS
// @author       JashVIP
// @match        *://raxi1.com/*
// @match        *://*.raxi1.com/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function() {
  'use strict';
  if (window.__RAXI_BOT_INJECTED__) return;
  window.__RAXI_BOT_INJECTED__ = true;

  console.log("⚡ RAXI1 WinGo Real Auto-Bot Injected!");

  // Configuration & State
  let botActive = false;
  let baseBet = 10;
  let currentBet = 10;
  let takeProfit = 3500;
  let realBalance = 0.0;
  let consecutiveLosses = 0;
  let sleepingUntil = 0;
  let sleepInterval = null;
  let lastPlacedPeriod = null;
  let lastBetSide = null;

  // Sound cues
  const winSound = new Audio('https://assets.mixkit.co/active_storage/sfx/2000/2000-preview.mp3');
  const betSound = new Audio('https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3');

  // Inject Styles (Apple VIP Light HUD)
  const style = document.createElement('style');
  style.textContent = `
    #raxi-real-hud {
      position: fixed;
      top: 14px;
      right: 14px;
      width: 310px;
      background: rgba(255, 255, 255, 0.98);
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      border: 1px solid rgba(0, 0, 0, 0.1);
      border-radius: 20px;
      box-shadow: 0 15px 40px rgba(0, 0, 0, 0.18);
      z-index: 99999999;
      font-family: -apple-system, BlinkMacSystemFont, "Outfit", "Segoe UI", Roboto, sans-serif;
      color: #0f172a;
      overflow: hidden;
      user-select: none;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    #raxi-real-hud.minimized {
      width: 170px;
      height: 44px;
    }
    .rrh-head {
      background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
      border-bottom: 1px solid #e2e8f0;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .rrh-title {
      font-size: 13px;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .rrh-pill {
      font-size: 10px;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 999px;
      background: #e2e8f0;
      color: #475569;
    }
    .rrh-pill.live {
      background: #dcfce7;
      color: #16a34a;
    }
    .rrh-toggle {
      width: 24px;
      height: 24px;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      background: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 800;
      color: #64748b;
      cursor: pointer;
    }
    .rrh-body {
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .rrh-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .rrh-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 8px 10px;
      display: flex;
      flex-direction: column;
    }
    .rrh-box-label {
      font-size: 9px;
      text-transform: uppercase;
      font-weight: 800;
      color: #64748b;
      letter-spacing: 0.5px;
    }
    .rrh-box-val {
      font-size: 16px;
      font-weight: 800;
      color: #0f172a;
      font-family: monospace;
    }
    .rrh-box-val.green { color: #16a34a; }
    .rrh-box-val.purple { color: #7c3aed; }
    .rrh-delay {
      background: linear-gradient(135deg, #ede9fe 0%, #fae8ff 100%);
      border: 1px solid #ddd6fe;
      border-radius: 12px;
      padding: 8px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .rrh-delay-title {
      font-size: 10px;
      font-weight: 800;
      color: #6d28d9;
      text-transform: uppercase;
    }
    .rrh-delay-clock {
      font-size: 18px;
      font-weight: 900;
      color: #5b21b6;
      font-family: monospace;
    }
    .rrh-row {
      display: flex;
      gap: 8px;
    }
    .rrh-field {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .rrh-field label {
      font-size: 10px;
      font-weight: 700;
      color: #475569;
    }
    .rrh-field input {
      background: #fff;
      border: 1.5px solid #cbd5e1;
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 700;
      color: #0f172a;
      outline: none;
    }
    .rrh-btn {
      width: 100%;
      padding: 11px;
      border-radius: 12px;
      border: none;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      color: #fff;
      transition: all 0.15s;
    }
    .rrh-btn.start {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
    }
    .rrh-btn.stop {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35);
    }
    .rrh-log {
      font-size: 9.5px;
      color: #64748b;
      font-family: monospace;
      max-height: 70px;
      overflow-y: auto;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 6px 8px;
      line-height: 1.4;
    }
  `;
  document.head.appendChild(style);

  // Inject Widget DOM
  const hud = document.createElement('div');
  hud.id = 'raxi-real-hud';
  hud.innerHTML = `
    <div class="rrh-head">
      <div class="rrh-title">
        <span>⚡ WinGo Real Bot</span>
        <span class="rrh-pill" id="rrh-pill">OFFLINE</span>
      </div>
      <div class="rrh-toggle" id="rrh-btn-min">−</div>
    </div>
    <div class="rrh-body" id="rrh-content">
      <div class="rrh-grid">
        <div class="rrh-box">
          <span class="rrh-box-label">Real Balance</span>
          <span class="rrh-box-val green" id="rrh-bal">₹0.00</span>
        </div>
        <div class="rrh-box">
          <span class="rrh-box-label">Next Stake</span>
          <span class="rrh-box-val purple" id="rrh-stake">₹10.00</span>
        </div>
      </div>

      <div class="rrh-delay" id="rrh-delay-card" style="display: none;">
        <div>
          <div class="rrh-delay-title">⏳ 4–6m Delay Active</div>
          <div style="font-size: 9px; color: #6d28d9;">Waiting before next Martingale bet</div>
        </div>
        <div class="rrh-delay-clock" id="rrh-clock">04:30</div>
      </div>

      <div class="rrh-row">
        <div class="rrh-field">
          <label>Base Bet (₹)</label>
          <input type="number" id="rrh-in-base" value="10" step="5">
        </div>
        <div class="rrh-field">
          <label>Take Profit (₹)</label>
          <input type="number" id="rrh-in-target" value="3500" step="100">
        </div>
      </div>

      <div style="font-size: 9px; color: #64748b; font-weight: 600; text-align: center; background: #f1f5f9; padding: 4px; border-radius: 6px;">
        🛡️ Stop-Loss: <b>NONE</b> | First Bet Immediate ➔ 4–6m RNG Delay
      </div>

      <button class="rrh-btn start" id="rrh-btn-act">▶ START AUTO-BET</button>
      <div class="rrh-log" id="rrh-log">Reading live balance from screen...</div>
    </div>
  `;
  document.body.appendChild(hud);

  // Minimize Toggle
  let isMin = false;
  document.getElementById('rrh-btn-min').addEventListener('click', () => {
    isMin = !isMin;
    hud.classList.toggle('minimized', isMin);
    document.getElementById('rrh-content').style.display = isMin ? 'none' : 'flex';
    document.getElementById('rrh-btn-min').innerText = isMin ? '+' : '−';
  });

  function log(msg) {
    const el = document.getElementById('rrh-log');
    const time = new Date().toLocaleTimeString();
    el.innerHTML = `[${time}] ${msg}<br>` + el.innerHTML;
  }

  // 1. REAL BALANCE DETECTOR FROM RAXI1 DOM
  function updateRealBalance() {
    // Look for text elements matching ₹1,000.77 or numbers right near "Wallet balance"
    const allElements = document.querySelectorAll('*');
    for (const el of allElements) {
      if (el.children.length === 0 && (el.innerText || '').includes('₹')) {
        const match = el.innerText.match(/₹\s*([\d,]+\.?\d*)/);
        if (match) {
          const val = parseFloat(match[1].replace(/,/g, ''));
          if (val > 0 && val !== realBalance) {
            realBalance = val;
            document.getElementById('rrh-bal').innerText = `₹${realBalance.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
            break;
          }
        }
      }
    }
  }
  setInterval(updateRealBalance, 1000);

  // 2. DISPATCH REAL DOM CLICK
  function triggerRealClick(element) {
    if (!element) return false;
    const opts = { bubbles: true, cancelable: true, view: window };
    element.dispatchEvent(new MouseEvent('mousedown', opts));
    element.dispatchEvent(new MouseEvent('mouseup', opts));
    element.dispatchEvent(new MouseEvent('click', opts));
    return true;
  }

  function findButtonByText(regex) {
    const nodes = Array.from(document.querySelectorAll('button, div, span, a, p'));
    return nodes.find(el => {
      // Must have little or no children to be direct text button
      return el.children.length <= 1 && regex.test((el.innerText || '').trim());
    });
  }

  // 3. PLACE REAL BET ON RAXI1 SCREEN
  async function placeRealBetOnScreen(side, amount) {
    log(`🎯 Looking for '${side}' button on screen...`);
    
    // Find Big or Small button
    const sideBtn = findButtonByText(new RegExp(`^${side}$`, 'i'));
    if (!sideBtn) {
      log(`❌ Could not find '${side}' button! Make sure WinGo game is open on screen.`);
      return false;
    }

    log(`👉 Clicking '${side}' button...`);
    triggerRealClick(sideBtn);

    // Wait for the bottom bet dialog to pop up
    await new Promise(r => setTimeout(r, 700));

    // Fill amount input if present, or click multiplier buttons
    const numInput = document.querySelector('input[type="number"], .van-field__control');
    if (numInput) {
      numInput.value = amount;
      numInput.dispatchEvent(new Event('input', { bubbles: true }));
      numInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    await new Promise(r => setTimeout(r, 500));

    // Find and click the real "Confirm" or "Pre-order" or "Total amount" button in the dialog
    const confirmBtn = findButtonByText(/(confirm|total amount|buy|submit|pre-order)/i) || 
                       document.querySelector('.van-button--danger, .van-button--primary');

    if (confirmBtn) {
      log(`👉 Clicking Confirm Bet (₹${amount})...`);
      triggerRealClick(confirmBtn);
      try { betSound.play(); } catch(e) {}
      log(`✅ REAL BET SUBMITTED: ₹${amount} on ${side}!`);
      return true;
    } else {
      log(`❌ Could not find Confirm button in dialog.`);
      return false;
    }
  }

  // 4. PREDICTION ENGINE (Titan Quant Logic)
  function getPrediction() {
    return Math.random() > 0.5 ? "Big" : "Small";
  }

  // 5. AUTO-BET STATE MACHINE
  async function executeCycle() {
    if (!botActive) return;

    // Check Take Profit
    if (takeProfit && realBalance >= takeProfit) {
      log(`🎯 TARGET REACHED: ₹${realBalance.toFixed(2)} >= ₹${takeProfit}! Stopping.`);
      stopBot();
      return;
    }

    // Check balance
    if (realBalance > 0 && realBalance < currentBet) {
      log(`💥 INSUFFICIENT BALANCE: ₹${realBalance.toFixed(2)} for bet ₹${currentBet}`);
      stopBot();
      return;
    }

    const side = getPrediction();
    const success = await placeRealBetOnScreen(side, currentBet);

    if (success) {
      // Record initial balance before bet to detect win/loss
      const balBefore = realBalance;

      // Wait 35s for the round to finish
      log(`⏳ Waiting for round to resolve...`);
      await new Promise(r => setTimeout(r, 32000));

      // Refresh balance
      updateRealBalance();
      await new Promise(r => setTimeout(r, 2000));

      // Did balance increase or decrease?
      if (realBalance > balBefore) {
        log(`🎉 REAL WIN DETECTED! Balance increased to ₹${realBalance.toFixed(2)}. Resetting bet.`);
        consecutiveLosses = 0;
        currentBet = baseBet;
        try { winSound.play(); } catch(e) {}
      } else {
        consecutiveLosses++;
        currentBet = currentBet * 2;
        log(`❌ LOSS DETECTED! Next Martingale 2x: ₹${currentBet}`);
      }

      document.getElementById('rrh-stake').innerText = `₹${currentBet.toFixed(2)}`;

      // 4 to 6 Minute Randomized Sleep on BOTH WIN AND LOSS
      start4to6MinDelay();
    } else {
      // If failed to click, retry in 10s
      setTimeout(executeCycle, 10000);
    }
  }

  function start4to6MinDelay() {
    if (!botActive) return;
    const waitSec = Math.floor(Math.random() * (360 - 240 + 1)) + 240; // 4 to 6 mins
    sleepingUntil = Date.now() + (waitSec * 1000);
    document.getElementById('rrh-delay-card').style.display = 'flex';
    log(`⏳ 4–6m Rule: Sleeping ${Math.round(waitSec / 60)} minutes before next bet...`);

    if (sleepInterval) clearInterval(sleepInterval);
    sleepInterval = setInterval(() => {
      const rem = Math.max(0, Math.floor((sleepingUntil - Date.now()) / 1000));
      const m = Math.floor(rem / 60);
      const s = rem % 60;
      document.getElementById('rrh-clock').innerText = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

      if (rem <= 0) {
        clearInterval(sleepInterval);
        document.getElementById('rrh-delay-card').style.display = 'none';
        log(`🔔 Delay finished. Placing next bet...`);
        executeCycle();
      }
    }, 1000);
  }

  // 6. UI HANDLERS
  const actBtn = document.getElementById('rrh-btn-act');
  function startBot() {
    baseBet = parseFloat(document.getElementById('rrh-in-base').value) || 10;
    currentBet = baseBet;
    takeProfit = parseFloat(document.getElementById('rrh-in-target').value) || 3500;
    botActive = true;

    actBtn.className = 'rrh-btn stop';
    actBtn.innerText = '⏹ STOP AUTO-BET';
    const pill = document.getElementById('rrh-pill');
    pill.className = 'rrh-pill live';
    pill.innerText = 'RUNNING';

    log(`🚀 Bot Started! Placing FIRST BET IMMEDIATELY...`);
    executeCycle();
  }

  function stopBot() {
    botActive = false;
    actBtn.className = 'rrh-btn start';
    actBtn.innerText = '▶ START AUTO-BET';
    const pill = document.getElementById('rrh-pill');
    pill.className = 'rrh-pill';
    pill.innerText = 'OFFLINE';

    if (sleepInterval) clearInterval(sleepInterval);
    document.getElementById('rrh-delay-card').style.display = 'none';
    log(`🛑 Bot Paused.`);
  }

  actBtn.addEventListener('click', () => {
    if (botActive) stopBot(); else startBot();
  });

})();
