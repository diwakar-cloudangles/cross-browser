#!/bin/bash

# Start virtual display
Xvfb :0 -screen 0 1280x720x24 &

# Wait for Xvfb
sleep 2

# Start the window manager
startlxde &

# Start Chrome
google-chrome --no-sandbox --disable-dev-shm-usage --start-maximized --display=:0 &

# Start VNC server
x11vnc -display :0 -forever -passwd password -rfbport 5900 -shared
