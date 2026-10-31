# VOROA WINGO 24/7 AUTO-BOT & VIP HUD

Automated Martingale prediction & betting engine for WinGo 30S and 1M with Cyber VIP dashboard.

## Deployment on Voroa
- **Runtime**: Python 3.11
- **Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Port**: Automatic via `$PORT` (default 8000)

## Features
- Strict 4 to 6-minute wait interval on both wins and losses
- Titan Quant Ensemble engine (doublet 2-2, dragon ride, zig-zag)
- Configurable base bet (₹10) and take profit target (₹350)
- NO STOP LOSS mode
- Safe Simulator & Live Platform API dual modes
