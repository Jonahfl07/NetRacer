"""Tunable numbers for the game, kept in one place."""

TRACK_MARGIN = 50       # gap between the window edge and the track, in pixels
CAR_SIZE = 20           # cars are drawn as CAR_SIZE x CAR_SIZE squares
MOVE_STEP = 5           # pixels a car moves per frame at normal speed
FRAME_MS = 5            # delay between animation frames

DRAWING_SIZE = 700
WINDOW_SIZE = 750

STARTING_RAM = 12
MAX_RAM = 12
RAM_RECHARGE_RATE = 0.2  # RAM regained per second

MAX_STACK_SIZE = 6
COUNTDOWN_SECONDS = 5    # quiet time before the stack starts resolving
RESOLVE_STEP_MS = 1000   # delay between resolving each stack item

DEFAULT_LAPS = 10
DEFAULT_PORT = 5000
