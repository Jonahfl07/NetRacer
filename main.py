"""Player 1: hosts the game. Start this first, then run main1.py.

    python main.py [--laps N] [--port PORT]
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "game"))

import cli

if __name__ == "__main__":
    sys.argv.insert(1, "host")
    cli.main()
