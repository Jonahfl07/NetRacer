"""Tunable numbers for the game, kept in one place."""

# Window and track layout (pixels)
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 690
TRACK_WIDTH = 440
TRACK_HEIGHT = 480
TRACK_MARGIN = 50       # gap between the track edge and the cars' racing line
CAR_SIZE = 20           # cars are drawn as CAR_SIZE x CAR_SIZE circles
CAR_DRAW_OFFSET = 14    # the opponent is drawn slightly offset so cars never hide each other

# Colours: you are blue, your opponent is orange (cars and stack entries)
MY_COLOUR = "#6cb4ff"
OPPONENT_COLOUR = "#ff9933"

# Movement
MOVE_STEP = 3           # pixels a car moves per frame at normal speed
FRAME_MS = 5            # delay between animation frames

# RAM
STARTING_RAM = 12
MAX_RAM = 12
RAM_RECHARGE_RATE = 0.2  # RAM regained per second

# The action stack
MAX_STACK_SIZE = 6
COUNTDOWN_SECONDS = 5    # quiet time before the stack starts resolving
RESOLVE_STEP_MS = 1000   # delay between resolving each stack item

DEFAULT_LAPS = 10
DEFAULT_PORT = 5000
