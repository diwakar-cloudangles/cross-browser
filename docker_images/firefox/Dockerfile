# Dockerfile for Firefox

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Step 1: Install base dependencies, VNC components, and PPA tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    software-properties-common \
    xvfb \
    x11vnc \
    openbox \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Step 2: Add Mozilla PPA and install Firefox
# This process ensures we install the traditional DEB package, not the Snap
RUN add-apt-repository -y ppa:mozillateam/ppa \
    && echo 'Package: *' > /etc/apt/preferences.d/mozilla-firefox \
    && echo 'Pin: release o=LP-PPA-mozillateam' >> /etc/apt/preferences.d/mozilla-firefox \
    && echo 'Pin-Priority: 1001' >> /etc/apt/preferences.d/mozilla-firefox \
    && apt-get update \
    && apt-get install -y firefox \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Set up VNC password
RUN mkdir -p /root/.vnc \
    && x11vnc -storepasswd "password" /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd

# Step 4: Copy Supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the VNC port
EXPOSE 5900

# Run Supervisor to start all services
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]