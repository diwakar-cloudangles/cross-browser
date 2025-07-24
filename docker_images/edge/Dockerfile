FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install VNC, Openbox, Supervisor, and dependencies for Edge
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    tigervnc-standalone-server \
    openbox \
    xterm \
    supervisor \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# --- Microsoft Edge Installation ---
# Add Microsoft GPG key and repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
    && install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ \
    && sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list' \
    && rm microsoft.gpg

# Install Edge
RUN apt-get update && apt-get install -y microsoft-edge-stable
# --- End Edge Installation ---

# --- TigerVNC Setup ---
RUN mkdir -p /root/.vnc \
    && echo "password" | vncpasswd -f > /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd

RUN touch /root/.Xauthority && chmod 600 /root/.Xauthority

# Create xstartup script to launch Edge
RUN echo "#!/bin/sh\n\
unset SESSION_MANAGER\n\
unset DBUS_SESSION_BUS_ADDRESS\n\
/usr/bin/openbox-session &\n\
/usr/bin/microsoft-edge-stable --no-sandbox --disable-gpu\n\
" > /root/.vnc/xstartup && chmod 755 /root/.vnc/xstartup
# --- End TigerVNC Setup ---

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5900

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]