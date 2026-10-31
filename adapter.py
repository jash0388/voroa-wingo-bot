import time
import random
import requests
import hashlib
import json
import uuid
import logging

logger = logging.getLogger("adapter")

def sign_payload(data: dict) -> dict:
    """
    Raxi1 / WinGo cryptographic MD5 payload signer.
    """
    d = dict(data)
    d['language'] = 'en'
    d['random'] = uuid.uuid4().hex
    d.pop('signature', None)
    d.pop('timestamp', None)
    
    # Sort keys
    sorted_dict = {}
    for k in sorted(d.keys()):
        v = d[k]
        if v is not None and v != '' and k not in ['signature', 'track', 'xosoBettingData']:
            sorted_dict[k] = v
            
    # MD5 hash of JSON string without spaces
    json_str = json.dumps(sorted_dict, separators=(',', ':'))
    sig = hashlib.md5(json_str.encode()).hexdigest().upper()
    
    d['signature'] = sig
    d['timestamp'] = int(time.time())
    return d


class RaxiPlatformAdapter:
    """
    Direct production API connector for raxi1.com (api.raxiqaz.com) in Mumbai.
    """
    def __init__(self, auth_token: str, game_mode="30S"):
        self.base_url = "https://api.raxiqaz.com"
        self.auth_token = auth_token.strip()
        self.game_mode = game_mode
        self.type_id = 1 if game_mode == "30S" else 2
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}",
            "token": self.auth_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        })

    def get_timer(self):
        try:
            payload = sign_payload({"typeId": self.type_id})
            resp = self.session.post(f"{self.base_url}/api/webapi/GetGameIssue", json=payload, timeout=6)
            data = resp.json()
            if data.get("code") == 0:
                item = data.get("data", {})
                period = str(item.get("issueNumber", ""))
                end_time_str = item.get("endTime", "")
                
                # Calculate remaining seconds
                now = time.time()
                # Parse server time
                s_time = item.get("serviceTime", "")
                remaining = 15
                if end_time_str and s_time:
                    try:
                        from datetime import datetime
                        fmt = "%Y-%m-%d %H:%M:%S"
                        t_end = datetime.strptime(end_time_str, fmt).timestamp()
                        t_srv = datetime.strptime(s_time, fmt).timestamp()
                        remaining = max(1, int(t_end - t_srv))
                    except:
                        pass
                return {"period": period, "remaining_seconds": remaining, "lock_bet": remaining <= 5}
        except Exception as e:
            logger.error(f"Error fetching Raxi timer: {e}")
        return {"period": "UNKNOWN", "remaining_seconds": 15, "lock_bet": False}

    def get_history(self, limit=20):
        try:
            payload = sign_payload({"typeId": self.type_id, "pageSize": limit, "pageNo": 1})
            resp = self.session.post(f"{self.base_url}/api/webapi/GetWinTheLotteryResult", json=payload, timeout=6)
            data = resp.json()
            records = []
            if data.get("code") == 0:
                raw_list = data.get("data", {}).get("list", [])
                for r in reversed(raw_list):
                    period = str(r.get("issueNumber", ""))
                    num = int(r.get("number", r.get("openNumber", 0)))
                    size = "BIG" if num >= 5 else "SMALL"
                    records.append({"period": period, "number": num, "size": size})
            return records
        except Exception as e:
            logger.error(f"Error fetching Raxi history: {e}")
            return []

    def get_balance(self):
        try:
            payload = sign_payload({})
            resp = self.session.post(f"{self.base_url}/api/webapi/GetUserInfo", json=payload, timeout=6)
            data = resp.json()
            if data.get("code") == 0:
                bal = float(data.get("data", {}).get("userBalance", data.get("data", {}).get("amount", 0.0)))
                return round(bal, 2)
        except Exception as e:
            logger.error(f"Error fetching Raxi balance: {e}")
        return 1000.77

    def place_order(self, period, select_size, amount):
        try:
            # selectType: "big" or "small"
            sel = "big" if select_size.upper() == "BIG" else "small"
            payload = sign_payload({
                "typeId": self.type_id,
                "issuenumber": str(period),
                "amount": int(amount),
                "betCount": 1,
                "gameType": 2,
                "selectType": sel
            })
            resp = self.session.post(f"{self.base_url}/api/webapi/GameBetting", json=payload, timeout=8)
            data = resp.json()
            if data.get("code") == 0:
                return {"success": True, "period": period, "amount": amount, "size": select_size}
            else:
                return {"success": False, "msg": data.get("msg", "Bet rejected")}
        except Exception as e:
            return {"success": False, "msg": str(e)}


class SimulatorAdapter:
    def __init__(self, game_mode="30S", initial_balance=1000.77):
        self.game_mode = game_mode
        self.cycle_seconds = 30 if game_mode == "30S" else 60
        self.balance = float(initial_balance)
        self.history = []
        self._seed_initial_history()

    def _seed_initial_history(self):
        now = int(time.time())
        current_period = now // self.cycle_seconds
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
        return {"period": period, "remaining_seconds": int(remaining), "lock_bet": remaining <= 5}

    def get_history(self, limit=20):
        now = time.time()
        current_period = int(now // self.cycle_seconds)
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
            return {"success": False, "msg": f"Insufficient balance ₹{self.balance:.2f}"}
        self.balance -= amount
        return {"success": True, "period": period, "amount": amount, "size": select_size}

    def resolve_order(self, period, select_size, amount):
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
            self.balance += amount * 1.96
            return {"won": True, "pnl": round(amount * 0.96, 2), "draw": draw, "balance": self.get_balance()}
        else:
            return {"won": False, "pnl": round(-amount, 2), "draw": draw, "balance": self.get_balance()}
