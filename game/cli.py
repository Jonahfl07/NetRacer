"""Start a two-player game.

    python main.py                         # host: wait for an opponent on port 5000
    python main1.py                        # join a game on this machine
    python main1.py 192.168.1.20           # join a game hosted on another machine
"""

import argparse

from guizero import App

import config
from game_manager import GameManager
from gui import Gui
from network import PeerConnection
from player import Player

def parse_args():
    parser = argparse.ArgumentParser(description="Two-player networked hacker racing game.")
    modes = parser.add_subparsers(dest="mode", required=True)

    host = modes.add_parser("host", help="wait for an opponent to join")
    host.add_argument("--port", type=int, default=config.DEFAULT_PORT)

    join = modes.add_parser("join", help="join a hosted game")
    join.add_argument("address", help="host machine, as HOST or HOST:PORT")

    for sub in (host, join):
        sub.add_argument("--laps", type=int, default=config.DEFAULT_LAPS,
                         help="laps needed to win (both players should use the same value)")
        sub.add_argument("--car", help="optional image for your car (default: a blue circle)")
        sub.add_argument("--opponent-car",
                         help="optional image for your opponent's car (default: an orange circle)")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.mode == "host":
        my_id = "host"
        connection = PeerConnection.host(args.port)
    else:
        my_id = "guest"
        address, _, port = args.address.partition(":")
        connection = PeerConnection.join(address, int(port or config.DEFAULT_PORT))

    app = App("Hack Racer", width=config.WINDOW_WIDTH, height=config.WINDOW_HEIGHT)
    me = Player("You", config.MY_COLOUR)
    opponent = Player("Your opponent", config.OPPONENT_COLOUR)
    game = GameManager(my_id, me, opponent, connection, args.laps, schedule=app.after)
    connection.start_receiving(game.receive, game.peer_disconnected)
    Gui(app, game, args.car, args.opponent_car)
    try:
        app.display()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
