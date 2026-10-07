#!/bin/bash
# Double-click to start a host and a second player on this Mac.
cd "$(dirname "$0")" || exit 1
PORT=5050
python3 main.py --port $PORT &
HOST_PID=$!
sleep 2
python3 main1.py localhost:$PORT
kill $HOST_PID 2>/dev/null
