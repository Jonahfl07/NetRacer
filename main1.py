"""Player 2: joins the game started by main.py.

    python main1.py [HOST[:PORT]] [--laps N]

With no address it joins a game on this machine.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "game"))

import cli

if __name__ == "__main__":
    rest = sys.argv[1:]
    if not rest or rest[0].startswith("-"):
        rest.insert(0, "127.0.0.1")
    sys.argv[1:] = ["join"] + rest
    cli.main()
