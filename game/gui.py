"""The game window, laid out like the design in the project report.

    RAM bar
    Stack: the actions waiting to resolve, next one on the left
    [boost buttons]  [track]  [hack buttons]

Buttons and bars are drawn on canvases rather than using native buttons,
because macOS ignores custom button colours.
"""

from guizero import Box, Drawing, Text, Window

import config
from boosts import BOOSTS
from car import Car

BACKGROUND = "#dedfff"
DARK = "#2b2b3b"
PURPLE = "#9494ff"
BOOST_GREEN = "#c2f5c9"
HACK_RED = "#ff6b6b"
DISABLED = "#cfd0e0"
DISABLED_TEXT = "#8a8a9c"
FONT = "Helvetica"

RAM_BAR_WIDTH = 600
RAM_BAR_HEIGHT = 36
STACK_WIDTH = 920
STACK_HEIGHT = 90
CHIP_WIDTH = 118
ARROW_GAP = 34
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 110

BOOST_BUTTONS = [0, 1, 2]  # Nitro, Firewall, Hyperthreading: down the left
HACK_BUTTONS = [3, 4]      # System Shutdown, Spike Deployment: down the right


def rounded_rect(canvas, x1, y1, x2, y2, radius=12, **options):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **options)


def make_canvas(parent, width, height, **layout):
    drawing = Drawing(parent, width=width, height=height, **layout)
    drawing.tk.config(bg=BACKGROUND, highlightthickness=0, bd=0)
    return drawing


class CanvasButton:
    """A clickable rounded rectangle that can be greyed out."""

    def __init__(self, parent, text, colour, command, width, height, font_size=13, **layout):
        self.text = text
        self.colour = colour
        self.command = command
        self.width = width
        self.height = height
        self.font_size = font_size
        self.enabled = True
        self.drawing = make_canvas(parent, width, height, **layout)
        self.canvas = self.drawing.tk
        self.drawing.when_clicked = lambda event: self._clicked()
        self._draw()

    def set_enabled(self, enabled):
        if enabled != self.enabled:
            self.enabled = enabled
            self._draw()

    def _clicked(self):
        if self.enabled:
            self.command()

    def _draw(self):
        canvas = self.canvas
        canvas.delete("all")
        canvas.config(cursor="hand2" if self.enabled else "arrow")
        fill = self.colour if self.enabled else DISABLED
        rounded_rect(canvas, 8, 8, self.width - 8, self.height - 8, radius=12,
                     fill=fill, outline=DARK if self.enabled else DISABLED_TEXT, width=2)
        canvas.create_text(
            self.width / 2, self.height / 2, text=self.text, justify="center",
            width=self.width - 24, font=(FONT, self.font_size, "bold"),
            fill=DARK if self.enabled else DISABLED_TEXT,
        )


class Gui:
    def __init__(self, app, game, my_car_image=None, opponent_car_image=None):
        self.app = app
        self.game = game
        self.result_window = None
        app.bg = BACKGROUND

        self.ram_drawing = make_canvas(app, RAM_BAR_WIDTH, RAM_BAR_HEIGHT)
        self.stack_drawing = make_canvas(app, STACK_WIDTH, STACK_HEIGHT)
        self.status_text = Text(app, text="", size=13, color=DARK)

        middle = Box(app, layout="grid")
        left = Box(middle, grid=[0, 0])
        self.track = make_canvas(middle, config.TRACK_WIDTH, config.TRACK_HEIGHT, grid=[1, 0])
        right = Box(middle, grid=[2, 0])
        self.laps_text = Text(app, text="", size=15, color=DARK)

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

        app.repeat(config.FRAME_MS, self._frame)
        app.repeat(1000, self._recharge)
        app.repeat(100, self._refresh)
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

    def _recharge(self):
        if not self.game.winner:
            self.game.me.recharge()
            self.game.opponent.recharge()

    def _refresh(self):
        game = self.game
        self._draw_ram()
        self._draw_stack()
        self.laps_text.value = (
            f"Your laps: {self.my_car.laps}/{game.max_laps}"
            f"        Opponent laps: {self.opponent_car.laps}/{game.max_laps}"
        )
        self.status_text.value = self._status_message()
        for index, button in self.buttons.items():
            button.set_enabled(game.can_cast(index))
        if self.result_window:
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
            return "Opponent's firewall is up: you can't cast"
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
        rounded_rect(canvas, 2, 2, RAM_BAR_WIDTH - 2, RAM_BAR_HEIGHT - 2, radius=10,
                     fill="white", outline=DARK, width=2)
        fill_width = (RAM_BAR_WIDTH - 10) * me.ram / me.max_ram
        if fill_width >= 20:
            rounded_rect(canvas, 5, 5, 5 + fill_width, RAM_BAR_HEIGHT - 5, radius=8,
                         fill=PURPLE, outline="")
        elif fill_width > 0:
            canvas.create_rectangle(5, 5, 5 + fill_width, RAM_BAR_HEIGHT - 5,
                                    fill=PURPLE, outline="")
        canvas.create_text(RAM_BAR_WIDTH / 2, RAM_BAR_HEIGHT / 2,
                           text=f"RAM: {int(me.ram)}/{me.max_ram}",
                           font=(FONT, 14, "bold"), fill=DARK)

    def _draw_stack(self):
        canvas = self.stack_drawing.tk
        canvas.delete("all")
        rounded_rect(canvas, 2, 2, STACK_WIDTH - 2, STACK_HEIGHT - 2, radius=14,
                     fill="white", outline=DARK, width=2)
        stack = self.game.stack
        items = list(reversed(stack.items()))  # next to resolve first, so leftmost
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
            x, mid - 6, x + 14, mid - 6, x + 14, mid - 12, x + 24, mid,
            x + 14, mid + 12, x + 14, mid + 6, x, mid + 6,
            fill="#dfe3e8", outline=DARK, width=2)

    def _draw_dots(self, canvas, x):
        mid = STACK_HEIGHT / 2
        for radius, offset in ((4, 0), (7, 18), (11, 40)):
            canvas.create_oval(x + offset - radius, mid - radius, x + offset + radius,
                               mid + radius, fill="white", outline=DARK, width=2)

    # End of race

    def _show_result(self):
        winner = self.game.winner
        headline = {"me": "Congratulations: You won!",
                    "opponent": "Good effort: Your opponent won!",
                    "tie": "Photo finish: It's a tie!"}[winner]
        window = Window(self.app, title="Race over", width=520, height=340, bg=BACKGROUND)
        window.when_closed = self.app.destroy
        banner = make_canvas(window, 480, 130)
        canvas = banner.tk
        rounded_rect(canvas, 4, 12, 476, 118, radius=12, fill="white", outline=DARK, width=2)
        canvas.create_text(240, 65, text=headline, width=440, justify="center",
                           font=(FONT, 22, "bold"), fill=DARK)
        row = Box(window, layout="grid")
        self.rematch_button = CanvasButton(row, "REMATCH", BOOST_GREEN, self._rematch_clicked,
                                           230, 90, font_size=18, grid=[0, 0])
        CanvasButton(row, "QUIT", HACK_RED, self.app.destroy, 230, 90, font_size=18, grid=[1, 0])
        self.result_status = Text(window, text="", size=13, color=DARK)
        self.result_window = window
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
        if self.result_window:
            self.result_window.when_closed = None
            self.result_window.destroy()
            self.result_window = None
        self._refresh()
