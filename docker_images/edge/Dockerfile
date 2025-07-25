FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for x11vnc
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    x11vnc \
    openbox \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Add and install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# --- x11vnc Setup ---
RUN mkdir -p /etc/x11vnc \
    && x11vnc -storepasswd "password" /etc/x11vnc/vncpwd \
    && chmod 644 /etc/x11vnc/vncpwd

# Supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5900
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]