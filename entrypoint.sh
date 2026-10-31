#!/bin/bash
set -e

PORT=${PORT:-8000}
RESOLUTION=${RESOLUTION:-"1280x800"}

echo "🚀 Starting Cloud Chrome on Voroa Server (Port: ${PORT}, Resolution: ${RESOLUTION})..."

# 1. Start Xvfb (Virtual Frame Buffer)
echo "Starting Xvfb on display :0..."
Xvfb :0 -screen 0 "${RESOLUTION}x24" -ac +extension GLX +render -noreset &
export DISPLAY=:0

# Wait for X server to initialize
for i in $(seq 1 30); do
    if xdpyinfo -display :0 >/dev/null 2>&1; then
        echo "✅ Xvfb display :0 is ready!"
        break
    fi
    sleep 0.5
done

# 2. Start Openbox Window Manager
echo "Starting Openbox..."
openbox &

# 3. Start x11vnc server
echo "Starting x11vnc on port 5900..."
x11vnc -display :0 -forever -shared -nopw -rfbport 5900 -listen 127.0.0.1 -noxdamage -bg

# 4. Configure noVNC index.html to auto-connect instantly
mkdir -p /usr/share/novnc
cat << 'EOF' > /usr/share/novnc/index.html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Cloud Chrome | Voroa Server</title>
    <meta http-equiv="refresh" content="0; url=vnc.html?autoconnect=true&resize=remote&reconnect=true">
    <style>
        body { background: #0f172a; color: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    </style>
</head>
<body>
    <p>⚡ Connecting to Cloud Chrome Desktop...</p>
</body>
</html>
EOF

# 5. Start websockify on $PORT bridging to VNC
echo "Starting websockify on port ${PORT}..."
websockify --web /usr/share/novnc ${PORT} 127.0.0.1:5900 &

# 6. Launch Chromium with auto-restart loop
mkdir -p /data/chrome-profile
(
    while true; do
        echo "Launching Chromium browser..."
        chromium \
            --no-sandbox \
            --disable-dev-shm-usage \
            --disable-gpu \
            --user-data-dir=/data/chrome-profile \
            --window-size=1280,800 \
            --window-position=0,0 \
            --start-maximized \
            --no-first-run \
            --no-default-browser-check \
            --password-store=basic \
            "https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkminghmkfjojehanbpfageekm" \
            "https://raxi1.com/#/" || true
        echo "Chromium exited. Relaunching in 2 seconds..."
        sleep 2
    done
) &

# Keep container running 24/7
echo "✅ Cloud Chrome running 24/7 on port ${PORT}!"
exec tail -f /dev/null
