#!/bin/bash
# Double-click to host a game for a friend on another computer.
cd "$(dirname "$0")" || exit 1
echo "Waiting for your friend to join on port 5000..."
python3 main.py
