#!/bin/bash
# Double-click to join a friend's game: type their address when asked.
cd "$(dirname "$0")" || exit 1
read -r -p "Host address (e.g. 192.168.1.20 or 100.x.y.z): " ADDRESS
python3 main1.py "$ADDRESS"
