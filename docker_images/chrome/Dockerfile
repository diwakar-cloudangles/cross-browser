FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Step 1: Install all prerequisite packages, but not Chrome itself yet.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    tigervnc-standalone-server \
    openbox \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Step 2: Add the official Google Chrome repository to the system.
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Step 3: Now that the system knows where to find Chrome, update and install it.
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# --- TigerVNC Setup ---
# 1. Create the password file
RUN mkdir -p /root/.vnc \
    && echo "password" | vncpasswd -f > /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd

# 2. Create the required .Xauthority file
RUN touch /root/.Xauthority && chmod 600 /root/.Xauthority

# 3. Create the xstartup script that TigerVNC will run to start the desktop
RUN echo "#!/bin/sh\n\
unset SESSION_MANAGER\n\
unset DBUS_SESSION_BUS_ADDRESS\n\
/usr/bin/openbox-session\n\
" > /root/.vnc/xstartup && chmod 755 /root/.vnc/xstartup
# --- End TigerVNC Setup ---

# Supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5900

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]