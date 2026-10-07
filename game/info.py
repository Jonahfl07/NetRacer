"""The "how to play" page shown before a game starts."""

from guizero import App, Box, Text

import config
from boosts import BOOSTS
from gui import BACKGROUND, BOOST_GREEN, DARK, FONT, HACK_RED, CanvasButton, make_canvas, rounded_rect

INTRO = [
    f"Every boost or hack you cast goes on a shared stack and restarts a {config.COUNTDOWN_SECONDS} second countdown.",
    "When it runs out, the stack resolves last in, first out. Casting costs RAM, which slowly recharges.",
]
CARD_WIDTH = 880
CARD_HEIGHT = 74


def _draw_card(parent, boost):
    drawing = make_canvas(parent, CARD_WIDTH, CARD_HEIGHT + 8)
    canvas = drawing.tk
    colour = HACK_RED if boost.is_hack else BOOST_GREEN
    rounded_rect(canvas, 4, 4, CARD_WIDTH - 4, CARD_HEIGHT, radius=12,
                 fill=colour, outline=DARK, width=2)
    kind = "HACK" if boost.is_hack else "BOOST"
    canvas.create_text(20, 24, anchor="w", text=f"{boost.name.upper()}   [{boost.cost} RAM]",
                       font=(FONT, 14, "bold"), fill=DARK)
    canvas.create_text(CARD_WIDTH - 20, 24, anchor="e", text=kind,
                       font=(FONT, 11, "bold"), fill=DARK)
    canvas.create_text(20, 52, anchor="w", width=CARD_WIDTH - 40, text=boost.description,
                       font=(FONT, 12), fill=DARK)


def show_info():
    """Show the page; return True if the player pressed Start, False if they closed it."""
    app = App("NetRacer: how to play", width=config.WINDOW_WIDTH, height=config.WINDOW_HEIGHT,
              bg=BACKGROUND)
    Text(app, text="How to play", size=26, font=FONT, color=DARK)
    for line in INTRO:
        Text(app, text=line, size=13, font=FONT, color=DARK)
    Box(app, width=1, height=8)
    for boost in BOOSTS:
        _draw_card(app, boost)
    started = []

    def start():
        started.append(True)
        app.destroy()

    row = Box(app)
    CanvasButton(row, "START", BOOST_GREEN, start, 260, 90, font_size=20)
    app.display()
    return bool(started)
