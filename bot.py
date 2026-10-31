import asyncio
import time
import random
import logging
from adapter import SimulatorAdapter, LivePlatformAdapter
from engine import analyze_history

logger = logging.getLogger("bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class WinGoAutoBot:
    def __init__(self):
        self.is_running = False
        self.mode = "SIMULATOR"  # or "LIVE"
        self.game_mode = "30S"   # or "1M"
        
        # User settings
        self.base_bet = 10.0
        self.current_bet = 10.0
        self.take_profit = 350.0  # None or float
        self.initial_balance = 300.0
        self.current_balance = 300.0
        
        # Strategy Wait Settings: 4 to 6 minutes on BOTH win & loss
        self.min_wait_seconds = 240 # 4 minutes
        self.max_wait_seconds = 360 # 6 minutes
        
        # State tracking
        self.status = "IDLE"  # IDLE, WAITING_BET_WINDOW, BET_SUBMITTED, SLEEPING_INTERVAL, STOPPED_PROFIT, STOPPED_BUSTED
        self.countdown_remaining = 0
        self.active_period = ""
        self.next_bet_time = 0
        self.stats = {
            "total_bets": 0,
            "wins": 0,
            "losses": 0,
            "net_pnl": 0.0,
            "consecutive_losses": 0,
            "max_consecutive_losses": 0
        }
        self.logs = []
        self.adapter = SimulatorAdapter(game_mode="30S", initial_balance=300.0)
        self._task = None

    def configure(self, mode="SIMULATOR", game_mode="30S", base_bet=10.0, take_profit=350.0, initial_bal=300.0, base_url="", auth_token=""):
        self.mode = mode
        self.game_mode = game_mode
        self.base_bet = float(base_bet)
        self.current_bet = float(base_bet)
        self.take_profit = float(take_profit) if take_profit else None
        self.initial_balance = float(initial_bal)
        self.current_balance = float(initial_bal)
        self.stats["consecutive_losses"] = 0
        
        if mode == "LIVE" and base_url and auth_token:
            self.adapter = LivePlatformAdapter(base_url, auth_token, game_mode=game_mode)
        else:
            self.adapter = SimulatorAdapter(game_mode=game_mode, initial_balance=initial_bal)
            
        self.add_log(f"Bot configured: Mode={mode}, Game={game_mode}, BaseBet=₹{base_bet}, TakeProfit=₹{take_profit or 'NONE'}, StopLoss=NONE")

    def add_log(self, message, event_type="INFO", data=None):
        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        self.logs.insert(0, entry)
        if len(self.logs) > 200:
            self.logs.pop()
        logger.info(f"[{event_type}] {message}")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.status = "RUNNING"
        self._task = asyncio.create_task(self._run_loop())
        self.add_log("🚀 Auto-Bet Bot started! Running continuous loop in background.")

    def stop(self, reason="Manual Stop"):
        self.is_running = False
        self.status = "STOPPED"
        if self._task:
            self._task.cancel()
        self.add_log(f"🛑 Bot halted: {reason}")

    async def _run_loop(self):
        try:
            while self.is_running:
                # 1. Update current balance
                bal = self.adapter.get_balance()
                self.current_balance = bal

                # 2. Check Take-Profit condition
                if self.take_profit and self.current_balance >= self.take_profit:
                    self.status = "STOPPED_PROFIT"
                    self.add_log(f"🎯 TARGET REACHED! Current Balance ₹{self.current_balance:.2f} >= Take-Profit ₹{self.take_profit:.2f}. Safely locked in profit!", "TARGET_HIT")
                    self.is_running = False
                    break

                # 3. Check if balance can cover current bet (No artificial stop loss, but physical zero check)
                if self.current_balance < self.current_bet:
                    self.status = "STOPPED_BUSTED"
                    self.add_log(f"💥 BUSTED! Balance ₹{self.current_balance:.2f} is insufficient for next Martingale bet ₹{self.current_bet:.2f}.", "BUSTED")
                    self.is_running = False
                    break

                # 4. Wait for the betting window of the active period
                self.status = "WAITING_BET_WINDOW"
                timer = self.adapter.get_timer()
                rem = timer["remaining_seconds"]
                period = timer["period"]
                self.active_period = period

                # If less than 6 seconds left, round is locking/ended: wait for new round
                if rem <= 6:
                    await asyncio.sleep(rem + 2)
                    continue

                # We want to place bet when timer is between 15s and 7s
                if rem > 12:
                    await asyncio.sleep(rem - 10)
                    timer = self.adapter.get_timer()
                    rem = timer["remaining_seconds"]
                    period = timer["period"]

                if rem <= 6:
                    await asyncio.sleep(rem + 2)
                    continue

                # 5. Run Quant Prediction Engine on historical draws
                history = self.adapter.get_history(20)
                analysis = analyze_history(history)
                predicted_size = analysis["size"]
                pattern = analysis["pattern"]

                # 6. Execute Bet
                self.status = "BET_SUBMITTED"
                bet_amount = self.current_bet
                self.add_log(f"🎯 Placed Bet ₹{bet_amount:.1f} on {predicted_size} for #{period} ({pattern})", "BET_PLACED")
                
                order = self.adapter.place_order(period, predicted_size, bet_amount)
                if not order.get("success", False):
                    self.add_log(f"❌ Bet failed: {order.get('msg', 'Error')}", "ERROR")
                    await asyncio.sleep(5)
                    continue

                self.stats["total_bets"] += 1

                # 7. Wait for round to resolve (remaining seconds + 3s buffer)
                wait_to_resolve = max(2, rem + 3)
                await asyncio.sleep(wait_to_resolve)

                # 8. Resolve the outcome
                if self.mode == "SIMULATOR":
                    res = self.adapter.resolve_order(period, predicted_size, bet_amount)
                    won = res["won"]
                    pnl = res["pnl"]
                    draw_num = res["draw"]["number"]
                    actual_size = res["draw"]["size"]
                else:
                    # In Live mode, fetch newest history record
                    await asyncio.sleep(2)
                    new_hist = self.adapter.get_history(5)
                    matching = [h for h in new_hist if str(h["period"]) == str(period)]
                    if matching:
                        actual_size = matching[0]["size"]
                        draw_num = matching[0]["number"]
                        won = (actual_size == predicted_size)
                    else:
                        won = False
                        actual_size = "?"
                        draw_num = "?"
                    pnl = bet_amount * 0.96 if won else -bet_amount

                # Update stats & Martingale state
                self.current_balance = self.adapter.get_balance()
                self.stats["net_pnl"] += pnl

                if won:
                    self.stats["wins"] += 1
                    self.stats["consecutive_losses"] = 0
                    self.current_bet = self.base_bet
                    outcome_str = f"WIN ✓ ({predicted_size} ➔ {actual_size} ({draw_num})) | PnL: +₹{pnl:.2f} | Bal: ₹{self.current_balance:.2f} | Bet reset to ₹{self.base_bet:.1f}"
                    self.add_log(outcome_str, "WIN", {"period": period, "pnl": pnl, "bal": self.current_balance})
                else:
                    self.stats["losses"] += 1
                    self.stats["consecutive_losses"] += 1
                    if self.stats["consecutive_losses"] > self.stats["max_consecutive_losses"]:
                        self.stats["max_consecutive_losses"] = self.stats["consecutive_losses"]
                    self.current_bet = bet_amount * 2.0
                    outcome_str = f"LOSS ✕ ({predicted_size} ➔ {actual_size} ({draw_num})) | PnL: -₹{abs(pnl):.2f} | Bal: ₹{self.current_balance:.2f} | Next Martingale: ₹{self.current_bet:.1f}"
                    self.add_log(outcome_str, "LOSS", {"period": period, "pnl": pnl, "bal": self.current_balance})

                # 9. Strict Rule: Wait 4 to 6 minutes (RNG interval) after BOTH WIN & LOSS
                wait_sec = random.randint(self.min_wait_seconds, self.max_wait_seconds)
                self.status = "SLEEPING_INTERVAL"
                self.next_bet_time = time.time() + wait_sec
                self.add_log(f"⏳ Waiting {wait_sec / 60:.1f} mins ({wait_sec}s) before placing next bet...", "WAITING")

                # Sleep in increments of 1s so UI timer updates smoothly and cancel is instant
                while time.time() < self.next_bet_time and self.is_running:
                    self.countdown_remaining = int(self.next_bet_time - time.time())
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            self.status = "STOPPED"
            self.add_log("Bot worker cancelled gracefully.", "INFO")
        except Exception as e:
            self.status = "ERROR"
            self.add_log(f"Fatal error in bot loop: {str(e)}", "ERROR")
            self.is_running = False

bot_instance = WinGoAutoBot()
