import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from bot import bot_instance

app = FastAPI(title="Voroa WinGo Auto-Bot")

class ConfigPayload(BaseModel):
    mode: str = "SIMULATOR"
    game_mode: str = "30S"
    base_bet: float = 10.0
    take_profit: Optional[float] = 350.0
    initial_bal: float = 300.0
    base_url: Optional[str] = ""
    auth_token: Optional[str] = ""

@app.get("/api/status")
async def get_status():
    return {
        "is_running": bot_instance.is_running,
        "status": bot_instance.status,
        "mode": bot_instance.mode,
        "game_mode": bot_instance.game_mode,
        "current_balance": bot_instance.current_balance,
        "base_bet": bot_instance.base_bet,
        "current_bet": bot_instance.current_bet,
        "take_profit": bot_instance.take_profit,
        "active_period": bot_instance.active_period,
        "countdown_remaining": bot_instance.countdown_remaining,
        "stats": bot_instance.stats,
        "logs": bot_instance.logs[:50]
    }

@app.post("/api/config")
async def update_config(cfg: ConfigPayload):
    if bot_instance.is_running:
        return JSONResponse(status_code=400, content={"error": "Stop the bot before updating configuration."})
    bot_instance.configure(
        mode=cfg.mode,
        game_mode=cfg.game_mode,
        base_bet=cfg.base_bet,
        take_profit=cfg.take_profit,
        initial_bal=cfg.initial_bal,
        base_url=cfg.base_url or "",
        auth_token=cfg.auth_token or ""
    )
    return {"success": True, "message": "Configuration updated successfully!"}

@app.post("/api/start")
async def start_bot():
    if bot_instance.is_running:
        return {"success": False, "message": "Bot is already running."}
    bot_instance.start()
    return {"success": True, "message": "Auto-bet bot started!"}

@app.post("/api/stop")
async def stop_bot():
    bot_instance.stop("User clicked stop")
    return {"success": True, "message": "Bot stopped."}

@app.get("/static_script.js", response_class=PlainTextResponse)
async def serve_user_script():
    with open("static_script.js", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
