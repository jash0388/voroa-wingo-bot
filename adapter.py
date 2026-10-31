import time
import random
import requests
import logging

logger = logging.getLogger("adapter")

class SimulatorAdapter:
    """
    Simulates real-time 30S or 1M draws for safe testing and verification.
    """
    def __init__(self, game_mode="30S", initial_balance=300.0):
        self.game_mode = game_mode
        self.cycle_seconds = 30 if game_mode == "30S" else 60
        self.balance = float(initial_balance)
        self.history = []
        self._seed_initial_history()

    def _seed_initial_history(self):
        current_time = int(time.time())
        current_period = current_time // self.cycle_seconds
        for i in range(20, 0, -1):
            p = str(current_period - i)
            num = random.randint(0, 9)
            size = "BIG" if num >= 5 else "SMALL"
            self.history.append({"period": p, "number": num, "size": size})

    def get_timer(self):
        now = time.time()
        elapsed = now % self.cycle_seconds
        remaining = self.cycle_seconds - elapsed
        period = str(int(now // self.cycle_seconds))
        return {
            "period": period,
            "remaining_seconds": int(remaining),
            "lock_bet": remaining <= 5
        }

    def get_history(self, limit=20):
        now = time.time()
        current_period = int(now // self.cycle_seconds)
        # Check if we need to resolve any past periods up to current_period - 1
        last_recorded = int(self.history[-1]["period"])
        for p in range(last_recorded + 1, current_period):
            num = random.randint(0, 9)
            size = "BIG" if num >= 5 else "SMALL"
            self.history.append({"period": str(p), "number": num, "size": size})
        return self.history[-limit:]

    def get_balance(self):
        return round(self.balance, 2)

    def place_order(self, period, select_size, amount):
        if self.balance < amount:
            return {"success": False, "msg": f"Insufficient balance ₹{self.balance:.2f} for ₹{amount:.2f}"}
        
        self.balance -= amount
        return {"success": True, "period": period, "amount": amount, "size": select_size}

    def resolve_order(self, period, select_size, amount):
        # Fetch the result for that period
        history = self.get_history(50)
        matching = [h for h in history if h["period"] == str(period)]
        if not matching:
            num = random.randint(0, 9)
            size = "BIG" if num >= 5 else "SMALL"
            matching = [{"period": str(period), "number": num, "size": size}]
            self.history.append(matching[0])

        draw = matching[0]
        won = (draw["size"] == select_size)
        if won:
            payout = amount * 1.96 # 1.96x return (96% profit)
            self.balance += payout
            return {"won": True, "pnl": round(amount * 0.96, 2), "draw": draw, "balance": self.get_balance()}
        else:
            return {"won": False, "pnl": round(-amount, 2), "draw": draw, "balance": self.get_balance()}


class LivePlatformAdapter:
    """
    Connects directly to the real gaming platform API endpoints using the user's authorization token.
    """
    def __init__(self, base_url, auth_token, game_mode="30S"):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.game_mode = game_mode
        self.type_id = 1 if game_mode == "30S" else 2
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "token": auth_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def get_timer(self):
        try:
            resp = self.session.post(f"{self.base_url}/api/web/winGo/getNoHandicap", json={"typeId": self.type_id}, timeout=6)
            data = resp.json()
            if data.get("code") == 0 or "data" in data:
                item = data.get("data", {})
                period = str(item.get("issueNumber", item.get("period", "")))
                remaining = int(item.get("remainingSeconds", item.get("seconds", 15)))
                return {"period": period, "remaining_seconds": remaining, "lock_bet": remaining <= 5}
        except Exception as e:
            logger.error(f"Error fetching timer: {e}")
        return {"period": "UNKNOWN", "remaining_seconds": 10, "lock_bet": True}

    def get_history(self, limit=20):
        try:
            resp = self.session.post(f"{self.base_url}/api/web/winGo/getHistory", json={"typeId": self.type_id, "pageSize": limit}, timeout=6)
            data = resp.json()
            records = []
            raw_list = data.get("data", {}).get("list", [])
            for r in reversed(raw_list):
                period = str(r.get("issueNumber", r.get("period", "")))
                num = int(r.get("number", r.get("openNumber", 0)))
                size = "BIG" if num >= 5 else "SMALL"
                records.append({"period": period, "number": num, "size": size})
            return records
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []

    def get_balance(self):
        try:
            resp = self.session.get(f"{self.base_url}/api/web/user/getBalance", timeout=6)
            data = resp.json()
            bal = float(data.get("data", {}).get("balance", data.get("data", {}).get("amount", 0.0)))
            return round(bal, 2)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0

    def place_order(self, period, select_size, amount):
        try:
            select_type = 1 if select_size == "BIG" else 2
            payload = {
                "typeId": self.type_id,
                "issueNumber": str(period),
                "selectType": select_type,
                "amount": int(amount),
                "multiplier": 1
            }
            resp = self.session.post(f"{self.base_url}/api/web/winGo/bet", json=payload, timeout=8)
            data = resp.json()
            if data.get("code") == 0 or data.get("msg") == "success":
                return {"success": True, "period": period, "amount": amount, "size": select_size}
            else:
                return {"success": False, "msg": data.get("msg", "Bet rejected")}
        except Exception as e:
            return {"success": False, "msg": str(e)}
