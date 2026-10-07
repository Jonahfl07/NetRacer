"""The game window, laid out like the design in the project report.

    RAM bar
    Stack: the actions waiting to resolve, next one on the left
    [boost buttons]  [track]  [hack buttons]

Buttons and bars are drawn on canvases rather than using native buttons,
because macOS ignores custom button colours.
"""

import math
import time

from guizero import Box, Text

import config
from boosts import BOOSTS
from car import Car
from vote import VoteScreen
from widgets import (BACKGROUND, BOOST_GREEN, DARK, DISABLED_TEXT, FONT, HACK_RED, PURPLE,
                     CanvasButton, make_canvas, rounded_rect)


RAM_BAR_WIDTH = 600
RAM_BAR_HEIGHT = 36
RAM_BAR_SLANT = 22      # how far the top edge is pushed right, like a Pokemon HP bar
DOT_CYCLE_SECONDS = 1.4  # one left-to-right pulse of the three dots
STACK_WIDTH = 920
STACK_HEIGHT = 90
CHIP_WIDTH = 118
ARROW_GAP = 34
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 110

BOOST_BUTTONS = [0, 1, 2]  # Nitro, Firewall, Hyperthreading: down the left
HACK_BUTTONS = [3, 4]      # System Shutdown, Spike Deployment: down the right


class Gui:
    def __init__(self, app, game, my_car_image=None, opponent_car_image=None):
        self.app = app
        self.game = game
        self.result_box = None
        app.bg = BACKGROUND

        # The race screen and the result screen take turns filling the one window.
        self.game_box = Box(app, width="fill", height="fill")
        self.ram_drawing = make_canvas(self.game_box, RAM_BAR_WIDTH, RAM_BAR_HEIGHT)
        self.stack_drawing = make_canvas(self.game_box, STACK_WIDTH, STACK_HEIGHT)
        self.status_text = Text(self.game_box, text="", size=13, color=DARK)

        middle = Box(self.game_box, layout="grid")
        left = Box(middle, grid=[0, 0])
        self.track = make_canvas(middle, config.TRACK_WIDTH, config.TRACK_HEIGHT, grid=[1, 0])
        right = Box(middle, grid=[2, 0])
        self.laps_text = Text(self.game_box, text="", size=15, color=DARK)

        self.buttons = {}
        for index in BOOST_BUTTONS:
            self.buttons[index] = self._make_button(left, index, BOOST_GREEN)
        # Two hacks beside three boosts: pad the top so they sit centred.
        Box(right, width=1, height=BUTTON_HEIGHT // 2)
        for index in HACK_BUTTONS:
            self.buttons[index] = self._make_button(right, index, HACK_RED)

        self._draw_track()
        self.my_car = Car(self.track, game.me, config.MY_COLOUR, 0, my_car_image)
        self.opponent_car = Car(self.track, game.opponent, config.OPPONENT_COLOUR,
                                config.CAR_DRAW_OFFSET, opponent_car_image)

        # Without --laps, the race opens with a vote on its length.
        self.vote = None
        if not game.started:
            self.game_box.hide()
            self.vote = VoteScreen(app, game, self._vote_finished)

        app.repeat(config.FRAME_MS, self._frame)
        app.repeat(1000, self._recharge)
        app.repeat(100, self._refresh)
        app.repeat(50, self._animate)
        self._refresh()

    def _make_button(self, parent, index, colour):
        boost = BOOSTS[index]
        return CanvasButton(
            parent, f"{boost.name.upper()} [{boost.cost}]", colour,
            lambda: self.game.cast(index), BUTTON_WIDTH, BUTTON_HEIGHT,
        )

    # Frame loop

    def _frame(self):
        game = self.game
        game.process_inbox()
        if not game.started:
            return
        if game.rematch_ready():
            self._start_rematch()
            return
        if game.winner:
            return
        game.tick()
        lapped = self.my_car.move(config.TRACK_WIDTH, config.TRACK_HEIGHT)
        lapped |= self.opponent_car.move(config.TRACK_WIDTH, config.TRACK_HEIGHT)
        if lapped:
            game.record_lap(self.my_car.laps, self.opponent_car.laps)
            if game.winner:
                self._show_result()

    def _animate(self):
        # The pulsing dots need redrawing faster than the 100 ms refresh.
        if not self.game.winner:
            self._draw_stack()

    def _vote_finished(self):
        self.game.finish_vote()
        self.game_box.show()

    def _recharge(self):
        if self.game.started and not self.game.winner:
            self.game.me.recharge()
            self.game.opponent.recharge()

    def _refresh(self):
        game = self.game
        self._draw_ram()
        self._draw_stack()
        self.laps_text.value = (
            f"Your laps: {self.my_car.laps}/{game.max_laps or '?'}"
            f"        Opponent laps: {self.opponent_car.laps}/{game.max_laps or '?'}"
        )
        self.status_text.value = self._status_message()
        for index, button in self.buttons.items():
            button.set_enabled(game.can_cast(index))
        if self.result_box:
            self._refresh_result()

    def _status_message(self):
        game = self.game
        if game.opponent_left:
            return "Your opponent has disconnected"
        if game.resolving:
            return "Resolving the stack... controls are locked"
        remaining = game.seconds_until_resolve()
        if remaining is not None:
            return f"Resolving in {remaining:.0f}s: you can still respond"
        if game.opponent.firewall_active:
            return "Opponent's firewall is up: your hacks are blocked"
        return "Cast a boost or a hack: each one starts a 5 second countdown"

    # Drawing

    def _draw_track(self):
        canvas = self.track.tk
        w, h, m = config.TRACK_WIDTH, config.TRACK_HEIGHT, config.TRACK_MARGIN
        rounded_rect(canvas, 2, 2, w - 2, h - 2, radius=14, fill="white", outline=DARK, width=2)
        half = config.CAR_SIZE / 2 + config.CAR_DRAW_OFFSET / 2
        canvas.create_rectangle(m + half, m + half, w - m - half, h - m - half,
                                outline="#c9c9d6", dash=(6, 6), width=2)
        canvas.create_text(m + half + 8, m + half - 20, text="START", anchor="w",
                           font=(FONT, 10, "bold"), fill="#8a8a9c")

    def _draw_ram(self):
        canvas = self.ram_drawing.tk
        canvas.delete("all")
        me = self.game.me
        width, height, slant = RAM_BAR_WIDTH, RAM_BAR_HEIGHT, RAM_BAR_SLANT
        canvas.create_polygon(
            2 + slant, 2, width - 2, 2, width - 2 - slant, height - 2, 2, height - 2,
            fill="white", outline=DARK, width=2, joinstyle="round")
        length = width - 10 - slant
        filled = length * me.ram / me.max_ram
        if filled > 0:
            canvas.create_polygon(
                5 + slant, 5, 5 + slant + filled, 5, 5 + filled, height - 5, 5, height - 5,
                fill=PURPLE, outline="")
        canvas.create_text((width + slant) / 2, height / 2,
                           text=f"RAM: {int(me.ram)}/{me.max_ram}",
                           font=(FONT, 14, "bold"), fill=DARK)

    def _draw_stack(self):
        canvas = self.stack_drawing.tk
        canvas.delete("all")
        rounded_rect(canvas, 2, 2, STACK_WIDTH - 2, STACK_HEIGHT - 2, radius=14,
                     fill="white", outline=DARK, width=2)
        stack = self.game.stack
        items = stack.items()  # oldest on the left; new actions join on the right and resolve first
        if not items:
            canvas.create_text(STACK_WIDTH / 2, STACK_HEIGHT / 2, text="Stack is empty",
                               font=(FONT, 14), fill=DISABLED_TEXT)
            return
        x = 20
        for position, action in enumerate(items):
            colour = config.MY_COLOUR if action.owner == self.game.my_id else config.OPPONENT_COLOUR
            rounded_rect(canvas, x, 18, x + CHIP_WIDTH, STACK_HEIGHT - 18, radius=10,
                         fill=colour, outline=DARK, width=2)
            canvas.create_text(x + CHIP_WIDTH / 2, STACK_HEIGHT / 2,
                               text=BOOSTS[action.boost].name.upper(), justify="center",
                               width=CHIP_WIDTH - 12, font=(FONT, 11, "bold"), fill=DARK)
            x += CHIP_WIDTH
            if position < len(items) - 1:
                self._draw_arrow(canvas, x + 5)
                x += ARROW_GAP
            elif len(items) < stack.max_size:
                self._draw_dots(canvas, x + 14)

    def _draw_arrow(self, canvas, x):
        mid = STACK_HEIGHT / 2
        canvas.create_polygon(
            x + 24, mid - 6, x + 10, mid - 6, x + 10, mid - 12, x, mid,
            x + 10, mid + 12, x + 10, mid + 6, x + 24, mid + 6,
            fill="#dfe3e8", outline=DARK, width=2)

    def _draw_dots(self, canvas, x):
        # Three dots that swell one after another, left to right, as a "your move" signal.
        mid = STACK_HEIGHT / 2
        phase = (time.time() / DOT_CYCLE_SECONDS) % 1
        for number, (radius, offset) in enumerate(((4, 0), (7, 18), (11, 40))):
            since = (phase - number * 0.2) % 1
            pulse = math.sin(math.pi * since / 0.4) if since < 0.4 else 0
            size = radius * (1 + 0.6 * pulse)
            canvas.create_oval(x + offset - size, mid - size, x + offset + size, mid + size,
                               fill=PURPLE if pulse > 0.5 else "white", outline=DARK, width=2)

    # End of race

    def _show_result(self):
        winner = self.game.winner
        headline = {"me": "Congratulations: You won!",
                    "opponent": "Good effort: Your opponent won!",
                    "tie": "Photo finish: It's a tie!"}[winner]
        self.game_box.hide()
        box = Box(self.app, width="fill", height="fill")
        Box(box, width=1, height=150)
        banner = make_canvas(box, 640, 190)
        canvas = banner.tk
        rounded_rect(canvas, 4, 12, 636, 178, radius=16, fill="white", outline=DARK, width=2)
        canvas.create_text(320, 70, text=headline, width=590, justify="center",
                           font=(FONT, 32, "bold"), fill=DARK)
        canvas.create_text(320, 135, justify="center", font=(FONT, 14), fill=DARK,
                           text=(f"Final laps: you {self.my_car.laps}/{self.game.max_laps}, "
                                 f"opponent {self.opponent_car.laps}/{self.game.max_laps}"))
        row = Box(box, layout="grid")
        self.rematch_button = CanvasButton(row, "REMATCH", BOOST_GREEN, self._rematch_clicked,
                                           290, 110, font_size=22, grid=[0, 0])
        CanvasButton(row, "QUIT", HACK_RED, self.app.destroy, 290, 110, font_size=22, grid=[1, 0])
        self.result_status = Text(box, text="", size=15, color=DARK)
        self.result_box = box
        self._refresh_result()

    def _rematch_clicked(self):
        self.game.request_rematch()
        self._refresh_result()

    def _refresh_result(self):
        game = self.game
        if game.opponent_left:
            message, can_click = "Your opponent has left, so there's no rematch", False
        elif game.i_want_rematch:
            message, can_click = "Waiting for your opponent to accept...", False
        elif game.opponent_wants_rematch:
            message, can_click = "Your opponent wants a rematch!", True
        else:
            message, can_click = "", True
        self.result_status.value = message
        self.rematch_button.set_enabled(can_click)

    def _start_rematch(self):
        self.game.start_rematch()
        self.my_car.reset()
        self.opponent_car.reset()
        if self.result_box:
            self.result_box.destroy()
            self.result_box = None
            self.game_box.show()
        self._refresh()
