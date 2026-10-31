FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8000
ENV DISPLAY=:0
ENV RESOLUTION=1280x800

# Install Chromium, Xvfb, x11vnc, openbox, noVNC, websockify, and required fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    xvfb \
    x11vnc \
    openbox \
    novnc \
    websockify \
    x11-utils \
    ca-certificates \
    curl \
    procps \
    fonts-dejavu \
    fonts-freefont-ttf \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY entrypoint.sh .
COPY raxi_autobet.user.js /data/raxi_autobet.user.js
RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
