import asyncio
import time
import random
import logging
from adapter import SimulatorAdapter, RaxiPlatformAdapter
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
        self.take_profit = 3500.0
        self.initial_balance = 1000.77
        self.current_balance = 1000.77
        
        # Strategy Wait Settings: 4 to 6 minutes on BOTH win & loss
        self.min_wait_seconds = 240 # 4 minutes
        self.max_wait_seconds = 360 # 6 minutes
        
        # State tracking
        self.status = "OFFLINE"  # OFFLINE, RUNNING, SLEEPING_INTERVAL, STOPPED_PROFIT, STOPPED_BUSTED
        self.countdown_remaining = 0
        self.active_period = ""
        self.next_bet_time = 0
        self.is_first_bet = True
        self.stats = {
            "total_bets": 0,
            "wins": 0,
            "losses": 0,
            "net_pnl": 0.0,
            "consecutive_losses": 0,
            "max_consecutive_losses": 0
        }
        self.logs = []
        self.adapter = SimulatorAdapter(game_mode="30S", initial_balance=1000.77)
        self._task = None

    def configure(self, mode="SIMULATOR", game_mode="30S", base_bet=10.0, take_profit=3500.0, initial_bal=1000.77, base_url="", auth_token=""):
        self.mode = mode
        self.game_mode = game_mode
        self.base_bet = float(base_bet)
        self.current_bet = float(base_bet)
        self.take_profit = float(take_profit) if take_profit else None
        self.initial_balance = float(initial_bal)
        self.current_balance = float(initial_bal)
        self.stats["consecutive_losses"] = 0
        self.is_first_bet = True
        
        if auth_token:
            self.adapter = RaxiPlatformAdapter(auth_token=auth_token, game_mode=game_mode)
            try:
                real_bal = self.adapter.get_balance()
                if real_bal > 0:
                    self.initial_balance = real_bal
                    self.current_balance = real_bal
            except Exception as e:
                logger.error(f"Error fetching initial balance: {e}")
        else:
            self.adapter = SimulatorAdapter(game_mode=game_mode, initial_balance=initial_bal)
            
        self.add_log(f"Config updated: Mode={self.mode}, BaseBet=₹{base_bet}, Target=₹{take_profit or 'NONE'}, LiveBalance=₹{self.current_balance:.2f}, StopLoss=NONE")

    def set_balance(self, new_bal: float):
        self.current_balance = float(new_bal)
        if hasattr(self.adapter, 'balance'):
            self.adapter.balance = float(new_bal)
        self.add_log(f"Balance updated across cloud server: ₹{self.current_balance:.2f}")

    def add_log(self, message, event_type="INFO", data=None):
        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        self.logs.insert(0, entry)
        if len(self.logs) > 150:
            self.logs.pop()
        logger.info(f"[{event_type}] {message}")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.status = "RUNNING"
        self.is_first_bet = True
        self._task = asyncio.create_task(self._run_loop())
        self.add_log("🚀 24/7 Cloud Bot started on Voroa Mumbai Server! First bet will place immediately.")

    def stop(self, reason="Manual Stop"):
        self.is_running = False
        self.status = "OFFLINE"
        if self._task:
            self._task.cancel()
        self.add_log(f"🛑 Bot paused: {reason}")

    async def _run_loop(self):
        try:
            while self.is_running:
                # 1. Check Take-Profit
                if self.take_profit and self.current_balance >= self.take_profit:
                    self.status = "STOPPED_PROFIT"
                    self.add_log(f"🎯 TARGET REACHED! Balance ₹{self.current_balance:.2f} >= Target ₹{self.take_profit:.2f}. Safely stopped with profit!", "TARGET_HIT")
                    self.is_running = False
                    break

                # 2. Check Insufficient Balance (No Stop-Loss, but cannot place bet if balance < bet)
                if self.current_balance < self.current_bet:
                    self.status = "STOPPED_BUSTED"
                    self.add_log(f"💥 BUSTED: Balance ₹{self.current_balance:.2f} is insufficient for next Martingale stake ₹{self.current_bet:.2f}.", "BUSTED")
                    self.is_running = False
                    break

                # 3. Handle Active Period & Betting Window
                timer = self.adapter.get_timer()
                rem = timer["remaining_seconds"]
                period = timer["period"]
                self.active_period = period

                # If first bet, we place immediately on this round
                self.status = "RUNNING"
                
                # If round has less than 5s, wait for next round to start
                if rem <= 5:
                    await asyncio.sleep(rem + 2)
                    timer = self.adapter.get_timer()
                    rem = timer["remaining_seconds"]
                    period = timer["period"]

                # 4. Run Quant Prediction Engine
                history = self.adapter.get_history(20)
                analysis = analyze_history(history)
                predicted_size = analysis["size"]
                pattern = analysis["pattern"]

                # 5. Place Bet
                bet_amount = self.current_bet
                self.add_log(f"🎯 Placed Bet ₹{bet_amount:.1f} on {predicted_size} for #{period} ({pattern})", "BET_PLACED")

                order = self.adapter.place_order(period, predicted_size, bet_amount)
                if not order.get("success", False):
                    self.add_log(f"❌ Bet failed: {order.get('msg', 'Error')}", "ERROR")
                    await asyncio.sleep(4)
                    continue

                self.stats["total_bets"] += 1
                self.is_first_bet = False

                # 6. Wait for round to resolve (wait remaining seconds + 3s buffer)
                wait_to_resolve = max(2, rem + 2)
                await asyncio.sleep(wait_to_resolve)

                # 7. Resolve outcome
                if self.mode == "SIMULATOR":
                    res = self.adapter.resolve_order(period, predicted_size, bet_amount)
                    won = res["won"]
                    pnl = res["pnl"]
                    draw_num = res["draw"]["number"]
                    actual_size = res["draw"]["size"]
                    self.current_balance = res["balance"]
                else:
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
                    try:
                        live_b = self.adapter.get_balance()
                        if live_b > 0:
                            self.current_balance = live_b
                        else:
                            self.current_balance += pnl
                    except:
                        self.current_balance += pnl

                self.stats["net_pnl"] += pnl

                # 8. Update Martingale Stake
                if won:
                    self.stats["wins"] += 1
                    self.stats["consecutive_losses"] = 0
                    self.current_bet = self.base_bet
                    self.add_log(f"✅ WIN on #{period}! ({predicted_size} ➔ {actual_size} ({draw_num})) | PnL: +₹{pnl:.2f} | Bal: ₹{self.current_balance:.2f} | Reset stake to ₹{self.base_bet:.1f}", "WIN")
                else:
                    self.stats["losses"] += 1
                    self.stats["consecutive_losses"] += 1
                    if self.stats["consecutive_losses"] > self.stats["max_consecutive_losses"]:
                        self.stats["max_consecutive_losses"] = self.stats["consecutive_losses"]
                    self.current_bet = bet_amount * 2.0
                    self.add_log(f"❌ LOSS on #{period}! ({predicted_size} ➔ {actual_size} ({draw_num})) | PnL: -₹{abs(pnl):.2f} | Bal: ₹{self.current_balance:.2f} | Next Martingale: ₹{self.current_bet:.1f}", "LOSS")

                # 9. Strict Rule: Wait 4 to 6 minutes (RNG interval) after BOTH WIN AND LOSS
                wait_sec = random.randint(self.min_wait_seconds, self.max_wait_seconds)
                self.status = "SLEEPING_INTERVAL"
                self.next_bet_time = time.time() + wait_sec
                self.add_log(f"⏳ Waiting {wait_sec / 60:.1f} mins ({wait_sec}s) before next bet...", "WAITING")

                # Count down smoothly on server
                while time.time() < self.next_bet_time and self.is_running:
                    self.countdown_remaining = max(0, int(self.next_bet_time - time.time()))
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            self.status = "OFFLINE"
            self.add_log("Bot worker stopped.", "INFO")
        except Exception as e:
            self.status = "ERROR"
            self.add_log(f"Worker error: {str(e)}", "ERROR")
            self.is_running = False

bot_instance = WinGoAutoBot()
